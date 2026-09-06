"""Fixture-linked unsafe composition evidence tests for issue #206."""

from __future__ import annotations

import unittest

from agentmem_ref.unsafe_composition_depth import build_unsafe_composition_depth_report
from agentmem_ref.unsafe_composition_harness import run_unsafe_composition_harness


class UnsafeCompositionEvidenceTests(unittest.TestCase):
    def test_fixture_linked_behavioral_harness_passes(self):
        result = run_unsafe_composition_harness()
        self.assertTrue(result["passed"], result)
        checks = result["checks"]
        self.assertTrue(checks["both_candidates_individually_admitted"])
        self.assertTrue(checks["unsafe_combination_rejected"])
        self.assertTrue(checks["blocked_composition_has_no_assembled_context"])
        self.assertTrue(checks["blocked_composition_has_no_downstream_influence"])
        self.assertTrue(checks["no_constraint_does_not_invent_block"])
        self.assertTrue(checks["unrelated_constraint_does_not_invent_block"])
        self.assertTrue(checks["candidate_order_cannot_bypass_gate"])
        self.assertTrue(checks["ordinary_recall_denial_survives_composition"])

    def test_blocked_surface_is_explicitly_empty(self):
        result = run_unsafe_composition_harness()["observed"]["blocked"]
        self.assertEqual(result["assembled_context"], [])
        self.assertEqual(result["downstream_influence"], [])
        self.assertEqual(result["reason"], "cross_domain_composition_prohibited")
        self.assertEqual(result["violated_constraint_refs"], ["fixture:memory-a-plus-memory-b"])

    def test_evidence_depth_is_d_f_h_only(self):
        report = build_unsafe_composition_depth_report("a" * 40)
        self.assertTrue(report["required_behavioral_cases_passed"], report)
        claim = report["claims"][0]
        self.assertEqual(claim["demonstrated_levels"], ["D", "F", "H"])
        self.assertEqual(claim["highest_demonstrated_level"], "H")
        self.assertEqual(claim["explicitly_unproven_levels"], ["R", "P"])
        self.assertEqual(claim["runtime_evidence_refs"], [])
        self.assertEqual(claim["production_evidence_refs"], [])

    def test_report_requires_exact_head(self):
        with self.assertRaisesRegex(ValueError, "exact 40-hex"):
            build_unsafe_composition_depth_report("main")


if __name__ == "__main__":
    unittest.main()
