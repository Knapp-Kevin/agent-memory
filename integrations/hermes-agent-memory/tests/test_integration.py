from __future__ import annotations

from contextlib import redirect_stdout
import importlib.metadata
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from agent_memory_hermes import HERMES_COMMIT, MUTATION_SURFACES, STRICT_BLOCKERS
from agent_memory_hermes.cli import main as cli_main
from agent_memory_hermes.config import IntegrationConfig, save_config
from agent_memory_hermes.coverage import build_coverage_report
from agent_memory_hermes.plugin import HermesPluginRuntime, _clear_runtime_cache_for_tests
from agent_memory_hermes.provider import AgentMemoryProvider, register_memory
from agent_memory_hermes.safe_plugin import register as register_plugin
from agent_memory_hermes import safe_plugin

HERE = Path(__file__).resolve().parent
FAKE_GOVERNOR = HERE / "fake_governor.py"


class FakePluginContext:
    def __init__(self) -> None:
        self.hooks: dict[str, object] = {}
        self.provider_factory = None

    def register_hook(self, event: str, callback) -> None:
        self.hooks[event] = callback

    def register_memory_provider(self, factory) -> None:
        self.provider_factory = factory


class HermesIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._old_env = dict(os.environ)
        _clear_runtime_cache_for_tests()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old_env)
        _clear_runtime_cache_for_tests()

    def governor_command(self, decision: str, capture: Path | None = None) -> tuple[str, ...]:
        return (
            sys.executable,
            str(FAKE_GOVERNOR),
            decision,
            str(capture) if capture is not None else "",
        )

    def test_package_publishes_both_supported_hermes_entry_points(self) -> None:
        plugin_eps = {
            ep.name: ep.value for ep in importlib.metadata.entry_points(group="hermes_agent.plugins")
        }
        provider_eps = {
            ep.name: ep.value
            for ep in importlib.metadata.entry_points(group="hermes_agent.memory_providers")
        }
        self.assertEqual(plugin_eps.get("agent-memory"), "agent_memory_hermes.safe_plugin:register")
        self.assertEqual(provider_eps.get("agent-memory"), "agent_memory_hermes.provider:register_memory")

    def test_registers_pre_post_hooks_and_memory_provider(self) -> None:
        ctx = FakePluginContext()
        register_plugin(ctx)
        register_memory(ctx)
        self.assertIn("pre_tool_call", ctx.hooks)
        self.assertIn("post_tool_call", ctx.hooks)
        self.assertIsNotNone(ctx.provider_factory)
        provider = ctx.provider_factory()
        self.assertIsInstance(provider, AgentMemoryProvider)
        self.assertEqual(provider.name, "agent-memory")

    def test_observe_records_memory_and_skill_proposals_without_raw_payloads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = IntegrationConfig(mode="observe")
            runtime = HermesPluginRuntime(tmp, config=config, observed_hermes_revision=HERMES_COMMIT)
            self.assertIsNone(
                runtime.on_pre_tool_call(
                    tool_name="memory",
                    args={"action": "add", "target": "memory", "content": "secret-value"},
                    session_id="s1",
                    tool_call_id="m1",
                )
            )
            self.assertIsNone(
                runtime.on_pre_tool_call(
                    tool_name="skill_manage",
                    args={"action": "create", "name": "learned-skill", "content": "procedure"},
                    session_id="s1",
                    tool_call_id="k1",
                )
            )
            runtime.on_post_tool_call(
                tool_name="memory",
                args={"action": "add", "target": "memory", "content": "secret-value"},
                result="Memory added successfully",
                session_id="s1",
                tool_call_id="m1",
                status="completed",
            )
            events = [json.loads(line) for line in runtime.store.path.read_text().splitlines()]
            proposals = [item for item in events if item["event_type"] == "durable_tool_proposal"]
            receipts = [item for item in events if item["event_type"] == "durable_tool_execution_receipt"]
            self.assertEqual(len(proposals), 2)
            self.assertEqual(len(receipts), 1)
            self.assertTrue(all(item["metadata"]["origin_hint"] == "unknown_model_tool" for item in proposals))
            self.assertTrue(all(item["payload_recorded"] is False for item in events))
            self.assertNotIn("secret-value", runtime.store.path.read_text())
            self.assertTrue(receipts[0]["metadata"]["admission_is_not_execution"])

    def test_govern_allow_preserves_lineage_for_external_governor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture = Path(tmp) / "candidate.json"
            config = IntegrationConfig(
                mode="govern",
                governor_command=self.governor_command("allow", capture),
                governor_required=True,
            )
            runtime = HermesPluginRuntime(tmp, config=config, observed_hermes_revision=HERMES_COMMIT)
            result = runtime.on_pre_tool_call(
                tool_name="skill_manage",
                args={
                    "action": "patch",
                    "name": "skill-d",
                    "lineage_refs": ["experience:A", "skill:B", "observation:C"],
                    "provenance_refs": ["session://recursive-learning/1"],
                },
                session_id="recursive-session",
                tool_call_id="recursive-call",
            )
            self.assertIsNone(result)
            candidate = json.loads(capture.read_text())
            self.assertEqual(candidate["lineage_refs"], ["experience:A", "skill:B", "observation:C"])
            self.assertEqual(candidate["provenance_refs"], ["session://recursive-learning/1"])
            self.assertEqual(candidate["authority_effect"], "none")

    def test_external_governor_can_reject_self_reinforcing_or_corrected_reproposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capture = Path(tmp) / "candidate.json"
            config = IntegrationConfig(
                mode="govern",
                governor_command=self.governor_command("reject", capture),
                governor_required=True,
            )
            runtime = HermesPluginRuntime(tmp, config=config, observed_hermes_revision=HERMES_COMMIT)
            blocked = runtime.on_pre_tool_call(
                tool_name="memory",
                args={
                    "action": "add",
                    "target": "memory",
                    "content": "old corrected value X",
                    "lineage_refs": ["experience:A", "skill:B", "skill:B-output:C"],
                    "provenance_refs": ["superseded://value-X", "current://value-Y"],
                },
                session_id="background-like-session",
                tool_call_id="reproposal",
            )
            self.assertEqual(blocked["action"], "block")
            candidate = json.loads(capture.read_text())
            self.assertIn("superseded://value-X", candidate["provenance_refs"])
            self.assertIn("skill:B-output:C", candidate["lineage_refs"])

    def test_required_governor_unavailable_or_invalid_fails_closed(self) -> None:
        for decision in ("exit-failure", "invalid-json", "invalid-decision"):
            with self.subTest(decision=decision), tempfile.TemporaryDirectory() as tmp:
                config = IntegrationConfig(
                    mode="govern",
                    governor_command=self.governor_command(decision),
                    governor_required=True,
                )
                runtime = HermesPluginRuntime(tmp, config=config, observed_hermes_revision=HERMES_COMMIT)
                blocked = runtime.on_pre_tool_call(
                    tool_name="memory",
                    args={"action": "add", "target": "memory", "content": "candidate"},
                    tool_call_id=decision,
                )
                self.assertEqual(blocked["action"], "block")

    def test_stage_is_blocked_instead_of_faking_native_hermes_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = IntegrationConfig(
                mode="govern",
                governor_command=self.governor_command("stage"),
                governor_required=True,
            )
            runtime = HermesPluginRuntime(tmp, config=config, observed_hermes_revision=HERMES_COMMIT)
            blocked = runtime.on_pre_tool_call(
                tool_name="skill_manage",
                args={"action": "edit", "name": "skill-x"},
                tool_call_id="stage-call",
            )
            self.assertEqual(blocked["action"], "block")
            self.assertIn("cannot create a native staged durable mutation", blocked["message"])

    def test_profile_drift_invalidates_govern_applicability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = IntegrationConfig(
                mode="govern",
                governor_command=self.governor_command("allow"),
                governor_required=True,
                require_exact_profile=True,
            )
            runtime = HermesPluginRuntime(tmp, config=config, observed_hermes_revision="0" * 40)
            blocked = runtime.on_pre_tool_call(
                tool_name="memory",
                args={"action": "add", "target": "memory", "content": "candidate"},
                tool_call_id="drift",
            )
            self.assertEqual(blocked["action"], "block")
            self.assertIn("profile is not current", blocked["message"])

    def test_fail_closed_wrapper_blocks_malformed_config_instead_of_throwing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "agent-memory").mkdir()
            (home / "agent-memory" / "config.json").write_text("{bad-json", encoding="utf-8")
            os.environ["HERMES_HOME"] = str(home)
            _clear_runtime_cache_for_tests()
            blocked = safe_plugin._pre_tool_hook(
                tool_name="memory",
                args={"action": "add", "content": "candidate"},
                tool_call_id="bad-config",
            )
            self.assertEqual(blocked["action"], "block")
            self.assertIn("failed before durable-state admission", blocked["message"])

    def test_strict_coverage_and_doctor_refuse_with_exact_six_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            save_config(home, IntegrationConfig(mode="observe"))
            report = build_coverage_report(
                IntegrationConfig(mode="strict"),
                observed_hermes_revision=HERMES_COMMIT,
            )
            self.assertEqual(len(report["surfaces"]), len(MUTATION_SURFACES))
            self.assertEqual(tuple(report["strict"]["blocking_surfaces"]), STRICT_BLOCKERS)
            self.assertFalse(report["strict"]["supported"])
            self.assertFalse(report["integration"]["ready"])
            statuses = {item["surface_id"]: item["status"] for item in report["surfaces"]}
            for blocker in STRICT_BLOCKERS:
                self.assertEqual(statuses[blocker], "uncovered")

            out = io.StringIO()
            with redirect_stdout(out):
                rc = cli_main(
                    [
                        "doctor",
                        "--hermes-home",
                        str(home),
                        "--hermes-revision",
                        HERMES_COMMIT,
                        "--mode",
                        "strict",
                        "--json",
                    ]
                )
            self.assertEqual(rc, 2)
            parsed = json.loads(out.getvalue())
            self.assertEqual(parsed["strict"]["blocking_surfaces"], list(STRICT_BLOCKERS))

    def test_coverage_keeps_approval_replay_and_curator_uncovered(self) -> None:
        report = build_coverage_report(
            IntegrationConfig(mode="govern", governor_command=("/bin/true",)),
            observed_hermes_revision=HERMES_COMMIT,
        )
        statuses = {item["surface_id"]: item["status"] for item in report["surfaces"]}
        self.assertEqual(statuses["approved_pending_memory_replay"], "uncovered")
        self.assertEqual(statuses["approved_pending_skill_replay"], "uncovered")
        self.assertEqual(statuses["deterministic_curator_archive"], "uncovered")
        self.assertEqual(statuses["foreground_builtin_memory_tool"], "intercepted")
        self.assertEqual(statuses["background_review_memory"], "intercepted")

    def test_provider_records_post_commit_mirror_and_failure_without_rollback_fiction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            os.environ["HERMES_HOME"] = str(home)
            os.environ["AGENT_MEMORY_HERMES_REVISION"] = HERMES_COMMIT
            save_config(home, IntegrationConfig(mode="observe"))
            provider = AgentMemoryProvider()
            provider.initialize("session-1", hermes_home=str(home), platform="cli")
            self.assertEqual(provider.prefetch("what changed?", session_id="session-1"), "")
            provider.sync_turn("user secret", "assistant response", session_id="session-1")
            provider.on_memory_write("add", "memory", "durable value", {"origin": "foreground"})
            self.assertEqual(provider.last_projection_state["canonical_builtin_state"], "committed")
            self.assertEqual(provider.last_projection_state["external_projection"], "observed")
            self.assertFalse(provider.last_projection_state["rollback_claimed"])

            os.environ["AGENT_MEMORY_HERMES_TEST_MIRROR_FAILURE"] = "1"
            with self.assertRaisesRegex(RuntimeError, "injected"):
                provider.on_memory_write("replace", "memory", "new durable value", None)
            failed = provider.last_projection_state
            self.assertEqual(failed["canonical_builtin_state"], "committed")
            self.assertEqual(failed["external_projection"], "failed")
            self.assertFalse(failed["settled"])
            self.assertFalse(failed["quiescent"])
            self.assertFalse(failed["rollback_claimed"])

            events_text = (home / "agent-memory" / "events.jsonl").read_text()
            self.assertNotIn("user secret", events_text)
            self.assertNotIn("durable value", events_text)
            self.assertIn("provider_memory_mirror_failed", events_text)


if __name__ == "__main__":
    unittest.main()
