from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agentmem_ref.cli import main
from agentmem_ref.configured_restart import ConfigBoundRestartRuntime
from agentmem_ref.doctor import diagnose, validate_configuration_file
from agentmem_ref.runtime_behavior import validate_runtime_behavior_contract
from agentmem_ref.runtime_config import RuntimeConfigurationError
from agentmem_ref.visibility import VisibilityOperation, VisibilityTracker


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "reference" / "fixtures" / "runtime-configuration"
COMPOSED = FIXTURES / "reference-composed-runtime.json"
ATTACHED = FIXTURES / "attached-existing-stack.json"
QUALIFICATIONS = FIXTURES / "qualification-bindings.json"


def _composed_plan():
    return validate_runtime_behavior_contract(json.loads(COMPOSED.read_text(encoding="utf-8")))


class CliDoctorTests(unittest.TestCase):
    def test_config_validate_reports_composed_runtime_without_overclaiming_authority(self) -> None:
        report = validate_configuration_file(COMPOSED)
        self.assertTrue(report["valid"])
        self.assertTrue(report["startable_configuration"])
        self.assertEqual(report["authority_effect"], "none")
        self.assertEqual(report["entry_mode"], "bootstrap_agent_memory_first")
        self.assertIn("reference-derived-index", report["required_projection_ids"])

    def test_attached_stack_requires_and_accepts_independent_qualification_bindings(self) -> None:
        with self.assertRaises(RuntimeConfigurationError):
            validate_configuration_file(ATTACHED)
        report = validate_configuration_file(ATTACHED, qualification_path=QUALIFICATIONS)
        self.assertTrue(report["valid"])
        self.assertEqual(report["entry_mode"], "attach_existing_stack")
        self.assertEqual(report["required_qualification_routes"], ["derived-code-graph"])
        self.assertEqual(report["qualification_binding_count"], 2)

    def test_doctor_without_state_is_truthful_about_initialization_and_provider_probe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "not-created"
            report = diagnose(COMPOSED, state_dir=state)
        self.assertEqual(report["configuration"]["status"], "valid")
        self.assertEqual(report["durable_state"]["status"], "not_initialized")
        self.assertEqual(report["recovery"]["status"], "not_attempted")
        self.assertEqual(report["provider_availability"]["status"], "not_probed")
        self.assertEqual(report["operational_readiness"], "configuration_valid_state_not_initialized")
        self.assertTrue(report["configuration_startable"])
        self.assertEqual(report["authority_effect"], "none")

    def test_doctor_recovers_exact_configuration_but_does_not_claim_provider_health(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = _composed_plan()
            ConfigBoundRestartRuntime.create(directory, tenant="tenant-acme", plan=plan)
            report = diagnose(COMPOSED, state_dir=directory)
        self.assertEqual(report["durable_state"]["status"], "recovered")
        self.assertEqual(report["recovery"]["status"], "recovered")
        self.assertEqual(report["currentness"]["status"], "not_observed")
        self.assertEqual(report["provider_availability"]["status"], "not_probed")
        self.assertEqual(report["operational_readiness"], "provider_availability_not_probed")

    def test_doctor_surfaces_pending_currentness_after_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = _composed_plan()
            runtime = ConfigBoundRestartRuntime.create(directory, tenant="tenant-acme", plan=plan)
            operation = VisibilityOperation(
                operation_id="visibility:cli-doctor",
                memory_id="memory:doctor",
                memory_version=1,
                operation_type="promotion",
                runtime_version=plan.runtime_version,
                profile_version=plan.profile_version,
                agent_memory_commit="a" * 40,
                required_projection_ids=("reference-derived-index",),
            )
            tracker = VisibilityTracker(operation)
            tracker.policy_decided()
            tracker.canonical_committed()
            tracker.projection_refresh_started("reference-derived-index")
            runtime.persist_visibility_snapshot(operation.operation_id, tracker.snapshot_for_restart())
            report = diagnose(COMPOSED, state_dir=directory)
        self.assertEqual(report["recovery"]["status"], "recovered")
        self.assertEqual(report["currentness"]["status"], "pending")
        self.assertEqual(report["currentness"]["pending_operations"], 1)
        self.assertEqual(report["operational_readiness"], "pending_currentness")

    def test_doctor_fails_closed_on_corrupt_configuration_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plan = _composed_plan()
            ConfigBoundRestartRuntime.create(directory, tenant="tenant-acme", plan=plan)
            binding = Path(directory) / "configuration-binding.json"
            value = json.loads(binding.read_text(encoding="utf-8"))
            value["configuration_digest"] = "sha256:" + "0" * 64
            binding.write_text(json.dumps(value), encoding="utf-8")
            report = diagnose(COMPOSED, state_dir=directory)
        self.assertEqual(report["recovery"]["status"], "failed_closed")
        self.assertFalse(report["configuration_startable"])
        self.assertEqual(report["operational_readiness"], "blocked_by_recovery_failure")

    def test_cli_json_output_is_machine_readable(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main(["config", "validate", "--config", str(COMPOSED), "--json"])
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertTrue(report["valid"])
        self.assertEqual(report["authority_effect"], "none")

    def test_cli_invalid_configuration_returns_refusal_exit_code(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("{}", encoding="utf-8")
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                code = main(["config", "validate", "--config", str(path), "--json"])
        self.assertEqual(code, 2)
        report = json.loads(output.getvalue())
        self.assertFalse(report["valid"])
        self.assertEqual(report["status"], "refused")


if __name__ == "__main__":
    unittest.main()
