"""Derivation currentness and governed scope propagation tests for issue #210."""

from __future__ import annotations

import copy
import unittest

from agentmem_ref.derivation_currentness import evaluate_derivation_currentness
from agentmem_ref.derivation_currentness_harness import run_derivation_currentness_harness
from agentmem_ref.derivation_evidence import derive_from, normalize_derivation


SCOPE = {
    "scope_ref": "scope:tenant-a/project-a",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}
NARROW = {
    "scope_ref": "scope:tenant-a/project-a/private",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}


def _derivation(*, confidence=0.8, transformer_trust="trusted"):
    return normalize_derivation(
        {
            "root_origin_refs": ["origin:a", "origin:b"],
            "immediate_source_refs": ["origin:a", "origin:b"],
            "source_trust": "bounded_trusted",
            "transformation": {
                "method": "summary",
                "transformer_ref": "transformer:test",
                "transformer_version": "v1",
                "transformer_trust": transformer_trust,
                "output_ref": "derived:test",
            },
            "scope": SCOPE,
            "evidence_refs": ["evidence:a", "evidence:b"],
            "confidence": {
                "signal_semantics": "summary_confidence",
                "estimator_ref": "estimator:test",
                "estimator_version": "v1",
                "value": confidence,
            },
            "created_at": "2026-08-13T03:15:00Z",
        },
        expected_scope=SCOPE,
    )


def _observations(state_a="current", state_b="current", evidence_class_a="ordinary"):
    return [
        {
            "origin_ref": "origin:a",
            "state": state_a,
            "evidence_class": evidence_class_a,
            "evidence_refs": [f"evidence:a:{state_a}"],
        },
        {
            "origin_ref": "origin:b",
            "state": state_b,
            "evidence_class": "ordinary",
            "evidence_refs": [f"evidence:b:{state_b}"],
        },
    ]


def _scope_observation(status="unchanged", scope_ref=SCOPE["scope_ref"], *, tenant="tenant-a", project="project-a"):
    return {
        "status": status,
        "current_scope_ref": scope_ref,
        "tenant_ref": tenant,
        "project_ref": project,
        "evidence_refs": [f"evidence:scope:{status}"],
    }


