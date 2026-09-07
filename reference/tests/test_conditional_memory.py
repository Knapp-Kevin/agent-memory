"""Model-internal conditional-memory research tests for issue #228."""

from __future__ import annotations

import unittest

from agentmem_ref.conditional_memory_harness import run_conditional_memory_harness


class ConditionalMemoryTests(unittest.TestCase):
    def test_research_harness_passes(self):
        result = run_conditional_memory_harness()
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["finding"]["existing_derivation_currentness_sufficient"])
        self.assertEqual(
            result["finding"]["missing_reusable_contract"],
            "model_internal_conditional_memory_influence_profile",
        )
        self.assertFalse(result["finding"]["new_canonical_memory_primitive_required"])
        self.assertFalse(result["finding"]["engram_dependency_required"])

    def test_stale_or_deleted_source_does_not_stop_physical_lookup_but_blocks_influence(self):
        result = run_conditional_memory_harness()
        by_id = {case["id"]: case for case in result["cases"]}
        for case_id in ("revoked-source-still-addressable", "deleted-source-still-addressable"):
            case = by_id[case_id]
            self.assertTrue(case["physical_lookup_resolves"])
            self.assertEqual(case["table_currentness"]["status"], "revalidation_required")
            self.assertEqual(case["gate"], "block_stale")

    def test_scope_and_suppression_gate_before_influence(self):
        result = run_conditional_memory_harness()
        by_id = {case["id"]: case for case in result["cases"]}
        self.assertEqual(by_id["cross-partition-address"]["gate"], "block_scope")
        self.assertEqual(by_id["overlay-suppresses-current-address"]["gate"], "block_suppressed")
        self.assertEqual(by_id["deterministic-address"]["gate"], "allow")

    def test_rebuild_creates_new_current_artifact_without_rewriting_history(self):
        result = run_conditional_memory_harness()
        replacement = result["replacement_table"]
        self.assertNotEqual(replacement["old_derivation_id"], replacement["new_derivation_id"])
        self.assertEqual(replacement["new_currentness"]["status"], "current")
        self.assertTrue(result["checks"]["historical_table_derivation_unchanged"])

    def test_collision_does_not_create_identity_scope_or_authority(self):
        result = run_conditional_memory_harness()
        collision = result["collision"]
        self.assertNotEqual(collision["first_tokens"], collision["second_tokens"])
        self.assertFalse(collision["source_identity_equal"])
        self.assertFalse(collision["authority_equivalent"])

    def test_table_deployment_and_partition_widening_remain_governed(self):
        result = run_conditional_memory_harness()
        deployment = result["deployment_decisions"]
        self.assertNotEqual(deployment["table_deployment"]["outcome"], "allow")
        self.assertEqual(deployment["partition_widening"]["outcome"], "block")


if __name__ == "__main__":
    unittest.main()
