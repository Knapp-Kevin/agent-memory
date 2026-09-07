"""P7 correction/deletion propagation across two concrete local stores."""

from __future__ import annotations

import sys
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule


def _prop_corpus():
    """Adjudications held by each store's evaluator, authored ahead of any
    proposal (ADR-037 step 4b-2, entry #24). The receiver's is its OWN: a
    sender receipt records the sender's authority and is never reused as the
    receiver's evidence."""
    return corpus_for(
        rule(rule_id="rule:source-deletion", target=MEMORY_ID,
             criterion="permanent-deletion", from_state="current",
             to_values=("deleted",)),
        rule(rule_id="rule:seed-promotion", target=MEMORY_ID,
             criterion="promotion", from_state="absent",
             to_values=("original governed decision",)),
        rule(rule_id="rule:source-correction", target=MEMORY_ID,
             criterion="value-correction", from_state="original governed decision",
             to_values=("corrected governed decision",)),
        rule(rule_id="rule:receiver-local", target=MEMORY_ID,
             criterion="lifecycle-notice", from_state="current",
             to_values=("corrected", "deleted")),
    )


def _seed_evidence():
    return _prop_corpus().evidence_for(
        target_reference=MEMORY_ID, criterion="promotion",
        pre_state="absent", proposed_value="original governed decision",
    )


def _correction_evidence():
    return _prop_corpus().evidence_for(
        target_reference=MEMORY_ID, criterion="value-correction",
        pre_state="original governed decision",
        proposed_value="corrected governed decision",
    )


def _notice_evidence(to_value):
    return _prop_corpus().evidence_for(
        target_reference=MEMORY_ID, criterion="lifecycle-notice",
        pre_state="current", proposed_value=to_value,
    )
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy, residue  # noqa: E402
from agentmem_ref.adapter import GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.interchange import (  # noqa: E402
    NOTICE_CORRECTION,
    NOTICE_DELETION,
    SourceLifecycleNotice,
    evaluate_source_notice,
)
from agentmem_ref.interchange_propagation import (  # noqa: E402
    apply_receiver_correction,
    apply_receiver_deletion,
)
from agentmem_ref.projections import (  # noqa: E402
    DETERMINISTIC,
    DERIVED_CONTENT,
    REPRODUCIBLE,
    Projection,
    ProjectionStore,
)
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

MEMORY_ID = "mem:two-store-decision"


def proposal(
    *,
    actor: str,
    operation: str,
    tenant: str,
    state_snapshot: str = "",
    review: bool = True,
) -> policy.Proposal:
    strength = {
        "promotion": ("reinforced", "canonical"),
        "correction": ("canonical", "canonical"),
        "permanent_deletion": ("canonical", "not_applicable"),
    }
    current_strength, proposed_strength = strength[operation]
    return policy.Proposal(
        proposal_id=f"{actor}:{operation}",
        actor_id=actor,
        charter_version="charter-1",
        target_reference=MEMORY_ID,
        target_class=policy.M4,
        scope=tenant,
        operation=operation,
        current_strength=current_strength,
        proposed_strength=proposed_strength,
        downstream_authority=policy.A2,
        reversibility="irreversible" if operation == "permanent_deletion" else "reversible",
        risk_class="medium",
        evidence_refs=(f"evidence:{operation}",),
        review_satisfied=review,
        approval_refs=(f"approval:{tenant}",) if review else (),
        state_snapshot=state_snapshot,
        tenant_ref=tenant,
        isolation_domain_refs=(f"domain:{tenant}",),
    )


def link():
    from agentmem_ref.interchange import InterchangeLink

    return InterchangeLink(
        memory_id=MEMORY_ID,
        source_system="system-a",
        receiver_system="system-b",
        source_crossing_receipt_ref="crossing:export",
        source_domain_refs=("domain:tenant-a",),
        receiver_domain_ref="domain:tenant-b",
    )


