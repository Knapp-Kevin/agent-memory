"""Evidence-depth assertions for issue #210."""

from __future__ import annotations

import unittest

from agentmem_ref.derivation_currentness_depth import build_derivation_currentness_depth_report


class DerivationCurrentnessDepthTests(unittest.TestCase):
    def test_all_claims_are_d_f_h_only(self):
        report = build_derivation_currentness_depth_report("a" * 40)
        self.assertTrue(report["required_behavioral_cases_passed"], report)
        self.assertEqual(len(report["claims"]), 3)
        for claim in report["claims"]:
            self.assertEqual(claim["demonstrated_levels"], ["D", "F", "H"])
            self.assertEqual(claim["highest_demonstrated_level"], "H")
            self.assertEqual(claim["explicitly_unproven_levels"], ["R", "P"])
            self.assertEqual(claim["runtime_evidence_refs"], [])
            self.assertEqual(claim["production_evidence_refs"], [])

    def test_report_requires_exact_head(self):
        with self.assertRaisesRegex(ValueError, "exact 40-hex"):
            build_derivation_currentness_depth_report("main")


if __name__ == "__main__":
    unittest.main()
