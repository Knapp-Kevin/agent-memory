"""P4.5c TRACE/cMCP-compatible external action evidence vectors."""

from __future__ import annotations

import importlib.metadata
import json
import sys
import unittest
from pathlib import Path

import jsonschema

from tests import pin_support
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.portable_evidence import IssuerKey, issue_evidence  # noqa: E402
from agentmem_ref.trace_action_evidence import (  # noqa: E402
    CMCP_RELEASE_COMMIT,
    CMCP_RUNTIME_VERSION,
    TRACE_RECEIPT_INVALID,
    TRACE_RECEIPT_MISSING_REQUIRED,
    TRACE_RECEIPT_UNVERIFIED,
    TRACE_RECEIPT_VALID_ACCEPTED,
    TRACE_RECEIPT_VALID_REJECTED,
    TRACE_RELEASE_COMMIT,
    TRACE_SDK_VERSION,
    TraceReceiptIssuer,
    detached_payload_hash,
    issue_trace_action_evidence,
    verify_trace_action_evidence,
)

AM_ISSUER = "issuer:agent-memory-reference"
DOMAIN_AUTH_STATE = "domain-auth:trace:31"
AM_KEY = IssuerKey(
    issuer_id=AM_ISSUER,
    key_id="am-key-2026-08",
    private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33))),
    valid_from="2026-08-01T00:00:00Z",
    valid_until="2026-08-31T23:59:59Z",
)
TRACE_ISSUER = TraceReceiptIssuer(
    issuer_id="spiffe://runtime.example/agent-memory-controller",
    private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(33, 65))),
)


