"""Autonomous maintenance / evidence-fusion research tests for #227."""

from __future__ import annotations

import unittest

from agentmem_ref.autonomous_maintenance_harness import run_autonomous_maintenance_harness


class AutonomousMaintenanceTests(unittest.TestCase):
    def test_research_harness_passes(self):
        result = run_autonomous_maintenance_harness()
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["finding"]["noisy_or_is_estimator_not_authority"])
        self.assertEqual(result["finding"]["missing_reusable_contract"], "maintenance_run_transaction_evidence")
        self.assertFalse(result["finding"]["broad_background_maintenance_authority_required"])

    def test_duplicate_derived_and_correlated_support_do_not_masquerade_as_independent(self):
        result = run_autonomous_maintenance_harness()
        by_id = {item["id"]: item for item in result["fusion_results"]}
        self.assertEqual(by_id["replayed-evidence-not-independent"]["support_groups"], 1)
        self.assertEqual(by_id["derived-self-citation-not-independent"]["support_groups"], 1)
        self.assertEqual(by_id["correlated-sources-one-dependence-group"]["support_groups"], 1)
        self.assertEqual(by_id["independent-positive-support"]["support_probability"], 0.7)

    def test_challenge_evidence_is_not_hidden_by_positive_support(self):
        result = run_autonomous_maintenance_harness()
        by_id = {item["id"]: item for item in result["fusion_results"]}
        case = by_id["challenge-evidence-remains-visible"]
        self.assertEqual(case["support_probability"], 0.9)
        self.assertEqual(case["challenge_probability"], 0.8)
        self.assertTrue(case["interpretation"]["challenge_evidence_preserved_separately"])

    def test_high_estimator_support_does_not_skip_pama(self):
        result = run_autonomous_maintenance_harness()
        by_id = {item["id"]: item for item in result["governance_results"]}
        self.assertEqual(by_id["high-fused-score-promotion"]["pama_outcome"], "require_review")
        self.assertEqual(by_id["protected-memory-deletion"]["pama_outcome"], "require_external_verification")
        self.assertEqual(by_id["cross-scope-consolidation"]["pama_outcome"], "block")
        for case in by_id.values():
            self.assertEqual(case["interpretation"]["fused_support_authority"], "none")

    def test_cursor_and_validation_transaction_invariants(self):
        result = run_autonomous_maintenance_harness()
        by_id = {item["id"]: item for item in result["transaction_results"]}
        self.assertEqual(by_id["partial-apply-rolls-back"]["cursor_before"], by_id["partial-apply-rolls-back"]["cursor_after"])
        self.assertEqual(by_id["failed-nonatomic-backend-quarantines"]["status"], "quarantined")
        self.assertFalse(by_id["failed-nonatomic-backend-quarantines"]["cursor_advanced"])
        self.assertTrue(by_id["validation-failure-retains-original"]["original_retained"])
        self.assertEqual(
            by_id["successful-validated-commit-advances-once"]["cursor_after"],
            by_id["successful-validated-commit-advances-once"]["cursor_before"] + 1,
        )
        self.assertFalse(by_id["revoked-source-rebuild-not-current"]["current_outputs"])
        self.assertFalse(by_id["index-only-rebuild-can-be-ledgered-housekeeping"]["semantic_memory_changed"])


if __name__ == "__main__":
    unittest.main()
