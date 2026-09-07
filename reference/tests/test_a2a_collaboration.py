"""Executable non-authority-bearing A2A collaboration cases for issue #194."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from agentmem_ref.a2a_collaboration import (
    A2A_RELEASE,
    A2A_SOURCE_COMMIT,
    normalize_a2a_collaboration,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "a2a-collaboration-evidence-matrix.json"


class A2ACollaborationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def _input_for(self, case: dict) -> dict:
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value.update(copy.deepcopy(case.get("overrides", {})))
        for key in case.get("remove", []):
            value.pop(key, None)
        return value

    def _normalize_case(self, case: dict) -> dict:
        expected = self.matrix["expected_context"] if case.get("use_expected_context") else None
        return normalize_a2a_collaboration(self._input_for(case), expected)

    def test_fixture_matrix(self):
        for case in self.matrix["cases"]:
            with self.subTest(case_id=case["case_id"]):
                result = self._normalize_case(case)
                self.assertEqual(result["schema_version"], "1.0.0")
                self.assertEqual(result["profile_version"], "0.1.0")
                self.assertEqual(result["protocol"]["release"], A2A_RELEASE)
                self.assertEqual(result["protocol"]["source_commit"], A2A_SOURCE_COMMIT)
                self.assertEqual(result["binding_status"], case["expected_binding"])
                self.assertEqual(result["governance_alignment"], case["expected_alignment"])
                self.assertEqual(result["interpretation"]["authority_effect"], "none")
                self.assertEqual(result["interpretation"]["delegated_memory_authority"], "not_established")
                self.assertEqual(result["interpretation"]["memory_admission"], "not_established")
                self.assertEqual(result["interpretation"]["semantic_correctness"], "not_established")
                self.assertEqual(result["interpretation"]["execution_claim"], "not_established")
                self.assertEqual(result["interpretation"]["lifecycle_satisfaction"], "not_established")
                self.assertEqual(result["interpretation"]["agent_card_authority"], "none")
                self.assertEqual(result["interpretation"]["task_completion_authority"], "none")

    def test_agent_card_capabilities_cannot_create_authority(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "agent-card-capabilities-are-not-authority")
        result = self._normalize_case(case)
        for hostile in ("agent_card_capabilities", "agent_card_skills", "delegated_memory_authority"):
            self.assertNotIn(hostile, result)
        self.assertEqual(result["interpretation"]["agent_card_authority"], "none")
        self.assertEqual(result["interpretation"]["delegated_memory_authority"], "not_established")

    def test_completed_remote_task_under_deny_is_conflict_not_authorization(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "completed-remote-task-under-local-deny")
        result = self._normalize_case(case)
        self.assertEqual(result["task_state"], "completed")
        self.assertEqual(result["effective_decision"], "deny")
        self.assertEqual(result["governance_alignment"], "remote_result_under_deny")
        self.assertEqual(result["interpretation"]["execution_claim"], "not_established")
        self.assertEqual(result["interpretation"]["task_completion_authority"], "none")

    def test_peer_authority_fields_are_discarded(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "inbound-artifact-hostile-authority-fields-ignored")
        result = self._normalize_case(case)
        for hostile in ("pama_outcome", "lifecycle_state", "permitted_actions", "authority_transition"):
            self.assertNotIn(hostile, result)
        self.assertEqual(result["export_classification"], "memory_candidate")
        self.assertEqual(result["interpretation"]["memory_admission"], "not_established")

    def test_inbound_artifact_is_candidate_not_admission(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "inbound-artifact-is-not-memory-admission")
        result = self._normalize_case(case)
        self.assertEqual(result["direction"], "inbound")
        self.assertEqual(result["interaction_kind"], "artifact")
        self.assertEqual(result["export_classification"], "memory_candidate")
        self.assertEqual(result["interpretation"]["memory_admission"], "not_established")
        self.assertIn("artifact_ref", result)
        self.assertNotIn("pama_decision_ref", result)

    def test_cross_tenant_task_correlation_fails_closed(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "cross-tenant-task-correlation-mismatch")
        result = self._normalize_case(case)
        self.assertEqual(result["binding_status"], "mismatch")
        self.assertEqual(result["governance_alignment"], "binding_mismatch")
        self.assertTrue(
            {"scope_ref_mismatch", "tenant_ref_mismatch", "project_ref_mismatch"}.issubset(
                set(result["binding_reasons"])
            )
        )

    def test_verified_remote_identity_is_not_semantic_correctness(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "verified-remote-identity-does-not-prove-correctness")
        result = self._normalize_case(case)
        self.assertEqual(result["external_evidence_refs"], ["external-evidence:verified-remote-agent"])
        self.assertEqual(result["interpretation"]["semantic_correctness"], "not_established")
        self.assertEqual(result["interpretation"]["delegated_memory_authority"], "not_established")

    def test_stale_or_revoked_outbound_memory_evidence_is_historical_only(self):
        base = copy.deepcopy(self.matrix["base_adapter_result"])
        for status in ("historical", "stale", "revoked"):
            with self.subTest(status=status):
                value = copy.deepcopy(base)
                value["memory_evidence_status"] = status
                result = normalize_a2a_collaboration(value, self.matrix["expected_context"])
                self.assertEqual(result["governance_alignment"], "historical_only")
                self.assertEqual(result["interpretation"]["delegated_memory_authority"], "not_established")

    def test_missing_trace_and_execution_witness_remain_unknown_not_negative_proof(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "missing-trace-and-execution-remain-evidence-gaps")
        result = self._normalize_case(case)
        self.assertNotIn("trace_correlation_ref", result)
        self.assertNotIn("execution_witness_ref", result)
        self.assertEqual(result["interpretation"]["execution_claim"], "not_established")
        self.assertEqual(result["interpretation"]["lifecycle_satisfaction"], "not_established")

    def test_peer_unavailability_does_not_widen_authority(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "remote-unavailable-governance-unavailable")
        result = self._normalize_case(case)
        self.assertEqual(result["task_state"], "unavailable")
        self.assertEqual(result["governance_status"], "unavailable")
        self.assertEqual(result["governance_alignment"], "blocked_governance_unavailable")
        self.assertNotIn("effective_decision", result)

    def test_raw_peer_content_and_memory_graph_are_never_copied(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value.update(
            {
                "full_memory_graph": {"secret": "do-not-copy"},
                "message_parts": [{"text": "do-not-copy"}],
                "artifact_body": {"raw": "do-not-copy"},
                "system_prompt": "do-not-copy",
                "hidden_reasoning": "do-not-copy",
                "authorization": "Bearer do-not-copy",
                "agent_card": {"skills": ["do-not-copy"]},
            }
        )
        result = normalize_a2a_collaboration(value, self.matrix["expected_context"])
        serialized = json.dumps(result)
        self.assertNotIn("do-not-copy", serialized)
        for key in (
            "full_memory_graph",
            "message_parts",
            "artifact_body",
            "system_prompt",
            "hidden_reasoning",
            "authorization",
            "agent_card",
        ):
            self.assertNotIn(key, result)

    def test_release_pin_is_exact(self):
        self.assertEqual(self.matrix["pinned_reference"]["release"], A2A_RELEASE)
        self.assertEqual(self.matrix["pinned_reference"]["commit"], A2A_SOURCE_COMMIT)

        wrong_release = copy.deepcopy(self.matrix["base_adapter_result"])
        wrong_release["protocol_release"] = "v0.3.0"
        with self.assertRaisesRegex(ValueError, "unsupported A2A release"):
            normalize_a2a_collaboration(wrong_release, self.matrix["expected_context"])

        wrong_commit = copy.deepcopy(self.matrix["base_adapter_result"])
        wrong_commit["protocol_source_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "source commit"):
            normalize_a2a_collaboration(wrong_commit, self.matrix["expected_context"])

    def test_context_projection_requires_governance_and_exact_context(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value["governance_status"] = "not_required"
        value.pop("effective_decision")
        with self.assertRaisesRegex(ValueError, "cannot declare governance not required"):
            normalize_a2a_collaboration(value, self.matrix["expected_context"])

        result = normalize_a2a_collaboration(copy.deepcopy(self.matrix["base_adapter_result"]), None)
        self.assertEqual(result["binding_status"], "mismatch")
        self.assertEqual(result["binding_reasons"], ["expected_context_missing"])
        self.assertEqual(result["governance_alignment"], "binding_mismatch")

    def test_require_approval_is_not_satisfied_by_task_or_peer_interaction(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        value["effective_decision"] = "require_approval"
        value.pop("approval_evidence_ref", None)
        result = normalize_a2a_collaboration(value, self.matrix["expected_context"])
        self.assertEqual(result["governance_alignment"], "approval_not_established")
        self.assertNotIn("approval_evidence_ref", result)

    def test_direction_and_kind_constraints(self):
        invalid_request = copy.deepcopy(self.matrix["base_adapter_result"])
        invalid_request["direction"] = "inbound"
        with self.assertRaisesRegex(ValueError, "task_request must be outbound"):
            normalize_a2a_collaboration(invalid_request, self.matrix["expected_context"])

        invalid_artifact = copy.deepcopy(self.matrix["base_adapter_result"])
        invalid_artifact.update(
            {
                "interaction_kind": "artifact",
                "artifact_ref": "a2a-artifact:bad",
                "export_classification": "explicit_non_memory",
                "memory_evidence_status": "not_applicable",
            }
        )
        with self.assertRaisesRegex(ValueError, "artifact observation must be inbound"):
            normalize_a2a_collaboration(invalid_artifact, self.matrix["expected_context"])

    def test_normalization_is_deterministic(self):
        value = copy.deepcopy(self.matrix["base_adapter_result"])
        first = normalize_a2a_collaboration(value, self.matrix["expected_context"])
        second = normalize_a2a_collaboration(copy.deepcopy(value), copy.deepcopy(self.matrix["expected_context"]))
        self.assertEqual(first, second)

    def test_adapter_removal_proof_retains_generic_evidence_only(self):
        case = next(case for case in self.matrix["cases"] if case["case_id"] == "adapter-removal-preserves-generic-evidence")
        result = self._normalize_case(case)
        self.assertEqual(result["protocol"]["name"], "a2a")
        self.assertIn("action_ref", result)
        self.assertIn("input_identity", result)
        self.assertIn("payload_digest", result)
        self.assertIn("pama_decision_ref", result)
        self.assertNotIn("a2a_client_object", result)
        self.assertNotIn("a2a_server_object", result)


if __name__ == "__main__":
    unittest.main()
