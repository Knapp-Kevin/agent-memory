"""Acceptance tests for issue #67 matched architecture-family evidence."""

from __future__ import annotations

import unittest

from agentmem_ref.architecture_family_closeout import run_closeout_evidence


class ArchitectureFamilyCloseoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run_closeout_evidence()
        cls.by_family = {item["family"]: item for item in cls.report["families"]}

    def test_all_non_latent_taxonomy_surfaces_have_matched_evidence(self):
        expected = {
            "file_document",
            "linked_note_vault",
            "lexical_vector_rag",
            "knowledge_graph_graphrag",
            "temporal_graph",
            "event_log_ledger",
            "relational_document_store",
            "hierarchical_tiered",
            "shared_distributed",
            "hybrid_composition",
        }
        self.assertEqual(set(self.by_family), expected)
        self.assertEqual(self.report["family_count"], 10)

    def test_cross_family_authority_boundaries_survive(self):
        for item in self.report["families"]:
            with self.subTest(family=item["family"]):
                self.assertEqual(item["authority_effect"], "none")
                self.assertFalse(item["retrieval_or_reachability_is_permission"])
                self.assertFalse(item["probabilistic_or_derived_state_has_write_authority"])
                self.assertTrue(item["provenance_reconstructable"])

    def test_stale_or_derived_surfaces_are_not_silently_admitted(self):
        self.assertFalse(self.by_family["lexical_vector_rag"]["stale_candidate_admitted"])
        self.assertFalse(self.by_family["knowledge_graph_graphrag"]["cached_reachability_admitted"])
        self.assertFalse(self.by_family["shared_distributed"]["stale_conflicting_write_committed"])

    def test_history_and_currentness_remain_distinct(self):
        self.assertTrue(self.by_family["event_log_ledger"]["current_truth_separate_from_history"])
        self.assertTrue(self.by_family["temporal_graph"]["current_truth_separate_from_history"])
        self.assertFalse(self.by_family["temporal_graph"]["historical_validity_is_current_authority"])

    def test_storage_and_tier_movement_do_not_create_authority(self):
        tiered = self.by_family["hierarchical_tiered"]
        self.assertTrue(tiered["tier_move_preserves_authority"])
        self.assertTrue(tiered["tier_move_preserves_scope"])
        self.assertFalse(tiered["storage_promotion_is_authority_promotion"])

    def test_deletion_residue_remains_explicit(self):
        residue_families = [item["family"] for item in self.report["families"] if item["deletion_residue_detected"]]
        self.assertGreaterEqual(len(residue_families), 8)
        self.assertFalse(self.by_family["event_log_ledger"]["tombstone_is_forgetting_proof"])


if __name__ == "__main__":
    unittest.main()
