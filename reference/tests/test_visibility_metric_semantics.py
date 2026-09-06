"""Focused truthfulness tests for #308 visibility metrics."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.visibility import VisibilityOperation, VisibilityTracker  # noqa: E402


COMMIT = "a" * 40


def operation() -> VisibilityOperation:
    return VisibilityOperation(
        operation_id="op:metric",
        memory_id="memory:metric",
        memory_version=1,
        operation_type="promotion",
        runtime_version="reference:1",
        profile_version="profile:1",
        agent_memory_commit=COMMIT,
        required_projection_ids=("idx:required",),
    )


class VisibilityMetricSemanticsTests(unittest.TestCase):
    def test_failed_projection_never_reports_currentness_latency(self):
        tracker = VisibilityTracker(operation())
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("idx:required")
        tracker.projection_refresh_failed("idx:required", detail="controlled failure")

        metric = tracker.evidence()["metrics"]["canonical_to_required_projections_current"]
        self.assertIsNone(metric["value_ns"])
        self.assertEqual(metric["reason"], "required_obligation_failed")

    def test_commit_identity_rejects_non_hex_lookalike(self):
        with self.assertRaises(ValueError):
            VisibilityOperation(
                operation_id="op:bad-sha",
                memory_id="memory:metric",
                memory_version=1,
                operation_type="promotion",
                runtime_version="reference:1",
                profile_version="profile:1",
                agent_memory_commit="z" * 40,
            )


if __name__ == "__main__":
    unittest.main()
