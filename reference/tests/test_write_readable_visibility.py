"""#308 write-to-readable visibility and runtime quiescence tests."""

from __future__ import annotations

import sys
import unittest

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy, projections  # noqa: E402

# Imported AFTER the sys.path setup above: `qualified_fixtures` imports
# `agentmem_ref`, so it cannot load until `reference/` is on the path. That same
# insert makes `tests` importable, so this absolute form resolves under all three
# CI invocation styles (`discover -t reference`, `reference.tests.X`, and
# `discover` without `-t`); a relative import fails under the third.
from tests.qualified_fixtures import corpus_for, registry_for, rule


def _visibility_corpus():
    """The evaluator's adjudication of this correction (ADR-037 4b-2)."""
    return corpus_for(rule(
        rule_id="rule:visibility-correction", target=SOURCE,
        criterion="value-correction", from_state="deploy window Thursday",
        to_values=("deploy window Friday",),
    ))

from agentmem_ref.adapter import Clock, GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.projection_governance import ProjectionGovernor  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402
from agentmem_ref.visibility import (  # noqa: E402
    ABSENCE,
    CURRENT_VALUE,
    FAILED,
    PENDING,
    VisibilityOperation,
    VisibilityTracker,
)


TENANT = "tenant:visibility"
SOURCE = "memory:visibility"
COMMIT = "a" * 40


class StepClock:
    def __init__(self, step: int = 100) -> None:
        self.value = 0
        self.step = step

    def __call__(self) -> int:
        current = self.value
        self.value += self.step
        return current


def proposal(**overrides) -> policy.Proposal:
    base = dict(
        proposal_id="proposal:visibility",
        actor_id="agent:visibility",
        charter_version="charter:visibility",
        target_reference=SOURCE,
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:visibility",),
        tenant_ref=TENANT,
        purpose="write_to_readable_visibility",
    )
    base.update(overrides)
    return policy.Proposal(**base)


def operation(
    *,
    memory_version: int = 1,
    operation_type: str = "promotion",
    required_projection_ids: tuple[str, ...] = (),
    optional_projection_ids: tuple[str, ...] = (),
    visibility_target: str = CURRENT_VALUE,
) -> VisibilityOperation:
    return VisibilityOperation(
        operation_id=f"op:{operation_type}:{memory_version}",
        memory_id=SOURCE,
        memory_version=memory_version,
        operation_type=operation_type,
        runtime_version="reference:1",
        profile_version="profile:visibility:1",
        agent_memory_commit=COMMIT,
        required_projection_ids=required_projection_ids,
        optional_projection_ids=optional_projection_ids,
        component_versions=("reference-adapter:1",),
        capability_versions=("governed-recall:1", "projection-freshness:1"),
        receipt_ref="receipt:visibility",
        correlation_ref="correlation:visibility",
        visibility_target=visibility_target,
        environment_ref="unit-test",
    )


