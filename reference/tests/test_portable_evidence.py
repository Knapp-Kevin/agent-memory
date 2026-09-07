"""P4.5a portable governance evidence core.

These tests exercise valid negative outcomes as well as signature and binding
failures. A denial with a valid signature is evidence, not a verifier malfunction;
an authorized delete with residual state remains a lifecycle failure.

Run: python -m unittest discover -s reference/tests -t reference
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import jsonschema
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.portable_evidence import (  # noqa: E402
    IssuerKey,
    RuntimeObservation,
    canonical_json,
    issue_evidence,
    verify_evidence,
)

ISSUER = "issuer:agent-memory-reference"
KEY = IssuerKey(
    issuer_id=ISSUER,
    key_id="key-2026-08",
    private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33))),
    valid_from="2026-08-01T00:00:00Z",
    valid_until="2026-08-31T23:59:59Z",
)
RECEIPT = {
    "schema_version": "1.0.0",
    "receipt_id": "receipt:42",
    "memory_id": "mem:alpha",
    "selected_action": "delete",
    "policy_version": "pama-2026-08",
    "timestamp": "2026-08-11T18:00:00Z",
}


def make_evidence(**overrides):
    args = dict(
        canonical_receipt=RECEIPT,
        issuer_id=ISSUER,
        key=KEY,
        issued_at="2026-08-11T18:00:01Z",
        action_ref="action:delete:42",
        memory_action="permanent_deletion",
        governance_disposition="committed",
        policy_ref="policy:pama-2026-08",
        authority_state_ref="authority:rev-12",
        decision_time="2026-08-11T18:00:00Z",
        scope_ref="scope:opaque:4fc2",
        before_state_ref="state:before:42",
        after_state_ref="state:after:42",
        lifecycle_result="satisfied",
        source_domain_ref="domain:opaque:project-a",
        destination_domain_ref="domain:opaque:archive",
        domain_authorization_state_ref="domain-auth:9",
    )
    args.update(overrides)
    return issue_evidence(**args)


class CanonicalizationTests(unittest.TestCase):
    def test_object_order_does_not_change_bytes(self):
        self.assertEqual(canonical_json({"b": 2, "a": 1}), canonical_json({"a": 1, "b": 2}))

    def test_floats_are_rejected_in_v1(self):
        with self.assertRaises(TypeError):
            canonical_json({"score": 0.9})


class PortableEvidenceTests(unittest.TestCase):
    def setUp(self):
        trust_key = KEY.trust_key()
        self.trust = {(trust_key.issuer_id, trust_key.key_id): trust_key}

    def test_happy_path_binds_receipt_action_policy_authority_and_domains(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            canonical_receipt=RECEIPT,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                execution_time="2026-08-11T18:00:02Z",
                policy_ref="policy:pama-2026-08",
                authority_state_ref="authority:rev-12",
                source_domain_ref="domain:opaque:project-a",
                destination_domain_ref="domain:opaque:archive",
                domain_authorization_state_ref="domain-auth:9",
                authority_valid_at_execution=True,
                domain_authorization_valid_at_execution=True,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "valid")
        self.assertEqual(result["receipt_resolution"], "resolved")
        self.assertEqual(result["governance_disposition"], "committed")
        self.assertEqual(result["runtime_execution"], "executed_as_authorized")
        self.assertEqual(result["lifecycle_satisfaction"], "satisfied")

    def test_projection_satisfies_the_versioned_json_schema(self):
        evidence = make_evidence()
        root = Path(__file__).resolve().parents[2]
        schema = json.loads((root / "schemas" / "portable-governance-evidence.schema.json").read_text())
        jsonschema.Draft202012Validator(schema).validate(evidence)

    def test_projection_contains_no_canonical_receipt_or_memory_content(self):
        evidence = make_evidence()
        rendered = str(evidence)
        self.assertNotIn("receipt_id", rendered)
        self.assertNotIn("memory_id", rendered)
        self.assertNotIn("selected_action", rendered)
        self.assertNotIn("mem:alpha", rendered)

    def test_tamper_is_invalid(self):
        evidence = make_evidence()
        evidence["governance"]["disposition"] = "denied"
        result = verify_evidence(evidence, self.trust)
        self.assertEqual(result["evidence_integrity"], "invalid")
        self.assertIn("signature_verification_failed", result["binding_failures"])

    def test_unknown_issuer_is_unverifiable_not_governance_denial(self):
        evidence = make_evidence()
        result = verify_evidence(evidence, {})
        self.assertEqual(result["evidence_integrity"], "unverifiable")
        self.assertEqual(result["governance_disposition"], "committed")

    def test_wrong_action_detects_replay_against_another_execution(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(action_ref="action:delete:99", authority_valid_at_execution=True),
        )
        self.assertEqual(result["evidence_integrity"], "invalid")
        self.assertIn("wrong_action_ref", result["binding_failures"])
        self.assertEqual(result["runtime_execution"], "execution_mismatch")

    def test_stale_policy_and_authority_state_fail_binding(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                policy_ref="policy:pama-2026-09",
                authority_state_ref="authority:rev-13",
                authority_valid_at_execution=True,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "invalid")
        self.assertIn("stale_or_wrong_policy_ref", result["binding_failures"])
        self.assertIn("stale_or_wrong_authority_state_ref", result["binding_failures"])

    def test_wrong_isolation_domain_fails_binding(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                source_domain_ref="domain:opaque:project-b",
                destination_domain_ref="domain:opaque:archive",
            ),
        )
        self.assertEqual(result["evidence_integrity"], "invalid")
        self.assertIn("wrong_source_domain", result["binding_failures"])

    def test_unauthorized_scope_broadening_fails_destination_binding(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                source_domain_ref="domain:opaque:project-a",
                destination_domain_ref="domain:opaque:organization-wide",
                domain_authorization_state_ref="domain-auth:9",
                authority_valid_at_execution=True,
                domain_authorization_valid_at_execution=True,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "invalid")
        self.assertIn("wrong_destination_domain", result["binding_failures"])
        self.assertEqual(result["runtime_execution"], "unverifiable")

    def test_stale_domain_authorization_state_fails_binding(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                source_domain_ref="domain:opaque:project-a",
                destination_domain_ref="domain:opaque:archive",
                domain_authorization_state_ref="domain-auth:10",
                authority_valid_at_execution=True,
                domain_authorization_valid_at_execution=True,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "invalid")
        self.assertIn(
            "stale_or_wrong_domain_authorization_state_ref",
            result["binding_failures"],
        )
        self.assertEqual(result["runtime_execution"], "unverifiable")

    def test_revoked_shared_domain_membership_makes_execution_unauthorized(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                execution_time="2026-08-11T18:00:02Z",
                source_domain_ref="domain:opaque:project-a",
                destination_domain_ref="domain:opaque:archive",
                domain_authorization_state_ref="domain-auth:9",
                authority_valid_at_execution=True,
                domain_authorization_valid_at_execution=False,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "valid")
        self.assertEqual(result["binding_failures"], [])
        self.assertEqual(result["runtime_execution"], "unauthorized_execution")

    def test_cross_domain_execution_without_membership_continuity_is_unverifiable(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                execution_time="2026-08-11T18:00:02Z",
                source_domain_ref="domain:opaque:project-a",
                destination_domain_ref="domain:opaque:archive",
                authority_valid_at_execution=True,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "valid")
        self.assertEqual(result["runtime_execution"], "unverifiable")

    def test_cross_domain_execution_without_signed_membership_state_is_unverifiable(self):
        evidence = make_evidence(domain_authorization_state_ref=None)
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                execution_time="2026-08-11T18:00:02Z",
                source_domain_ref="domain:opaque:project-a",
                destination_domain_ref="domain:opaque:archive",
                authority_valid_at_execution=True,
                domain_authorization_valid_at_execution=True,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "valid")
        self.assertEqual(result["runtime_execution"], "unverifiable")

    def test_execution_before_decision_fails_binding(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                execution_time="2026-08-11T17:59:59Z",
                authority_valid_at_execution=True,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "invalid")
        self.assertIn("execution_precedes_decision", result["binding_failures"])

    def test_unknown_execution_time_authority_fails_closed(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                execution_time="2026-08-11T18:00:02Z",
            ),
        )
        self.assertEqual(result["evidence_integrity"], "valid")
        self.assertEqual(result["runtime_execution"], "unverifiable")

    def test_authority_revoked_between_decision_and_execution_is_unauthorized(self):
        evidence = make_evidence()
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                execution_time="2026-08-11T18:00:02Z",
                source_domain_ref="domain:opaque:project-a",
                destination_domain_ref="domain:opaque:archive",
                domain_authorization_state_ref="domain-auth:9",
                authority_valid_at_execution=False,
                domain_authorization_valid_at_execution=True,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "valid")
        self.assertEqual(result["binding_failures"], [])
        self.assertEqual(result["governance_disposition"], "committed")
        self.assertEqual(result["runtime_execution"], "unauthorized_execution")

    def test_valid_denial_plus_runtime_action_is_unauthorized_execution(self):
        evidence = make_evidence(governance_disposition="denied", lifecycle_result="not_applicable")
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(action_ref="action:delete:42", authority_valid_at_execution=True),
        )
        self.assertEqual(result["evidence_integrity"], "valid")
        self.assertEqual(result["governance_disposition"], "denied")
        self.assertEqual(result["runtime_execution"], "unauthorized_execution")

    def test_authorized_delete_can_still_have_residual_lifecycle_failure(self):
        evidence = make_evidence(lifecycle_result="residual")
        result = verify_evidence(
            evidence,
            self.trust,
            runtime=RuntimeObservation(
                action_ref="action:delete:42",
                source_domain_ref="domain:opaque:project-a",
                destination_domain_ref="domain:opaque:archive",
                domain_authorization_state_ref="domain-auth:9",
                authority_valid_at_execution=True,
                domain_authorization_valid_at_execution=True,
            ),
        )
        self.assertEqual(result["evidence_integrity"], "valid")
        self.assertEqual(result["runtime_execution"], "executed_as_authorized")
        self.assertEqual(result["lifecycle_satisfaction"], "residual")

    def test_detached_verification_survives_pruned_canonical_content(self):
        evidence = make_evidence()
        result = verify_evidence(evidence, self.trust)
        self.assertEqual(result["evidence_integrity"], "valid")
        self.assertEqual(result["receipt_resolution"], "detached")

    def test_wrong_canonical_receipt_fails_binding(self):
        evidence = make_evidence()
        wrong = dict(RECEIPT, receipt_id="receipt:other")
        result = verify_evidence(evidence, self.trust, canonical_receipt=wrong)
        self.assertEqual(result["evidence_integrity"], "invalid")
        self.assertEqual(result["receipt_resolution"], "mismatch")

    def test_historical_public_key_remains_verifiable_after_rotation(self):
        old_key = IssuerKey(
            issuer_id=ISSUER,
            key_id="key-old",
            private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(33, 65))),
            valid_from="2026-07-01T00:00:00Z",
            valid_until="2026-08-15T00:00:00Z",
        )
        new_key = IssuerKey(
            issuer_id=ISSUER,
            key_id="key-new",
            private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(65, 97))),
            valid_from="2026-08-15T00:00:01Z",
        )
        evidence = make_evidence(key=old_key, issued_at="2026-08-11T18:00:01Z")
        old_trust = old_key.trust_key()
        new_trust = new_key.trust_key()
        trust = {
            (old_trust.issuer_id, old_trust.key_id): old_trust,
            (new_trust.issuer_id, new_trust.key_id): new_trust,
        }
        result = verify_evidence(evidence, trust)
        self.assertEqual(result["evidence_integrity"], "valid")

    def test_revoked_key_cannot_issue_new_evidence(self):
        revoked = IssuerKey(
            issuer_id=ISSUER,
            key_id="key-revoked",
            private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(97, 129))),
            valid_from="2026-08-01T00:00:00Z",
            revoked_at="2026-08-10T00:00:00Z",
        )
        with self.assertRaises(ValueError):
            make_evidence(key=revoked, issued_at="2026-08-11T18:00:01Z")


if __name__ == "__main__":
    unittest.main()
