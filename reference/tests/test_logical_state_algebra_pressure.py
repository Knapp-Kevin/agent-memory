"""Acceptance tests for issue #276 logical-state algebra pressure evidence."""

from __future__ import annotations

import unittest

from agentmem_ref.logical_state_algebra_pressure import run_logical_state_algebra_pressure


class LogicalStateAlgebraPressureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run_logical_state_algebra_pressure("a" * 40)
        cls.by_id = {item["id"]: item for item in cls.report["scenarios"]}

    def test_all_declared_pressure_scenarios_execute(self):
        self.assertEqual(self.report["scenario_count"], 8)
        self.assertEqual(set(self.by_id), {f"LSA-{index:02d}" for index in range(1, 9)})

    def test_existing_contracts_express_current_fixture_set(self):
        self.assertTrue(self.report["aggregate"]["all_existing_contracts_express_scenarios"])
        self.assertFalse(self.report["aggregate"]["missing_generic_primitive_observed"])
        self.assertEqual(self.report["aggregate"]["current_recommendation"], "no_new_algebra")

    def test_stronger_engine_is_not_manufactured_by_fixture_success(self):
        self.assertFalse(self.report["aggregate"]["stronger_engine_evidence_observed"])
        self.assertTrue(any("stronger-engine" in item.lower() for item in self.report["limitations"]))

    def test_relational_transaction_does_not_close_derived_lifecycle(self):
        checks = self.by_id["LSA-01"]["checks"]
        self.assertTrue(checks["stale_projection_detected"])
        self.assertTrue(checks["delete_residue_detected"])
        self.assertTrue(checks["transaction_not_derived_cleanup"])

    def test_graph_reachability_does_not_become_permission(self):
        checks = self.by_id["LSA-02"]["checks"]
        self.assertTrue(checks["stale_derived_path_detected"])
        self.assertTrue(checks["cached_reachability_not_admitted"])
        self.assertTrue(checks["reachability_not_permission"])

    def test_event_integrity_remains_separate_from_current_truth_and_forgetting(self):
        checks = self.by_id["LSA-03"]["checks"]
        self.assertTrue(checks["current_truth_separate_from_history"])
        self.assertTrue(checks["tombstone_not_forgetting_proof"])
        self.assertTrue(checks["history_not_authority"])

    def test_hybrid_delete_residue_prevents_silent_lifecycle_closure(self):
        checks = self.by_id["LSA-04"]["checks"]
        self.assertTrue(checks["stale_cross_surface_state_detected"])
        self.assertTrue(checks["residual_projection_detected"])
        self.assertTrue(checks["deletion_closure_names_canonical_source"])

    def test_conflicting_shared_writers_do_not_fall_through_to_last_write_wins_truth(self):
        checks = self.by_id["LSA-05"]["checks"]
        self.assertTrue(checks["conflicting_writer_detected"])
        self.assertTrue(checks["shared_membership_not_mutation_authority"])
        self.assertTrue(checks["stale_conflicting_write_not_committed"])

    def test_partial_maintenance_uses_existing_transaction_evidence(self):
        checks = self.by_id["LSA-06"]["checks"]
        self.assertTrue(checks["maintenance_harness_passed"])
        self.assertTrue(checks["cursor_requires_commit_and_validation"])
        self.assertTrue(checks["constituent_pama_remains_authoritative"])

    def test_predictive_usefulness_cannot_restore_revoked_source_authority(self):
        checks = self.by_id["LSA-07"]["checks"]
        self.assertTrue(checks["conditional_memory_harness_passed"])
        self.assertTrue(checks["deterministic_address_not_admission"])
        self.assertTrue(checks["source_deletion_not_internal_forgetting"])
        self.assertTrue(checks["new_canonical_primitive_not_required"])

    def test_backend_replacement_keeps_logical_identity_separate_from_physical_ids(self):
        checks = self.by_id["LSA-08"]["checks"]
        self.assertTrue(checks["logical_identity_preserved"])
        self.assertTrue(checks["physical_identity_changed"])
        self.assertTrue(checks["content_identity_separate_from_physical_identity"])
        self.assertTrue(checks["migration_binds_logical_identity"])

    def test_exact_commit_binding_is_required(self):
        with self.assertRaises(ValueError):
            run_logical_state_algebra_pressure("not-a-commit")


if __name__ == "__main__":
    unittest.main()
