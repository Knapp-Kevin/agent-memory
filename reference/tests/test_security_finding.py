"""Executable security finding evidence tests for issue #198."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from agentmem_ref.security_finding import (
    GARAK_COMMIT,
    GARAK_TAG,
    SNYK_AGENT_SCAN_COMMIT,
    SNYK_AGENT_SCAN_TAG,
    normalize_garak_eval,
    normalize_snyk_agent_scan_projection,
)
from agentmem_ref.security_finding_harness import run_security_finding_harness

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "security-finding-evidence-matrix.json"


class SecurityFindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))
        cls.expected = cls.matrix["expected_context"]

    def test_behavioral_harness_covers_two_materially_different_families(self):
        harness = run_security_finding_harness()
        self.assertTrue(harness["passed"], harness)
        self.assertEqual(set(harness["cases"]), {"garak", "snyk_agent_scan"})
        for case in harness["cases"].values():
            self.assertTrue(case["passed"], case)

    def test_garak_pin_and_eval_counts_are_preserved(self):
        result = normalize_garak_eval(copy.deepcopy(self.matrix["garak_hit"]), self.expected)
        self.assertEqual(result["source"]["version"], GARAK_TAG)
        self.assertEqual(result["source"]["source_commit"], GARAK_COMMIT)
        self.assertEqual(result["source"]["source_contract_status"], "stable_pinned")
        self.assertEqual(result["finding_family"], "behavioral_probe")
        self.assertEqual(result["result"]["passed"], 1)
        self.assertEqual(result["result"]["fails"], 3)
        self.assertEqual(result["result"]["total_evaluated"], 4)
        self.assertEqual(result["result"]["verdict"], "mixed")
        self.assertEqual(result["result"]["source_metric"]["name"], "garak_pass_rate")
        self.assertEqual(result["result"]["source_metric"]["value"], 0.25)

    def test_garak_hit_is_evidence_not_authority_or_universal_fact(self):
        result = normalize_garak_eval(copy.deepcopy(self.matrix["garak_hit"]), self.expected)
        self.assertEqual(result["interpretation"]["authority_effect"], "none")
        self.assertEqual(result["interpretation"]["universal_vulnerability"], "not_established")
        self.assertEqual(result["interpretation"]["standing_policy"], "not_established")
        self.assertEqual(result["interpretation"]["memory_admission"], "not_established")
        self.assertEqual(result["interpretation"]["certification_claim"], "none")
        self.assertNotIn("pama_outcome", result)
        self.assertNotIn("standing_policy", result)

    def test_garak_no_hit_does_not_prove_safety(self):
        result = normalize_garak_eval(copy.deepcopy(self.matrix["garak_no_hit"]), self.expected)
        self.assertEqual(result["result"]["verdict"], "no_hit")
        self.assertEqual(result["interpretation"]["safety_claim"], "not_established")
        self.assertTrue(any("not proof of safety" in item for item in result["known_limitations"]))

    def test_garak_rejects_version_or_eval_contract_drift(self):
        wrong_version = copy.deepcopy(self.matrix["garak_hit"])
        wrong_version["garak_version"] = "0.15.1"
        with self.assertRaisesRegex(ValueError, "unsupported garak version"):
            normalize_garak_eval(wrong_version, self.expected)

        wrong_commit = copy.deepcopy(self.matrix["garak_hit"])
        wrong_commit["garak_source_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source commit"):
            normalize_garak_eval(wrong_commit, self.expected)

        bad_counts = copy.deepcopy(self.matrix["garak_hit"])
        bad_counts["eval_record"]["fails"] = 2
        with self.assertRaisesRegex(ValueError, "passed \+ fails"):
            normalize_garak_eval(bad_counts, self.expected)

    def test_snyk_projection_is_experimental_but_generic_schema_is_stable(self):
        result = normalize_snyk_agent_scan_projection(copy.deepcopy(self.matrix["snyk_active"]), self.expected)
        self.assertEqual(result["source"]["version"], SNYK_AGENT_SCAN_TAG)
        self.assertEqual(result["source"]["source_commit"], SNYK_AGENT_SCAN_COMMIT)
        self.assertEqual(result["source"]["source_contract_status"], "experimental_projection")
        self.assertEqual(result["finding_family"], "supply_chain_configuration")
        self.assertEqual(result["execution_context"]["target_execution"], "observed")
        self.assertEqual(result["execution_context"]["sandbox"], "isolated")
        self.assertEqual(result["execution_context"]["consent"], "granted")
        self.assertNotIn("experimental_issue_code", result)
        self.assertNotIn("experimental_response_blob", result)
        self.assertNotIn("pama_outcome", result)
        serialized = json.dumps(result)
        self.assertNotIn("THIS_FIELD_MAY_CHANGE", serialized)
        self.assertNotIn("must-not-copy", serialized)

    def test_snyk_declined_scan_is_not_run_not_fabricated_finding(self):
        result = normalize_snyk_agent_scan_projection(copy.deepcopy(self.matrix["snyk_declined"]), self.expected)
        self.assertEqual(result["result"]["status"], "declined")
        self.assertEqual(result["result"]["verdict"], "not_run")
        self.assertEqual(result["finding_state"], "not_run")
        self.assertEqual(result["candidate_classification"], "conformance_evidence")
        self.assertEqual(result["execution_context"]["target_execution"], "not_observed")
        self.assertEqual(result["execution_context"]["consent"], "declined")
        self.assertEqual(result["interpretation"]["safety_claim"], "not_established")

    def test_declined_snyk_scan_cannot_claim_execution(self):
        value = copy.deepcopy(self.matrix["snyk_declined"])
        value["mcp_server_execution"] = "executed"
        with self.assertRaisesRegex(ValueError, "declined Snyk MCP scan"):
            normalize_snyk_agent_scan_projection(value, self.expected)

    def test_partial_and_target_unavailable_remain_explicit(self):
        partial = copy.deepcopy(self.matrix["snyk_active"])
        partial.update({"result_status": "partial", "verdict": "unknown", "mcp_server_execution": "could_execute"})
        partial_result = normalize_snyk_agent_scan_projection(partial, self.expected)
        self.assertEqual(partial_result["result"]["status"], "partial")
        self.assertEqual(partial_result["result"]["verdict"], "unknown")
        self.assertEqual(partial_result["execution_context"]["target_execution"], "possible")

        unavailable = copy.deepcopy(self.matrix["snyk_active"])
        unavailable.update({"result_status": "target_unavailable", "verdict": "not_run", "mcp_server_execution": "not_executed"})
        unavailable_result = normalize_snyk_agent_scan_projection(unavailable, self.expected)
        self.assertEqual(unavailable_result["result"]["status"], "target_unavailable")
        self.assertEqual(unavailable_result["interpretation"]["safety_claim"], "not_established")

    def test_cross_tenant_environment_binding_fails_closed(self):
        value = copy.deepcopy(self.matrix["snyk_active"])
        value.update(
            {
                "scope_ref": "scope:tenant-b/project-b",
                "tenant_ref": "tenant-b",
                "project_ref": "project-b",
                "environment_ref": "env:prod-b",
            }
        )
        result = normalize_snyk_agent_scan_projection(value, self.expected)
        self.assertEqual(result["binding_status"], "mismatch")
        self.assertTrue(
            {
                "scope_ref_mismatch",
                "tenant_ref_mismatch",
                "project_ref_mismatch",
                "environment_ref_mismatch",
            }.issubset(set(result["binding_reasons"]))
        )

    def test_reproduction_strengthens_lineage_not_authority(self):
        original = normalize_garak_eval(copy.deepcopy(self.matrix["garak_hit"]), self.expected)
        reproduced_source = copy.deepcopy(self.matrix["garak_hit"])
        reproduced_source.update(
            {
                "reproduction_state": "reproduced",
                "finding_state": "reproduced",
                "prior_finding_refs": [original["finding_id"]],
                "raw_evidence_digest": "sha256:" + "e" * 64,
                "observed_at": "2026-08-12T22:57:00Z",
            }
        )
        reproduced = normalize_garak_eval(reproduced_source, self.expected)
        self.assertNotEqual(original["finding_id"], reproduced["finding_id"])
        self.assertEqual(reproduced["lineage"]["prior_finding_refs"], [original["finding_id"]])
        self.assertEqual(reproduced["reproduction_state"], "reproduced")
        self.assertEqual(reproduced["interpretation"]["authority_effect"], "none")
        self.assertEqual(reproduced["interpretation"]["universal_vulnerability"], "not_established")

    def test_remediation_without_rescan_does_not_become_resolved(self):
        original = normalize_garak_eval(copy.deepcopy(self.matrix["garak_hit"]), self.expected)
        remediation_source = copy.deepcopy(self.matrix["garak_hit"])
        remediation_source.update(
            {
                "finding_state": "remediation_applied",
                "prior_finding_refs": [original["finding_id"]],
                "remediation_refs": ["remediation:patch-1"],
                "raw_evidence_digest": "sha256:" + "f" * 64,
                "observed_at": "2026-08-12T22:58:00Z",
            }
        )
        remediation = normalize_garak_eval(remediation_source, self.expected)
        self.assertEqual(remediation["finding_state"], "remediation_applied")
        self.assertEqual(remediation["lineage"]["rescan_refs"], [])
        self.assertNotEqual(remediation["finding_state"], "resolved")
        self.assertEqual(remediation["interpretation"]["safety_claim"], "not_established")

    def test_rescan_and_conflicting_findings_preserve_append_only_refs(self):
        hit = normalize_garak_eval(copy.deepcopy(self.matrix["garak_hit"]), self.expected)
        no_hit_source = copy.deepcopy(self.matrix["garak_no_hit"])
        no_hit_source.update(
            {
                "finding_state": "rescanned",
                "prior_finding_refs": [hit["finding_id"]],
                "rescan_refs": ["rescan:after-remediation-1"],
                "conflict_refs": [hit["finding_id"]],
            }
        )
        no_hit = normalize_garak_eval(no_hit_source, self.expected)
        self.assertEqual(no_hit["result"]["verdict"], "no_hit")
        self.assertEqual(no_hit["lineage"]["prior_finding_refs"], [hit["finding_id"]])
        self.assertEqual(no_hit["lineage"]["conflict_refs"], [hit["finding_id"]])
        self.assertEqual(no_hit["interpretation"]["safety_claim"], "not_established")

    def test_two_families_share_same_generic_interpretation_contract(self):
        garak = normalize_garak_eval(copy.deepcopy(self.matrix["garak_hit"]), self.expected)
        snyk = normalize_snyk_agent_scan_projection(copy.deepcopy(self.matrix["snyk_active"]), self.expected)
        self.assertNotEqual(garak["finding_family"], snyk["finding_family"])
        self.assertEqual(set(garak["interpretation"]), set(snyk["interpretation"]))
        self.assertEqual(garak["interpretation"]["authority_effect"], "none")
        self.assertEqual(snyk["interpretation"]["authority_effect"], "none")
        self.assertEqual(garak["schema_version"], snyk["schema_version"])
        self.assertEqual(garak["profile_version"], snyk["profile_version"])


if __name__ == "__main__":
    unittest.main()
