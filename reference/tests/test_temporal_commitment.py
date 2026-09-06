"""Adversarial tests for ADR-031 temporal commitments."""

from __future__ import annotations

import copy
import hashlib
import json
import unittest
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agentmem_ref.temporal_commitment import (
    UOR_CONTENT_REFERENCE_PROFILE,
    address_temporal_commitment,
    build_external_witness_evidence,
    build_temporal_commitment,
    detect_linear_forks,
    document_ref,
    evaluate_linear_order,
    evaluate_temporal_currentness,
    sign_temporal_commitment,
    verify_temporal_attestation,
    verify_witness_binding,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "reference" / "testdata" / "temporal-commitment-adversarial.json"
LOCAL_PROFILE = "test/local-rfc8785-sha256"
DOCUMENT_PROFILE = "agent-memory/rfc8785-sha256-document-ref"


def sha_address(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class TemporalCommitmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        cls.private_key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(cls.fixture["test_key"]["seed_hex"]))
        cls.public_key = cls.private_key.public_key()
        cls.key_ref = cls.fixture["test_key"]["key_ref"]

    def build(self, base=None, **ordering):
        material = copy.deepcopy(base or self.fixture["base"])
        return build_temporal_commitment(
            event_type=material["event_type"],
            subject_ref=material["subject_ref"],
            payload_digest=material["payload_digest"],
            temporal_claims=material["temporal_claims"],
            scope_ref=material["scope_ref"],
            domain_schema_ref=material["domain_schema_ref"],
            domain_schema_digest=material["domain_schema_digest"],
            projection_profile=material["projection_profile"],
            projection_version=material["projection_version"],
            **ordering,
        )

    def linear(self, *, sequence, predecessor_refs=(), base=None, profile=LOCAL_PROFILE):
        return self.build(
            base,
            ordering_mode="linear_stream",
            stream_ref="stream:a",
            sequence=sequence,
            predecessor_reference_profile=profile,
            predecessor_refs=predecessor_refs,
        )

    def test_material_mutations_change_content_identity(self):
        base = self.fixture["base"]
        original = self.build(base)
        original_ref = address_temporal_commitment(original, address_fn=sha_address)
        for mutation in self.fixture["mutations"]:
            with self.subTest(mutation=mutation["id"]):
                changed = copy.deepcopy(base)
                if mutation["field"] == "event_time":
                    changed["temporal_claims"]["event_time"] = mutation["value"]
                else:
                    changed[mutation["field"]] = mutation["value"]
                changed_ref = address_temporal_commitment(self.build(changed), address_fn=sha_address)
                self.assertNotEqual(original_ref, changed_ref)

        profile_changed = copy.deepcopy(base)
        profile_changed["projection_version"] = "0.2.0"
        self.assertNotEqual(
            original_ref,
            address_temporal_commitment(self.build(profile_changed), address_fn=sha_address),
        )

    def test_requires_a_non_null_temporal_claim(self):
        material = copy.deepcopy(self.fixture["base"])
        material["temporal_claims"] = {"valid_from": None, "valid_to": None}
        with self.assertRaisesRegex(ValueError, "non-null temporal claim"):
            self.build(material)

    def test_predecessor_and_reference_profile_mutations_change_descendant_identity(self):
        root = self.linear(sequence=0)
        root_ref = address_temporal_commitment(root, address_fn=sha_address)
        child = self.linear(sequence=1, predecessor_refs=[root_ref])
        child_ref = address_temporal_commitment(child, address_fn=sha_address)

        mutated_ref = self.linear(sequence=1, predecessor_refs=["sha256:" + "9" * 64])
        self.assertNotEqual(child_ref, address_temporal_commitment(mutated_ref, address_fn=sha_address))

        mutated_profile = self.linear(sequence=1, predecessor_refs=[root_ref], profile="test/other-profile")
        self.assertNotEqual(child_ref, address_temporal_commitment(mutated_profile, address_fn=sha_address))

    def test_signature_binds_exact_reference_and_profile(self):
        commitment = self.build()
        content_ref = address_temporal_commitment(commitment, address_fn=sha_address)
        attestation = sign_temporal_commitment(
            content_ref=content_ref,
            private_key=self.private_key,
            key_ref=self.key_ref,
            content_reference_profile=LOCAL_PROFILE,
        )
        verified = verify_temporal_attestation(attestation, public_key=self.public_key, trust_status="trusted")
        self.assertEqual(verified["cryptographic_status"], "valid")
        self.assertTrue(verified["trusted_signer"])
        self.assertEqual(verified["authority_effect"], "none")

        tampered = copy.deepcopy(attestation)
        tampered["content_ref"] = "sha256:" + "8" * 64
        invalid = verify_temporal_attestation(tampered, public_key=self.public_key, trust_status="trusted")
        self.assertEqual(invalid["cryptographic_status"], "invalid")

        profile_tampered = copy.deepcopy(attestation)
        profile_tampered["content_reference_profile"] = "other/profile"
        invalid_profile = verify_temporal_attestation(profile_tampered, public_key=self.public_key, trust_status="trusted")
        self.assertEqual(invalid_profile["cryptographic_status"], "invalid")

    def test_valid_signature_does_not_prove_time_truth_or_authority(self):
        material = copy.deepcopy(self.fixture["base"])
        material["temporal_claims"]["event_time"] = "2099-01-01T00:00:00Z"
        commitment = self.build(material)
        content_ref = address_temporal_commitment(commitment, address_fn=sha_address)
        attestation = sign_temporal_commitment(
            content_ref=content_ref,
            private_key=self.private_key,
            key_ref=self.key_ref,
            content_reference_profile=LOCAL_PROFILE,
        )
        result = verify_temporal_attestation(attestation, public_key=self.public_key, trust_status="trusted")
        self.assertEqual(result["cryptographic_status"], "valid")
        self.assertEqual(result["trusted_time"], "not_established")
        self.assertEqual(result["event_truth"], "not_established")
        self.assertEqual(result["authority_effect"], "none")

    def test_untrusted_or_revoked_signer_can_remain_cryptographically_valid(self):
        commitment = self.build()
        content_ref = address_temporal_commitment(commitment, address_fn=sha_address)
        attestation = sign_temporal_commitment(
            content_ref=content_ref,
            private_key=self.private_key,
            key_ref=self.key_ref,
            content_reference_profile=LOCAL_PROFILE,
        )
        for trust_status in ("untrusted", "revoked", "unknown"):
            with self.subTest(trust_status=trust_status):
                result = verify_temporal_attestation(attestation, public_key=self.public_key, trust_status=trust_status)
                self.assertEqual(result["cryptographic_status"], "valid")
                self.assertFalse(result["trusted_signer"])
                self.assertEqual(result["authority_effect"], "none")

    def test_linear_order_requires_real_predecessor_and_exact_reference_profile(self):
        root = self.linear(sequence=0)
        root_ref = address_temporal_commitment(root, address_fn=sha_address)
        child = self.linear(sequence=1, predecessor_refs=[root_ref])

        missing = evaluate_linear_order(child)
        self.assertEqual(missing["status"], "missing_predecessor_evidence")
        self.assertFalse(missing["complete_history_proven"])

        valid = evaluate_linear_order(
            child,
            predecessor_commitment=root,
            address_fn=sha_address,
            address_profile=LOCAL_PROFILE,
        )
        self.assertEqual(valid["status"], "valid")
        self.assertTrue(valid["local_order_valid"])
        self.assertFalse(valid["complete_history_proven"])
        self.assertFalse(valid["non_equivocation_proven"])

        wrong_profile = evaluate_linear_order(
            child,
            predecessor_commitment=root,
            address_fn=sha_address,
            address_profile="test/other-profile",
        )
        self.assertEqual(wrong_profile["status"], "invalid")
        self.assertIn("predecessor_reference_profile_mismatch", wrong_profile["reason_codes"])

    def test_cross_scope_predecessor_is_invalid(self):
        root = self.linear(sequence=0)
        root_ref = address_temporal_commitment(root, address_fn=sha_address)
        changed = copy.deepcopy(self.fixture["base"])
        changed["scope_ref"] = "scope:tenant-b/project-alpha"
        child = self.linear(sequence=1, predecessor_refs=[root_ref], base=changed)
        result = evaluate_linear_order(
            child,
            predecessor_commitment=root,
            address_fn=sha_address,
            address_profile=LOCAL_PROFILE,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertIn("cross_scope_predecessor", result["reason_codes"])

    def test_fork_is_exposed_and_node_bindings_are_verified(self):
        root = self.linear(sequence=0)
        root_ref = address_temporal_commitment(root, address_fn=sha_address)
        child_a = self.linear(sequence=1, predecessor_refs=[root_ref])
        changed = copy.deepcopy(self.fixture["base"])
        changed["payload_digest"] = "sha256:" + "7" * 64
        child_b = self.linear(sequence=1, predecessor_refs=[root_ref], base=changed)
        nodes = [
            {"content_ref": root_ref, "commitment": root},
            {"content_ref": address_temporal_commitment(child_a, address_fn=sha_address), "commitment": child_a},
            {"content_ref": address_temporal_commitment(child_b, address_fn=sha_address), "commitment": child_b},
        ]
        forks = detect_linear_forks(
            nodes,
            address_fn=sha_address,
            content_reference_profile=LOCAL_PROFILE,
        )
        self.assertEqual(len(forks), 1)
        self.assertIsNone(forks[0]["canonical_child"])
        self.assertEqual(forks[0]["authority_effect"], "none")

        forged = copy.deepcopy(nodes)
        forged[1]["content_ref"] = "sha256:" + "5" * 64
        with self.assertRaisesRegex(ValueError, "does not match commitment"):
            detect_linear_forks(
                forged,
                address_fn=sha_address,
                content_reference_profile=LOCAL_PROFILE,
            )

    def test_external_witness_binds_subject_and_reference_profile_but_not_event_time(self):
        commitment = self.build()
        content_ref = address_temporal_commitment(commitment, address_fn=sha_address)
        witness = build_external_witness_evidence(
            witness_profile="rfc3161-verified-by-host",
            subject_kind="temporal_commitment",
            subject_reference_profile=LOCAL_PROFILE,
            subject_ref=content_ref,
            claim_kind="existence_by_time",
            verification_status="verified",
            witnessed_at="2026-08-13T19:01:00Z",
            proof_ref="evidence:tsa:1",
        )
        result = verify_witness_binding(
            witness,
            expected_subject_reference_profile=LOCAL_PROFILE,
            expected_subject_ref=content_ref,
        )
        self.assertTrue(result["bound"])
        self.assertFalse(result["event_occurrence_time_proven"])
        self.assertEqual(result["authority_effect"], "none")

        wrong_ref = verify_witness_binding(
            witness,
            expected_subject_reference_profile=LOCAL_PROFILE,
            expected_subject_ref="sha256:" + "6" * 64,
        )
        self.assertFalse(wrong_ref["bound"])
        wrong_profile = verify_witness_binding(
            witness,
            expected_subject_reference_profile="other/profile",
            expected_subject_ref=content_ref,
        )
        self.assertFalse(wrong_profile["bound"])

    def test_attestation_can_be_witnessed_as_a_separate_subject(self):
        commitment = self.build()
        content_ref = address_temporal_commitment(commitment, address_fn=sha_address)
        attestation = sign_temporal_commitment(
            content_ref=content_ref,
            private_key=self.private_key,
            key_ref=self.key_ref,
            content_reference_profile=LOCAL_PROFILE,
        )
        attestation_ref = document_ref(attestation)
        witness = build_external_witness_evidence(
            witness_profile="scitt-receipt-verified-by-host",
            subject_kind="signer_attestation",
            subject_reference_profile=DOCUMENT_PROFILE,
            subject_ref=attestation_ref,
            claim_kind="inclusion",
            verification_status="verified",
            proof_ref="evidence:scitt:receipt:1",
        )
        self.assertTrue(
            verify_witness_binding(
                witness,
                expected_subject_reference_profile=DOCUMENT_PROFILE,
                expected_subject_ref=attestation_ref,
            )["bound"]
        )

    def test_supersession_currentness_does_not_rewrite_historical_commitment_or_signature(self):
        commitment = self.build()
        original = copy.deepcopy(commitment)
        content_ref = address_temporal_commitment(commitment, address_fn=sha_address)
        attestation = sign_temporal_commitment(
            content_ref=content_ref,
            private_key=self.private_key,
            key_ref=self.key_ref,
            content_reference_profile=LOCAL_PROFILE,
        )
        signature_before = attestation["signature"]
        superseding_ref = "sha256:" + "4" * 64
        currentness = evaluate_temporal_currentness(
            commitment_reference_profile=LOCAL_PROFILE,
            commitment_ref=content_ref,
            status="superseded",
            evaluated_at="2026-08-13T20:00:00Z",
            evidence_refs=["evidence:correction:1"],
            superseding_refs=[superseding_ref],
        )
        self.assertEqual(commitment, original)
        self.assertEqual(attestation["signature"], signature_before)
        self.assertFalse(currentness["interpretation"]["historical_commitment_mutated"])
        self.assertFalse(currentness["interpretation"]["cryptographic_validity_changed"])
        self.assertEqual(currentness["interpretation"]["authority_effect"], "none")

    def test_invalid_validity_interval_is_rejected(self):
        material = copy.deepcopy(self.fixture["base"])
        material["temporal_claims"]["valid_from"] = "2026-08-14T00:00:00Z"
        material["temporal_claims"]["valid_to"] = "2026-08-13T00:00:00Z"
        with self.assertRaisesRegex(ValueError, "valid_from"):
            self.build(material)

    def test_optional_uor_unavailability_does_not_block_local_profile(self):
        commitment = self.build()

        def unavailable(_: bytes) -> str:
            raise RuntimeError("simulated optional UOR binding unavailable")

        with self.assertRaisesRegex(RuntimeError, "UOR binding unavailable"):
            address_temporal_commitment(commitment, address_fn=unavailable)

        local_ref = address_temporal_commitment(commitment, address_fn=sha_address)
        attestation = sign_temporal_commitment(
            content_ref=local_ref,
            private_key=self.private_key,
            key_ref=self.key_ref,
            content_reference_profile=LOCAL_PROFILE,
        )
        self.assertEqual(attestation["interpretation"]["authority_effect"], "none")
        self.assertNotEqual(attestation["content_reference_profile"], UOR_CONTENT_REFERENCE_PROFILE)


if __name__ == "__main__":
    unittest.main()
