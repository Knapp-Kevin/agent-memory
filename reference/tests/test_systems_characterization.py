"""P9 systems/economic characterization tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.systems_characterization import build_report  # noqa: E402


class SystemsCharacterizationTests(unittest.TestCase):
    def test_report_preserves_structural_and_timing_boundaries(self):
        report = build_report("a" * 40, sizes=(5, 20), repeats=2)

        self.assertEqual(report["profile"], "agent-memory-p9-systems-characterization")
        self.assertTrue(report["structural_invariants_passed"])
        self.assertTrue(report["method"]["latency_is_observational_only"])
        self.assertTrue(report["method"]["latency_is_not_a_conformance_gate"])
        self.assertTrue(report["method"]["cost_units_are_provider_neutral"])

        write = report["write_amplification"]
        self.assertEqual(write["canonical_mutations"], 1)
        self.assertEqual(write["audit_events"], 4)
        self.assertEqual(write["decision_receipts"], 1)
        self.assertEqual(write["evidence_records_per_canonical_mutation"], 5)
        self.assertGreater(write["serialized_evidence_bytes"], 0)

        self.assertEqual(
            [row["candidate_count"] for row in report["recall_scaling"]],
            [5, 20],
        )
        self.assertEqual(
            [row["closure_nodes"] for row in report["deletion_propagation_scaling"]],
            [5, 20],
        )
        for family in ("recall_scaling", "deletion_propagation_scaling"):
            for row in report[family]:
                self.assertEqual(row["timing"]["samples"], 2)
                self.assertGreaterEqual(row["timing"]["minimum_ns"], 0)
                self.assertGreaterEqual(row["timing"]["maximum_ns"], row["timing"]["minimum_ns"])

    def test_exact_commit_and_workload_shape_fail_closed(self):
        with self.assertRaises(ValueError):
            build_report("short")
        with self.assertRaises(ValueError):
            build_report("a" * 40, sizes=(10, 10))
        with self.assertRaises(ValueError):
            build_report("a" * 40, sizes=(20, 10))
        with self.assertRaises(ValueError):
            build_report("a" * 40, repeats=0)


if __name__ == "__main__":
    unittest.main()
