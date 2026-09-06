"""Executable precedent applicability scenarios for issue #181."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from agentmem_ref.governance_projection import (
    MaterialCondition,
    PrecedentInput,
    ProjectionRequest,
    build_governance_projection,
)
from agentmem_ref.precedent_applicability import evaluate_projection, summarize_metrics

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "precedent-applicability-matrix.json"
REPORT = ROOT / "reports" / "examples" / "precedent-applicability-results.example.json"


def _projection_from_scenario(scenario: dict) -> dict:
    precedents: list[PrecedentInput] = []
    for spec in scenario["precedents"]:
        repeat = int(spec.get("repeat", 1))
        for index in range(repeat):
            conditions = tuple(
                MaterialCondition(
                    name=name,
                    precedent_value=values[0],
                    current_value=values[1],
                    evidence_refs=(f"evidence:{scenario['case_id']}:{name}",),
                )
                for name, values in spec["conditions"].items()
            )
            precedents.append(
                PrecedentInput(
                    memory_ref=f"{spec['ref_prefix']}:{index + 1}",
                    polarity=spec["polarity"],
                    conditions=conditions,
                    source_type=spec["source_type"],
                    source_ref=f"source:{scenario['case_id']}:{spec['ref_prefix']}:{index + 1}",
                    validity_status=spec["validity"],
                    independent_adjudication=spec["independent_adjudication"],
                    outcome_refs=(f"outcome:{scenario['case_id']}:{index + 1}",),
                    policy_version_ref="policy:v1",
                )
            )

    return build_governance_projection(
        ProjectionRequest(
            projection_id=f"projection:{scenario['case_id']}",
            current_context_ref=f"context:{scenario['case_id']}",
            domain_refs=("tenant-a", "project-a"),
            scope_relationship=scenario["scope_relationship"],
            precedents=tuple(precedents),
            source_snapshot_ref=f"snapshot:{scenario['case_id']}",
            generated_at="2026-08-12T21:10:00Z",
            purpose_ref="purpose:precedent-evaluation",
            privacy_minimized=True,
        )
    )


class PrecedentApplicabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_required_scenario_matrix_and_metrics(self):
        evaluated = []
        seen = set()
        for scenario in self.matrix["scenarios"]:
            with self.subTest(case_id=scenario["case_id"]):
                projection = _projection_from_scenario(scenario)
                result = evaluate_projection(projection)
                seen.add(scenario["case_id"])

                self.assertEqual(result["applicability"], scenario["expected_applicability"])
                self.assertEqual(result["recommended_handling"], scenario["expected_handling"])
                self.assertEqual(result["authority_effect"], "none")
                self.assertFalse(result["can_authorize_execution"])
                self.assertNotIn("permitted_actions", result)
                self.assertNotIn("selected_action", result)
                self.assertNotIn("standing_grant", result)

                evaluated.append({"result": result, "expected": scenario["expected"]})

        required = {
            "repeated-safe-equivalent",
            "force-protected-branch-near-match",
            "stale-ci-state",
            "cross-tenant-near-match",
            "incident-dominates-positive-history",
            "policy-generated-repetition-does-not-inflate-human-count",
            "expired-approval-evidence",
            "novel-insufficient-evidence",
        }
        self.assertEqual(seen, required)
        metrics = summarize_metrics(evaluated)
        self.assertEqual(metrics, self.matrix["expected_behavior"])

        report = json.loads(REPORT.read_text(encoding="utf-8"))
        reported_metrics = {key: report[key] for key in metrics}
        self.assertEqual(reported_metrics, metrics)

    def test_force_push_material_differences_are_explicit(self):
        scenario = next(
            item for item in self.matrix["scenarios"]
            if item["case_id"] == "force-protected-branch-near-match"
        )
        result = evaluate_projection(_projection_from_scenario(scenario))
        difference_names = {item["condition"] for item in result["material_differences"]}
        self.assertEqual(difference_names, {"target", "protected", "force"})

    def test_negative_incident_survives_positive_frequency(self):
        scenario = next(
            item for item in self.matrix["scenarios"]
            if item["case_id"] == "incident-dominates-positive-history"
        )
        result = evaluate_projection(_projection_from_scenario(scenario))
        self.assertEqual(result["independent_human_evidence_count"], 5)
        self.assertEqual(result["policy_or_derived_evidence_count"], 1)
        self.assertTrue(result["incident_or_negative_evidence_present"])
        self.assertEqual(result["recommended_handling"], "escalate")

    def test_policy_outcomes_do_not_launder_into_independent_human_count(self):
        scenario = next(
            item for item in self.matrix["scenarios"]
            if item["case_id"] == "policy-generated-repetition-does-not-inflate-human-count"
        )
        result = evaluate_projection(_projection_from_scenario(scenario))
        self.assertEqual(result["independent_human_evidence_count"], 1)
        self.assertEqual(result["policy_or_derived_evidence_count"], 6)

    def test_unknown_material_condition_never_becomes_match(self):
        scenario = next(
            item for item in self.matrix["scenarios"]
            if item["case_id"] == "novel-insufficient-evidence"
        )
        result = evaluate_projection(_projection_from_scenario(scenario))
        self.assertTrue(result["unknown_conditions"])
        self.assertEqual(result["applicability"], "insufficient_evidence")
        self.assertNotEqual(result["recommended_handling"], "reduce_redundant_review")

    def test_probabilistic_projection_mode_is_rejected_in_v01(self):
        projection = _projection_from_scenario(self.matrix["scenarios"][0])
        probabilistic = copy.deepcopy(projection)
        probabilistic["derivation"] = {
            "mode": "semantic_similarity",
            "reconstructable": True,
            "source_snapshot_ref": "snapshot:semantic",
            "estimator_ref": "estimator:embedding",
            "estimator_version": "1.0.0",
            "uncertainty_summary": {"confidence": "not-authority"},
        }
        with self.assertRaisesRegex(ValueError, "accepts only"):
            evaluate_projection(probabilistic)


if __name__ == "__main__":
    unittest.main()
