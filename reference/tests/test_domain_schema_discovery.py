"""Progressive domain-schema research harness tests for issue #226."""

from __future__ import annotations

import unittest

from agentmem_ref.domain_schema_discovery_harness import run_domain_schema_discovery_harness


class DomainSchemaDiscoveryTests(unittest.TestCase):
    def test_progressive_domain_schema_pressure_test_passes(self):
        result = run_domain_schema_discovery_harness()
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["finding"]["existing_pama_dimensions_sufficient_for_authority_bounding"])
        self.assertEqual(result["finding"]["canonical_operation_gap"], "domain_schema_mutation")
        self.assertTrue(result["finding"]["generic_other_is_not_recommended_as_final_contract"])
        self.assertFalse(result["finding"]["new_domain_ontology_core_schema_required"])
        self.assertFalse(result["finding"]["cognee_dependency_required"])

    def test_high_consequence_cases_use_existing_stricter_operations(self):
        result = run_domain_schema_discovery_harness()
        observed = {case["id"]: case for case in result["observed"]}
        self.assertEqual(observed["cross-tenant-relation-widening"]["pama_operation"], "scope_expansion")
        self.assertEqual(observed["cross-tenant-relation-widening"]["pama_outcome"], "block")
        self.assertEqual(observed["privileged-entity-from-untrusted-input"]["pama_operation"], "policy_mutation")
        self.assertEqual(
            observed["privileged-entity-from-untrusted-input"]["pama_outcome"],
            "require_external_verification",
        )

    def test_domain_discovery_never_self_commits(self):
        result = run_domain_schema_discovery_harness()
        for case in result["observed"]:
            if case["classification"] != "derived_projection_maintenance":
                self.assertFalse(case["self_commit_allowed"], case)
                self.assertEqual(case["interpretation"]["estimator_authority"], "none")
                self.assertFalse(case["interpretation"]["historical_objects_rewritten"])

    def test_replay_revocation_residue_and_conflict_boundaries(self):
        result = run_domain_schema_discovery_harness()
        observed = {case["id"]: case for case in result["observed"]}
        self.assertEqual(observed["replayed-proposal-not-corroboration"]["independent_root_count"], 1)
        self.assertEqual(observed["revoked-source-basis"]["currentness"], "revalidation_required")
        self.assertFalse(observed["migration-with-stale-projection-residue"]["commit_complete"])
        self.assertFalse(observed["concurrent-incompatible-proposals"]["last_writer_wins_allowed"])

    def test_index_only_rebuild_is_not_domain_schema_mutation(self):
        result = run_domain_schema_discovery_harness()
        observed = {case["id"]: case for case in result["observed"]}
        index_case = observed["index-only-rebuild"]
        self.assertEqual(index_case["classification"], "derived_projection_maintenance")
        self.assertFalse(index_case["operation_gap"])
        self.assertEqual(index_case["minimum_posture"], "separate_maintenance_governance")


if __name__ == "__main__":
    unittest.main()
