"""Executable P7 governed memory interchange evidence."""

from __future__ import annotations

import sys
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.crossing import CrossingRequest, evaluate_crossing  # noqa: E402
from agentmem_ref.interchange import (  # noqa: E402
    NOTICE_CORRECTION,
    NOTICE_DELETION,
    SourceLifecycleNotice,
    build_export_bundle,
    evaluate_source_notice,
    import_bundle,
)


def memory_unit() -> dict:
    return {
        "schema_version": "1.0.0",
        "id": "mem:portable-decision",
        "type": "decision",
        "state": "crystallized",
        "scope": {
            "owner_principal": "user:alice",
            "tenant": "tenant-a",
            "project": "project-a",
            "purpose": "security-review",
            "isolation_domain_refs": ["domain:project-a"],
            "primary_isolation_domain_ref": "domain:project-a",
        },
        "sensitivity": {"labels": ["internal"]},
        "provenance": {
            "origin": "system-a",
            "observer": "agent:planner",
            "method": "governed decision",
            "timestamp": "2026-08-11T20:00:00Z",
            "source_refs": ["evidence:decision-source"],
        },
        "evidence": [{"id": "evidence:decision-source", "kind": "decision_record", "ref": "local://decision/42", "confidence": 1.0}],
        "saturation": {"sigma": 0.95, "calibrated": True, "durability_dimensions": ["certified_decision"]},
        "authority": {
            "pama_outcome": "allow_with_ledger",
            "risk_class": "medium",
            "policy_version": "sender-policy-7",
            "authority_refs": ["authority:sender"],
            "permitted_actions": ["retain"],
            "prohibited_actions": [],
            "selection_mode": "deterministic",
        },
        "created_at": "2026-08-11T20:00:00Z",
    }


def _export_corpus(target):
    """The evaluator's adjudication of permitted export destinations."""
    return corpus_for(rule(
        rule_id="rule:export-to-system-b", target=target, criterion="scope-expansion",
        from_state="domain:project-a", to_values=("domain:system-b-import",),
    ))


def _receiver_corpus(target):
    """The RECEIVER's own adjudication. The sender's crossing receipt records
    the sender's authority and is deliberately never reused here -- that is the
    authority/evidence collapse the operator ruled against."""
    return corpus_for(rule(
        rule_id="rule:receiver-admits", target=target, criterion="scope-admission",
        from_state="tenant-a", to_values=("tenant-b",),
    ))


def _notice_corpus(target):
    """Receiver-local adjudication of lifecycle notices. A source notice
    establishes that the remote source changed; it grants no local authority."""
    return corpus_for(rule(
        rule_id="rule:receiver-lifecycle", target=target, criterion="lifecycle-notice",
        from_state="crystallized", to_values=("deleted",),
    ))


def crossing(*, reviewed: bool) -> dict:
    request = CrossingRequest(
        operation="export",
        source_domain_refs=("domain:project-a",),
        destination_domain_refs=("domain:system-b-import",),
        actor="agent:planner",
        principal="user:alice",
        purpose="security-review",
        representation_kind="canonical_memory",
        source_refs=("mem:portable-decision",),
        authority_refs=("authority:sender",),
        policy_refs=("policy:sender-export",),
        provenance_refs=("evidence:decision-source",),
        before_scope_refs=("domain:project-a",),
        after_scope_refs=("domain:system-b-import",),
    )
    proposal = policy.Proposal(
        proposal_id="sender-export", actor_id="agent:planner", charter_version="charter-a",
        target_reference="mem:portable-decision", target_class=policy.M4, scope="tenant-a",
        operation="scope_expansion", current_strength="crystallized", proposed_strength="crystallized",
        downstream_authority=policy.A2, reversibility="reversible", risk_class="medium",
        evidence_refs=("evidence:decision-source",), review_satisfied=reviewed,
        approval_refs=("approval:sender-security-owner",) if reviewed else (),
    )
    # ADR-037 step 4b-2: expected semantic change (entry #24).
    # The evaluator holds an adjudication authored ahead of this proposal: from
    # domain:project-a, this memory may be exported to domain:system-b-import.
    # The proposal is checked against it and cannot author it. Authority
    # (`approval:sender-security-owner`) stays out of the evidential proof --
    # it belongs in the receipt, not in the evidential class.
    corpus = _export_corpus(proposal.target_reference)
    return evaluate_crossing(
        request, proposal, receipt_id="crossing:sender-export", timestamp="2026-08-11T20:01:00Z",
        decision_receipt_ref="decision:sender-export", ledger_ref="ledger:sender-export",
        evidence=corpus.evidence_for(
            target_reference=proposal.target_reference, criterion="scope-expansion",
            pre_state="domain:project-a", proposed_value="domain:system-b-import",
        ) if reviewed else None,
        verifier_registry=registry_for(corpus) if reviewed else None,
    ).receipt


