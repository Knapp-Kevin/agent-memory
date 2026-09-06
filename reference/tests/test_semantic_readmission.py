"""Semantic re-admission signals are estimator evidence, never mutation authority."""

from __future__ import annotations

import unittest

from agentmem_ref.readmission import (
    NO_SEMANTIC_SIGNAL,
    READMITTED,
    REJECTED,
    REQUIRE_RECONCILIATION,
    RejectedValueRegistry,
    SemanticSimilaritySignal,
    route_semantic_similarity,
)


class SemanticReadmissionPrimitiveTests(unittest.TestCase):
    def _registry(self) -> RejectedValueRegistry:
        registry = RejectedValueRegistry()
        registry.reject(
            memory_id="mem:deploy-window",
            value="deploy window is Thursday",
            superseded_fact_uuid="fact:old",
            correction_proposal_id="proposal:correction",
            evidence_refs=("evidence:correction",),
            authority_refs=("approval:owner",),
            scope="tenant-a",
            rejected_at="2026-08-12T18:00:00Z",
        )
        return registry

    def test_rejection_metadata_preserves_authority_scope_and_lifecycle_without_raw_content(self):
        registry = self._registry()
        active = registry.active_records("mem:deploy-window")

        self.assertEqual(len(active), 1)
        record = active[0]
        self.assertEqual(record["authority_refs"], ["approval:owner"])
        self.assertEqual(record["scope"], "tenant-a")
        self.assertEqual(record["lifecycle_state"], REJECTED)
        self.assertTrue(record["active"])
        self.assertTrue(record["rejection_id"].startswith("rejection:sha256:"))
        self.assertNotIn("value", record)
        self.assertNotIn("fact_text", record)

    def test_semantic_match_routes_only_to_reconciliation(self):
        registry = self._registry()
        rejection_ref = registry.active_records("mem:deploy-window")[0]["rejection_id"]
        signal = SemanticSimilaritySignal(
            memory_id="mem:deploy-window",
            rejection_ref=rejection_ref,
            estimator_id="semantic-review-test",
            estimator_version="1.0.0",
            candidate_match=True,
            confidence=0.94,
            evidence_refs=("evidence:paraphrase",),
        )

        routing = route_semantic_similarity(signal)

        self.assertTrue(routing.review_required)
        self.assertEqual(routing.consequence, REQUIRE_RECONCILIATION)
        self.assertNotIn(routing.consequence, {"allow", "block", "readmit", "reject"})
        evidence = signal.as_evidence()
        self.assertEqual(evidence["signal_semantics"], "candidate_match_for_reconciliation_not_authority")
        self.assertEqual(evidence["estimator_id"], "semantic-review-test")
        self.assertNotIn("authority", evidence)
        self.assertNotIn("decision", evidence)

    def test_semantic_nonmatch_does_not_create_permission(self):
        registry = self._registry()
        rejection_ref = registry.active_records("mem:deploy-window")[0]["rejection_id"]
        signal = SemanticSimilaritySignal(
            memory_id="mem:deploy-window",
            rejection_ref=rejection_ref,
            estimator_id="semantic-review-test",
            estimator_version="1.0.0",
            candidate_match=False,
            confidence=0.12,
        )

        routing = route_semantic_similarity(signal)

        self.assertFalse(routing.review_required)
        self.assertEqual(routing.consequence, NO_SEMANTIC_SIGNAL)
        self.assertNotIn(routing.consequence, {"allow", "block", "readmit", "reject"})

    def test_readmission_updates_lifecycle_without_erasing_history(self):
        registry = self._registry()
        record = registry.readmit(
            memory_id="mem:deploy-window",
            value="deploy window is Thursday",
            proposal_id="proposal:approved-reversal",
            readmitted_at="2026-08-12T19:00:00Z",
        )

        self.assertIsNotNone(record)
        history = registry.history("mem:deploy-window", "deploy window is Thursday")
        self.assertEqual(len(history), 1)
        self.assertFalse(history[0]["active"])
        self.assertEqual(history[0]["lifecycle_state"], READMITTED)
        self.assertEqual(history[0]["readmission_proposal_id"], "proposal:approved-reversal")

    def test_permanent_deletion_can_purge_rejection_fingerprints(self):
        registry = self._registry()
        registry.reject(
            memory_id="mem:other",
            value="other rejected value",
            superseded_fact_uuid="fact:other",
            correction_proposal_id="proposal:other",
            evidence_refs=("evidence:other",),
            authority_refs=("approval:other",),
            scope="tenant-a",
            rejected_at="2026-08-12T18:10:00Z",
        )

        purged = registry.purge_memory("mem:deploy-window")

        self.assertEqual(purged, 1)
        self.assertEqual(registry.active_records("mem:deploy-window"), ())
        self.assertEqual(registry.history("mem:deploy-window", "deploy window is Thursday"), ())
        self.assertEqual(len(registry.active_records("mem:other")), 1)

    def test_signal_rejects_invalid_confidence(self):
        with self.assertRaises(ValueError):
            SemanticSimilaritySignal(
                memory_id="mem:deploy-window",
                rejection_ref="rejection:sha256:test",
                estimator_id="semantic-review-test",
                estimator_version="1.0.0",
                candidate_match=True,
                confidence=1.1,
            )


if __name__ == "__main__":
    unittest.main()