class TraceActionEvidenceTests(unittest.TestCase):
    def setUp(self):
        am_trust = AM_KEY.trust_key()
        self.am_trust = {(am_trust.issuer_id, am_trust.key_id): am_trust}
        trace_trust = TRACE_ISSUER.trust_key()
        self.trace_trust = {trace_trust.key_id: trace_trust}
        self.call_id = "call:trace:delete:42"
        self.action_ref = "action:delete:42"

    def _receipt_and_portable(self, lifecycle: str = "residual"):
        receipt = {
            "schema_version": "1.0.0",
            "receipt_id": "receipt:trace:delete:42",
            "memory_id": "mem:trace:alpha",
            "requested_action": "permanent_deletion",
            "policy_version": "pama-2026-08",
            "permitted_actions": ["permanent_deletion"],
            "selected_action": "permanent_deletion",
            "selection_mode": "deterministic",
            "timestamp": "2026-08-11T21:00:01Z",
        }
        portable = issue_evidence(
            receipt,
            issuer_id=AM_ISSUER,
            key=AM_KEY,
            issued_at="2026-08-11T21:00:02Z",
            action_ref=self.action_ref,
            memory_action="permanent_deletion",
            governance_disposition="committed",
            policy_ref="policy:pama-2026-08",
            authority_state_ref="authority:rev-31",
            decision_time="2026-08-11T21:00:01Z",
            scope_ref="scope:opaque:trace-test",
            before_state_ref="sha256:" + "1" * 64,
            after_state_ref="sha256:" + "2" * 64,
            lifecycle_result=lifecycle,
            source_domain_ref="domain:opaque:project-a",
            destination_domain_ref="domain:opaque:deleted",
            domain_authorization_state_ref=DOMAIN_AUTH_STATE,
        )
        return receipt, portable

    def _bundle(self, lifecycle: str = "residual", outcome: str = "accepted"):
        receipt, portable = self._receipt_and_portable(lifecycle)
        bundle = issue_trace_action_evidence(
            portable,
            issuer=TRACE_ISSUER,
            call_id=self.call_id,
            execution_outcome=outcome,
            execution_time="2026-08-11T21:00:03Z",
        )
        return receipt, portable, bundle

    def _verify(self, receipt, portable, bundle, **kwargs):
        return verify_trace_action_evidence(
            bundle,
            portable,
            self.am_trust,
            self.trace_trust,
            canonical_receipt=receipt,
            observed_call_id=kwargs.pop("observed_call_id", self.call_id),
            observed_action_ref=kwargs.pop("observed_action_ref", self.action_ref),
            authority_valid_at_execution=kwargs.pop("authority_valid_at_execution", True),
            domain_authorization_valid_at_execution=kwargs.pop(
                "domain_authorization_valid_at_execution", True
            ),
            **kwargs,
        )

    @unittest.skipUnless(
        pin_support.pinned("agentrust-trace", TRACE_SDK_VERSION),
        "agentrust-trace is not installed at the pinned version",
    )
    def test_pinned_trace_release_identity_is_explicit(self):
        self.assertEqual(importlib.metadata.version("agentrust-trace"), TRACE_SDK_VERSION)
        self.assertEqual(TRACE_SDK_VERSION, "0.9.0")
        self.assertEqual(TRACE_RELEASE_COMMIT, "94271a1630601c94e80a23263d9750cb8d39f1f4")
        self.assertEqual(CMCP_RUNTIME_VERSION, "0.4.0")
        self.assertEqual(CMCP_RELEASE_COMMIT, "a2e95151356c9ae6c545330c900f3d4af0e447c1")

    def test_accepted_receipt_preserves_residual_lifecycle(self):
        receipt, portable, bundle = self._bundle("residual", "accepted")
        result = self._verify(receipt, portable, bundle)
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_VALID_ACCEPTED)
        self.assertEqual(result["trace_binding"], "valid")
        self.assertEqual(result["external_execution_outcome"], "accepted")
        self.assertEqual(result["agent_memory"]["governance_disposition"], "committed")
        self.assertEqual(result["agent_memory"]["runtime_execution"], "executed_as_authorized")
        self.assertEqual(result["agent_memory"]["lifecycle_satisfaction"], "residual")
        self.assertEqual(bundle["detached_payload"]["domain_authorization_state_ref"], DOMAIN_AUTH_STATE)

    def test_same_action_receipt_can_preserve_satisfied_lifecycle(self):
        receipt, portable, bundle = self._bundle("satisfied", "accepted")
        result = self._verify(receipt, portable, bundle)
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_VALID_ACCEPTED)
        self.assertEqual(result["agent_memory"]["lifecycle_satisfaction"], "satisfied")

    def test_valid_rejection_is_negative_evidence_not_malformed_evidence(self):
        receipt, portable, bundle = self._bundle("residual", "rejected")
        result = self._verify(receipt, portable, bundle)
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_VALID_REJECTED)
        self.assertEqual(result["trace_binding"], "valid")
        self.assertEqual(result["external_execution_outcome"], "rejected")
        self.assertEqual(result["agent_memory"]["governance_disposition"], "committed")
        self.assertEqual(result["agent_memory"]["lifecycle_satisfaction"], "residual")

    def test_valid_trace_receipt_does_not_override_revoked_domain_membership(self):
        receipt, portable, bundle = self._bundle("residual", "accepted")
        result = self._verify(
            receipt,
            portable,
            bundle,
            domain_authorization_valid_at_execution=False,
        )
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_VALID_ACCEPTED)
        self.assertEqual(result["trace_binding"], "valid")
        self.assertEqual(result["agent_memory"]["evidence_integrity"], "valid")
        self.assertEqual(result["agent_memory"]["runtime_execution"], "unauthorized_execution")

    def test_wrong_call_id_blocks_replay(self):
        receipt, portable, bundle = self._bundle()
        result = self._verify(receipt, portable, bundle, observed_call_id="call:trace:other")
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_INVALID)
        self.assertIn("wrong_call_id", result["binding_failures"])

    def test_wrong_action_ref_blocks_replay(self):
        receipt, portable, bundle = self._bundle()
        result = self._verify(receipt, portable, bundle, observed_action_ref="action:other")
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_INVALID)
        self.assertIn("wrong_action_ref", result["binding_failures"])
        self.assertEqual(result["agent_memory"]["runtime_execution"], "execution_mismatch")
        self.assertIn("wrong_action_ref", result["agent_memory"]["binding_failures"])

    def test_detached_payload_tamper_is_detected(self):
        receipt, portable, bundle = self._bundle()
        bundle["detached_payload"]["execution_outcome"] = "rejected"
        result = self._verify(receipt, portable, bundle)
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_INVALID)
        self.assertIn("detached_payload_hash_mismatch", result["binding_failures"])

    def test_envelope_signature_tamper_is_detected(self):
        receipt, portable, bundle = self._bundle()
        bundle["external_execution_evidence"]["issuer"] = "spiffe://attacker.example/controller"
        result = self._verify(receipt, portable, bundle)
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_INVALID)
        self.assertTrue(
            "external_issuer_identity_mismatch" in result["binding_failures"]
            or "external_evidence_signature_invalid" in result["binding_failures"]
        )

    def test_unknown_external_issuer_is_unverified_not_invalid(self):
        receipt, portable, bundle = self._bundle()
        result = verify_trace_action_evidence(
            bundle,
            portable,
            self.am_trust,
            {},
            canonical_receipt=receipt,
            observed_call_id=self.call_id,
            observed_action_ref=self.action_ref,
            authority_valid_at_execution=True,
            domain_authorization_valid_at_execution=True,
        )
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_UNVERIFIED)
        self.assertEqual(result["trace_binding"], "unverifiable")
        self.assertEqual(result["binding_failures"], [])
        self.assertEqual(result["agent_memory"]["evidence_integrity"], "valid")
        self.assertEqual(result["agent_memory"]["runtime_execution"], "executed_as_authorized")

    def test_required_receipt_missing_is_distinct(self):
        receipt, portable = self._receipt_and_portable()
        result = verify_trace_action_evidence(
            None,
            portable,
            self.am_trust,
            self.trace_trust,
            canonical_receipt=receipt,
        )
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_MISSING_REQUIRED)
        self.assertIn("required_action_receipt_missing", result["binding_failures"])

    def test_isolation_domain_mismatch_is_detected(self):
        receipt, portable, bundle = self._bundle()
        bundle["detached_payload"]["destination_domain_ref"] = "domain:opaque:wrong"
        bundle["external_execution_evidence"]["evidence_hash"] = detached_payload_hash(
            bundle["detached_payload"]
        )
        result = self._verify(receipt, portable, bundle)
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_INVALID)
        self.assertIn("destination_domain_ref_mismatch", result["binding_failures"])

    def test_domain_authorization_state_mismatch_is_detected(self):
        receipt, portable, bundle = self._bundle()
        bundle["detached_payload"]["domain_authorization_state_ref"] = "domain-auth:trace:wrong"
        bundle["external_execution_evidence"]["evidence_hash"] = detached_payload_hash(
            bundle["detached_payload"]
        )
        result = self._verify(receipt, portable, bundle)
        self.assertEqual(result["trace_receipt_status"], TRACE_RECEIPT_INVALID)
        self.assertIn("domain_authorization_state_ref_mismatch", result["binding_failures"])

    def test_bundle_is_content_free_and_schema_valid(self):
        _, _, bundle = self._bundle()
        rendered = json.dumps(bundle, sort_keys=True)
        self.assertNotIn("secret-memory", rendered)
        self.assertNotIn("memory content", rendered.lower())

        root = Path(__file__).resolve().parents[2]
        schema = json.loads((root / "schemas" / "trace-action-evidence-bundle.schema.json").read_text())
        jsonschema.Draft202012Validator(schema).validate(bundle)

    def test_envelope_uses_existing_cmcp_six_field_shape(self):
        _, _, bundle = self._bundle()
        self.assertEqual(
            set(bundle["external_execution_evidence"]),
            {
                "issuer",
                "issuer_key_id",
                "signature",
                "evidence_hash",
                "evidence_type",
                "linked_call_id",
            },
        )
        self.assertEqual(bundle["external_execution_evidence"]["evidence_type"], "opaque-receipt")


if __name__ == "__main__":
    unittest.main()
