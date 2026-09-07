"""Execution witness and enforcement posture tests for issue #152 Phase 3."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agentmem_ref import policy
from agentmem_ref.enforcement_composition import PROVIDER_NONE, build_projection, compose
from agentmem_ref.enforcement_evidence import build_execution_witness, build_posture_report

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "enforcement-evidence-matrix.json"
OPERATION = "promotion"


def _proposal() -> policy.Proposal:
    return policy.Proposal(
        proposal_id="proposal:enforcement-evidence",
        actor_id="agent:planner",
        charter_version="charter:enforcement-evidence",
        target_reference="mem:enforcement-evidence",
        target_class=policy.M4,
        scope="tenant-a",
        operation=OPERATION,
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A3,
        reversibility="reversible",
        risk_class="high",
        evidence_refs=("evidence:proposal",),
        state_snapshot="state:v1",
        tenant_ref="tenant-a",
        purpose="enforcement-evidence",
        isolation_domain_refs=("domain:project-a",),
        required_isolation_domain_refs=("domain:project-a",),
    )


def _decision(outcome: str) -> policy.Decision:
    if outcome in (policy.ALLOW, policy.ALLOW_WITH_LEDGER):
        permitted = (OPERATION, "collect_more_evidence", "defer")
        prohibited = ()
    elif outcome == policy.REQUIRE_REVIEW:
        permitted = ("enter_pending_verification", "collect_more_evidence", "defer")
        prohibited = (OPERATION,)
    elif outcome == policy.REQUIRE_EXTERNAL_VERIFICATION:
        permitted = ("request_external_verification", "collect_more_evidence", "defer")
        prohibited = (OPERATION,)
    else:
        permitted = ()
        prohibited = (OPERATION,)
    return policy.Decision(
        outcome=outcome,
        permitted_actions=permitted,
        prohibited_actions=prohibited,
        policy_version="ref-enforcement-evidence-test",
    )


def _composition(outcome: str) -> dict:
    projection = build_projection(_proposal(), _decision(outcome))
    return compose(projection, provider_mode=PROVIDER_NONE)


class EnforcementEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_witness_matrix(self):
        violation_count = 0
        for case in self.matrix["witness_cases"]:
            with self.subTest(case_id=case["case_id"]):
                composition = _composition(case["local_pama_outcome"])
                witness = build_execution_witness(
                    composition,
                    action_ref=f"action:{case['case_id']}",
                    witness_ref=f"witness-source:{case['case_id']}",
                    enforcement_mode=case["enforcement_mode"],
                    delivery_status=case["delivery_status"],
                    enforcement_point_status=case["enforcement_point_status"],
                    action_status=case["action_status"],
                    liveness_status=case["liveness_status"],
                    observed_at="2026-08-12T21:20:00Z",
                    evidence_refs=(f"evidence:{case['case_id']}",),
                )
                self.assertEqual(witness["input_identity"], composition["input_identity"])
                self.assertEqual(witness["composition_id"], composition["composition_id"])
                self.assertEqual(witness["decision_alignment"], case["expected_alignment"])
                self.assertIn("lifecycle_satisfaction_not_established", witness["non_claims"])
                self.assertIn("execution_witness_does_not_create_memory_authority", witness["non_claims"])
                if witness["decision_alignment"] == "violation":
                    violation_count += 1

        self.assertEqual(violation_count, self.matrix["expected_behavior"]["decision_violations_observed"])
        self.assertEqual(len(self.matrix["witness_cases"]), self.matrix["expected_behavior"]["witness_cases"])

    def test_denied_action_executing_is_negative_evidence_not_invalid_input(self):
        composition = _composition(policy.BLOCK)
        witness = build_execution_witness(
            composition,
            action_ref="action:executed-despite-deny",
            witness_ref="runtime:audit:1",
            enforcement_mode="cooperative",
            delivery_status="delivered",
            enforcement_point_status="reached",
            action_status="executed",
            liveness_status="degraded",
            observed_at="2026-08-12T21:20:00Z",
        )
        self.assertEqual(witness["effective_decision"], "deny")
        self.assertEqual(witness["action_status"], "executed")
        self.assertEqual(witness["decision_alignment"], "violation")

    def test_witness_identity_mismatch_is_rejected(self):
        composition = _composition(policy.ALLOW_WITH_LEDGER)
        with self.assertRaisesRegex(ValueError, "input identity"):
            build_execution_witness(
                composition,
                action_ref="action:mismatch",
                witness_ref="runtime:audit:mismatch",
                enforcement_mode="mechanical",
                delivery_status="delivered",
                enforcement_point_status="reached",
                action_status="executed",
                liveness_status="healthy",
                observed_at="2026-08-12T21:20:00Z",
                observed_input_identity="sha256:" + "0" * 64,
            )

    def test_action_outcome_requires_observed_enforcement_point(self):
        composition = _composition(policy.BLOCK)
        with self.assertRaisesRegex(ValueError, "without observing the enforcement point"):
            build_execution_witness(
                composition,
                action_ref="action:overclaim",
                witness_ref="runtime:audit:overclaim",
                enforcement_mode="unknown",
                delivery_status="delivered",
                enforcement_point_status="not_observed",
                action_status="prevented",
                liveness_status="unknown",
                observed_at="2026-08-12T21:20:00Z",
            )

    def test_posture_matrix_separates_configuration_capability_and_observation(self):
        counts = {
            "configuration_only": 0,
            "witness_capability_only": 0,
            "observed_enforcement": 0,
        }
        for case in self.matrix["posture_cases"]:
            with self.subTest(case_id=case["case_id"]):
                report = build_posture_report(
                    policy_context_ref="policy-context:fixture",
                    configured_governance=case["configured_governance"],
                    memory_write=case["memory_write"],
                    recall_admission=case["recall_admission"],
                    background_maintenance=case["background_maintenance"],
                    external_import=case["external_import"],
                    execution_witness=case["execution_witness"],
                    observed_witness_count=case["observed_witness_count"],
                    liveness_status=case["liveness_status"],
                    generated_at="2026-08-12T21:20:00Z",
                    evidence_refs=(f"evidence:{case['case_id']}",),
                )
                self.assertEqual(report["evidence_scope"], case["expected_evidence_scope"])
                counts[report["evidence_scope"]] += 1

        self.assertEqual(counts["configuration_only"], self.matrix["expected_behavior"]["configuration_only_postures"])
        self.assertEqual(counts["witness_capability_only"], self.matrix["expected_behavior"]["witness_capability_only_postures"])
        self.assertEqual(counts["observed_enforcement"], self.matrix["expected_behavior"]["observed_enforcement_postures"])

    def test_absent_witness_capability_cannot_claim_observed_witnesses(self):
        with self.assertRaisesRegex(ValueError, "absent execution witness"):
            build_posture_report(
                policy_context_ref="policy-context:invalid",
                configured_governance=True,
                memory_write="cooperative",
                recall_admission="unknown",
                background_maintenance="unknown",
                external_import="cooperative",
                execution_witness="absent",
                observed_witness_count=1,
                liveness_status="degraded",
                generated_at="2026-08-12T21:20:00Z",
            )


if __name__ == "__main__":
    unittest.main()
