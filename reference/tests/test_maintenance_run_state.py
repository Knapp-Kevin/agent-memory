"""Transaction, validation, and cursor cases for maintenance-run evidence."""

from __future__ import annotations

import unittest

from agentmem_ref.maintenance_run import next_cursor
from agentmem_ref.maintenance_run_rules import validate_rules
from agentmem_ref.maintenance_run_state import seal
from tests._maintenance_run_cases import run_record

ALLOWED = {
    "decision_ref": "pama-decision:maintenance:promotion",
    "operation": "promotion",
    "outcome": "allow_with_ledger",
}


class MaintenanceRunStateTests(unittest.TestCase):
    def test_clean_commit_advances_once_and_replay_is_rejected(self):
        record = run_record(constituent_decisions=(ALLOWED,))
        validate_rules(record)
        seen: set[str] = set()
        self.assertEqual(next_cursor(record, 10, seen), 11)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            next_cursor(record, 11, seen)

    def test_validation_failure_keeps_cursor_and_quarantines(self):
        record = run_record(
            cursor_after=10,
            constituent_decisions=(ALLOWED,),
            transaction_status="quarantined",
            commit_status="succeeded",
            validation_status="failed",
            quarantine_ref="quarantine:1",
        )
        validate_rules(record)
        self.assertEqual(next_cursor(record, 10, set()), 10)

    def test_partial_apply_with_cursor_change_is_rejected(self):
        record = run_record(
            constituent_decisions=(ALLOWED,),
            transaction_status="rolled_back",
            commit_status="partial",
            validation_status="failed",
            rollback_ref="rollback:1",
        )
        with self.assertRaisesRegex(ValueError, "cursor"):
            validate_rules(record)

    def test_partial_apply_can_roll_back_without_consuming_input(self):
        record = run_record(
            cursor_after=10,
            constituent_decisions=(ALLOWED,),
            transaction_status="rolled_back",
            commit_status="partial",
            validation_status="failed",
            rollback_ref="rollback:1",
        )
        validate_rules(record)
        self.assertEqual(next_cursor(record, 10, set()), 10)

    def test_stale_source_cannot_be_committed(self):
        record = run_record(
            constituent_decisions=(ALLOWED,),
            source_currentness="revoked",
        )
        with self.assertRaisesRegex(ValueError, "source"):
            validate_rules(record)

        blocked = run_record(
            cursor_after=10,
            constituent_decisions=(ALLOWED,),
            transaction_status="blocked_stale_source",
            commit_status="not_attempted",
            validation_status="not_run",
            source_currentness="revoked",
        )
        validate_rules(blocked)

    def test_policy_drift_requires_revalidation_evidence(self):
        stale = run_record(
            constituent_decisions=(ALLOWED,),
            policy_version="policy:1",
            commit_policy_version="policy:2",
        )
        with self.assertRaisesRegex(ValueError, "revalidation"):
            validate_rules(stale)

        refreshed = run_record(
            run_id="run:refreshed",
            constituent_decisions=(ALLOWED,),
            policy_version="policy:1",
            commit_policy_version="policy:2",
            policy_revalidation_ref="revalidation:2",
        )
        validate_rules(refreshed)

    def test_housekeeping_can_advance_without_semantic_decision(self):
        record = run_record(
            planned_operations=("index_rebuild",),
            constituent_decisions=(),
            housekeeping_only=True,
            semantic_memory_changed=False,
        )
        validate_rules(record)
        self.assertEqual(next_cursor(record, 10, set()), 11)

    def test_housekeeping_cannot_claim_semantic_change(self):
        record = run_record(
            planned_operations=("index_rebuild",),
            constituent_decisions=(),
            housekeeping_only=True,
            semantic_memory_changed=True,
        )
        with self.assertRaisesRegex(ValueError, "housekeeping"):
            validate_rules(record)

    def test_digest_tampering_is_detected(self):
        record = run_record(constituent_decisions=(ALLOWED,))
        record["output_refs"] = ["output:tampered"]
        with self.assertRaisesRegex(ValueError, "digest"):
            validate_rules(record)

    def test_cursor_continuity_is_checked(self):
        record = run_record(constituent_decisions=(ALLOWED,))
        validate_rules(record)
        with self.assertRaisesRegex(ValueError, "cursor"):
            next_cursor(record, 9, set())


if __name__ == "__main__":
    unittest.main()
