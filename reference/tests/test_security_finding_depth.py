"""D/F/H/R/P accounting tests for P2-B scanner adapters."""

from __future__ import annotations

import unittest

from agentmem_ref.security_finding_depth import build_security_finding_depth_report

COMMIT = "3" * 40


class SecurityFindingDepthTests(unittest.TestCase):
    def test_scanner_adapters_are_d_f_h_only(self):
        report = build_security_finding_depth_report(COMMIT)
        self.assertTrue(report["required_behavioral_cases_passed"])
        self.assertEqual(len(report["claims"]), 2)
        for claim in report["claims"]:
            self.assertEqual(claim["demonstrated_levels"], ["D", "F", "H"])
            self.assertEqual(claim["highest_demonstrated_level"], "H")
            self.assertEqual(claim["explicitly_unproven_levels"], ["R", "P"])
            self.assertEqual(claim["runtime_evidence_refs"], [])
            self.assertEqual(claim["production_evidence_refs"], [])
            self.assertTrue(claim["behavioral_passed"])
            self.assertIn("does not assert external certification", claim["non_certification_statement"])

    def test_no_composite_score_or_live_scanner_claim(self):
        report = build_security_finding_depth_report(COMMIT)
        self.assertNotIn("score", report)
        self.assertNotIn("composite_score", report)
        rendered_limits = " ".join(report["known_limits"])
        self.assertIn("does not execute a live garak scan", rendered_limits)
        self.assertIn("R remains unproven", rendered_limits)
        self.assertIn("Production evidence P", rendered_limits)

    def test_exact_head_is_required(self):
        with self.assertRaisesRegex(ValueError, "exact 40-hex commit"):
            build_security_finding_depth_report("not-a-commit")


if __name__ == "__main__":
    unittest.main()
