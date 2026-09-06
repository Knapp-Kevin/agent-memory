"""Runtime evidence for concurrent conflicting mutations."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.concurrency_evidence import run_concurrency_evidence  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas" / "concurrency-evidence.schema.json"


class ConcurrencyEvidenceTests(unittest.TestCase):
    def test_same_snapshot_conflict_fails_closed(self):
        report = run_concurrency_evidence("0" * 40)

        self.assertTrue(report["passed"])
        self.assertEqual(
            report["observed_behavior"],
            {
                "silent_last_writer_wins": False,
                "conflict_recorded": True,
                "state_version_revalidated": True,
            },
        )
        self.assertTrue(report["outcomes"]["proposal_a"]["committed"])
        self.assertFalse(report["outcomes"]["proposal_b"]["committed"])
        self.assertEqual(report["outcomes"]["proposal_b"]["refusal"], "stale_authorization")
        self.assertEqual(report["outcomes"]["proposal_b"]["selected_action"], "defer")
        self.assertEqual(report["outcomes"]["substrate_write_count"], 1)
        self.assertEqual(report["outcomes"]["surviving_fact_count"], 1)
        self.assertEqual(report["outcomes"]["final_state"], "v1")

    def test_conflict_is_reconstructable_from_state_refs_and_receipt(self):
        report = run_concurrency_evidence("1" * 40)
        conflict = report["conflict_record"]
        rejected = report["outcomes"]["proposal_b"]

        self.assertEqual(conflict["rejected_receipt_ref"], rejected["receipt_ref"])
        self.assertEqual(conflict["expected_state"], "v0")
        self.assertEqual(conflict["observed_state"], "v1")
        self.assertEqual(conflict["resolution"], "defer")
        self.assertEqual(conflict["reason"], "stale_authorization")

    def test_report_is_deterministic(self):
        first = run_concurrency_evidence("2" * 40)
        second = run_concurrency_evidence("2" * 40)
        self.assertEqual(first, second)

    def test_report_conforms_to_schema(self):
        report = run_concurrency_evidence("3" * 40)
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(report)

    def test_exact_commit_is_required(self):
        with self.assertRaises(ValueError):
            run_concurrency_evidence("main")


if __name__ == "__main__":
    unittest.main()
