"""Executable boundary-crossing receipt evidence for proposed ADR-022."""

from __future__ import annotations

import sys
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.crossing import CrossingRequest, evaluate_crossing  # noqa: E402


def proposal(**overrides) -> policy.Proposal:
    base = dict(
        proposal_id="crossing-1",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference="mem:security-summary",
        target_class=policy.M4,
        scope="tenant-a",
        operation="scope_expansion",
        current_strength="crystallized",
        proposed_strength="crystallized",
        downstream_authority=policy.A2,
        reversibility="reversible",
        risk_class="medium",
        evidence_refs=("evidence:source-scope",),
        tenant_ref="tenant-a",
        purpose="security-review",
    )
    base.update(overrides)
    return policy.Proposal(**base)


def request(**overrides) -> CrossingRequest:
    base = dict(
        operation="share",
        source_domain_refs=("domain:project-a",),
        destination_domain_refs=("domain:shared-security",),
        actor="agent:planner",
        principal="user:alice",
        purpose="security-review",
        representation_kind="summary",
        source_refs=("mem:security-summary",),
        sensitivity_labels=("internal",),
        membership_refs=("membership:shared-security",),
        authority_refs=("authority:security-share",),
        policy_refs=("policy:memory-scope",),
        provenance_refs=("provenance:summary-build",),
        before_scope_refs=("domain:project-a",),
        after_scope_refs=("domain:shared-security",),
    )
    base.update(overrides)
    return CrossingRequest(**base)


def _crossing_corpus(target, to_domain="domain:partner-analytics"):
    """The evaluator's adjudication of permitted export destinations.

    ADR-037 step 4b-2 (entry #24): authored ahead of any proposal, so a caller
    can present a crossing against it but cannot author one. Authority
    (`approval:security-owner`) stays in the receipt, not in the evidential
    class.
    """
    return corpus_for(rule(
        rule_id="rule:approved-export", target=target, criterion="scope-expansion",
        from_state="domain:internal", to_values=(to_domain,),
    ))


def _crossing_evidence(target, to_domain="domain:partner-analytics"):
    corpus = _crossing_corpus(target, to_domain)
    return (
        corpus.evidence_for(target_reference=target, criterion="scope-expansion",
                            pre_state="domain:internal", proposed_value=to_domain),
        registry_for(corpus),
    )


class BoundaryCrossingTests(unittest.TestCase):
    def test_unreviewed_scope_crossing_is_receipted_but_not_committed(self):
        result = evaluate_crossing(
            request(),
            proposal(),
            receipt_id="crossing:review-required",
            timestamp="2026-08-11T20:00:00Z",
        )

        self.assertFalse(result.committed)
        self.assertEqual(result.decision.outcome, policy.REQUIRE_REVIEW)
        self.assertEqual(result.receipt["outcome"], "review_required")
        self.assertEqual(result.receipt["source_domain_refs"], ["domain:project-a"])
        self.assertEqual(result.receipt["destination_domain_refs"], ["domain:shared-security"])

    def test_external_review_can_commit_crossing_without_changing_source_semantics(self):
        _ev, _reg = _crossing_evidence("mem:security-summary", "domain:shared-security")
        result = evaluate_crossing(
            request(),
            proposal(
                review_satisfied=True,
                approval_refs=("approval:security-owner",),
            ),
            receipt_id="crossing:committed",
            timestamp="2026-08-11T20:00:01Z",
            decision_receipt_ref="decision:scope-expansion",
            ledger_ref="ledger:crossing-1",
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_ev, verifier_registry=_reg,
        )

        self.assertTrue(result.committed)
        self.assertEqual(result.decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(result.receipt["outcome"], "committed")
        self.assertEqual(result.receipt["pama_disposition"], "allow_with_ledger")
        self.assertEqual(result.receipt["operation"], "share")
        self.assertEqual(result.receipt["requested_consequence"], "scope_expansion")

    def test_crossing_disguised_as_ordinary_operation_is_blocked(self):
        result = evaluate_crossing(
            request(operation="summarize_for"),
            proposal(operation="promotion"),
            receipt_id="crossing:disguised",
            timestamp="2026-08-11T20:00:02Z",
        )

        self.assertFalse(result.committed)
        self.assertEqual(result.decision.outcome, policy.BLOCK)
        self.assertEqual(result.receipt["outcome"], "blocked")
        self.assertIn("scope_expansion", result.decision.prohibited_actions)

    def test_self_approval_blocks_crossing(self):
        result = evaluate_crossing(
            request(operation="export"),
            proposal(
                approves_own_authority=True,
                review_satisfied=True,
                approval_refs=("approval:self",),
            ),
            receipt_id="crossing:self-approved",
            timestamp="2026-08-11T20:00:03Z",
        )

        self.assertFalse(result.committed)
        self.assertEqual(result.decision.outcome, policy.BLOCK)
        self.assertEqual(result.receipt["outcome"], "blocked")

    def test_privacy_minimized_representation_does_not_self_authorize_export(self):
        result = evaluate_crossing(
            request(
                operation="export",
                destination_domain_refs=("domain:external-partner",),
                privacy_minimized=True,
                redaction_ref="redaction:approved-shape",
            ),
            proposal(),
            receipt_id="crossing:minimized",
            timestamp="2026-08-11T20:00:04Z",
        )

        self.assertFalse(result.committed)
        self.assertTrue(result.receipt["representation"]["privacy_minimized"])
        self.assertEqual(result.receipt["outcome"], "review_required")

    def test_reviewed_privacy_minimized_export_can_commit_without_redaction_becoming_authority(self):
        _ev2, _reg2 = _crossing_evidence("mem:security-summary", "domain:external-partner")
        result = evaluate_crossing(
            request(
                operation="export",
                destination_domain_refs=("domain:external-partner",),
                representation_kind="redacted_summary",
                privacy_minimized=True,
                redaction_ref="redaction:approved-shape",
                after_scope_refs=("domain:external-partner",),
                authority_refs=("authority:external-export",),
            ),
            proposal(
                review_satisfied=True,
                approval_refs=("approval:data-owner",),
            ),
            receipt_id="crossing:authorized-redacted-export",
            timestamp="2026-08-11T20:00:05Z",
            decision_receipt_ref="decision:authorized-redacted-export",
            ledger_ref="ledger:authorized-redacted-export",
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            # The redaction still confers no authority -- that property is
            # asserted below and unchanged. Only the discharge route moved.
            evidence=_ev2, verifier_registry=_reg2,
        )

        self.assertTrue(result.committed)
        self.assertEqual(result.decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(result.receipt["operation"], "export")
        self.assertEqual(result.receipt["destination_domain_refs"], ["domain:external-partner"])
        self.assertEqual(result.receipt["representation"]["kind"], "redacted_summary")
        self.assertTrue(result.receipt["representation"]["privacy_minimized"])
        self.assertEqual(result.receipt["representation"]["redaction_ref"], "redaction:approved-shape")
        self.assertEqual(result.receipt["pama_disposition"], "allow_with_ledger")
        self.assertEqual(result.receipt["decision_receipt_ref"], "decision:authorized-redacted-export")

    def test_crossing_requires_explicit_source_and_destination_domains(self):
        with self.assertRaises(ValueError):
            evaluate_crossing(
                request(destination_domain_refs=()),
                proposal(),
                receipt_id="crossing:missing-domain",
                timestamp="2026-08-11T20:00:06Z",
            )


if __name__ == "__main__":
    unittest.main()
