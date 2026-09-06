"""Executable evidence for the ADR-029 governance-projection boundary."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.governance_projection import (  # noqa: E402
    MaterialCondition,
    PrecedentInput,
    ProjectionRequest,
    build_governance_projection,
)


class GovernanceProjectionTests(unittest.TestCase):
    def _request(self, precedents: tuple[PrecedentInput, ...]) -> ProjectionRequest:
        return ProjectionRequest(
            projection_id="projection:test:1",
            current_context_ref="action:test:current",
            domain_refs=("tenant:a", "repo:a"),
            scope_relationship="same",
            purpose_ref="purpose:publish",
            precedents=precedents,
            source_snapshot_ref="snapshot:test:1",
            generated_at="2026-08-12T15:30:00Z",
            sensitivity_labels=("repository_metadata",),
        )

    def test_matching_human_precedent_is_context_not_permission(self):
        precedent = PrecedentInput(
            memory_ref="memory:feature-push",
            polarity="supportive",
            source_type="human_adjudication",
            source_ref="approval:1",
            independent_adjudication=True,
            authority_ref="principal:owner",
            rationale_ref="rationale:1",
            rationale_summary="Approved for a non-protected feature branch with current CI.",
            policy_version_ref="policy:v3",
            outcome_refs=("outcome:success",),
            conditions=(
                MaterialCondition("protected_target", False, False),
                MaterialCondition("force", False, False),
                MaterialCondition("ci_current", True, True),
            ),
        )

        projection = build_governance_projection(self._request((precedent,)))

        self.assertEqual(projection["precedents"][0]["relationship"], "material_match")
        self.assertEqual(projection["precedents"][0]["polarity"], "supportive")
        self.assertTrue(projection["derivation"]["reconstructable"])
        self.assertEqual(projection["derivation"]["mode"], "deterministic_condition_match")
        self.assertNotIn("decision", projection)
        self.assertNotIn("verdict", projection)
        self.assertNotIn("permission", projection)
        self.assertNotIn("risk_score", projection)
        self.assertNotIn("require_approval", projection)

    def test_material_mismatch_does_not_inherit_superficial_positive_precedent(self):
        prior_safe = PrecedentInput(
            memory_ref="memory:feature-push",
            polarity="supportive",
            source_type="human_adjudication",
            source_ref="approval:1",
            independent_adjudication=True,
            conditions=(
                MaterialCondition("protected_target", False, True),
                MaterialCondition("force", False, True),
                MaterialCondition("ci_current", True, False),
            ),
        )
        prior_denial = PrecedentInput(
            memory_ref="memory:force-main-denial",
            polarity="cautionary",
            source_type="human_adjudication",
            source_ref="denial:1",
            independent_adjudication=True,
            conditions=(
                MaterialCondition("protected_target", True, True),
                MaterialCondition("force", True, True),
            ),
        )

        projection = build_governance_projection(self._request((prior_safe, prior_denial)))

        first, second = projection["precedents"]
        self.assertEqual(first["relationship"], "material_mismatch")
        self.assertEqual(
            [condition["comparison"] for condition in first["material_conditions"]],
            ["mismatch", "mismatch", "mismatch"],
        )
        self.assertEqual(second["relationship"], "material_match")
        self.assertEqual(projection["negative_precedent_refs"], ["memory:force-main-denial"])

    def test_policy_generated_allow_cannot_claim_independent_human_adjudication(self):
        precedent = PrecedentInput(
            memory_ref="memory:policy-allow",
            polarity="supportive",
            source_type="policy_outcome",
            source_ref="policy-decision:1",
            independent_adjudication=True,
            conditions=(MaterialCondition("target", "feature", "feature"),),
        )

        with self.assertRaisesRegex(ValueError, "independent_adjudication"):
            build_governance_projection(self._request((precedent,)))

    def test_unknown_condition_remains_unknown_instead_of_becoming_match(self):
        precedent = PrecedentInput(
            memory_ref="memory:unknown-ci",
            polarity="neutral",
            source_type="runtime_observation",
            source_ref="runtime:1",
            conditions=(MaterialCondition("ci_current", True, None),),
        )

        projection = build_governance_projection(self._request((precedent,)))

        item = projection["precedents"][0]
        self.assertEqual(item["relationship"], "unknown")
        self.assertEqual(item["material_conditions"][0]["comparison"], "unknown")

    def test_same_inputs_rebuild_the_same_projection(self):
        precedent = PrecedentInput(
            memory_ref="memory:stable",
            polarity="supportive",
            source_type="human_adjudication",
            source_ref="approval:stable",
            independent_adjudication=True,
            conditions=(MaterialCondition("environment", "staging", "staging"),),
        )
        request = self._request((precedent,))

        self.assertEqual(
            build_governance_projection(request),
            build_governance_projection(request),
        )


if __name__ == "__main__":
    unittest.main()