class DerivationCurrentnessTests(unittest.TestCase):
    def test_fixture_linked_harness_passes(self):
        result = run_derivation_currentness_harness()
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["checks"]["scope_reduction_requires_revalidation"])
        self.assertTrue(result["checks"]["root_revocation_propagates_to_second"])
        self.assertTrue(result["checks"]["shared_revocation_requires_revalidation"])

    def test_all_current_roots_and_unchanged_scope_are_current(self):
        result = evaluate_derivation_currentness(
            _derivation(),
            source_observations=_observations(),
            scope_observation=_scope_observation(),
            evaluated_at="2026-08-13T03:16:00Z",
        )
        self.assertEqual(result["applicability"]["status"], "current")
        self.assertFalse(result["applicability"]["revalidation_required"])
        self.assertEqual(result["applicability"]["reasons"], [])

    def test_missing_root_is_unknown_and_extra_source_cannot_substitute(self):
        result = evaluate_derivation_currentness(
            _derivation(),
            source_observations=[
                {
                    "origin_ref": "origin:a",
                    "state": "current",
                    "evidence_class": "ordinary",
                    "evidence_refs": ["evidence:a"],
                },
                {
                    "origin_ref": "origin:unrelated",
                    "state": "current",
                    "evidence_class": "ordinary",
                    "evidence_refs": ["evidence:unrelated"],
                },
            ],
            scope_observation=_scope_observation(),
            evaluated_at="2026-08-13T03:16:01Z",
        )
        self.assertEqual(result["applicability"]["status"], "unknown")
        self.assertTrue(result["applicability"]["revalidation_required"])
        self.assertIn("missing_source_observation:origin:b", result["applicability"]["reasons"])
        self.assertEqual(result["unexpected_source_refs"], ["origin:unrelated"])
        missing = next(item for item in result["source_observations"] if item["origin_ref"] == "origin:b")
        self.assertFalse(missing["observed"])
        self.assertEqual(missing["state"], "unknown")

    def test_deleted_and_tombstoned_are_distinct_revalidation_reasons(self):
        deleted = evaluate_derivation_currentness(
            _derivation(),
            source_observations=_observations(state_a="deleted"),
            scope_observation=_scope_observation(),
            evaluated_at="2026-08-13T03:16:02Z",
        )
        tombstoned = evaluate_derivation_currentness(
            _derivation(),
            source_observations=_observations(state_a="tombstoned"),
            scope_observation=_scope_observation(),
            evaluated_at="2026-08-13T03:16:03Z",
        )
        self.assertIn("source_deleted:origin:a", deleted["applicability"]["reasons"])
        self.assertIn("source_tombstoned:origin:a", tombstoned["applicability"]["reasons"])
        self.assertEqual(deleted["applicability"]["status"], "revalidation_required")
        self.assertEqual(tombstoned["applicability"]["status"], "revalidation_required")

    def test_multi_hop_child_uses_original_root_lineage_for_currentness(self):
        first = _derivation()
        child = derive_from(
            first,
            {
                "method": "compression",
                "transformer_ref": "transformer:child",
                "transformer_version": "v2",
                "transformer_trust": "trusted",
                "output_ref": "derived:child",
                "evidence_refs": ["evidence:child"],
                "created_at": "2026-08-13T03:16:04Z",
            },
            expected_scope=SCOPE,
        )
        result = evaluate_derivation_currentness(
            child,
            source_observations=_observations(state_a="revoked"),
            scope_observation=_scope_observation(),
            evaluated_at="2026-08-13T03:16:05Z",
        )
        self.assertEqual(child["root_origin_refs"], ["origin:a", "origin:b"])
        self.assertNotIn(first["derivation_id"], child["root_origin_refs"])
        self.assertIn("source_revoked:origin:a", result["applicability"]["reasons"])
        self.assertEqual(result["applicability"]["status"], "revalidation_required")

    def test_negative_and_adversarial_source_character_survives_trusted_transform(self):
        result = evaluate_derivation_currentness(
            _derivation(transformer_trust="trusted"),
            source_observations=_observations(evidence_class_a="adversarial"),
            scope_observation=_scope_observation(),
            evaluated_at="2026-08-13T03:16:06Z",
        )
        self.assertEqual(result["evidence_character"], "negative_or_adversarial")
        self.assertEqual(result["interpretation"]["authority_effect"], "none")

    def test_confidence_and_transformer_trust_do_not_change_currentness(self):
        high = evaluate_derivation_currentness(
            _derivation(confidence=0.99, transformer_trust="trusted"),
            source_observations=_observations(state_a="revoked"),
            scope_observation=_scope_observation(),
            evaluated_at="2026-08-13T03:16:07Z",
        )
        low = evaluate_derivation_currentness(
            _derivation(confidence=0.01, transformer_trust="untrusted"),
            source_observations=_observations(state_a="revoked"),
            scope_observation=_scope_observation(),
            evaluated_at="2026-08-13T03:16:08Z",
        )
        self.assertEqual(high["applicability"]["status"], low["applicability"]["status"])
        self.assertEqual(high["applicability"]["reasons"], low["applicability"]["reasons"])

    def test_currentness_evaluation_does_not_mutate_historical_derivation(self):
        derivation = _derivation()
        before = copy.deepcopy(derivation)
        result = evaluate_derivation_currentness(
            derivation,
            source_observations=_observations(state_a="superseded"),
            scope_observation=_scope_observation(),
            evaluated_at="2026-08-13T03:16:09Z",
        )
        self.assertEqual(derivation, before)
        self.assertEqual(derivation["derivation_id"], before["derivation_id"])
        self.assertFalse(result["interpretation"]["historical_derivation_mutated"])
        self.assertFalse(result["interpretation"]["prior_authorization_reusable"])
        self.assertEqual(result["interpretation"]["memory_admission"], "not_established")
        self.assertEqual(result["interpretation"]["certification_claim"], "none")

    def test_explicit_scope_narrowing_requires_basis_refs(self):
        with self.assertRaisesRegex(ValueError, "scope_basis_refs"):
            derive_from(
                _derivation(),
                {
                    "method": "rebuild",
                    "transformer_ref": "transformer:scope",
                    "transformer_version": "v1",
                    "transformer_trust": "trusted",
                    "output_ref": "derived:narrowed",
                    "evidence_refs": ["evidence:narrow"],
                    "created_at": "2026-08-13T03:16:10Z",
                },
                narrowed_scope=NARROW,
            )

    def test_explicit_scope_narrowing_is_recorded_and_transformer_override_is_ignored(self):
        child = derive_from(
            _derivation(),
            {
                "method": "rebuild",
                "transformer_ref": "transformer:scope",
                "transformer_version": "v1",
                "transformer_trust": "trusted",
                "output_ref": "derived:narrowed",
                "evidence_refs": ["evidence:narrow"],
                "created_at": "2026-08-13T03:16:11Z",
                "scope": {
                    "scope_ref": "scope:tenant-b/all",
                    "tenant_ref": "tenant-b",
                    "project_ref": "project-b",
                },
            },
            expected_scope=NARROW,
            narrowed_scope=NARROW,
            scope_basis_refs=("evidence:scope-reduction",),
        )
        self.assertEqual(child["scope"]["scope_ref"], NARROW["scope_ref"])
        self.assertEqual(child["scope"]["tenant_ref"], "tenant-a")
        self.assertEqual(child["scope"]["project_ref"], "project-a")
        self.assertEqual(child["scope"]["relation"], "narrowed")
        self.assertEqual(child["scope"]["basis_refs"], ["evidence:scope-reduction"])
        self.assertEqual(child["binding"]["status"], "exact")

    def test_scope_narrowing_cannot_change_tenant_or_project(self):
        for bad_scope, message in (
            (
                {
                    "scope_ref": "scope:tenant-b/private",
                    "tenant_ref": "tenant-b",
                    "project_ref": "project-a",
                },
                "tenant_ref",
            ),
            (
                {
                    "scope_ref": "scope:tenant-a/other-project/private",
                    "tenant_ref": "tenant-a",
                    "project_ref": "project-b",
                },
                "project_ref",
            ),
        ):
            with self.assertRaisesRegex(ValueError, message):
                derive_from(
                    _derivation(),
                    {
                        "method": "rebuild",
                        "transformer_ref": "transformer:scope",
                        "transformer_version": "v1",
                        "transformer_trust": "trusted",
                        "output_ref": "derived:bad-narrow",
                        "evidence_refs": ["evidence:narrow"],
                        "created_at": "2026-08-13T03:16:12Z",
                    },
                    narrowed_scope=bad_scope,
                    scope_basis_refs=("evidence:scope-reduction",),
                )

    def test_scope_narrowing_must_actually_change_scope_ref(self):
        with self.assertRaisesRegex(ValueError, "must differ"):
            derive_from(
                _derivation(),
                {
                    "method": "rebuild",
                    "transformer_ref": "transformer:scope",
                    "transformer_version": "v1",
                    "transformer_trust": "trusted",
                    "output_ref": "derived:not-narrowed",
                    "evidence_refs": ["evidence:narrow"],
                    "created_at": "2026-08-13T03:16:13Z",
                },
                narrowed_scope=SCOPE,
                scope_basis_refs=("evidence:scope-reduction",),
            )

    def test_duplicate_source_observation_is_rejected(self):
        duplicated = _observations() + [_observations()[0]]
        with self.assertRaisesRegex(ValueError, "duplicate source observation"):
            evaluate_derivation_currentness(
                _derivation(),
                source_observations=duplicated,
                scope_observation=_scope_observation(),
                evaluated_at="2026-08-13T03:16:14Z",
            )


if __name__ == "__main__":
    unittest.main()
