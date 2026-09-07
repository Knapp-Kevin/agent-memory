"""Adversarial tests for provider-neutral temporal transparency evidence (#265)."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from agentmem_ref.temporal_transparency import (
    build_transparency_receipt_evidence,
    verify_transparency_binding,
)

SUBJECT = "sha256:" + "11" * 32
ROOT = "sha256:" + "22" * 32
PRIOR_ROOT = "sha256:" + "33" * 32


class TemporalTransparencyTests(unittest.TestCase):
    def build(self, **changes):
        values = {
            "subject_reference_profile": "agent-memory/rfc8785-sha256-document-ref",
            "subject_ref": SUBJECT,
            "claim_kind": "inclusion",
            "vds_profile": "rfc9942/rfc9162-sha256",
            "verification_status": "verified",
            "receipt_ref": "evidence:receipt:1",
            "verifier_profile": "test/receipt-verifier",
            "verifier_version": "1",
            "verifier_source_ref": "source:test:1",
            "evidence_refs": ["evidence:raw:1"],
            "tree_size": 7,
            "root_ref": ROOT,
        }
        values.update(changes)
        with patch("agentmem_ref.temporal_transparency.receipts.validate"):
            return build_transparency_receipt_evidence(**values)

    def verify(self, evidence, *, subject=SUBJECT, profile="agent-memory/rfc8785-sha256-document-ref"):
        with patch("agentmem_ref.temporal_transparency.receipts.validate"):
            return verify_transparency_binding(
                evidence,
                expected_subject_reference_profile=profile,
                expected_subject_ref=subject,
            )

    def test_verified_inclusion_is_bounded_to_exact_subject(self):
        result = self.verify(self.build())
        self.assertTrue(result["bound"])
        self.assertTrue(result["inclusion_verified"])
        self.assertFalse(result["complete_history_proven"])
        self.assertFalse(result["global_non_equivocation_proven"])
        self.assertEqual(result["authority_effect"], "none")

    def test_wrong_subject_or_reference_profile_rejects_binding(self):
        evidence = self.build()
        self.assertFalse(self.verify(evidence, subject="sha256:" + "44" * 32)["bound"])
        self.assertFalse(self.verify(evidence, profile="other/profile")["bound"])

    def test_consistency_receipt_proves_only_bounded_append_only_transition(self):
        evidence = self.build(
            claim_kind="consistency",
            tree_size=11,
            prior_tree_size=7,
            root_ref=ROOT,
            prior_root_ref=PRIOR_ROOT,
        )
        result = self.verify(evidence)
        self.assertTrue(result["append_only_transition_verified"])
        self.assertFalse(result["complete_history_proven"])
        self.assertFalse(result["global_non_equivocation_proven"])
        self.assertFalse(result["event_occurrence_time_proven"])
        self.assertEqual(result["currentness"], "not_established")

    def test_consistency_requires_monotonic_tree_size(self):
        with self.assertRaisesRegex(ValueError, "prior_tree_size < tree_size"):
            self.build(
                claim_kind="consistency",
                tree_size=7,
                prior_tree_size=7,
                root_ref=ROOT,
                prior_root_ref=PRIOR_ROOT,
            )

    def test_unverified_receipt_cannot_bind(self):
        result = self.verify(self.build(verification_status="unknown", evidence_refs=[]))
        self.assertFalse(result["bound"])
        self.assertFalse(result["inclusion_verified"])
        self.assertEqual(result["authority_effect"], "none")

    def test_verified_receipt_requires_evidence_reference(self):
        with self.assertRaisesRegex(ValueError, "requires evidence_refs"):
            self.build(evidence_refs=[])


if __name__ == "__main__":
    unittest.main()
