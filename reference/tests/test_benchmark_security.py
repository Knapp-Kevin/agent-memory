"""Tests for the P5 benchmark/security scorecard."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.benchmark_security import build_report, with_metric  # noqa: E402

COMMIT = "1" * 40


class BenchmarkSecurityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = build_report(COMMIT, stochastic_trials=40)

    def test_scorecard_passes_without_scalar_quality_score(self):
        self.assertTrue(self.report["hard_gates_passed"])
        self.assertNotIn("score", self.report)
        self.assertNotIn("quality_score", self.report)
        self.assertEqual(len(self.report["hard_gates"]), 7)

    def test_all_cases_have_explicit_nonzero_denominators(self):
        for name, case in self.report["cases"].items():
            with self.subTest(case=name):
                self.assertGreater(case["denominator"], 0)
                self.assertGreaterEqual(case["numerator"], 0)

    def test_zero_tolerance_gates_cannot_be_averaged_away(self):
        zero_tolerance = [
            "cross_scope_admission_rate",
            "blocked_action_escape_rate",
            "authority_from_confidence_count",
            "stochastic_action_set_violation_rate",
            "silent_overwrite_rate",
            "deletion_residue_rate",
        ]
        for metric in zero_tolerance:
            with self.subTest(metric=metric):
                mutated = with_metric(self.report, metric, 1)
                self.assertFalse(mutated["hard_gates_passed"])
                gate = next(item for item in mutated["hard_gates"] if item["metric"] == metric)
                self.assertFalse(gate["passed"])

    def test_stale_authorization_gate_requires_complete_rejection(self):
        mutated = with_metric(self.report, "stale_authorization_rejection_rate", 0)
        self.assertFalse(mutated["hard_gates_passed"])
        gate = next(
            item for item in mutated["hard_gates"]
            if item["metric"] == "stale_authorization_rejection_rate"
        )
        self.assertEqual(gate["rule"], "== 1")
        self.assertFalse(gate["passed"])

    def test_concurrency_and_stale_authorization_are_measured_separately(self):
        metrics = self.report["metrics"]
        self.assertEqual(metrics["stale_authorization_rejection_rate"], 1.0)
        self.assertEqual(metrics["silent_overwrite_rate"], 0.0)
        self.assertTrue(self.report["cases"]["concurrent_conflict"]["details"]["conflict_recorded"])
        self.assertTrue(self.report["cases"]["concurrent_conflict"]["details"]["state_version_revalidated"])

    def test_bad_commit_is_rejected(self):
        with self.assertRaises(ValueError):
            build_report("not-a-commit", stochastic_trials=1)

    def test_nonpositive_stochastic_trials_are_rejected(self):
        with self.assertRaises(ValueError):
            build_report(COMMIT, stochastic_trials=0)


if __name__ == "__main__":
    unittest.main()
