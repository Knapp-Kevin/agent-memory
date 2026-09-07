"""Privacy-safe runtime trace correlation tests for issue #185."""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from agentmem_ref.runtime_trace_correlation import normalize_trace_correlation

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "runtime-trace-correlation-matrix.json"


class RuntimeTraceCorrelationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def _adapter_for(self, case: dict) -> dict:
        adapter = copy.deepcopy(self.matrix["base_adapter_result"])
        adapter.update(copy.deepcopy(case.get("overrides", {})))
        for name in case.get("remove_fields", []):
            adapter.pop(name, None)
        return adapter

    def test_normalized_matrix(self):
        counts = {"exact": 0, "mismatch": 0, "not_evaluated": 0}
        for case in self.matrix["cases"]:
            with self.subTest(case_id=case["case_id"]):
                result = normalize_trace_correlation(
                    self._adapter_for(case),
                    self.matrix["expected_context"],
                )
                self.assertEqual(result["binding_status"], case["expected_binding_status"])
                self.assertEqual(result["binding_reasons"], case["expected_binding_reasons"])
                self.assertEqual(result["authority_effect"], "none")
                self.assertEqual(result["execution_claim"], "not_established")
                self.assertEqual(result["lifecycle_satisfaction"], "not_established")
                counts[result["binding_status"]] += 1

                if result["telemetry_status"] == "observed":
                    self.assertIn("trace_id", result)
                    self.assertIn("span_id", result)
                else:
                    self.assertNotIn("trace_id", result)
                    self.assertNotIn("span_id", result)
                    self.assertNotIn("parent_span_id", result)

        expected = self.matrix["expected_behavior"]
        self.assertEqual(len(self.matrix["cases"]), expected["normalized_cases"])
        self.assertEqual(counts["exact"], expected["exact_bindings"])
        self.assertEqual(counts["mismatch"], expected["mismatched_bindings"])
        self.assertEqual(counts["not_evaluated"], expected["not_evaluated_bindings"])

    def test_invalid_trace_and_span_ids_fail_closed(self):
        failures = 0
        for case in self.matrix["invalid_cases"]:
            with self.subTest(case_id=case["case_id"]):
                adapter = self._adapter_for(case)
                with self.assertRaisesRegex(ValueError, case["expected_error"]):
                    normalize_trace_correlation(adapter, self.matrix["expected_context"])
                failures += 1
        self.assertEqual(failures, self.matrix["expected_behavior"]["invalid_id_cases"])

    def test_raw_sensitive_adapter_fields_are_discarded(self):
        adapter = copy.deepcopy(self.matrix["base_adapter_result"])
        adapter.update(copy.deepcopy(self.matrix["raw_sensitive_field_probe"]))
        result = normalize_trace_correlation(adapter, self.matrix["expected_context"])

        forbidden = {
            "memory_content",
            "prompt",
            "system_instructions",
            "tool_request_payload",
            "hidden_reasoning",
            "rationale",
            "full_receipt",
        }
        self.assertFalse(forbidden & result.keys())
        preserved = sum(1 for key in self.matrix["raw_sensitive_field_probe"] if key in result)
        self.assertEqual(preserved, self.matrix["expected_behavior"]["raw_sensitive_fields_preserved"])

    def test_sampling_unknown_does_not_upgrade_evidence(self):
        case = next(item for item in self.matrix["cases"] if item["case_id"] == "observed-sampling-unknown-exact")
        result = normalize_trace_correlation(self._adapter_for(case), self.matrix["expected_context"])
        self.assertEqual(result["sampling_state"], "unknown")
        self.assertEqual(result["binding_status"], "exact")
        self.assertEqual(result["execution_claim"], "not_established")

    def test_missing_telemetry_is_not_non_execution_evidence(self):
        case = next(item for item in self.matrix["cases"] if item["case_id"] == "telemetry-not-observed")
        result = normalize_trace_correlation(self._adapter_for(case), self.matrix["expected_context"])
        self.assertEqual(result["telemetry_status"], "not_observed")
        self.assertEqual(result["binding_status"], "not_evaluated")
        self.assertEqual(result["execution_claim"], "not_established")
        self.assertNotIn("action_not_executed", result.values())

    def test_execution_witness_remains_a_reference_not_a_trace_claim(self):
        result = normalize_trace_correlation(
            self.matrix["base_adapter_result"],
            self.matrix["expected_context"],
        )
        self.assertEqual(result["execution_witness_ref"], "execution-witness:456")
        self.assertEqual(result["execution_claim"], "not_established")

    def test_unobserved_telemetry_cannot_carry_trace_ids(self):
        adapter = copy.deepcopy(self.matrix["base_adapter_result"])
        adapter["telemetry_status"] = "not_observed"
        with self.assertRaisesRegex(ValueError, "must not claim trace or span identifiers"):
            normalize_trace_correlation(adapter, self.matrix["expected_context"])


if __name__ == "__main__":
    unittest.main()
