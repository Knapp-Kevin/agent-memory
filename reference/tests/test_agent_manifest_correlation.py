"""P4.5b Agent Manifest memory checkpoint correlation.

The upstream Agent Manifest implementation owns checkpoint/delta verification.
These tests import the pinned release directly, execute its RFC 9162 path, and
then prove that Agent Memory can correlate to the accepted or rejected checkpoint
without treating checkpoint integrity as memory-governance or forgetting proof.
"""

from __future__ import annotations

import importlib.metadata
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone

from tests import pin_support
from pathlib import Path

import jsonschema
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from agent_manifest._memory_delta import (  # type: ignore[import-not-found]
        MemoryCheckpoint,
        build_memory_tree,
        memory_merkletree,
        verify_delta,
    )
except ImportError:  # local low-dependency runs may omit the comparator
    MemoryCheckpoint = None  # type: ignore[assignment,misc]
    build_memory_tree = None  # type: ignore[assignment]
    memory_merkletree = None  # type: ignore[assignment]
    verify_delta = None  # type: ignore[assignment]

from agentmem_ref.agent_manifest_correlation import (  # noqa: E402
    AGENT_MANIFEST_SDK_VERSION,
    AGENT_MANIFEST_UPSTREAM_COMMIT,
    checkpoint_payload,
    checkpoint_reference,
    correlate_agent_manifest_delta,
)
from agentmem_ref.portable_evidence import IssuerKey, issue_evidence  # noqa: E402

ISSUER = "issuer:agent-memory-reference"
KEY = IssuerKey(
    issuer_id=ISSUER,
    key_id="key-2026-08",
    private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33))),
    valid_from="2026-08-01T00:00:00Z",
    valid_until="2026-08-31T23:59:59Z",
)
APPROVED_AT = datetime(2026, 8, 11, 20, 0, 0, tzinfo=timezone.utc)


