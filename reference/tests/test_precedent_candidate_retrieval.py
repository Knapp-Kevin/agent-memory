"""Adversarial acceptance tests for issue #233 precedent candidate retrieval."""

from __future__ import annotations

import unittest

from agentmem_ref.precedent_candidate_harness import FIXTURE_CASE_IDS, run_reference_scenarios
from agentmem_ref.precedent_candidate_retrieval import selected_candidate_refs


class PrecedentCandidateRetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run_reference_scenarios()
        cls.rows = {row["case_id"]: row for row in cls.report["scenarios"]}

    def test_fixture_matrix_is_complete(self):
        self.assertEqual(tuple(self.report["fixture_case_ids"]), FIXTURE_CASE_IDS)
        self.assertEqual(self.report["scenario_count"], len(FIXTURE_CASE_IDS))
        self.assertEqual(set(self.rows), set(FIXTURE_CASE_IDS))

    def test_estimator_evidence_is_reconstructable_and_explicitly_non_authoritative(self):
        for row in self.report["scenarios"]:
            with self.subTest(case_id=row["case_id"]):
                evidence = row["evidence"]
                estimator = evidence["estimator"]
                self.assertTrue(estimator["estimator_id"])
                self.assertTrue(estimator["estimator_version"])
                self.assertTrue(estimator["configuration_ref"])
                self.assertTrue(estimator["threshold_ref"])
                self.assertTrue(estimator["score_semantics"])
                self.assertTrue(estimator["calibration_posture"])
                self.assertTrue(evidence["input_projection"]["identity"])
                self.assertTrue(evidence["input_projection"]["privacy_minimized"])
                self.assertTrue(evidence["run_ref"])
                self.assertTrue(evidence["executed_at"])
                self.assertEqual(evidence["authority_effect"], "none")
                self.assertFalse(evidence["can_authorize_execution"])
                self.assertFalse(evidence["can_change_permitted_actions"])
                self.assertFalse(evidence["can_create_grant_or_policy"])
                self.assertNotIn("permitted_actions", evidence)
                self.assertNotIn("standing_grant", evidence)
                for candidate in evidence["candidates"]:
                    self.assertEqual(candidate["score_semantics"], estimator["score_semantics"])
                    self.assertEqual(candidate["historical_rationale_treatment"], "data_not_instruction")
                    self.assertEqual(candidate["authority_effect"], "none")
                    self.assertFalse(candidate["can_authorize_execution"])
                    self.assertFalse(candidate["can_change_permitted_actions"])
                    self.assertFalse(candidate["can_create_grant_or_policy"])

    def test_safe_paraphrase_recovery_reaches_deterministic_applicability(self):
        row = self.rows["safe-paraphrase-recovery"]
        self.assertIn("precedent:safe-paraphrase", selected_candidate_refs(row["evidence"]))
        result = row["deterministic_results"][0]["applicability_result"]
        self.assertEqual(result["applicability"], "materially_equivalent")
        self.assertEqual(result["recommended_handling"], "reduce_redundant_review")
        self.assertEqual(result["authority_effect"], "none")
        self.assertFalse(result["can_authorize_execution"])

    def test_unsafe_near_matches_are_candidates_but_never_safe_equivalence(self):
        cases = {
            "force-main-near-match": {"target", "protected", "force"},
            "staging-vs-production": {"environment"},
            "ordinary-vs-sensitive-material": {"sensitivity"},
        }
        for case_id, expected_differences in cases.items():
            with self.subTest(case_id=case_id):
                row = self.rows[case_id]
                self.assertTrue(selected_candidate_refs(row["evidence"]))
                result = row["deterministic_results"][0]["applicability_result"]
                actual = {item["condition"] for item in result["material_differences"]}
                self.assertTrue(expected_differences.issubset(actual))
                self.assertNotEqual(result["recommended_handling"], "reduce_redundant_review")

    def test_cross_scope_and_stale_matches_are_blocked_by_deterministic_layer(self):
        cross = self.rows["cross-tenant-near-match"]
        self.assertTrue(selected_candidate_refs(cross["evidence"]))
        cross_result = cross["deterministic_results"][0]["applicability_result"]
        self.assertEqual(cross_result["applicability"], "materially_different")
        self.assertEqual(cross_result["recommended_handling"], "escalate")

        stale = self.rows["stale-revoked-exact-semantic-match"]
        self.assertTrue(selected_candidate_refs(stale["evidence"]))
        stale_result = stale["deterministic_results"][0]["applicability_result"]
        self.assertEqual(stale_result["applicability"], "stale")
        self.assertNotEqual(stale_result["recommended_handling"], "reduce_redundant_review")

    def test_negative_incident_is_not_suppressed_by_positive_candidate(self):
        row = self.rows["negative-incident-precedent"]
        selected = set(selected_candidate_refs(row["evidence"]))
        self.assertEqual(selected, {"precedent:positive-history", "precedent:incident-history"})
        by_ref = {
            item["candidate_precedent_ref"]: item["applicability_result"]
            for item in row["deterministic_results"]
        }
        incident = by_ref["precedent:incident-history"]
        self.assertTrue(incident["incident_or_negative_evidence_present"])
        self.assertEqual(incident["applicability"], "conflicting")
        self.assertEqual(incident["recommended_handling"], "escalate")

    def test_policy_generated_repetition_does_not_inflate_human_evidence(self):
        row = self.rows["policy-generated-repetition"]
        self.assertEqual(len(selected_candidate_refs(row["evidence"])), 7)
        for item in row["deterministic_results"]:
            result = item["applicability_result"]
            self.assertEqual(result["independent_human_evidence_count"], 1)
            self.assertEqual(result["policy_or_derived_evidence_count"], 6)

    def test_ambiguous_low_confidence_candidate_remains_explicit_but_unselected(self):
        row = self.rows["ambiguous-low-confidence-retrieval"]
        evidence = row["evidence"]
        self.assertEqual(evidence["status"], "completed")
        self.assertEqual(len(evidence["candidates"]), 1)
        candidate = evidence["candidates"][0]
        self.assertLess(candidate["score"], evidence["estimator"]["threshold"])
        self.assertFalse(candidate["above_threshold"])
        self.assertEqual(selected_candidate_refs(evidence), ())
        self.assertEqual(row["deterministic_results"], [])

    def test_estimator_failure_is_fail_closed_and_deterministic_fallback_survives(self):
        for case_id, expected_status in (
            ("estimator-unavailable-fallback", "unavailable"),
            ("unsupported-estimator-version-fallback", "unsupported"),
        ):
            with self.subTest(case_id=case_id):
                row = self.rows[case_id]
                evidence = row["evidence"]
                self.assertEqual(evidence["status"], expected_status)
                self.assertEqual(evidence["candidates"], [])
                self.assertFalse(evidence["failure"]["fail_open"])
                self.assertEqual(selected_candidate_refs(evidence), ())
                self.assertTrue(row["fallback_success"])
                fallback = row["fallback_result"]
                self.assertEqual(fallback["recommended_handling"], "reduce_redundant_review")
                self.assertEqual(fallback["authority_effect"], "none")
                self.assertFalse(fallback["can_authorize_execution"])

    def test_instruction_shaped_rationale_is_treated_as_data(self):
        row = self.rows["instruction-shaped-historical-rationale"]
        candidate = row["evidence"]["candidates"][0]
        self.assertEqual(candidate["historical_rationale_treatment"], "data_not_instruction")
        result = row["deterministic_results"][0]["applicability_result"]
        self.assertEqual(result["recommended_handling"], "reduce_redundant_review")
        self.assertEqual(result["authority_effect"], "none")
        self.assertFalse(result["can_authorize_execution"])

    def test_metrics_keep_retrieval_usefulness_separate_from_governance_safety(self):
        metrics = self.report["metrics"]
        retrieval = metrics["retrieval_usefulness"]
        safety = metrics["governance_safety"]

        self.assertEqual(retrieval["cases_evaluated"], len(FIXTURE_CASE_IDS))
        self.assertEqual(retrieval["candidate_recall_on_paraphrased_equivalent_cases"], 1.0)
        self.assertEqual(retrieval["irrelevant_candidate_rate"], 0.0)
        self.assertGreater(retrieval["unsafe_near_match_candidate_rate"], 0.0)

        self.assertEqual(safety["final_unsafe_equivalence_false_positives"], 0)
        self.assertEqual(safety["material_difference_misses"], 0)
        self.assertEqual(safety["negative_precedent_misses"], 0)
        self.assertEqual(safety["cross_scope_leakage_failures"], 0)
        self.assertEqual(safety["stale_precedent_reuse_failures"], 0)
        self.assertEqual(safety["independent_human_attribution_errors"], 0)
        self.assertEqual(safety["estimator_unavailable_fallback_success"], 1.0)


if __name__ == "__main__":
    unittest.main()
