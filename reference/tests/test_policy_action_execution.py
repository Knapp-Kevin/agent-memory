"""Sprint 4c-2 (ADR-038, plan LD2/LD2b): `action_execution` in the base table, the authority-class
floors independent of it, and `Decision.constraints` derived from the proposal so a discharge cannot
remove them. The 52 pre-existing cells and both floors are pinned as literals before the table is
extended."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref import receipts  # noqa: E402
from agentmem_ref.core.evidence_qualification import EvidenceItem, group_by_dependence  # noqa: E402

ALLOW = "allow_with_ledger"
REVIEW = "require_review"
EXTERNAL = "require_external_verification"
BLOCK = "block"
RISKS = ("low", "medium", "high", "critical")

FROZEN = {
    ("runtime_assembly", "low"): ALLOW, ("runtime_assembly", "medium"): ALLOW, ("runtime_assembly", "high"): REVIEW, ("runtime_assembly", "critical"): REVIEW,
    ("score_adjustment", "low"): ALLOW, ("score_adjustment", "medium"): ALLOW, ("score_adjustment", "high"): REVIEW, ("score_adjustment", "critical"): BLOCK,
    ("link_creation", "low"): ALLOW, ("link_creation", "medium"): ALLOW, ("link_creation", "high"): REVIEW, ("link_creation", "critical"): REVIEW,
    ("link_deletion", "low"): ALLOW, ("link_deletion", "medium"): REVIEW, ("link_deletion", "high"): REVIEW, ("link_deletion", "critical"): EXTERNAL,
    ("correction", "low"): REVIEW, ("correction", "medium"): REVIEW, ("correction", "high"): REVIEW, ("correction", "critical"): EXTERNAL,
    ("decision_overwrite", "low"): REVIEW, ("decision_overwrite", "medium"): REVIEW, ("decision_overwrite", "high"): EXTERNAL, ("decision_overwrite", "critical"): EXTERNAL,
    ("domain_schema_mutation", "low"): REVIEW, ("domain_schema_mutation", "medium"): REVIEW, ("domain_schema_mutation", "high"): EXTERNAL, ("domain_schema_mutation", "critical"): EXTERNAL,
    ("promotion", "low"): ALLOW, ("promotion", "medium"): REVIEW, ("promotion", "high"): REVIEW, ("promotion", "critical"): EXTERNAL,
    ("crystallization", "low"): REVIEW, ("crystallization", "medium"): REVIEW, ("crystallization", "high"): EXTERNAL, ("crystallization", "critical"): EXTERNAL,
    ("pruning", "low"): ALLOW, ("pruning", "medium"): ALLOW, ("pruning", "high"): REVIEW, ("pruning", "critical"): EXTERNAL,
    ("permanent_deletion", "low"): REVIEW, ("permanent_deletion", "medium"): REVIEW, ("permanent_deletion", "high"): EXTERNAL, ("permanent_deletion", "critical"): EXTERNAL,
    ("scope_expansion", "low"): REVIEW, ("scope_expansion", "medium"): REVIEW, ("scope_expansion", "high"): EXTERNAL, ("scope_expansion", "critical"): BLOCK,
    ("policy_mutation", "low"): REVIEW, ("policy_mutation", "medium"): EXTERNAL, ("policy_mutation", "high"): EXTERNAL, ("policy_mutation", "critical"): EXTERNAL,
}
ACTION_CELLS = (ALLOW, REVIEW, REVIEW, EXTERNAL)
A4_CELLS = (REVIEW, REVIEW, REVIEW, EXTERNAL)
A5_CELLS = (EXTERNAL, EXTERNAL, EXTERNAL, EXTERNAL)
# The cells the floor lifts: A4 at low; A5 at low, medium, high. Elsewhere the cell already equals
# or exceeds the floor and `_apply_floors` (strict `>`) emits no reason.
LIFTED = {(policy.A4, "low"), (policy.A5, "low"), (policy.A5, "medium"), (policy.A5, "high")}


def _action(risk: str, authority: str = policy.A3, *, operation: str = "action_execution", target_class: str = policy.M3) -> policy.Proposal:
    """An action proposal carrying no modifier lift: one evidence ref, reversible, domains bound."""
    return policy.Proposal(
        proposal_id=f"p-{operation}-{authority}-{risk}", actor_id="agent:a", charter_version="v1",
        target_reference="skill:release-workflow@v1", target_class=target_class, scope="project:example",
        operation=operation, current_strength="promoted", proposed_strength="promoted",
        downstream_authority=authority, reversibility="reversible", risk_class=risk,
        evidence_refs=("evidence:release-notes",), state_snapshot="v1",
        isolation_domain_refs=("domain:project-a",), required_isolation_domain_refs=("domain:project-a",),
    )


class ExistingTablePinned(unittest.TestCase):
    def test_existing_cells_and_floors_unchanged(self):
        self.assertEqual({k: v for k, v in policy._BASE_TABLE.items() if k[0] != "action_execution"}, FROZEN)
        self.assertEqual(len(FROZEN), 52)
        self.assertEqual(policy._AUTHORITY_FLOOR, {policy.A4: REVIEW, policy.A5: EXTERNAL})
        self.assertEqual(policy._TARGET_FLOOR, {policy.M4: REVIEW, policy.M5: REVIEW})


class ActionExecutionMatrix(unittest.TestCase):
    def test_action_execution_matrix(self):
        expected = {policy.A0: ACTION_CELLS, policy.A1: ACTION_CELLS, policy.A2: ACTION_CELLS, policy.A3: ACTION_CELLS,
                    policy.A4: A4_CELLS, policy.A5: A5_CELLS}
        checked = 0
        for authority, cells in expected.items():
            for risk, cell in zip(RISKS, cells):
                with self.subTest(authority=authority, risk=risk):
                    decision = policy.evaluate(_action(risk, authority))
                    self.assertEqual(decision.outcome, cell)
                    floor_reason = f"authority floor {authority}"
                    if (authority, risk) in LIFTED:
                        self.assertIn(floor_reason, decision.reasons)
                    else:
                        self.assertNotIn(floor_reason, decision.reasons)
                    checked += 1
        self.assertEqual(checked, 24)

    def test_authority_change_still_falls_through(self):
        for risk in RISKS:
            with self.subTest(risk=risk):
                decision = policy.evaluate(_action(risk, operation="authority_change"))
                self.assertEqual(decision.outcome, REVIEW)
                self.assertFalse(any(reason.startswith("authority floor") for reason in decision.reasons))
        self.assertNotIn(("authority_change", "low"), policy._BASE_TABLE)

    def test_schema_admits_action_execution(self):
        proposal = _action("low")
        decision = policy.evaluate(proposal)
        document = receipts.build_pama_decision(proposal, decision, "action_execution", "deterministic", "receipt-1")
        self.assertEqual(document["mutation"]["operation"], "action_execution")
        self.assertEqual(document["decision"]["outcome"], ALLOW)
        with self.assertRaises(ValueError):
            receipts.build_pama_decision(_action("low", operation="action_transmutation"),
                                         policy.evaluate(_action("low")), "action_transmutation", "deterministic", "receipt-2")


class ConstraintsDerivedFromProposal(unittest.TestCase):
    def test_constraints_are_derived_from_the_proposal(self):
        self.assertEqual(policy.evaluate(_action("low", policy.A3)).constraints, ("risk_cell",))
        self.assertEqual(policy.evaluate(_action("low", policy.A4)).constraints, ("risk_cell", f"authority_floor:{policy.A4}"))
        self.assertEqual(policy.evaluate(_action("medium", policy.A4)).constraints, ("risk_cell", f"authority_floor:{policy.A4}"))
        self.assertEqual(policy.evaluate(_action("low", policy.A3, target_class=policy.M4)).constraints,
                         ("risk_cell", f"target_floor:{policy.M4}"))
        self.assertEqual(policy.evaluate(_action("low", policy.A5, target_class=policy.M5)).constraints,
                         ("risk_cell", f"target_floor:{policy.M5}", f"authority_floor:{policy.A5}"))

    def test_discharge_keeps_the_authority_constraint(self):
        # A memory operation at A4/low: the cell is allow_with_ledger, the floor lifts it to
        # require_review, and one asserted artifact-bound item discharges that review on the
        # memory path. The constraint survives the discharge; only the outcome changes.
        proposal = _action("low", policy.A4, operation="promotion", target_class=policy.M2)
        item = EvidenceItem(ref="evidence:release-notes", artifact_ref="artifact:notes", digest="sha256:" + "0" * 64,
                            verifier="unregistered", failure_domain="test")
        discharged = policy.evaluate_with_qualified_evidence(proposal, group_by_dependence((item,)))
        self.assertEqual(discharged.outcome, ALLOW)
        self.assertIn(f"authority_floor:{policy.A4}", discharged.constraints)
        attested = policy.evaluate_with_external_verification(
            _action("low", policy.A5, operation="promotion", target_class=policy.M2),
            policy.ExternalVerification(bound_proposal_id="p-promotion-A5_GOVERNANCE_CHANGE-low", verifier_principal_id="policy:delegate",
                                        authority_kind=policy.DELEGATED_POLICY, max_risk_class="critical"))
        self.assertEqual(attested.outcome, ALLOW)
        self.assertIn(f"authority_floor:{policy.A5}", attested.constraints)


if __name__ == "__main__":
    unittest.main()
