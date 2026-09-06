"""Adversarial state-machine tests for #265 temporal signer trust evidence."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from agentmem_ref.temporal_trust import build_signer_trust_evidence, evaluate_attestation_trust


class TemporalTrustTests(unittest.TestCase):
    def setUp(self):
        self.public_key = object()
        self.attestation = {"signer": {"key_ref": "key:agent-a:1"}}

    def evidence(self, *, digest="sha256:" + "11" * 32, trust_status="trusted", verification_status="verified", valid_from=None, valid_to=None):
        return {
            "schema_version": "1.0.0",
            "profile_id": "agent-memory/temporal-signer-trust",
            "key_ref": "key:agent-a:1",
            "public_key_digest": digest,
            "trust_status": trust_status,
            "verification_status": verification_status,
            "trust_source_ref": "trust-store:test:v1",
            "verified_at": "2026-08-13T22:01:00Z",
            "evidence_refs": ["evidence:trust:1"] if verification_status == "verified" else [],
            "valid_from": valid_from,
            "valid_to": valid_to,
            "interpretation": {
                "authority_effect": "none",
                "currentness": "not_established",
                "trusted_time": "not_established",
                "event_truth": "not_established"
            }
        }

    def evaluate(self, evidence):
        with patch("agentmem_ref.temporal_trust.receipts.validate"), patch(
            "agentmem_ref.temporal_trust.verify_temporal_attestation",
            return_value={"cryptographic_status": "valid"},
        ), patch(
            "agentmem_ref.temporal_trust.public_key_digest",
            return_value="sha256:" + "11" * 32,
        ):
            return evaluate_attestation_trust(
                self.attestation,
                public_key=self.public_key,
                trust_evidence=evidence,
                evaluated_at="2026-08-13T22:02:00Z",
            )

    def test_exact_verified_binding_can_establish_trusted_signer(self):
        result = self.evaluate(self.evidence())
        self.assertTrue(result["trusted_signer"])
        self.assertTrue(result["key_ref_matches"])
        self.assertTrue(result["key_material_matches"])
        self.assertEqual(result["authority_effect"], "none")
        self.assertEqual(result["currentness"], "not_established")

    def test_reused_key_ref_with_different_material_does_not_inherit_trust(self):
        result = self.evaluate(self.evidence(digest="sha256:" + "22" * 32))
        self.assertFalse(result["trusted_signer"])
        self.assertTrue(result["key_ref_matches"])
        self.assertFalse(result["key_material_matches"])
        self.assertIn("public_key_mismatch", result["reason_codes"])

    def test_unverified_trust_evidence_is_not_trusted(self):
        result = self.evaluate(self.evidence(verification_status="unknown"))
        self.assertFalse(result["trusted_signer"])
        self.assertIn("trust_evidence_not_verified", result["reason_codes"])

    def test_revoked_trust_is_separate_from_key_possession(self):
        result = self.evaluate(self.evidence(trust_status="revoked"))
        self.assertEqual(result["key_possession_status"], "valid")
        self.assertFalse(result["trusted_signer"])
        self.assertIn("trust_status_revoked", result["reason_codes"])
        self.assertEqual(result["authority_effect"], "none")

    def test_expired_trust_evidence_is_not_current_trust(self):
        result = self.evaluate(self.evidence(
            valid_from="2026-08-01T00:00:00Z",
            valid_to="2026-08-10T00:00:00Z",
        ))
        self.assertFalse(result["trusted_signer"])
        self.assertFalse(result["within_validity"])
        self.assertIn("trust_evidence_outside_validity", result["reason_codes"])

    def test_builder_requires_evidence_for_verified_trust(self):
        with patch(
            "agentmem_ref.temporal_trust.public_key_digest",
            return_value="sha256:" + "11" * 32,
        ), patch("agentmem_ref.temporal_trust.receipts.validate"):
            with self.assertRaisesRegex(ValueError, "requires evidence_refs"):
                build_signer_trust_evidence(
                    key_ref="key:agent-a:1",
                    public_key=self.public_key,
                    trust_status="trusted",
                    verification_status="verified",
                    trust_source_ref="trust-store:test:v1",
                    verified_at="2026-08-13T22:01:00Z",
                    evidence_refs=[],
                )


if __name__ == "__main__":
    unittest.main()