def imported_memory() -> dict:
    return {
        "schema_version": "1.0.0",
        "id": MEMORY_ID,
        "type": "decision",
        "state": "crystallized",
        "scope": {
            "owner_principal": "user:alice",
            "tenant": "tenant-b",
            "isolation_domain_refs": ["domain:tenant-b"],
            "source_isolation_domain_refs": ["domain:tenant-a"],
        },
        "provenance": {
            "origin": "system-a",
            "observer": "agent:source",
            "method": "governed interchange",
            "timestamp": "2026-08-11T20:00:00Z",
        },
        "evidence": [{"id": "evidence:import", "kind": "interchange", "ref": "crossing:export", "confidence": 1.0}],
        "saturation": {"sigma": 0.9, "calibrated": True, "durability_dimensions": ["decision"]},
        "authority": {"pama_outcome": "allow_with_ledger", "risk_class": "medium"},
        "created_at": "2026-08-11T20:00:00Z",
    }


class TwoStorePropagationTests(unittest.TestCase):
    def setUp(self):
        self.sender_store = InMemoryTemporalGraph()
        self.receiver_store = InMemoryTemporalGraph()
        self.sender = GovernedMemoryAdapter(self.sender_store, "tenant-a",
            verifier_registry=registry_for(_prop_corpus()))
        self.receiver = GovernedMemoryAdapter(self.receiver_store, "tenant-b",
            verifier_registry=registry_for(_prop_corpus()))

        sender_initial = self.sender.commit_proposal(
            proposal(actor="agent:source", operation="promotion", tenant="tenant-a"),
            "original governed decision",
            evidence=_seed_evidence(),
        )
        receiver_initial = self.receiver.commit_proposal(
            proposal(actor="agent:receiver", operation="promotion", tenant="tenant-b"),
            "original governed decision",
            evidence=_seed_evidence(),
        )
        self.assertTrue(sender_initial.committed)
        self.assertTrue(receiver_initial.committed)
        assert sender_initial.fact_uuid and receiver_initial.fact_uuid
        self.sender_fact = sender_initial.fact_uuid
        self.receiver_fact = receiver_initial.fact_uuid

    def test_correction_propagates_as_receiver_local_governed_supersession(self):
        sender_correction = self.sender.commit_proposal(
            proposal(actor="agent:source", operation="correction", tenant="tenant-a"),
            "corrected governed decision",
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_correction_evidence(),
        )
        self.assertTrue(sender_correction.committed)

        notice = SourceLifecycleNotice(
            "notice:correction",
            "system-a",
            MEMORY_ID,
            NOTICE_CORRECTION,
            (sender_correction.receipt["receipt_id"],),
            source_state="corrected",
            source_receipt_ref=sender_correction.receipt["receipt_id"],
        )
        receiver_correction_proposal = proposal(actor="agent:receiver", operation="correction", tenant="tenant-b")
        notice_result = evaluate_source_notice(
            imported_memory(),
            link(),
            notice,
            receiver_proposal=receiver_correction_proposal,
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            # The RECEIVER supplies its own evidence; the sender's receipt is
            # never reused as the receiver's allow decision.
            evidence=_notice_evidence("corrected"),
            verifier_registry=registry_for(_prop_corpus()),
        )
        self.assertEqual(notice_result.local_action, "schedule_local_correction")

        propagated = apply_receiver_correction(
            self.receiver,
            self.receiver_store,
            proposal=receiver_correction_proposal,
            superseded_fact_uuid=self.receiver_fact,
            corrected_text="corrected governed decision",
            invalid_at="2026-08-11T21:00:00Z",
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_correction_evidence(),
        )
        self.assertTrue(propagated.commit.committed)
        self.assertIsNotNone(propagated.replacement_fact_uuid)
        old = self.receiver_store.get_fact(self.receiver_fact)
        self.assertIsNotNone(old)
        assert old is not None
        self.assertTrue(old.is_event_invalid)
        self.assertIsNotNone(self.receiver_store.get_fact(propagated.replacement_fact_uuid))
        self.assertEqual(propagated.commit.receipt["selected_action"], "correction")

    def test_clean_receiver_deletion_reuses_p4_residue_measurement(self):
        projections = ProjectionStore()
        projections.declare(
            Projection(
                projection_id="receiver:index",
                basis=((MEMORY_ID, self.receiver.state_version(MEMORY_ID)),),
                transform=DETERMINISTIC,
                content_class=DERIVED_CONTENT,
                rebuild=REPRODUCIBLE,
                scope="tenant-b",
            )
        )

        sender_delete = self.sender.governed_delete(
            proposal(actor="agent:source", operation="permanent_deletion", tenant="tenant-a"),
            self.sender_fact,
            evidence=_prop_corpus().evidence_for(
                target_reference=MEMORY_ID, criterion="permanent-deletion",
                pre_state="current", proposed_value="deleted"),
        )
        self.assertTrue(sender_delete.committed)

        receiver_delete_proposal = proposal(actor="agent:receiver", operation="permanent_deletion", tenant="tenant-b")
        notice_result = evaluate_source_notice(
            imported_memory(),
            link(),
            SourceLifecycleNotice(
                "notice:delete", "system-a", MEMORY_ID, NOTICE_DELETION,
                (sender_delete.receipt["receipt_id"],), source_receipt_ref=sender_delete.receipt["receipt_id"],
            ),
            receiver_proposal=receiver_delete_proposal,
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_notice_evidence("deleted"),
            verifier_registry=registry_for(_prop_corpus()),
        )
        self.assertEqual(notice_result.local_action, "schedule_local_deletion")

        propagated = apply_receiver_deletion(
            self.receiver,
            projections,
            proposal=receiver_delete_proposal,
            fact_uuid=self.receiver_fact,
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_prop_corpus().evidence_for(
                target_reference=MEMORY_ID, criterion="permanent-deletion",
                pre_state="current", proposed_value="deleted"),
        )
        self.assertTrue(propagated.commit.committed)
        self.assertIsNone(self.receiver_store.get_fact(self.receiver_fact))
        self.assertIsNotNone(self.receiver.tombstone(self.receiver_fact))
        self.assertEqual(propagated.buckets[residue.UNDECLARED], [])
        self.assertTrue(propagated.measurement.hard_gate_passed)
        self.assertEqual(propagated.measurement.lifecycle_satisfaction, "satisfied")

    def test_late_receiver_projection_prevents_false_forgetting_claim(self):
        projections = ProjectionStore()
        projections.declare(
            Projection(
                projection_id="receiver:known-index",
                basis=((MEMORY_ID, self.receiver.state_version(MEMORY_ID)),),
                transform=DETERMINISTIC,
                content_class=DERIVED_CONTENT,
                rebuild=REPRODUCIBLE,
                scope="tenant-b",
            )
        )
        late = Projection(
            projection_id="receiver:late-cache",
            basis=((MEMORY_ID, self.receiver.state_version(MEMORY_ID)),),
            transform=DETERMINISTIC,
            content_class=DERIVED_CONTENT,
            rebuild=REPRODUCIBLE,
            scope="tenant-b",
            note="declared after purge traversal to model hidden/late receiver residue",
        )

        receiver_delete_proposal = proposal(actor="agent:receiver", operation="permanent_deletion", tenant="tenant-b")
        propagated = apply_receiver_deletion(
            self.receiver,
            projections,
            proposal=receiver_delete_proposal,
            fact_uuid=self.receiver_fact,
            late_projections=(late,),
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            # The property under test -- a late projection prevents a false
            # forgetting claim -- is unchanged.
            evidence=_prop_corpus().evidence_for(
                target_reference=MEMORY_ID, criterion="permanent-deletion",
                pre_state="current", proposed_value="deleted"),
        )

        self.assertTrue(propagated.commit.committed)
        self.assertEqual(propagated.buckets[residue.UNDECLARED], ["receiver:late-cache"])
        self.assertEqual(propagated.independently_observed_residual, ("receiver:late-cache",))
        self.assertFalse(propagated.measurement.hard_gate_passed)
        self.assertEqual(propagated.measurement.lifecycle_satisfaction, "residual")


if __name__ == "__main__":
    unittest.main()