class VisibilityContractTests(unittest.TestCase):
    def test_sync_canonical_only_write_reaches_quiescence_without_fake_projection_latency(self):
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, TENANT, Clock(),
            verifier_registry=registry_for(_visibility_corpus()))
        result = adapter.commit_proposal(proposal(), "visibility token current")
        self.assertTrue(result.committed)

        tracker = VisibilityTracker(operation(), clock_ns=StepClock())
        tracker.policy_decided()
        tracker.canonical_committed()

        recall = adapter.governed_recall("visibility token current")
        self.assertEqual(recall.admitted, [result.fact_uuid])
        tracker.governed_recall_current_visible()
        tracker.context_current_visible()
        tracker.stale_current_blocked()

        evidence = tracker.evidence()
        self.assertTrue(evidence["disposition"]["settled"])
        self.assertTrue(evidence["disposition"]["quiescent"])
        self.assertEqual(evidence["disposition"]["posture"], "quiescent")
        self.assertEqual(
            evidence["metrics"]["canonical_to_required_projections_current"]["reason"],
            "not_applicable",
        )
        self.assertEqual(
            evidence["metrics"]["request_to_quiescence"]["reason"],
            "observed",
        )

    def test_deferred_projection_blocks_quiescence_while_old_physical_fact_is_not_admitted(self):
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, TENANT, Clock(),
            verifier_registry=registry_for(_visibility_corpus()))
        first = adapter.commit_proposal(proposal(), "deploy window Thursday")
        self.assertTrue(first.committed)

        governor = ProjectionGovernor(adapter)
        governor.declare(
            "idx:visibility",
            (SOURCE,),
            projections.DETERMINISTIC,
            projections.REFERENCE_ONLY,
            projections.REPRODUCIBLE,
            TENANT,
        )
        self.assertEqual(governor.freshness("idx:visibility"), projections.CURRENT)

        corrected = adapter.commit_proposal(
            proposal(
                proposal_id="proposal:visibility:correction",
                operation="correction",
                current_strength="promoted",
                proposed_strength="promoted",
                approval_refs=("approval:owner",),
                review_satisfied=True,
            ),
            "deploy window Friday",
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_visibility_corpus().evidence_for(
                target_reference=SOURCE, criterion="value-correction",
                pre_state="deploy window Thursday",
                proposed_value="deploy window Friday"),
        )
        self.assertTrue(corrected.committed)
        self.assertEqual(adapter.state_version(SOURCE), 2)
        self.assertEqual(governor.freshness("idx:visibility"), projections.STALE)

        tracker = VisibilityTracker(
            operation(memory_version=2, operation_type="correction", required_projection_ids=("idx:visibility",)),
            clock_ns=StepClock(),
        )
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("idx:visibility")

        old_recall = adapter.governed_recall("Thursday")
        self.assertIn(first.fact_uuid, old_recall.candidates)
        self.assertNotIn(first.fact_uuid, old_recall.admitted)
        self.assertEqual(old_recall.refusals[first.fact_uuid], "superseded_not_current")
        tracker.stale_current_blocked()

        current_recall = adapter.governed_recall("Friday")
        self.assertEqual(current_recall.admitted, [corrected.fact_uuid])
        tracker.governed_recall_current_visible()
        tracker.context_current_visible()

        before_rebuild = tracker.evaluate()
        self.assertFalse(before_rebuild["settled"])
        self.assertFalse(before_rebuild["quiescent"])
        self.assertIn("projection:idx:visibility", before_rebuild["pending_required_obligations"])

        rebuilt = governor.propose_rebuild("idx:visibility")
        self.assertTrue(rebuilt.committed)
        self.assertTrue(rebuilt.categorical)
        self.assertEqual(governor.freshness("idx:visibility"), projections.CURRENT)
        tracker.projection_refresh_satisfied("idx:visibility")

        after_rebuild = tracker.evaluate()
        self.assertTrue(after_rebuild["settled"])
        self.assertTrue(after_rebuild["quiescent"])

    def test_explicit_required_refresh_failure_is_settled_but_not_quiescent(self):
        tracker = VisibilityTracker(
            operation(required_projection_ids=("idx:required",)),
            clock_ns=StepClock(),
        )
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("idx:required")
        tracker.projection_refresh_failed("idx:required", detail="provider unavailable")
        tracker.governed_recall_current_visible()
        tracker.context_current_visible()
        tracker.stale_current_blocked()

        evidence = tracker.evidence()
        self.assertTrue(evidence["disposition"]["settled"])
        self.assertFalse(evidence["disposition"]["quiescent"])
        self.assertEqual(evidence["disposition"]["posture"], "degraded")
        self.assertIn("projection:idx:required", evidence["disposition"]["failed_required_obligations"])
        self.assertEqual(
            next(
                item for item in evidence["obligations"]
                if item["obligation_id"] == "projection:idx:required"
            )["status"],
            FAILED,
        )
        self.assertNotIn("quiescence_reached", [phase["phase"] for phase in evidence["phases"]])

    def test_pending_projection_obligation_survives_restart_without_fabricated_duration(self):
        tracker = VisibilityTracker(
            operation(required_projection_ids=("idx:restart",)),
            clock_ns=StepClock(),
        )
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("idx:restart")
        snapshot = tracker.snapshot_for_restart()

        restored = VisibilityTracker.restore_after_restart(snapshot, clock_ns=StepClock(step=250))
        projection = next(
            obligation for obligation in restored.evidence()["obligations"]
            if obligation["obligation_id"] == "projection:idx:restart"
        )
        self.assertEqual(projection["status"], PENDING)
        self.assertEqual(restored.evidence()["timing"]["segment"], 1)

        restored.projection_refresh_satisfied("idx:restart")
        restored.governed_recall_current_visible()
        restored.context_current_visible()
        restored.stale_current_blocked()
        final = restored.evidence()

        self.assertTrue(final["disposition"]["quiescent"])
        self.assertEqual(
            final["metrics"]["request_to_quiescence"]["reason"],
            "cross_restart_monotonic_segments",
        )

    def test_deletion_cannot_quiesce_while_required_residue_work_is_pending(self):
        tracker = VisibilityTracker(
            operation(
                memory_version=2,
                operation_type="permanent_deletion",
                required_projection_ids=("projection:residue",),
                visibility_target=ABSENCE,
            ),
            clock_ns=StepClock(),
        )
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("projection:residue")
        tracker.governed_recall_current_visible()
        tracker.context_current_visible()
        tracker.stale_current_blocked()

        pending = tracker.evaluate()
        self.assertFalse(pending["quiescent"])
        self.assertIn("projection:projection:residue", pending["pending_required_obligations"])

        tracker.projection_refresh_satisfied("projection:residue")
        complete = tracker.evaluate()
        self.assertTrue(complete["quiescent"])

    def test_explicit_refusal_is_terminal_without_inventing_mutation_phases(self):
        tracker = VisibilityTracker(operation(), clock_ns=StepClock())
        tracker.policy_decided()
        tracker.canonical_refused(detail="policy denied mutation")

        evidence = tracker.evidence()
        self.assertTrue(evidence["disposition"]["settled"])
        self.assertTrue(evidence["disposition"]["quiescent"])
        canonical = next(
            phase for phase in evidence["phases"] if phase["phase"] == "canonical_commit_complete"
        )
        self.assertEqual(canonical["status"], "not_applicable")
        self.assertIsNone(canonical["offset_ns"])

    def test_configuration_fails_closed_on_ambiguous_projection_declarations(self):
        with self.assertRaises(ValueError):
            operation(required_projection_ids=("idx:1", "idx:1"))
        with self.assertRaises(ValueError):
            operation(required_projection_ids=("idx:1",), optional_projection_ids=("idx:1",))
        with self.assertRaises(ValueError):
            VisibilityOperation(
                operation_id="op:bad",
                memory_id=SOURCE,
                memory_version=1,
                operation_type="promotion",
                runtime_version="reference:1",
                profile_version="profile:1",
                agent_memory_commit="short",
            )


if __name__ == "__main__":
    unittest.main()
