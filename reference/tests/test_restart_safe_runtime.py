from __future__ import annotations

import json
import tempfile
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule

BRANCH_MEMORY = "memory:deploy-branch"


def _branch_corpus():
    """The evaluator's adjudication of release-branch corrections."""
    return corpus_for(rule(
        rule_id="rule:release-branch", target=BRANCH_MEMORY,
        criterion="value-correction", from_state="release_branch = release",
        to_values=("release_branch = main",),
    ))
from pathlib import Path

from agentmem_ref import policy
from agentmem_ref.adapter import RecallContext
from agentmem_ref.restart_runtime import (
    CapabilityBinding,
    RestartSafeRuntime,
    RuntimeProfile,
    RuntimeRecoveryError,
)
from agentmem_ref.visibility import VisibilityOperation, VisibilityTracker


COMMIT = "85970029b6ada43ef0844c5f58b504a8c642d5e0"


def _binding(*, component_version: str = "1.0.0") -> CapabilityBinding:
    return CapabilityBinding(
        component_id="reference-governed-memory",
        component_version=component_version,
        capability_id="governed-memory-core",
        capability_version="1.0.0",
        maturity="reference_qualified",
        evidence_ref="evidence:reference-runtime-core-v1",
    )


def _profile(*, profile_version: str = "1.0.0") -> RuntimeProfile:
    return RuntimeProfile(
        runtime_version="0.1.0-reference",
        profile_id="reference-project-memory",
        profile_version=profile_version,
        bindings=(_binding(),),
    )


def _proposal(
    proposal_id: str,
    *,
    operation: str,
    target_reference: str = "memory:release-branch",
    state_snapshot: str = "",
    review_satisfied: bool = False,
    approval_refs: tuple[str, ...] = (),
) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="agent:test",
        charter_version="charter-v1",
        target_reference=target_reference,
        target_class=policy.M2,
        scope="tenant-acme",
        operation=operation,
        current_strength="observed",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=(f"evidence:{proposal_id}",),
        review_satisfied=review_satisfied,
        approval_refs=approval_refs,
        state_snapshot=state_snapshot,
        tenant_ref="tenant-acme",
        isolation_domain_refs=("tenant-acme", "project-alpha"),
        required_isolation_domain_refs=("project-alpha",),
        project_ref="project-alpha",
        purpose="release-planning",
    )


def _context(*, project_ref: str = "project-alpha") -> RecallContext:
    return RecallContext(
        target_domain_refs=("tenant-acme", "project-alpha"),
        principal_ref="agent:test",
        project_ref=project_ref,
        purpose="release-planning",
    )


class RestartSafeRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.profile = _profile()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_release_branch_survives_restart_with_currentness_scope_and_stale_replay(self) -> None:
        session_a = RestartSafeRuntime.create(self.root, tenant="tenant-acme", profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        learned = session_a.commit_proposal(
            _proposal("proposal-release", operation="promotion"),
            "release_branch = release",
        )
        self.assertTrue(learned.committed)
        release_uuid = learned.fact_uuid
        self.assertIsNotNone(release_uuid)
        self.assertEqual(session_a.adapter.state_version("memory:release-branch"), 1)

        session_b = RestartSafeRuntime.recover(self.root, profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        recalled = session_b.adapter.governed_recall("release_branch", _context())
        self.assertEqual(recalled.admitted, [release_uuid])

        correction = _proposal(
            "proposal-main",
            operation="correction",
            state_snapshot="v1",
            review_satisfied=True,
            approval_refs=("approval:release-branch-main",),
        )
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        corrected = session_b.commit_proposal(
            correction, "release_branch = main",
            evidence=_branch_corpus().evidence_for(
                target_reference=BRANCH_MEMORY, criterion="value-correction",
                pre_state="release_branch = release",
                proposed_value="release_branch = main"),
        )
        self.assertTrue(corrected.committed)
        main_uuid = corrected.fact_uuid
        self.assertIsNotNone(main_uuid)
        self.assertNotEqual(main_uuid, release_uuid)
        self.assertEqual(session_b.adapter.state_version("memory:release-branch"), 2)

        replay = session_b.commit_proposal(correction, "release_branch = main")
        self.assertFalse(replay.committed)
        self.assertEqual(replay.refusal, "stale_authorization")

        session_c = RestartSafeRuntime.recover(self.root, profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        current = session_c.adapter.governed_recall("release_branch", _context())
        self.assertEqual(current.admitted, [main_uuid])
        self.assertEqual(current.refusals[release_uuid], "superseded_not_current")
        self.assertEqual(session_c.adapter.current_fact_uuid("memory:release-branch"), main_uuid)
        history = session_c.adapter.rejected_value_history("memory:release-branch", "release_branch = release")
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0]["active"])

        wrong_project = session_c.adapter.governed_recall(
            "release_branch",
            _context(project_ref="project-beta"),
        )
        self.assertNotIn(main_uuid, wrong_project.admitted)
        self.assertEqual(wrong_project.refusals[main_uuid], "project_scope_mismatch")

        session_d = RestartSafeRuntime.recover(self.root, profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        after_restart = session_d.adapter.governed_recall("release_branch", _context())
        self.assertEqual(after_restart.admitted, [main_uuid])
        self.assertEqual(after_restart.refusals[release_uuid], "superseded_not_current")
        replay_after_restart = session_d.commit_proposal(correction, "release_branch = main")
        self.assertFalse(replay_after_restart.committed)
        self.assertEqual(replay_after_restart.refusal, "stale_authorization")

    def test_pending_visibility_obligations_survive_restart_without_fake_quiescence(self) -> None:
        runtime = RestartSafeRuntime.create(self.root, tenant="tenant-acme", profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        operation = VisibilityOperation(
            operation_id="visibility:release-main",
            memory_id="memory:release-branch",
            memory_version=2,
            operation_type="correction",
            runtime_version=self.profile.runtime_version,
            profile_version=self.profile.profile_version,
            agent_memory_commit=COMMIT,
            required_projection_ids=("search-index",),
            component_versions=("reference-governed-memory@1.0.0",),
            capability_versions=("governed-memory-core@1.0.0",),
        )
        tracker = VisibilityTracker(operation)
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("search-index")
        self.assertFalse(tracker.evaluate()["quiescent"])

        runtime.persist_visibility_snapshot(operation.operation_id, tracker.snapshot_for_restart())
        recovered = RestartSafeRuntime.recover(self.root, profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        restored = VisibilityTracker.restore_after_restart(
            recovered.visibility_snapshots[operation.operation_id]
        )
        after = restored.evaluate()
        self.assertFalse(after["settled"])
        self.assertFalse(after["quiescent"])
        self.assertIn("projection:search-index", after["pending_required_obligations"])
        self.assertEqual(
            recovered.recovery_evidence.recovered_visibility_operations,
            (operation.operation_id,),
        )

    def test_corrupt_checkpoint_fails_closed(self) -> None:
        runtime = RestartSafeRuntime.create(self.root, tenant="tenant-acme", profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        runtime.commit_proposal(
            _proposal("proposal-release", operation="promotion"),
            "release_branch = release",
        )
        path = self.root / "governance.json"
        governance = json.loads(path.read_text(encoding="utf-8"))
        governance["tenant"] = "attacker-tenant"
        path.write_text(json.dumps(governance), encoding="utf-8")
        with self.assertRaisesRegex(RuntimeRecoveryError, "governance checkpoint digest mismatch"):
            RestartSafeRuntime.recover(self.root, profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))

    def test_missing_governance_state_fails_closed(self) -> None:
        RestartSafeRuntime.create(self.root, tenant="tenant-acme", profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        (self.root / "governance.json").unlink()
        with self.assertRaisesRegex(RuntimeRecoveryError, "required runtime state missing"):
            RestartSafeRuntime.recover(self.root, profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))

    def test_component_interpretation_cannot_silently_change_after_restart(self) -> None:
        RestartSafeRuntime.create(self.root, tenant="tenant-acme", profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        with self.assertRaisesRegex(RuntimeRecoveryError, "interpretation changed after restart"):
            RestartSafeRuntime.recover(
                self.root,
                profile=self.profile,
                available_bindings=(_binding(component_version="2.0.0"),),
            )
        with self.assertRaisesRegex(RuntimeRecoveryError, "profile/component interpretation changed"):
            RestartSafeRuntime.recover(self.root, profile=_profile(profile_version="2.0.0"))

    def test_recovery_preserves_identifier_progress(self) -> None:
        runtime = RestartSafeRuntime.create(self.root, tenant="tenant-acme", profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        first = runtime.commit_proposal(
            _proposal("proposal-first", operation="promotion"),
            "release_branch = release",
        )
        recovered = RestartSafeRuntime.recover(self.root, profile=self.profile,
            verifier_registry=registry_for(_branch_corpus()))
        second = recovered.commit_proposal(
            _proposal(
                "proposal-second",
                operation="promotion",
                target_reference="memory:deploy-branch",
            ),
            "deploy_branch = deploy",
        )
        self.assertTrue(second.committed)
        self.assertNotEqual(second.fact_uuid, first.fact_uuid)


if __name__ == "__main__":
    unittest.main()
