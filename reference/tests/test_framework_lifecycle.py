"""Executable generic framework lifecycle cases for issue #189."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agentmem_ref.framework_lifecycle import (
    MutationReplayGuard,
    build_framework_lifecycle_event,
    classify_checkpoint_relation,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "framework-lifecycle-maf-matrix.json"


class FrameworkLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_checkpoint_relation_uses_lineage_not_iteration_count(self):
        lineage = self.matrix["checkpoint_lineage"]
        for case in self.matrix["cases"]:
            with self.subTest(case_id=case["case_id"]):
                relation = classify_checkpoint_relation(
                    case["resume_checkpoint"],
                    case["latest_checkpoint"],
                    lineage,
                )
                self.assertEqual(relation, case["expected_relation"])
        self.assertEqual(self.matrix["cases"][0]["iteration_count"], self.matrix["cases"][1]["iteration_count"])

    def test_framework_persistence_classification_never_establishes_admission(self):
        expected = self.matrix["expected_context"]
        for classification in self.matrix["persistence_classifications"]:
            with self.subTest(classification=classification):
                event = build_framework_lifecycle_event(
                    framework_id="microsoft-agent-framework",
                    framework_version="python-1.13.0",
                    framework_source_ref="github://microsoft/agent-framework/python-1.13.0",
                    framework_source_commit=self.matrix["pinned_reference"]["commit"],
                    event_type="checkpoint_saved",
                    run_ref="run:1",
                    workflow_ref="workflow:1",
                    persistence_classification=classification,
                    checkpoint_ref="checkpoint-2",
                    previous_checkpoint_ref="checkpoint-1",
                    checkpoint_relation="current",
                    checkpoint_format_version="1.0",
                    iteration_count=1,
                    action_ref=expected["action_ref"],
                    input_identity=expected["input_identity"],
                    scope_ref=expected["scope_ref"],
                    tenant_ref=expected["tenant_ref"],
                    project_ref=expected["project_ref"],
                    expected_context=expected,
                    occurred_at="2026-08-12T21:40:00Z",
                    evidence_refs=("evidence:checkpoint-2",),
                )
                self.assertEqual(event["binding_status"], "exact")
                self.assertEqual(event["interpretation"]["authority_effect"], "none")
                self.assertEqual(event["interpretation"]["memory_admission"], "not_established")
                self.assertEqual(event["interpretation"]["lifecycle_satisfaction"], "not_established")
                self.assertEqual(event["interpretation"]["checkpoint_rollback_authority"], "not_established")

    def test_retry_reuses_committed_receipt(self):
        guard = MutationReplayGuard()
        key = "maf:run-1:mutation-1"
        self.assertIsNone(guard.prior_receipt(key))
        self.assertEqual(guard.record(key, "receipt:1"), "recorded")
        self.assertEqual(guard.prior_receipt(key), "receipt:1")
        self.assertEqual(guard.record(key, "receipt:1"), "replay")
        with self.assertRaisesRegex(ValueError, "different receipt"):
            guard.record(key, "receipt:other")

    def test_cross_scope_framework_event_is_mismatch(self):
        expected = self.matrix["expected_context"]
        event = build_framework_lifecycle_event(
            framework_id="microsoft-agent-framework",
            framework_version="python-1.13.0",
            framework_source_ref="github://microsoft/agent-framework/python-1.13.0",
            framework_source_commit=self.matrix["pinned_reference"]["commit"],
            event_type="resume",
            run_ref="run:cross-scope",
            workflow_ref="workflow:1",
            persistence_classification="execution_state",
            checkpoint_ref="checkpoint-2",
            checkpoint_relation="current",
            action_ref=expected["action_ref"],
            input_identity=expected["input_identity"],
            scope_ref="scope:tenant-b/project-b",
            tenant_ref="tenant-b",
            project_ref="project-b",
            expected_context=expected,
            occurred_at="2026-08-12T21:41:00Z",
        )
        self.assertEqual(event["binding_status"], "mismatch")
        self.assertEqual(
            event["binding_reasons"],
            ["scope_ref_mismatch", "tenant_ref_mismatch", "project_ref_mismatch"],
        )

    def test_trace_correlation_is_optional(self):
        event = build_framework_lifecycle_event(
            framework_id="microsoft-agent-framework",
            framework_version="python-1.13.0",
            framework_source_ref="github://microsoft/agent-framework/python-1.13.0",
            framework_source_commit=self.matrix["pinned_reference"]["commit"],
            event_type="mutation_committed",
            run_ref="run:no-trace",
            workflow_ref="workflow:1",
            persistence_classification="evidence",
            action_ref="action:no-trace",
            decision_receipt_ref="receipt:no-trace",
            occurred_at="2026-08-12T21:42:00Z",
            evidence_refs=("evidence:governance-preserved",),
        )
        self.assertNotIn("trace_correlation_ref", event)
        self.assertIn("decision_receipt_ref", event)
        self.assertEqual(event["interpretation"]["authority_effect"], "none")

    def test_checkpoint_write_failure_does_not_erase_committed_receipt(self):
        event = build_framework_lifecycle_event(
            framework_id="microsoft-agent-framework",
            framework_version="python-1.13.0",
            framework_source_ref="github://microsoft/agent-framework/python-1.13.0",
            framework_source_commit=self.matrix["pinned_reference"]["commit"],
            event_type="checkpoint_write_failed",
            run_ref="run:checkpoint-failed",
            workflow_ref="workflow:1",
            persistence_classification="evidence",
            action_ref="action:committed-before-checkpoint-failure",
            decision_receipt_ref="receipt:already-committed",
            idempotency_key="maf:run:committed-before-checkpoint-failure",
            occurred_at="2026-08-12T21:42:30Z",
            evidence_refs=("evidence:checkpoint-write-failure",),
        )
        self.assertEqual(event["event_type"], "checkpoint_write_failed")
        self.assertEqual(event["decision_receipt_ref"], "receipt:already-committed")
        self.assertEqual(event["interpretation"]["checkpoint_rollback_authority"], "not_established")
        self.assertEqual(event["interpretation"]["memory_admission"], "not_established")

    def test_checkpoint_metadata_requires_checkpoint_identity(self):
        with self.assertRaisesRegex(ValueError, "requires checkpoint_ref"):
            build_framework_lifecycle_event(
                framework_id="microsoft-agent-framework",
                framework_version="python-1.13.0",
                framework_source_ref="github://microsoft/agent-framework/python-1.13.0",
                framework_source_commit=self.matrix["pinned_reference"]["commit"],
                event_type="resume",
                run_ref="run:bad",
                workflow_ref="workflow:1",
                persistence_classification="execution_state",
                checkpoint_relation="stale",
                occurred_at="2026-08-12T21:43:00Z",
            )


if __name__ == "__main__":
    unittest.main()
