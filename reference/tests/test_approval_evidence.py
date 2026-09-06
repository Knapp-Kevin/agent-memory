"""Approval continuity tests for issue #187 / #152."""

from __future__ import annotations

import copy
import json
import unittest
from dataclasses import replace
from pathlib import Path

from agentmem_ref import policy
from agentmem_ref.approval_evidence import build_approval_evidence, verify_approval_evidence
from agentmem_ref.enforcement_composition import PROVIDER_NONE, build_projection, compose
from agentmem_ref.enforcement_evidence import build_execution_witness

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "approval-evidence-matrix.json"
OPERATION = "promotion"


def _proposal(*, proposal_id: str = "proposal:approval", state_snapshot: str = "state:v1") -> policy.Proposal:
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="agent:planner",
        charter_version="charter:approval",
        target_reference="mem:approval",
        target_class=policy.M4,
        scope="tenant-a",
        operation=OPERATION,
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A3,
        reversibility="reversible",
        risk_class="high",
        evidence_refs=("evidence:proposal",),
        state_snapshot=state_snapshot,
        tenant_ref="tenant-a",
        purpose="approval-continuity",
        isolation_domain_refs=("domain:project-a",),
        required_isolation_domain_refs=("domain:project-a",),
    )


def _decision(outcome: str) -> policy.Decision:
    if outcome == policy.REQUIRE_REVIEW:
        permitted = ("enter_pending_verification", "collect_more_evidence", "defer")
        prohibited = (OPERATION,)
    elif outcome == policy.BLOCK:
        permitted = ()
        prohibited = (OPERATION, "enter_pending_verification")
    else:
        permitted = (OPERATION, "collect_more_evidence", "defer")
        prohibited = ()
    return policy.Decision(
        outcome=outcome,
        permitted_actions=permitted,
        prohibited_actions=prohibited,
        policy_version="ref-approval-test",
    )


def _composition(outcome: str, *, proposal: policy.Proposal | None = None) -> dict:
    projection = build_projection(proposal or _proposal(), _decision(outcome))
    return compose(projection, provider_mode=PROVIDER_NONE)


def _approval(composition: dict, case: dict, scope_ref: str) -> dict:
    return build_approval_evidence(
        composition,
        principal_ref="principal:human-reviewer",
        authority_evidence_ref="authority:reviewer-role:v1",
        scope_ref=scope_ref,
        outcome=case["approval_outcome"],
        mechanism_ref="approval-host:reference",
        issued_at=case["issued_at"],
        expires_at=case.get("expires_at"),
        revoked_at=case.get("revoked_at"),
        revocation_evidence_ref=case.get("revocation_evidence_ref"),
        evidence_refs=(f"evidence:{case['case_id']}",),
    )


class ApprovalEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_verification_matrix(self):
        counts = {"current": 0, "stale": 0, "invalid": 0, "denied": 0, "not_applicable": 0}
        for case in self.matrix["cases"]:
            with self.subTest(case_id=case["case_id"]):
                composition = _composition(case["composition_outcome"])
                approval = _approval(composition, case, self.matrix["scope_ref"])
                approval.update(copy.deepcopy(case["mutations"]))
                result = verify_approval_evidence(
                    approval,
                    composition,
                    expected_scope_ref=self.matrix["scope_ref"],
                    observed_at=self.matrix["observed_at"],
                )
                self.assertEqual(result["status"], case["expected_status"])
                self.assertEqual(result["satisfies_required_approval"], case["expected_satisfies"])
                self.assertFalse(result["reusable_authority"])
                counts[result["status"]] += 1

        expected = self.matrix["expected_behavior"]
        self.assertEqual(len(self.matrix["cases"]), expected["verification_cases"])
        self.assertEqual(counts["current"], expected["current_satisfying_cases"])
        self.assertEqual(counts["stale"], expected["stale_cases"])
        self.assertEqual(counts["invalid"], expected["invalid_cases"])
        self.assertEqual(counts["denied"], expected["denied_cases"])
        self.assertEqual(counts["not_applicable"], expected["not_applicable_cases"])

    def test_verified_current_approval_can_satisfy_require_approval_execution(self):
        composition = _composition(policy.REQUIRE_REVIEW)
        case = self.matrix["cases"][0]
        approval = _approval(composition, case, self.matrix["scope_ref"])
        verification = verify_approval_evidence(
            approval,
            composition,
            expected_scope_ref=self.matrix["scope_ref"],
            observed_at=self.matrix["observed_at"],
        )
        witness = build_execution_witness(
            composition,
            action_ref="action:approved-execution",
            witness_ref="runtime:audit:approved",
            enforcement_mode="mechanical",
            delivery_status="delivered",
            enforcement_point_status="reached",
            action_status="executed",
            liveness_status="healthy",
            observed_at=self.matrix["observed_at"],
            approval_verification=verification,
        )
        self.assertEqual(witness["approval_evidence_ref"], approval["approval_id"])
        self.assertEqual(witness["approval_evidence_status"], "verified_current")
        self.assertEqual(witness["decision_alignment"], "consistent")

    def test_bare_approval_reference_does_not_satisfy_require_approval(self):
        composition = _composition(policy.REQUIRE_REVIEW)
        witness = build_execution_witness(
            composition,
            action_ref="action:bare-ref",
            witness_ref="runtime:audit:bare-ref",
            enforcement_mode="cooperative",
            delivery_status="delivered",
            enforcement_point_status="reached",
            action_status="executed",
            liveness_status="healthy",
            observed_at=self.matrix["observed_at"],
            approval_evidence_ref="approval:unverified",
        )
        self.assertEqual(witness["approval_evidence_status"], "unverified")
        self.assertEqual(witness["decision_alignment"], "unverifiable")

    def test_expired_approval_remains_stale_in_execution_witness(self):
        composition = _composition(policy.REQUIRE_REVIEW)
        case = next(item for item in self.matrix["cases"] if item["case_id"] == "expired-approval")
        approval = _approval(composition, case, self.matrix["scope_ref"])
        verification = verify_approval_evidence(
            approval,
            composition,
            expected_scope_ref=self.matrix["scope_ref"],
            observed_at=self.matrix["observed_at"],
        )
        witness = build_execution_witness(
            composition,
            action_ref="action:expired-approval",
            witness_ref="runtime:audit:expired",
            enforcement_mode="cooperative",
            delivery_status="delivered",
            enforcement_point_status="reached",
            action_status="executed",
            liveness_status="healthy",
            observed_at=self.matrix["observed_at"],
            approval_verification=verification,
        )
        self.assertEqual(witness["approval_evidence_status"], "stale")
        self.assertEqual(witness["decision_alignment"], "unverifiable")

    def test_approval_cannot_widen_deny(self):
        composition = _composition(policy.BLOCK)
        case = next(item for item in self.matrix["cases"] if item["case_id"] == "approval-cannot-widen-deny")
        approval = _approval(composition, case, self.matrix["scope_ref"])
        verification = verify_approval_evidence(
            approval,
            composition,
            expected_scope_ref=self.matrix["scope_ref"],
            observed_at=self.matrix["observed_at"],
        )
        self.assertEqual(verification["status"], "not_applicable")
        self.assertFalse(verification["satisfies_required_approval"])

        witness = build_execution_witness(
            composition,
            action_ref="action:deny-still-executed",
            witness_ref="runtime:audit:deny",
            enforcement_mode="cooperative",
            delivery_status="delivered",
            enforcement_point_status="reached",
            action_status="executed",
            liveness_status="degraded",
            observed_at=self.matrix["observed_at"],
            approval_verification=verification,
        )
        self.assertEqual(witness["approval_evidence_status"], "not_applicable")
        self.assertEqual(witness["decision_alignment"], "violation")

    def test_approval_replay_against_changed_state_fails_identity_binding(self):
        first_composition = _composition(policy.REQUIRE_REVIEW, proposal=_proposal(state_snapshot="state:v1"))
        second_composition = _composition(policy.REQUIRE_REVIEW, proposal=_proposal(state_snapshot="state:v2"))
        case = self.matrix["cases"][0]
        approval = _approval(first_composition, case, self.matrix["scope_ref"])

        verification = verify_approval_evidence(
            approval,
            second_composition,
            expected_scope_ref=self.matrix["scope_ref"],
            observed_at=self.matrix["observed_at"],
        )
        self.assertEqual(verification["status"], "invalid")
        self.assertIn("input_identity_mismatch", verification["reasons"])
        self.assertFalse(verification["satisfies_required_approval"])

    def test_execution_witness_rejects_verification_from_other_composition(self):
        first_composition = _composition(policy.REQUIRE_REVIEW, proposal=_proposal(proposal_id="proposal:first"))
        second_composition = _composition(policy.REQUIRE_REVIEW, proposal=_proposal(proposal_id="proposal:second"))
        case = self.matrix["cases"][0]
        approval = _approval(first_composition, case, self.matrix["scope_ref"])
        verification = verify_approval_evidence(
            approval,
            first_composition,
            expected_scope_ref=self.matrix["scope_ref"],
            observed_at=self.matrix["observed_at"],
        )

        with self.assertRaisesRegex(ValueError, "approval verification input identity"):
            build_execution_witness(
                second_composition,
                action_ref="action:replay",
                witness_ref="runtime:audit:replay",
                enforcement_mode="mechanical",
                delivery_status="delivered",
                enforcement_point_status="reached",
                action_status="executed",
                liveness_status="healthy",
                observed_at=self.matrix["observed_at"],
                approval_verification=verification,
            )


if __name__ == "__main__":
    unittest.main()
