"""Contract tests for the P6 Mem0 comparator report evaluator.

The real Mem0 execution runs in an isolated CI environment. These tests protect
the repository-side classification/report semantics without adding Mem0 as a
first-party test dependency.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.mem0_comparator import (  # noqa: E402
    CLASSIFICATIONS,
    CONFIGURABLE,
    NATIVE,
    WRAPPER_REQUIRED,
    _scenario,
    evaluate_report,
)


class Mem0ComparatorContractTests(unittest.TestCase):
    def _report(self):
        return {
            "scenarios": {
                "scope": _scenario(CONFIGURABLE, True, {"cross_scope_hits": 0}, "authenticate scope above Mem0"),
                "identity": _scenario(NATIVE, True, {"laundered": False}, "retain authority above identity hygiene"),
                "direct_id": _scenario(WRAPPER_REQUIRED, True, {"scope_argument": False}, "gate direct-ID access"),
            }
        }

    def test_existing_five_value_vocabulary_is_preserved(self):
        self.assertEqual(
            CLASSIFICATIONS,
            {
                "NATIVE",
                "CONFIGURABLE",
                "WRAPPER_REQUIRED",
                "NOT_REPRESENTABLE",
                "UNKNOWN_NEEDS_TEST",
            },
        )

    def test_execution_success_requires_every_scenario_to_pass(self):
        report = self._report()
        self.assertTrue(evaluate_report(report))
        report["scenarios"]["scope"]["passed"] = False
        self.assertFalse(evaluate_report(report))

    def test_unknown_classification_fails_closed(self):
        report = self._report()
        report["scenarios"]["scope"]["classification"] = "GOOD_ENOUGH"
        self.assertFalse(evaluate_report(report))

    def test_empty_scenario_set_fails_closed(self):
        self.assertFalse(evaluate_report({"scenarios": {}}))

    def test_scenario_constructor_rejects_new_vocabulary(self):
        with self.assertRaises(ValueError):
            _scenario("PASSING_GRADE", True, {}, "not a real classification")

    def test_report_contract_has_no_scalar_score_semantics(self):
        report = self._report()
        self.assertNotIn("score", report)
        self.assertNotIn("quality_score", report)
        for scenario in report["scenarios"].values():
            self.assertIn("classification", scenario)
            self.assertIn("agent_memory_wrapper_implication", scenario)


if __name__ == "__main__":
    unittest.main()
