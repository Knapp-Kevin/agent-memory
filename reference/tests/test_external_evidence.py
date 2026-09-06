"""Vendor-neutral external trust/attestation evidence tests for issue #180."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from agentmem_ref.external_evidence import (
    EvidenceContext,
    TRACE_PEER,
    TRACE_RELEASE,
    TRACE_VERSION,
    normalize_external_evidence,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "external-evidence-normalization-matrix.json"


class ExternalEvidenceNormalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(MATRIX.read_text(encoding="utf-8"))
        context = cls.data["context"]
        cls.context = EvidenceContext(
            subject_ref=context["subject_ref"],
            scope=context["scope"],
            tenant_ref=context["tenant_ref"],
            resource_ref=context["resource_ref"],
            action_ref=context["action_ref"],
        )
        cls.observed_at = context["observed_at"]

    def _normalize_case(self, case: dict) -> dict:
        record = copy.deepcopy(self.data["base_adapter_result"])
        record.update(copy.deepcopy(case["input_overrides"]))
        for field in case["remove_fields"]:
            record.pop(field, None)
        return normalize_external_evidence(
            record,
            context=self.context,
            observed_at=self.observed_at,
        )

    def test_trace_reference_is_exactly_pinned(self):
        pinned = self.data["pinned_reference"]
        self.assertEqual(pinned["source_peer"], TRACE_PEER)
        self.assertEqual(pinned["source_version"], TRACE_VERSION)
        self.assertEqual(pinned["source_release_ref"], TRACE_RELEASE)

    def test_adversarial_matrix(self):
        for case in self.data["cases"]:
            with self.subTest(case_id=case["case_id"]):
                result = self._normalize_case(case)
                self.assertEqual(result["applicability"]["status"], case["expected_status"])
                for reason in case["expected_reasons"]:
                    self.assertIn(reason, result["applicability"]["reasons"])

                self.assertEqual(result["interpretation"]["authority_effect"], "none")
                self.assertEqual(result["interpretation"]["memory_authority"], "not_established")
                self.assertEqual(result["interpretation"]["semantic_correctness"], "not_established")
                self.assertEqual(result["interpretation"]["lifecycle_satisfaction"], "not_established")

    def test_verified_identity_and_execution_claim_do_not_create_memory_authority(self):
        result = self._normalize_case(self.data["cases"][0])
        self.assertEqual(result["verification"]["status"], "verified")
        self.assertEqual(result["claim"]["type"], "execution")
        self.assertEqual(result["applicability"]["status"], "applicable")
        self.assertEqual(result["interpretation"]["authority_effect"], "none")
        self.assertNotIn("pama_outcome", result)
        self.assertNotIn("permitted_actions", result)

    def test_wrong_scope_remains_mismatch_even_when_verified(self):
        case = next(case for case in self.data["cases"] if case["case_id"] == "verified-wrong-scope")
        result = self._normalize_case(case)
        self.assertEqual(result["verification"]["status"], "verified")
        self.assertEqual(result["applicability"]["status"], "mismatch")
        self.assertIn("scope_mismatch", result["applicability"]["reasons"])

    def test_unknown_verification_is_not_coerced_to_valid(self):
        case = next(case for case in self.data["cases"] if case["case_id"] == "unknown-verification")
        result = self._normalize_case(case)
        self.assertEqual(result["verification"]["status"], "unknown")
        self.assertEqual(result["applicability"]["status"], "insufficient_evidence")

    def test_expired_and_revoked_evidence_are_not_current_authority(self):
        for case_id in ("expired-evidence", "revoked-evidence"):
            case = next(case for case in self.data["cases"] if case["case_id"] == case_id)
            result = self._normalize_case(case)
            self.assertEqual(result["applicability"]["status"], "stale")
            self.assertEqual(result["interpretation"]["authority_effect"], "none")

    def test_decision_evidence_does_not_claim_enforcement_or_execution(self):
        case = next(
            case
            for case in self.data["cases"]
            if case["case_id"] == "decision-evidence-does-not-become-execution"
        )
        result = self._normalize_case(case)
        self.assertEqual(result["claim"]["type"], "decision")
        self.assertIn("decision_ref", result["claim"])
        self.assertIn("decision_disposition", result["claim"])
        self.assertNotIn("enforcement_posture", result["claim"])
        self.assertNotIn("execution_posture", result["claim"])

    def test_runtime_attestation_does_not_claim_semantic_correctness(self):
        record = copy.deepcopy(self.data["base_adapter_result"])
        record["claim_type"] = "runtime_configuration"
        record.pop("execution_posture", None)
        record.pop("enforcement_posture", None)
        result = normalize_external_evidence(
            record,
            context=self.context,
            observed_at=self.observed_at,
        )
        self.assertEqual(result["applicability"]["status"], "applicable")
        self.assertEqual(result["interpretation"]["semantic_correctness"], "not_established")

    def test_peer_only_authority_fields_are_dropped(self):
        case = next(case for case in self.data["cases"] if case["case_id"] == "peer-only-authority-fields-ignored")
        result = self._normalize_case(case)
        serialized = json.dumps(result, sort_keys=True)
        self.assertNotIn("pama_outcome", serialized)
        self.assertNotIn("permitted_actions", serialized)
        self.assertNotIn("trust_score", serialized)
        self.assertNotIn("lifecycle_state", serialized)
        self.assertEqual(result["interpretation"]["authority_effect"], "none")

    def test_adapter_removal_leaves_only_generic_evidence_contract(self):
        result = self._normalize_case(self.data["cases"][0])
        self.assertEqual(result["source"]["peer"], "TRACE")
        self.assertEqual(result["source"]["adapter_id"], "agent-memory.trace-reference-adapter")
        self.assertNotIn("raw_payload", result)
        self.assertNotIn("trace_record", result)
        self.assertNotIn("signature", result)
        self.assertIn("evidence_digest", result)
        self.assertIn("record_ref", result["source"])

    def test_malformed_peer_evidence_is_rejected_before_normalization(self):
        record = copy.deepcopy(self.data["base_adapter_result"])
        record["parse_status"] = "malformed"
        with self.assertRaisesRegex(ValueError, "malformed/unparsed"):
            normalize_external_evidence(
                record,
                context=self.context,
                observed_at=self.observed_at,
            )

    def test_missing_required_context_binding_is_mismatch_not_optimistic_match(self):
        record = copy.deepcopy(self.data["base_adapter_result"])
        record.pop("resource_ref")
        result = normalize_external_evidence(
            record,
            context=self.context,
            observed_at=self.observed_at,
        )
        self.assertEqual(result["applicability"]["status"], "mismatch")
        self.assertIn("missing_resource_ref_binding", result["applicability"]["reasons"])


if __name__ == "__main__":
    unittest.main()
