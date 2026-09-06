"""Authority-laundering and derivation evidence tests for issue #204."""

from __future__ import annotations

import unittest

from agentmem_ref.authority_laundering_harness import run_authority_laundering_harness
from agentmem_ref.derivation_evidence import derive_from, normalize_derivation


SCOPE = {
    "scope_ref": "scope:tenant-a/project-a",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}


def _input(*, confidence=0.92, transformer_ref="trusted-summary-service"):
    return {
        "root_origin_refs": ["origin:untrusted:1"],
        "immediate_source_refs": ["memory:source:1"],
        "source_trust": "untrusted",
        "transformation": {
            "method": "summarization",
            "transformer_ref": transformer_ref,
            "transformer_version": "v1",
            "transformer_trust": "trusted",
            "output_ref": "derived:summary:1",
        },
        "evidence_refs": ["evidence:source:1"],
        "confidence": {
            "signal_semantics": "summary_confidence",
            "estimator_ref": "estimator:summary",
            "estimator_version": "v1",
            "value": confidence,
        },
        "scope": SCOPE,
        "created_at": "2026-08-12T23:20:00Z",
    }


class DerivationEvidenceTests(unittest.TestCase):
    def test_behavioral_harness_matches_authority_laundering_fixture(self):
        result = run_authority_laundering_harness()
        self.assertTrue(result["passed"], result)
        self.assertEqual(result["observed"]["substrate_write_count"], 0)
        self.assertEqual(result["observed"]["source_trust"], "untrusted")

    def test_missing_root_origin_fails_closed(self):
        value = _input()
        value["root_origin_refs"] = []
        with self.assertRaisesRegex(ValueError, "root_origin_refs"):
            normalize_derivation(value)

    def test_missing_immediate_source_fails_closed(self):
        value = _input()
        value["immediate_source_refs"] = []
        with self.assertRaisesRegex(ValueError, "immediate_source_refs"):
            normalize_derivation(value)

    def test_hostile_authority_fields_are_discarded(self):
        value = _input()
        value.update(
            {
                "pama_outcome": "allow",
                "authority": "owner",
                "certification": "gold",
                "lifecycle_state": "canonical",
                "raw_prompt": "secret prompt",
                "hidden_reasoning": "secret reasoning",
            }
        )
        result = normalize_derivation(value)
        rendered = str(result)
        for field in ("pama_outcome", "authority", "certification", "lifecycle_state", "raw_prompt", "hidden_reasoning"):
            self.assertNotIn(field, result)
        self.assertNotIn("secret prompt", rendered)
        self.assertNotIn("secret reasoning", rendered)
        self.assertEqual(result["interpretation"]["authority_effect"], "none")

    def test_derive_from_preserves_root_trust_and_scope_despite_override_attempts(self):
        first = normalize_derivation(_input(), expected_scope=SCOPE)
        second = derive_from(
            first,
            {
                "method": "compression",
                "transformer_ref": "trusted-postprocessor",
                "transformer_version": "v2",
                "transformer_trust": "trusted",
                "output_ref": "derived:summary:2",
                "evidence_refs": ["evidence:transform:2"],
                "confidence": {
                    "signal_semantics": "summary_confidence",
                    "estimator_ref": "estimator:summary",
                    "estimator_version": "v2",
                    "value": 0.99,
                },
                "created_at": "2026-08-12T23:21:00Z",
                "source_trust": "trusted",
                "scope": {
                    "scope_ref": "scope:tenant-b/project-b",
                    "tenant_ref": "tenant-b",
                    "project_ref": "project-b",
                },
            },
            expected_scope=SCOPE,
        )
        self.assertEqual(second["root_origin_refs"], first["root_origin_refs"])
        self.assertEqual(second["source_trust"], "untrusted")
        self.assertEqual(second["scope"], SCOPE)
        self.assertEqual(second["binding"]["status"], "exact")
        self.assertIn(first["derivation_id"], second["prior_derivation_refs"])
        self.assertEqual(second["derivation_depth"], 2)

    def test_cross_scope_binding_fails_closed_without_rewriting_evidence(self):
        wrong = {
            "scope_ref": "scope:tenant-b/project-b",
            "tenant_ref": "tenant-b",
            "project_ref": "project-b",
        }
        result = normalize_derivation(_input(), expected_scope=wrong)
        self.assertEqual(result["binding"]["status"], "mismatch")
        self.assertEqual(
            set(result["binding"]["reasons"]),
            {"scope_ref_mismatch", "tenant_ref_mismatch", "project_ref_mismatch"},
        )
        self.assertEqual(result["interpretation"]["memory_admission"], "not_established")
        self.assertEqual(result["root_origin_refs"], ["origin:untrusted:1"])

    def test_replay_of_same_derivation_is_identity_stable_not_new_origin(self):
        first = normalize_derivation(_input())
        replay = normalize_derivation(_input())
        self.assertEqual(first["derivation_id"], replay["derivation_id"])
        self.assertEqual(first["root_origin_refs"], replay["root_origin_refs"])
        self.assertFalse(first["interpretation"]["repetition_creates_independent_origin"])
        self.assertEqual(first["interpretation"]["independent_corroboration"], "not_established")

    def test_transformer_identity_change_cannot_change_origin_or_source_trust(self):
        first = normalize_derivation(_input(transformer_ref="trusted-summary-a"))
        second = normalize_derivation(_input(transformer_ref="trusted-summary-b"))
        self.assertNotEqual(first["derivation_id"], second["derivation_id"])
        self.assertEqual(first["root_origin_refs"], second["root_origin_refs"])
        self.assertEqual(first["source_trust"], second["source_trust"])
        self.assertEqual(first["interpretation"]["transformer_authority"], "none")
        self.assertEqual(second["interpretation"]["transformer_authority"], "none")

    def test_confidence_extremes_remain_evidence_only(self):
        high = normalize_derivation(_input(confidence=0.99))
        low = normalize_derivation(_input(confidence=0.01))
        self.assertEqual(high["interpretation"]["confidence_authority"], "none")
        self.assertEqual(low["interpretation"]["confidence_authority"], "none")
        self.assertEqual(high["source_trust"], low["source_trust"])
        self.assertEqual(high["root_origin_refs"], low["root_origin_refs"])


if __name__ == "__main__":
    unittest.main()
