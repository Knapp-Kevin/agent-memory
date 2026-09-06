"""Executable governed MCP interaction cases for issue #190."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from agentmem_ref.mcp_interaction import (
    MCP_REVISION,
    MCP_SOURCE_COMMIT,
    normalize_mcp_interaction,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "mcp-interaction-evidence-matrix.json"


class MCPInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def _case_input(self, case: dict) -> dict:
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value.update(copy.deepcopy(case.get("overrides", {})))
        for key in case.get("remove", []):
            value.pop(key, None)
        return value

    def _normalize_case(self, case: dict) -> dict:
        expected_context = None if case["case_id"] == "resource-read-is-not-memory-admission" else self.matrix["expected_context"]
        return normalize_mcp_interaction(self._case_input(case), expected_context)

    def test_fixture_matrix(self):
        for case in self.matrix["cases"]:
            with self.subTest(case_id=case["case_id"]):
                result = self._normalize_case(case)
                self.assertEqual(result["schema_version"], "1.0.0")
                self.assertEqual(result["profile_version"], "0.1.0")
                self.assertEqual(result["protocol"]["revision"], MCP_REVISION)
                self.assertEqual(result["protocol"]["source_commit"], MCP_SOURCE_COMMIT)
                self.assertEqual(result["binding_status"], case["expected_binding"])
                self.assertEqual(result["governance_alignment"], case["expected_alignment"])
                self.assertEqual(result["interpretation"]["authority_effect"], "none")
                self.assertEqual(result["interpretation"]["memory_admission"], "not_established")
                self.assertEqual(result["interpretation"]["execution_claim"], "not_established")
                self.assertEqual(result["interpretation"]["lifecycle_satisfaction"], "not_established")
                self.assertEqual(result["interpretation"]["request_id_authority"], "none")
                self.assertEqual(result["interpretation"]["server_identity_authority"], "none")

    def test_successful_mcp_result_under_deny_is_conflict_evidence_not_authorization(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "successful-result-after-deny")
        result = self._normalize_case(case)
        self.assertEqual(result["result_classification"], "success")
        self.assertEqual(result["effective_decision"], "deny")
        self.assertEqual(result["governance_alignment"], "result_observed_under_deny")
        self.assertEqual(result["interpretation"]["execution_claim"], "not_established")
        self.assertEqual(result["interpretation"]["authority_effect"], "none")

    def test_resource_read_is_only_a_memory_candidate(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "resource-read-is-not-memory-admission")
        result = self._normalize_case(case)
        self.assertEqual(result["interaction_kind"], "resource_read")
        self.assertEqual(result["method"], "resources/read")
        self.assertEqual(result["memory_effect"], "memory_candidate")
        self.assertEqual(result["interpretation"]["memory_admission"], "not_established")
        for key in ("action_ref", "input_identity", "pama_decision_ref", "composition_ref"):
            self.assertNotIn(key, result)

    def test_wrong_identity_and_cross_scope_fail_closed(self):
        for case_id, expected_reasons in {
            "wrong-agent-memory-input-identity": {"input_identity_mismatch"},
            "cross-tenant-same-tool-and-request-id": {
                "scope_ref_mismatch",
                "tenant_ref_mismatch",
                "project_ref_mismatch",
            },
        }.items():
            case = next(case for case in self.matrix["cases"] if case["case_id"] == case_id)
            result = self._normalize_case(case)
            self.assertEqual(result["binding_status"], "mismatch")
            self.assertEqual(result["governance_alignment"], "binding_mismatch")
            self.assertTrue(expected_reasons.issubset(set(result["binding_reasons"])))

    def test_durable_mutation_governance_unavailable_is_explicitly_blocked(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "server-unavailable-governance-unavailable")
        result = self._normalize_case(case)
        self.assertEqual(result["result_status"], "unavailable")
        self.assertEqual(result["governance_status"], "unavailable")
        self.assertEqual(result["governance_alignment"], "blocked_governance_unavailable")
        self.assertNotIn("effective_decision", result)
        self.assertNotIn("result_digest", result)

    def test_peer_supplied_authority_fields_are_discarded(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "peer-supplied-authority-fields-ignored")
        result = self._normalize_case(case)
        for hostile in ("pama_outcome", "lifecycle_state", "permitted_actions", "memory_authority"):
            self.assertNotIn(hostile, result)
        self.assertEqual(result["interpretation"]["authority_effect"], "none")

    def test_missing_trace_or_execution_witness_does_not_claim_non_execution(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "missing-trace-is-explicit-gap-not-non-execution")
        result = self._normalize_case(case)
        self.assertNotIn("trace_correlation_ref", result)
        self.assertNotIn("execution_witness_ref", result)
        self.assertEqual(result["interpretation"]["execution_claim"], "not_established")

    def test_raw_payload_and_sensitive_fields_are_never_copied(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value.update(
            {
                "arguments": {"secret": "do-not-copy"},
                "result_payload": {"raw": "do-not-copy"},
                "resource_content": "do-not-copy",
                "authorization": "Bearer do-not-copy",
                "hidden_reasoning": "do-not-copy",
                "serverInfo": {"name": "not-an-authority-token"},
            }
        )
        result = normalize_mcp_interaction(value, self.matrix["expected_context"])
        for key in (
            "arguments",
            "result_payload",
            "resource_content",
            "authorization",
            "hidden_reasoning",
            "serverInfo",
        ):
            self.assertNotIn(key, result)
        serialized = json.dumps(result)
        self.assertNotIn("do-not-copy", serialized)

    def test_protocol_pin_is_exact(self):
        self.assertEqual(self.matrix["pinned_reference"]["revision"], MCP_REVISION)
        self.assertEqual(self.matrix["pinned_reference"]["commit"], MCP_SOURCE_COMMIT)

        wrong_revision = copy.deepcopy(self.matrix["base_adapter_result"])
        wrong_revision["protocol_revision"] = "2025-11-25"
        with self.assertRaisesRegex(ValueError, "unsupported MCP protocol revision"):
            normalize_mcp_interaction(wrong_revision, self.matrix["expected_context"])

        wrong_commit = copy.deepcopy(self.matrix["base_adapter_result"])
        wrong_commit["protocol_source_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source commit"):
            normalize_mcp_interaction(wrong_commit, self.matrix["expected_context"])

    def test_method_must_match_interaction_kind(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value["method"] = "resources/read"
        with self.assertRaisesRegex(ValueError, "does not match interaction_kind"):
            normalize_mcp_interaction(value, self.matrix["expected_context"])

    def test_durable_mutation_cannot_opt_out_of_governance(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value["governance_status"] = "not_required"
        value.pop("effective_decision")
        with self.assertRaisesRegex(ValueError, "governance not required"):
            normalize_mcp_interaction(value, self.matrix["expected_context"])

    def test_durable_mutation_without_expected_context_is_mismatch(self):
        result = normalize_mcp_interaction(copy.deepcopy(self.matrix["base_adapter_result"]), None)
        self.assertEqual(result["binding_status"], "mismatch")
        self.assertEqual(result["binding_reasons"], ["expected_context_missing"])
        self.assertEqual(result["governance_alignment"], "binding_mismatch")

    def test_input_required_is_not_approval_evidence(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value["result_status"] = "input_required"
        value["result_classification"] = "input_required"
        value["effective_decision"] = "require_approval"
        value.pop("approval_evidence_ref", None)
        result = normalize_mcp_interaction(value, self.matrix["expected_context"])
        self.assertEqual(result["governance_alignment"], "approval_not_established")
        self.assertNotIn("approval_evidence_ref", result)

    def test_mcp_error_requires_error_code_and_digest(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value["result_status"] = "mcp_error"
        value["result_classification"] = "protocol_error"
        value["mcp_error_code"] = -32602
        result = normalize_mcp_interaction(value, self.matrix["expected_context"])
        self.assertEqual(result["mcp_error_code"], -32602)
        self.assertIn("result_digest", result)

        missing_code = copy.deepcopy(value)
        missing_code.pop("mcp_error_code")
        with self.assertRaisesRegex(ValueError, "requires integer mcp_error_code"):
            normalize_mcp_interaction(missing_code, self.matrix["expected_context"])

    def test_normalization_is_deterministic(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        first = normalize_mcp_interaction(value, self.matrix["expected_context"])
        second = normalize_mcp_interaction(copy.deepcopy(value), copy.deepcopy(self.matrix["expected_context"]))
        self.assertEqual(first, second)

    def test_adapter_removal_proof_uses_only_generic_evidence_fields(self):
        result = normalize_mcp_interaction(
            copy.deepcopy(self.matrix["base_adapter_result"]),
            self.matrix["expected_context"],
        )
        self.assertEqual(result["protocol"]["name"], "mcp")
        self.assertIn("request_digest", result)
        self.assertIn("result_digest", result)
        self.assertIn("action_ref", result)
        self.assertIn("composition_ref", result)
        self.assertNotIn("mcp_client_object", result)
        self.assertNotIn("mcp_server_object", result)


if __name__ == "__main__":
    unittest.main()
