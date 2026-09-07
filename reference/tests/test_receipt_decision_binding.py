"""Decision receipt completeness and backward-compatibility tests.

Run: python -m unittest discover -s reference/tests -t reference
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy, receipts  # noqa: E402


class ReceiptDecisionBindingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.proposal = policy.Proposal(
            proposal_id="proposal:receipt-binding",
            actor_id="actor:test",
            charter_version="charter:1",
            target_reference="memory:test",
            target_class=policy.M2,
            scope="project:test",
            operation="promotion",
            current_strength="tentative",
            proposed_strength="promoted",
            downstream_authority=policy.A1,
            reversibility="reversible",
            risk_class="low",
            evidence_refs=("evidence:test",),
            state_snapshot="v1",
        )
        self.decision = policy.evaluate(self.proposal)
        self.assertEqual(self.decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.receipt = receipts.build_receipt(
            receipt_id="receipt:test",
            proposal=self.proposal,
            decision=self.decision,
            selected_action="promotion",
            selection_mode="deterministic",
            timestamp="2026-08-12T00:00:00Z",
            before_state="v1",
            after_state="v2",
        )
        self.pama = receipts.build_pama_decision(
            self.proposal,
            self.decision,
            "promotion",
            "deterministic",
            "receipt:test",
        )

    def test_new_receipt_reconstructs_authority_and_backlinks_to_decision(self):
        self.assertEqual(self.receipt["schema_version"], "1.1.0")
        self.assertEqual(
            self.receipt["decision_ref"],
            receipts.decision_ref_for(self.proposal.proposal_id),
        )
        self.assertEqual(self.receipt["decision_outcome"], policy.ALLOW_WITH_LEDGER)
        receipts.verify_receipt_decision_pair(self.receipt, self.pama)

    def test_historical_1_0_receipt_remains_schema_valid(self):
        historical = {
            "schema_version": "1.0.0",
            "receipt_id": "receipt:historical",
            "requested_action": "promotion",
            "policy_version": "ref-p1",
            "permitted_actions": ["promotion"],
            "prohibited_actions": [],
            "selected_action": "promotion",
            "selection_mode": "deterministic",
            "timestamp": "2026-08-01T00:00:00Z",
        }
        receipts.validate("decision-receipt.schema.json", historical)

    def test_1_1_receipt_requires_decision_ref(self):
        mutant = copy.deepcopy(self.receipt)
        mutant.pop("decision_ref")
        with self.assertRaises(ValueError):
            receipts.validate("decision-receipt.schema.json", mutant)

    def test_1_1_receipt_requires_decision_outcome(self):
        mutant = copy.deepcopy(self.receipt)
        mutant.pop("decision_outcome")
        with self.assertRaises(ValueError):
            receipts.validate("decision-receipt.schema.json", mutant)

    def test_wrong_decision_ref_is_rejected(self):
        mutant = copy.deepcopy(self.receipt)
        mutant["decision_ref"] = "pama-decision:other"
        with self.assertRaisesRegex(ValueError, "decision_ref"):
            receipts.verify_receipt_decision_pair(mutant, self.pama)

    def test_wrong_decision_outcome_is_rejected(self):
        mutant = copy.deepcopy(self.receipt)
        mutant["decision_outcome"] = "require_review"
        with self.assertRaisesRegex(ValueError, "decision_outcome"):
            receipts.verify_receipt_decision_pair(mutant, self.pama)

    def test_wrong_receipt_backlink_is_rejected(self):
        mutant = copy.deepcopy(self.pama)
        mutant["decision"]["decision_receipt_ref"] = "receipt:other"
        with self.assertRaisesRegex(ValueError, "does not point back"):
            receipts.verify_receipt_decision_pair(self.receipt, mutant)

    def test_outcome_envelope_inconsistency_is_rejected_at_build_time(self):
        inconsistent = policy.Decision(
            outcome=policy.ALLOW_WITH_LEDGER,
            permitted_actions=("collect_more_evidence",),
            prohibited_actions=("promotion",),
            policy_version=policy.POLICY_VERSION,
        )
        with self.assertRaisesRegex(ValueError, "must permit the requested action"):
            receipts.build_receipt(
                receipt_id="receipt:bad",
                proposal=self.proposal,
                decision=inconsistent,
                selected_action="collect_more_evidence",
                selection_mode="deterministic",
                timestamp="2026-08-12T00:00:00Z",
                before_state="v1",
                after_state="v1",
            )


if __name__ == "__main__":
    unittest.main()
