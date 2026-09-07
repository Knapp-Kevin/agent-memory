"""D/F/H/R/P accounting for sleeper-poisoning behavioral proof."""

from __future__ import annotations

import unittest

from agentmem_ref.sleeper_poisoning_depth import build_sleeper_poisoning_depth_report

COMMIT = "4" * 40


class SleeperPoisoningDepthTests(unittest.TestCase):
    def test_sleeper_claim_is_d_f_h_only(self):
        report = build_sleeper_poisoning_depth_report(COMMIT)
        self.assertTrue(report["required_behavioral_cases_passed"])
        self.assertEqual(len(report["claims"]), 1)
        claim = report["claims"][0]
        self.assertEqual(claim["claim_id"], "poisoning:sleeper-delayed-trigger-recall")
        self.assertEqual(claim["demonstrated_levels"], ["D", "F", "H"])
        self.assertEqual(claim["highest_demonstrated_level"], "H")
        self.assertEqual(claim["explicitly_unproven_levels"], ["R", "P"])
        self.assertEqual(claim["runtime_evidence_refs"], [])
        self.assertEqual(claim["production_evidence_refs"], [])

    def test_no_runtime_production_or_composite_claim(self):
        report = build_sleeper_poisoning_depth_report(COMMIT)
        self.assertNotIn("score", report)
        self.assertNotIn("composite_score", report)
        limits = " ".join(report["known_limits"])
        self.assertIn("earns H evidence only", limits)
        self.assertIn("Production evidence P is explicitly unproven", limits)

    def test_exact_head_is_required(self):
        with self.assertRaisesRegex(ValueError, "exact 40-hex commit"):
            build_sleeper_poisoning_depth_report("not-a-commit")


if __name__ == "__main__":
    unittest.main()