@unittest.skipIf(MemoryCheckpoint is None, "agent-manifest comparator is not installed")
class AgentManifestCorrelationTests(unittest.TestCase):
    def setUp(self):
        trust = KEY.trust_key()
        self.trust = {(trust.issuer_id, trust.key_id): trust}
        self.before_ops = [
            {"op": "PUT", "key": "memory:key:alpha", "value": "secret-memory-value"},
        ]
        self.after_ops = [
            *self.before_ops,
            {"op": "DEL", "key": "memory:key:alpha"},
        ]
        self.previous = MemoryCheckpoint.from_ops(
            self.before_ops,
            "kv",
            seq=7,
            approved_at=APPROVED_AT,
            ttl_seconds=3600,
            max_delta_fraction=1.0,
        )
        self.new = MemoryCheckpoint.from_ops(
            self.after_ops,
            "kv",
            seq=8,
            approved_at=APPROVED_AT,
            ttl_seconds=3600,
            max_delta_fraction=1.0,
        )
        tree = memory_merkletree(self.after_ops, "kv")
        self.proof = tree.consistency_proof(self.previous.tree_size)
        self.verdict = verify_delta(
            self.previous,
            self.new,
            self.after_ops,
            self.proof,
            now=APPROVED_AT + timedelta(seconds=5),
        )

    def _receipt_and_evidence(
        self,
        lifecycle_result: str = "residual",
        *,
        include_checkpoint: bool = True,
        receipt_action: str = "permanent_deletion",
        portable_action: str = "permanent_deletion",
    ):
        previous_ref = checkpoint_reference(self.previous)
        new_ref = checkpoint_reference(self.new)
        receipt = {
            "schema_version": "1.0.0",
            "receipt_id": "receipt:manifest-del:8",
            "memory_id": "mem:alpha",
            "requested_action": receipt_action,
            "policy_version": "pama-2026-08",
            "permitted_actions": [receipt_action],
            "selected_action": receipt_action,
            "selection_mode": "deterministic",
            "evidence_refs": [new_ref] if include_checkpoint else [],
            "timestamp": "2026-08-11T20:00:01Z",
        }
        evidence = issue_evidence(
            receipt,
            issuer_id=ISSUER,
            key=KEY,
            issued_at="2026-08-11T20:00:02Z",
            action_ref="action:delete:manifest:8",
            memory_action=portable_action,
            governance_disposition="committed",
            policy_ref="policy:pama-2026-08",
            authority_state_ref="authority:rev-21",
            decision_time="2026-08-11T20:00:01Z",
            scope_ref="scope:opaque:manifest-test",
            before_state_ref=previous_ref,
            after_state_ref=new_ref,
            lifecycle_result=lifecycle_result,
            source_domain_ref="domain:opaque:project-a",
            destination_domain_ref="domain:opaque:deleted",
        )
        return receipt, evidence

    def _correlate(self, lifecycle_result: str = "residual", *, include_checkpoint: bool = True, verdict=None):
        receipt, evidence = self._receipt_and_evidence(lifecycle_result, include_checkpoint=include_checkpoint)
        verdict = verdict or self.verdict
        return correlate_agent_manifest_delta(
            evidence,
            receipt,
            self.trust,
            previous_checkpoint=self.previous,
            new_checkpoint=self.new,
            delta_accepted=verdict.accepted,
            delta_reason=verdict.reason,
            representation="kv",
        )

    @unittest.skipUnless(
        pin_support.pinned("agent-manifest", AGENT_MANIFEST_SDK_VERSION),
        "agent-manifest is not installed at the pinned version",
    )
    def test_pinned_release_and_repository_identity_are_explicit(self):
        self.assertEqual(importlib.metadata.version("agent-manifest"), AGENT_MANIFEST_SDK_VERSION)
        self.assertEqual(AGENT_MANIFEST_SDK_VERSION, "0.11.2")
        self.assertEqual(AGENT_MANIFEST_UPSTREAM_COMMIT, "9d26ac84461e829dba8ff97ca35748eeb874debe")

    def test_upstream_v02_normative_kv_root_vector_matches(self):
        root = build_memory_tree(
            [
                {"op": "PUT", "key": "a", "value": 1},
                {"op": "PUT", "key": "b", "value": 2},
            ],
            "kv",
        )
        self.assertEqual(
            root,
            "sha256:9a41dee8ec223727525f8b26685e413664190d2b82cd62d4f7c15180a9e1f5af",
        )

    def test_upstream_checkpoint_advance_executed_with_del_is_accepted(self):
        self.assertEqual(self.after_ops[-1]["op"], "DEL")
        self.assertTrue(self.verdict.accepted)
        self.assertEqual(self.verdict.reason, "accepted")
        self.assertEqual(self.new.tree_size, self.previous.tree_size + 1)
        self.assertGreater(self.new.seq, self.previous.seq)

    def test_valid_del_checkpoint_does_not_imply_forgetting(self):
        correlation = self._correlate("residual")
        self.assertEqual(correlation["correlation_integrity"], "valid")
        self.assertEqual(correlation["agent_manifest"]["delta_verification"], "accepted")
        self.assertEqual(correlation["agent_memory"]["memory_action"], "permanent_deletion")
        self.assertEqual(correlation["agent_memory"]["governance_disposition"], "committed")
        self.assertEqual(correlation["agent_memory"]["lifecycle_satisfaction"], "residual")
        self.assertNotIn("operation_kind", correlation["agent_manifest"])

    def test_same_valid_del_checkpoint_can_accompany_satisfied_lifecycle(self):
        correlation = self._correlate("satisfied")
        self.assertEqual(correlation["correlation_integrity"], "valid")
        self.assertEqual(correlation["agent_manifest"]["delta_verification"], "accepted")
        self.assertEqual(correlation["agent_memory"]["memory_action"], "permanent_deletion")
        self.assertEqual(correlation["agent_memory"]["lifecycle_satisfaction"], "satisfied")

    def test_rejected_manifest_delta_is_a_valid_correlated_negative_outcome(self):
        bad_verdict = verify_delta(
            self.previous,
            self.new,
            self.after_ops,
            [],
            now=APPROVED_AT + timedelta(seconds=5),
        )
        self.assertFalse(bad_verdict.accepted)
        self.assertEqual(bad_verdict.reason, "drift")
        correlation = self._correlate("residual", verdict=bad_verdict)
        self.assertEqual(correlation["correlation_integrity"], "valid")
        self.assertEqual(correlation["agent_manifest"]["delta_verification"], "rejected")
        self.assertEqual(correlation["agent_manifest"]["delta_reason"], "drift")

    def test_receipt_must_reference_the_new_checkpoint(self):
        correlation = self._correlate("residual", include_checkpoint=False)
        self.assertEqual(correlation["correlation_integrity"], "invalid")
        self.assertIn("receipt_missing_checkpoint_ref", correlation["binding_failures"])

    def test_receipt_action_must_match_signed_portable_memory_action(self):
        receipt, evidence = self._receipt_and_evidence(
            "residual",
            receipt_action="retain",
            portable_action="permanent_deletion",
        )
        correlation = correlate_agent_manifest_delta(
            evidence,
            receipt,
            self.trust,
            previous_checkpoint=self.previous,
            new_checkpoint=self.new,
            delta_accepted=self.verdict.accepted,
            delta_reason=self.verdict.reason,
            representation="kv",
        )
        self.assertEqual(correlation["correlation_integrity"], "invalid")
        self.assertNotIn("portable_evidence_invalid", correlation["binding_failures"])
        self.assertIn("receipt_memory_action_mismatch", correlation["binding_failures"])

    def test_portable_before_and_after_state_must_match_checkpoint_refs(self):
        receipt, evidence = self._receipt_and_evidence("residual")
        evidence["state"]["after_ref"] = checkpoint_reference(self.previous)
        correlation = correlate_agent_manifest_delta(
            evidence,
            receipt,
            self.trust,
            previous_checkpoint=self.previous,
            new_checkpoint=self.new,
            delta_accepted=self.verdict.accepted,
            delta_reason=self.verdict.reason,
            representation="kv",
        )
        self.assertEqual(correlation["correlation_integrity"], "invalid")
        self.assertIn("portable_evidence_invalid", correlation["binding_failures"])
        self.assertIn("after_checkpoint_ref_mismatch", correlation["binding_failures"])

    def test_checkpoint_projection_rejects_malformed_hash_and_naive_time(self):
        bad_hash = {
            "memory_root": "sha256:not-a-digest",
            "tree_size": 1,
            "seq": 1,
            "approved_at": "2026-08-11T20:00:00Z",
            "ttl_seconds": 3600,
        }
        with self.assertRaises(ValueError):
            checkpoint_payload(bad_hash)

        naive_time = dict(bad_hash)
        naive_time["memory_root"] = "sha256:" + ("0" * 64)
        naive_time["approved_at"] = "2026-08-11T20:00:00"
        with self.assertRaises(ValueError):
            checkpoint_payload(naive_time)

    def test_correlation_artifact_is_content_free_and_schema_valid(self):
        correlation = self._correlate("residual")
        rendered = json.dumps(correlation, sort_keys=True)
        self.assertNotIn("secret-memory-value", rendered)
        self.assertNotIn("memory:key:alpha", rendered)

        root = Path(__file__).resolve().parents[2]
        schema = json.loads((root / "schemas" / "agent-manifest-memory-correlation.schema.json").read_text())
        jsonschema.Draft202012Validator(schema).validate(correlation)


if __name__ == "__main__":
    unittest.main()