def receiver_proposal(*, reviewed: bool = True) -> policy.Proposal:
    return policy.Proposal(
        proposal_id="receiver-import", actor_id="agent:receiver", charter_version="charter-b",
        target_reference="mem:portable-decision", target_class=policy.M4, scope="tenant-b",
        operation="scope_expansion", current_strength="crystallized", proposed_strength="crystallized",
        downstream_authority=policy.A2, reversibility="reversible", risk_class="medium",
        evidence_refs=("crossing:sender-export",), review_satisfied=reviewed,
        approval_refs=("approval:receiver-security-owner",) if reviewed else (),
    )


def notice_proposal(operation: str, *, reviewed: bool) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=f"receiver-{operation}", actor_id="agent:receiver", charter_version="charter-b",
        target_reference="mem:portable-decision", target_class=policy.M4, scope="tenant-b",
        operation=operation, current_strength="crystallized", proposed_strength="corrected",
        downstream_authority=policy.A2, reversibility="reversible", risk_class="medium",
        evidence_refs=("notice:source-change",), review_satisfied=reviewed,
        approval_refs=("approval:receiver-security-owner",) if reviewed else (),
    )


class InterchangeTests(unittest.TestCase):
    def imported(self):
        bundle = build_export_bundle(memory_unit(), sender_system="system-a", receiver_system="system-b", crossing_receipt=crossing(reviewed=True))
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # The receiver supplies its OWN evidence. The sender's crossing receipt
        # records the sender's authority and is deliberately not reused here --
        # that would be the authority/evidence collapse the operator ruled
        # against.
        recv = _receiver_corpus("mem:portable-decision")
        result = import_bundle(
            bundle, receiver_domain_ref="domain:system-b-import",
            receiver_proposal=receiver_proposal(), expected_owner_principal="user:alice",
            evidence=recv.evidence_for(
                target_reference="mem:portable-decision", criterion="scope-admission",
                pre_state="tenant-a", proposed_value="tenant-b",
            ),
            verifier_registry=registry_for(recv),
        )
        self.assertTrue(result.admitted)
        self.assertIsNotNone(result.memory)
        self.assertIsNotNone(result.link)
        return result.memory, result.link

    def test_export_requires_committed_sender_crossing(self):
        with self.assertRaises(ValueError):
            build_export_bundle(memory_unit(), sender_system="system-a", receiver_system="system-b", crossing_receipt=crossing(reviewed=False))

    def test_receiver_does_not_inherit_sender_allow(self):
        bundle = build_export_bundle(memory_unit(), sender_system="system-a", receiver_system="system-b", crossing_receipt=crossing(reviewed=True))
        result = import_bundle(bundle, receiver_domain_ref="domain:system-b-import", receiver_proposal=receiver_proposal(reviewed=False), expected_owner_principal="user:alice")
        self.assertFalse(result.admitted)
        self.assertEqual(result.decision.outcome, policy.REQUIRE_REVIEW)

    def test_ownership_conflict_fails_closed(self):
        bundle = build_export_bundle(memory_unit(), sender_system="system-a", receiver_system="system-b", crossing_receipt=crossing(reviewed=True))
        result = import_bundle(bundle, receiver_domain_ref="domain:system-b-import", receiver_proposal=receiver_proposal(), expected_owner_principal="user:bob")
        self.assertFalse(result.admitted)
        self.assertEqual(result.refusal, "ownership_conflict")

    def test_successful_import_preserves_semantics_and_rebinds_local_scope(self):
        original = memory_unit()
        imported, link = self.imported()
        self.assertEqual(imported["id"], original["id"])
        self.assertEqual(imported["state"], original["state"])
        self.assertEqual(imported["provenance"], original["provenance"])
        self.assertEqual(imported["sensitivity"], original["sensitivity"])
        self.assertEqual(imported["scope"]["owner_principal"], "user:alice")
        self.assertEqual(imported["scope"]["isolation_domain_refs"], ["domain:system-b-import"])
        self.assertEqual(imported["scope"]["source_isolation_domain_refs"], ["domain:project-a"])
        self.assertEqual(link.source_system, "system-a")

    def test_source_deletion_notice_does_not_delete_without_local_authority(self):
        imported, link = self.imported()
        before = dict(imported)
        result = evaluate_source_notice(
            imported, link,
            SourceLifecycleNotice("notice:delete", "system-a", imported["id"], NOTICE_DELETION, ("receipt:source-delete",), source_state="tombstoned"),
            receiver_proposal=notice_proposal("permanent_deletion", reviewed=False),
        )
        self.assertTrue(result.recognized)
        self.assertFalse(result.local_action == "schedule_local_deletion")
        self.assertEqual(result.local_action, "pending_local_governance")
        self.assertEqual(imported, before)

    def test_locally_authorized_deletion_notice_schedules_local_deletion_only(self):
        imported, link = self.imported()
        result = evaluate_source_notice(
            imported, link,
            SourceLifecycleNotice("notice:delete", "system-a", imported["id"], NOTICE_DELETION, ("receipt:source-delete",)),
            receiver_proposal=notice_proposal("permanent_deletion", reviewed=True),
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            # Receiver-local deletion authority now needs its own evidence: a
            # record of the local decision to honour the source's notice. The
            # source receipt is not reused -- that is the sender's authority.
            evidence=_notice_corpus(imported["id"]).evidence_for(
                target_reference=imported["id"], criterion="lifecycle-notice",
                pre_state="crystallized", proposed_value="deleted",
            ),
            verifier_registry=registry_for(_notice_corpus(imported["id"])),
        )
        self.assertEqual(result.decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(result.local_action, "schedule_local_deletion")
        self.assertEqual(imported["state"], "crystallized")

    def test_correction_notice_requires_receiver_local_correction_authority(self):
        imported, link = self.imported()
        result = evaluate_source_notice(
            imported, link,
            SourceLifecycleNotice("notice:correction", "system-a", imported["id"], NOTICE_CORRECTION, ("receipt:source-correction",), source_state="corrected"),
            receiver_proposal=notice_proposal("correction", reviewed=False),
        )
        self.assertEqual(result.local_action, "pending_local_governance")
        self.assertEqual(result.decision.outcome, policy.REQUIRE_REVIEW)

    def test_notice_from_unlinked_system_is_rejected(self):
        imported, link = self.imported()
        result = evaluate_source_notice(
            imported, link,
            SourceLifecycleNotice("notice:spoof", "system-c", imported["id"], NOTICE_DELETION, ("receipt:fake",)),
            receiver_proposal=notice_proposal("permanent_deletion", reviewed=True),
        )
        self.assertFalse(result.recognized)
        self.assertEqual(result.refusal, "source_system_mismatch")


if __name__ == "__main__":
    unittest.main()
