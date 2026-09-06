from __future__ import annotations

import unittest

from agentmem_ref import policy
from agentmem_ref.approval_evidence import build_approval_evidence
from agentmem_ref.enforcement_composition import PROVIDER_NONE, build_projection, compose
from agentmem_ref.precedent_applicability import evaluate_projection
from agentmem_ref.reusable_grant_harness import (
    EXPIRES,
    GENERATED,
    ISSUED,
    OPERATION,
    POLICY,
    SCOPE,
    _grant,
    _proposal,
    projection,
    run_harness,
)
from agentmem_ref.reusable_grants import (
    evaluate_pama_with_reusable_grant,
    evaluate_reusable_grant,
    ratify_reusable_grant,
)


class ReusableGrantTests(unittest.TestCase):
    def test_adversarial_harness(self):
        report = run_harness()
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # A row was added, not re-graded: the high-risk scenario now parks
        # (R5 requires human confirmation for this proposal, which precedent
        # cannot supply) and a medium-risk row shows the discharge that remains.
        self.assertEqual(report["metrics"]["scenario_count"], 13)
        self.assertEqual(report["metrics"]["safe_review_discharges"], 1)
        self.assertEqual(report["metrics"]["unsafe_grant_activations"], 0)
        self.assertEqual(report["metrics"]["authority_transition_failures"], 0)
        self.assertEqual(report["metrics"]["policy_derived_attribution_errors"], 0)
        self.assertEqual(report["metrics"]["pama_widening_failures"], 0)
        self.assertEqual(report["metrics"]["recursive_authority_inflation_failures"], 0)
        self.assertEqual(report["metrics"]["failed_scenarios"], 0)
        self.assertTrue(report["duplicate-history-guard"]["passed"])

    def test_proposal_cannot_self_ratify_with_historical_decision(self):
        proposal_doc = _proposal(projection("projection:self-ratify"))
        with self.assertRaisesRegex(ValueError, "separate authority transition"):
            ratify_reusable_grant(
                proposal_doc,
                ratification_ref=proposal_doc["supporting_human_decision_refs"][0],
                ratifying_principal_ref="principal:operator",
                ratifier_authority_evidence_ref="authority:operator",
                ratifier_authority_verified=True,
                approved_operation=proposal_doc["requested_operation"],
                approved_scope_refs=tuple(proposal_doc["scope_refs"]),
                approved_material_conditions=tuple(proposal_doc["material_conditions"]),
                policy_version_ref=proposal_doc["policy_version_ref"],
                issued_at=ISSUED,
                expires_at=EXPIRES,
                revocation_mechanism_ref=proposal_doc["revocation_mechanism_ref"],
            )

    def test_unverified_ratifier_cannot_create_grant(self):
        proposal_doc = _proposal(projection("projection:unverified-ratifier"))
        with self.assertRaisesRegex(ValueError, "independently verified"):
            ratify_reusable_grant(
                proposal_doc,
                ratification_ref="ratification:new",
                ratifying_principal_ref="principal:operator",
                ratifier_authority_evidence_ref="authority:operator",
                ratifier_authority_verified=False,
                approved_operation=proposal_doc["requested_operation"],
                approved_scope_refs=tuple(proposal_doc["scope_refs"]),
                approved_material_conditions=tuple(proposal_doc["material_conditions"]),
                policy_version_ref=proposal_doc["policy_version_ref"],
                issued_at=ISSUED,
                expires_at=EXPIRES,
                revocation_mechanism_ref=proposal_doc["revocation_mechanism_ref"],
            )

    def test_ratification_cannot_widen_scope_operation_or_expiry(self):
        proposal_doc = _proposal(projection("projection:no-widen"))
        common = dict(
            ratification_ref="ratification:new",
            ratifying_principal_ref="principal:operator",
            ratifier_authority_evidence_ref="authority:operator",
            ratifier_authority_verified=True,
            approved_material_conditions=tuple(proposal_doc["material_conditions"]),
            policy_version_ref=POLICY,
            issued_at=ISSUED,
            revocation_mechanism_ref=proposal_doc["revocation_mechanism_ref"],
        )
        with self.assertRaisesRegex(ValueError, "operation"):
            ratify_reusable_grant(proposal_doc, approved_operation="correction", approved_scope_refs=(SCOPE,), expires_at=EXPIRES, **common)
        with self.assertRaisesRegex(ValueError, "scope"):
            ratify_reusable_grant(proposal_doc, approved_operation=OPERATION, approved_scope_refs=("tenant:b",), expires_at=EXPIRES, **common)
        with self.assertRaisesRegex(ValueError, "validity"):
            ratify_reusable_grant(proposal_doc, approved_operation=OPERATION, approved_scope_refs=(SCOPE,), expires_at="2026-08-15T16:00:00Z", **common)

    def test_one_action_approval_remains_non_reusable(self):
        p = policy.Proposal(
            proposal_id="proposal:one-action",
            actor_id="agent:fixture",
            charter_version="charter:v1",
            target_reference="memory:alpha",
            target_class=policy.M2,
            scope=SCOPE,
            operation=OPERATION,
            current_strength="medium",
            proposed_strength="medium",
            downstream_authority=policy.A1,
            reversibility="reversible",
            risk_class="high",
            evidence_refs=("evidence:1",),
            state_snapshot="state:v1",
            tenant_ref=SCOPE,
            purpose="test",
        )
        decision = policy.evaluate(p)
        composition = compose(build_projection(p, decision), provider_mode=PROVIDER_NONE)
        approval = build_approval_evidence(
            composition,
            principal_ref="principal:operator",
            authority_evidence_ref="authority:operator",
            scope_ref=SCOPE,
            outcome="approved",
            mechanism_ref="approval-host:test",
            issued_at=GENERATED,
            expires_at=EXPIRES,
        )
        self.assertFalse(approval["reusable_authority"])

    def test_semantic_projection_cannot_seed_grant_proposal(self):
        proj = projection("projection:semantic")
        proj["derivation"] = {
            "mode": "semantic_similarity",
            "reconstructable": True,
            "source_snapshot_ref": "snapshot:semantic",
            "estimator_ref": "estimator:test",
            "estimator_version": "1",
            "uncertainty_summary": {},
        }
        with self.assertRaisesRegex(ValueError, "exact_identity or deterministic_condition_match"):
            evaluate_projection(proj)

    def test_current_grant_cannot_discharge_external_verification(self):
        proj = projection("projection:pama-external")
        proposal_doc = _proposal(proj)
        grant = _grant(proposal_doc)
        evaluation = evaluate_reusable_grant(
            grant,
            proj,
            expected_operation=OPERATION,
            current_policy_version_ref=POLICY,
            observed_at="2026-08-13T17:00:00Z",
            ratification_evidence_present=True,
        )
        pama = policy.Proposal(
            proposal_id="pama:external",
            actor_id="agent:fixture",
            charter_version="charter:v1",
            target_reference="memory:alpha",
            target_class=policy.M4,
            scope=SCOPE,
            operation="correction",
            current_strength="medium",
            proposed_strength="medium",
            downstream_authority=policy.A4,
            reversibility="irreversible",
            risk_class="critical",
            evidence_refs=("evidence:1",),
        )
        decision = evaluate_pama_with_reusable_grant(pama, evaluation)
        self.assertEqual(decision.outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)


if __name__ == "__main__":
    unittest.main()
