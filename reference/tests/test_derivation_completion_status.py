"""Transformation completion/mode regressions absorbed from draft #203 into #210."""

from __future__ import annotations

import unittest

from agentmem_ref.derivation_currentness import evaluate_derivation_currentness
from agentmem_ref.derivation_evidence import derive_from, normalize_derivation

SCOPE = {
    "scope_ref": "scope:tenant-a/project-a",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}


def _derivation(*, mode="deterministic", status="complete"):
    return normalize_derivation(
        {
            "root_origin_refs": ["origin:a"],
            "immediate_source_refs": ["origin:a"],
            "source_trust": "bounded_trusted",
            "transformation": {
                "method": "summary",
                "mode": mode,
                "status": status,
                "transformer_ref": "transformer:test",
                "transformer_version": "v1",
                "transformer_trust": "trusted",
                "output_ref": f"derived:{mode}:{status}",
            },
            "scope": SCOPE,
            "evidence_refs": ["evidence:a"],
            "created_at": "2026-08-13T03:20:00Z",
        },
        expected_scope=SCOPE,
    )


def _evaluate(derivation, source_state="current"):
    return evaluate_derivation_currentness(
        derivation,
        source_observations=[
            {
                "origin_ref": "origin:a",
                "state": source_state,
                "evidence_class": "ordinary",
                "evidence_refs": [f"evidence:a:{source_state}"],
            }
        ],
        scope_observation={
            "status": "unchanged",
            "current_scope_ref": SCOPE["scope_ref"],
            "tenant_ref": SCOPE["tenant_ref"],
            "project_ref": SCOPE["project_ref"],
            "evidence_refs": ["evidence:scope:current"],
        },
        evaluated_at="2026-08-13T03:20:01Z",
    )


class DerivationCompletionStatusTests(unittest.TestCase):
    def test_partial_transformation_is_not_current_evidence(self):
        derivation = _derivation(mode="probabilistic", status="partial")
        result = _evaluate(derivation)
        self.assertEqual(derivation["transformation"]["mode"], "probabilistic")
        self.assertEqual(derivation["transformation"]["status"], "partial")
        self.assertEqual(result["applicability"]["status"], "revalidation_required")
        self.assertIn("transformation_partial", result["applicability"]["reasons"])

    def test_failed_transformation_is_not_current_evidence(self):
        result = _evaluate(_derivation(status="failed"))
        self.assertEqual(result["applicability"]["status"], "revalidation_required")
        self.assertIn("transformation_failed", result["applicability"]["reasons"])

    def test_complete_deterministic_and_probabilistic_transforms_share_authority_boundary(self):
        deterministic = _evaluate(_derivation(mode="deterministic", status="complete"), source_state="revoked")
        probabilistic = _evaluate(_derivation(mode="probabilistic", status="complete"), source_state="revoked")
        self.assertEqual(deterministic["applicability"]["status"], "revalidation_required")
        self.assertEqual(probabilistic["applicability"]["status"], "revalidation_required")
        self.assertEqual(deterministic["applicability"]["reasons"], probabilistic["applicability"]["reasons"])
        self.assertEqual(deterministic["interpretation"]["authority_effect"], "none")
        self.assertEqual(probabilistic["interpretation"]["authority_effect"], "none")

    def test_child_derivation_preserves_explicit_mode_and_status(self):
        child = derive_from(
            _derivation(),
            {
                "method": "projection",
                "mode": "probabilistic",
                "status": "partial",
                "transformer_ref": "transformer:child",
                "transformer_version": "v2",
                "transformer_trust": "trusted",
                "output_ref": "derived:child",
                "evidence_refs": ["evidence:child"],
                "created_at": "2026-08-13T03:20:02Z",
            },
            expected_scope=SCOPE,
        )
        self.assertEqual(child["transformation"]["mode"], "probabilistic")
        self.assertEqual(child["transformation"]["status"], "partial")
        self.assertEqual(_evaluate(child)["applicability"]["status"], "revalidation_required")

    def test_legacy_derivation_without_mode_or_status_remains_schema_valid_and_defaults_complete(self):
        legacy = normalize_derivation(
            {
                "root_origin_refs": ["origin:a"],
                "immediate_source_refs": ["origin:a"],
                "source_trust": "bounded_trusted",
                "transformation": {
                    "method": "summary",
                    "transformer_ref": "transformer:legacy",
                    "transformer_version": "v1",
                    "transformer_trust": "trusted",
                    "output_ref": "derived:legacy",
                },
                "scope": SCOPE,
                "evidence_refs": ["evidence:a"],
                "created_at": "2026-08-13T03:20:03Z",
            },
            expected_scope=SCOPE,
        )
        self.assertNotIn("mode", legacy["transformation"])
        self.assertNotIn("status", legacy["transformation"])
        self.assertEqual(_evaluate(legacy)["applicability"]["status"], "current")


if __name__ == "__main__":
    unittest.main()
