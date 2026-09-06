"""Vendor-neutral external policy composition tests for issue #152."""

from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

from agentmem_ref import policy
from agentmem_ref.enforcement_composition import (
    ALLOW,
    DENY,
    EXECUTION_UNKNOWN,
    PROVIDER_ADVISORY,
    PROVIDER_AUTHORITATIVE,
    PROVIDER_NONE,
    REQUIRE_APPROVAL,
    STATUS_AVAILABLE,
    STATUS_INVALID,
    STATUS_STALE_IDENTITY,
    DeterministicFakeProvider,
    build_external_decision,
    build_projection,
    compose,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "external-policy-composition-matrix.json"
OPERATION = "promotion"


def _proposal(*, state_snapshot: str = "v1") -> policy.Proposal:
    return policy.Proposal(
        proposal_id="proposal:external-policy",
        actor_id="agent:planner",
        charter_version="charter:external-policy",
        target_reference="mem:external-policy",
        target_class=policy.M4,
        scope="tenant-a",
        operation=OPERATION,
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A3,
        reversibility="reversible",
        risk_class="medium",
        evidence_refs=("evidence:proposal",),
        state_snapshot=state_snapshot,
        tenant_ref="tenant-a",
        purpose="external-policy-composition",
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
    elif outcome == policy.BLOCK:
        permitted = ()
        prohibited = (OPERATION, "enter_pending_verification", "request_external_verification")
    else:
        permitted = ("collect_more_evidence", "defer")
        prohibited = (OPERATION,)
    return policy.Decision(
        outcome=outcome,
        permitted_actions=permitted,
        prohibited_actions=prohibited,
        policy_version="ref-external-policy-test",
    )


def _external(projection: dict, decision: str, *, stale: bool = False) -> dict:
    identity = projection["input_identity"]
    if stale:
        identity = "sha256:" + ("0" * 64 if identity != "sha256:" + "0" * 64 else "1" * 64)
    return build_external_decision(
        provider_id="fixture-provider",
        provider_version="1.0.0",
        input_identity=identity,
        decision=decision,
        reason=f"fixture decision {decision}",
        issued_at="2026-08-12T18:00:00Z",
        evidence={"fixture": True},
    )


class EnforcementCompositionTests(unittest.TestCase):
    def test_projection_identity_binds_state_and_pama_outcome(self):
        proposal = _proposal(state_snapshot="v1")
        allow = build_projection(proposal, _decision(policy.ALLOW_WITH_LEDGER))
        state_changed = build_projection(replace(proposal, state_snapshot="v2"), _decision(policy.ALLOW_WITH_LEDGER))
        decision_changed = build_projection(proposal, _decision(policy.REQUIRE_REVIEW))

        self.assertNotEqual(allow["input_identity"], state_changed["input_identity"])
        self.assertNotEqual(allow["input_identity"], decision_changed["input_identity"])
        self.assertEqual(allow["pama_decision_ref"], "pama-decision:proposal:external-policy")
        self.assertNotIn("content", allow)
        self.assertNotIn("fact_text", allow)

    def test_receipt_ref_does_not_change_action_identity(self):
        proposal = _proposal()
        decision = _decision(policy.ALLOW_WITH_LEDGER)
        before_receipt = build_projection(proposal, decision)
        after_receipt = build_projection(proposal, decision, receipt_ref="receipt:1")

        self.assertEqual(before_receipt["input_identity"], after_receipt["input_identity"])
        self.assertEqual(after_receipt["receipt_ref"], "receipt:1")

    def test_external_allow_cannot_loosen_local_block(self):
        projection = build_projection(_proposal(), _decision(policy.BLOCK))
        result = compose(
            projection,
            provider_mode=PROVIDER_ADVISORY,
            external_decision=_external(projection, "allow"),
        )
        self.assertEqual(result["local_normalized_decision"], DENY)
        self.assertEqual(result["effective_decision"], DENY)

    def test_external_allow_cannot_discharge_local_review(self):
        projection = build_projection(_proposal(), _decision(policy.REQUIRE_REVIEW))
        result = compose(
            projection,
            provider_mode=PROVIDER_ADVISORY,
            external_decision=_external(projection, "allow"),
        )
        self.assertEqual(result["local_normalized_decision"], REQUIRE_APPROVAL)
        self.assertEqual(result["effective_decision"], REQUIRE_APPROVAL)

    def test_external_deny_tightens_local_allow(self):
        projection = build_projection(_proposal(), _decision(policy.ALLOW_WITH_LEDGER))
        result = compose(
            projection,
            provider_mode=PROVIDER_ADVISORY,
            external_decision=_external(projection, "deny"),
        )
        self.assertEqual(result["local_normalized_decision"], ALLOW)
        self.assertEqual(result["effective_decision"], DENY)

    def test_stale_external_identity_is_not_applied(self):
        projection = build_projection(_proposal(), _decision(policy.ALLOW_WITH_LEDGER))
        stale = _external(projection, "deny", stale=True)

        advisory = compose(projection, provider_mode=PROVIDER_ADVISORY, external_decision=stale)
        authoritative = compose(projection, provider_mode=PROVIDER_AUTHORITATIVE, external_decision=stale)

        self.assertEqual(advisory["external_provider_status"], STATUS_STALE_IDENTITY)
        self.assertEqual(advisory["effective_decision"], ALLOW)
        self.assertEqual(authoritative["external_provider_status"], STATUS_STALE_IDENTITY)
        self.assertEqual(authoritative["effective_decision"], DENY)

    def test_invalid_provider_result_is_explicit_and_fail_closed_when_authoritative(self):
        projection = build_projection(_proposal(), _decision(policy.ALLOW_WITH_LEDGER))
        invalid = {
            "schema_version": "1.0.0",
            "provider_id": "broken-provider",
            "provider_version": "1.0.0",
            "input_identity": projection["input_identity"],
            "decision": "permit-ish",
            "reason": "invalid vocabulary",
            "issued_at": "2026-08-12T18:00:00Z",
        }
        advisory = compose(projection, provider_mode=PROVIDER_ADVISORY, external_decision=invalid)
        authoritative = compose(projection, provider_mode=PROVIDER_AUTHORITATIVE, external_decision=invalid)

        self.assertEqual(advisory["external_provider_status"], STATUS_INVALID)
        self.assertEqual(advisory["effective_decision"], ALLOW)
        self.assertEqual(authoritative["external_provider_status"], STATUS_INVALID)
        self.assertEqual(authoritative["effective_decision"], DENY)

    def test_fake_provider_is_deterministic_and_bound(self):
        projection = build_projection(_proposal(), _decision(policy.ALLOW_WITH_LEDGER))
        provider = DeterministicFakeProvider(decision="escalate")

        first = provider.evaluate(projection)
        second = provider.evaluate(projection)

        self.assertEqual(first, second)
        self.assertEqual(first["input_identity"], projection["input_identity"])
        result = compose(projection, provider_mode=PROVIDER_ADVISORY, external_decision=first)
        self.assertEqual(result["external_provider_status"], STATUS_AVAILABLE)
        self.assertEqual(result["effective_decision"], REQUIRE_APPROVAL)

    def test_composition_receipt_never_claims_execution_without_witness(self):
        projection = build_projection(_proposal(), _decision(policy.ALLOW_WITH_LEDGER))
        result = compose(projection, provider_mode=PROVIDER_NONE)

        self.assertEqual(result["execution_status"], EXECUTION_UNKNOWN)
        self.assertNotIn("execution_evidence_ref", result)
        self.assertNotIn(result["execution_status"], {"executed", "prevented", "enforced"})

    def test_fixture_matrix(self):
        data = json.loads(MATRIX.read_text(encoding="utf-8"))
        for case in data["composition_cases"]:
            with self.subTest(case_id=case["case_id"]):
                projection = build_projection(_proposal(), _decision(case["local_pama_outcome"]))
                external = None
                if case["external_decision"] is not None:
                    external = _external(
                        projection,
                        case["external_decision"],
                        stale=case["identity_mode"] == "stale",
                    )
                result = compose(
                    projection,
                    provider_mode=case["provider_mode"],
                    external_decision=external,
                )
                self.assertEqual(result["external_provider_status"], case["expected_provider_status"])
                self.assertEqual(result["effective_decision"], case["expected_effective_decision"])
                self.assertEqual(result["execution_status"], case["expected_execution_status"])


if __name__ == "__main__":
    unittest.main()
