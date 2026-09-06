"""Evidence-depth assertions for issue #204."""

from __future__ import annotations

import unittest

from agentmem_ref.authority_laundering_depth import build_authority_laundering_depth_report


class AuthorityLaunderingDepthTests(unittest.TestCase):
    def test_report_is_d_f_h_only(self):
        report = build_authority_laundering_depth_report("a" * 40)
        self.assertTrue(report["required_behavioral_cases_passed"], report)
        claim = report["claims"][0]
        self.assertEqual(claim["demonstrated_levels"], ["D", "F", "H"])
        self.assertEqual(claim["highest_demonstrated_level"], "H")
        self.assertEqual(claim["explicitly_unproven_levels"], ["R", "P"])
        self.assertEqual(claim["runtime_evidence_refs"], [])
        self.assertEqual(claim["production_evidence_refs"], [])

    def test_report_rejects_non_exact_commit(self):
        with self.assertRaisesRegex(ValueError, "exact 40-hex"):
            build_authority_laundering_depth_report("main")


if __name__ == "__main__":
    unittest.main()
