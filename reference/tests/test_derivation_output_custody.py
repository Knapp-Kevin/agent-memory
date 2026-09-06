"""Typed/digested derivation output custody tests for issue #212."""

from __future__ import annotations

import unittest

from agentmem_ref.derivation_currentness import evaluate_derivation_currentness
from agentmem_ref.derivation_evidence import derive_from, normalize_derivation

SCOPE = {
    "scope_ref": "scope:tenant-a/project-a",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}
DIGEST_A = "sha256:" + "a" * 64
DIGEST_B = "sha256:" + "b" * 64


def _input(*, digest=DIGEST_A, include_type=True, include_digest=True):
    transformation = {
        "method": "summary",
        "mode": "probabilistic",
        "status": "complete",
        "transformer_ref": "transformer:summary",
        "transformer_version": "v1",
        "transformer_trust": "trusted",
        "output_ref": "artifact:summary:1",
        "raw_output": "sensitive derived content must not enter custody evidence",
        "output_payload": {"content": "also must not survive"},
    }
    if include_type:
        transformation["output_type"] = "text/summary"
    if include_digest:
        transformation["output_digest"] = digest
    return {
        "root_origin_refs": ["origin:a"],
        "immediate_source_refs": ["origin:a"],
        "source_trust": "bounded_trusted",
        "transformation": transformation,
        "scope": SCOPE,
        "evidence_refs": ["evidence:a"],
        "created_at": "2026-08-13T03:25:00Z",
    }


def _currentness(derivation):
    return evaluate_derivation_currentness(
        derivation,
        source_observations=[
            {
                "origin_ref": "origin:a",
                "state": "current",
                "evidence_class": "ordinary",
                "evidence_refs": ["evidence:a:current"],
            }
        ],
        scope_observation={
            "status": "unchanged",
            "current_scope_ref": SCOPE["scope_ref"],
            "tenant_ref": SCOPE["tenant_ref"],
            "project_ref": SCOPE["project_ref"],
            "evidence_refs": ["evidence:scope:current"],
        },
        evaluated_at="2026-08-13T03:25:01Z",
    )


class DerivationOutputCustodyTests(unittest.TestCase):
    def test_typed_digested_output_is_preserved_without_raw_payload(self):
        result = normalize_derivation(_input(), expected_scope=SCOPE)
        transform = result["transformation"]
        self.assertEqual(transform["output_ref"], "artifact:summary:1")
        self.assertEqual(transform["output_type"], "text/summary")
        self.assertEqual(transform["output_digest"], DIGEST_A)
        self.assertNotIn("raw_output", transform)
        self.assertNotIn("output_payload", transform)
        rendered = str(result)
        self.assertNotIn("sensitive derived content", rendered)
        self.assertNotIn("also must not survive", rendered)

    def test_output_type_without_digest_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be supplied together"):
            normalize_derivation(_input(include_digest=False))

    def test_output_digest_without_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must be supplied together"):
            normalize_derivation(_input(include_type=False))

    def test_malformed_output_digest_is_rejected(self):
        for malformed in (
            "sha256:abc",
            "sha256:" + "A" * 64,
            "sha512:" + "a" * 64,
            "a" * 64,
        ):
            with self.subTest(malformed=malformed):
                with self.assertRaisesRegex(ValueError, "sha256:<64 lowercase hex>"):
                    normalize_derivation(_input(digest=malformed))

    def test_same_typed_digested_transformation_replays_identity_stably(self):
        first = normalize_derivation(_input())
        second = normalize_derivation(_input())
        self.assertEqual(first["derivation_id"], second["derivation_id"])
        self.assertEqual(first["transformation"], second["transformation"])
        self.assertFalse(first["interpretation"]["repetition_creates_independent_origin"])

    def test_changed_digest_changes_identity_but_not_authority_interpretation(self):
        first = normalize_derivation(_input(digest=DIGEST_A))
        second = normalize_derivation(_input(digest=DIGEST_B))
        self.assertNotEqual(first["derivation_id"], second["derivation_id"])
        self.assertEqual(first["interpretation"], second["interpretation"])
        self.assertEqual(first["interpretation"]["authority_effect"], "none")
        self.assertEqual(first["interpretation"]["independent_corroboration"], "not_established")

    def test_child_derivation_preserves_typed_digested_custody(self):
        parent = normalize_derivation(_input())
        child = derive_from(
            parent,
            {
                "method": "compression",
                "mode": "deterministic",
                "status": "complete",
                "transformer_ref": "transformer:compression",
                "transformer_version": "v2",
                "transformer_trust": "trusted",
                "output_ref": "artifact:summary:2",
                "output_type": "application/summary+json",
                "output_digest": DIGEST_B,
                "evidence_refs": ["evidence:compression"],
                "created_at": "2026-08-13T03:25:02Z",
                "raw_output": "must still be ignored",
            },
            expected_scope=SCOPE,
        )
        transform = child["transformation"]
        self.assertEqual(transform["output_type"], "application/summary+json")
        self.assertEqual(transform["output_digest"], DIGEST_B)
        self.assertNotIn("raw_output", transform)
        self.assertEqual(child["root_origin_refs"], parent["root_origin_refs"])

    def test_legacy_output_ref_only_record_remains_valid(self):
        legacy = _input(include_type=False, include_digest=False)
        result = normalize_derivation(legacy, expected_scope=SCOPE)
        self.assertEqual(result["transformation"]["output_ref"], "artifact:summary:1")
        self.assertNotIn("output_type", result["transformation"])
        self.assertNotIn("output_digest", result["transformation"])
        self.assertEqual(_currentness(result)["applicability"]["status"], "current")

    def test_digest_custody_does_not_change_currentness_or_create_authority(self):
        typed = normalize_derivation(_input(digest=DIGEST_A), expected_scope=SCOPE)
        other_digest = normalize_derivation(_input(digest=DIGEST_B), expected_scope=SCOPE)
        typed_currentness = _currentness(typed)
        other_currentness = _currentness(other_digest)
        self.assertEqual(typed_currentness["applicability"], other_currentness["applicability"])
        self.assertEqual(typed_currentness["interpretation"]["authority_effect"], "none")
        self.assertEqual(other_currentness["interpretation"]["authority_effect"], "none")
        self.assertEqual(typed["interpretation"]["certification_claim"], "none")
        self.assertEqual(other_digest["interpretation"]["memory_admission"], "not_established")


if __name__ == "__main__":
    unittest.main()
