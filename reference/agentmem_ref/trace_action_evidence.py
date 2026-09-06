"""P4.5c TRACE/cMCP-compatible external action evidence.

This module adapts P4.5a portable Agent Memory governance evidence into the
existing AgenTrust external-execution-evidence shape. TRACE/cMCP owns receipt
integrity and call binding. Agent Memory remains authoritative for PAMA,
memory-action semantics, lifecycle satisfaction, and isolation-domain meaning.

Two canonicalization domains are intentionally preserved:

* detached payload: RFC 8785/JCS, matching TRACE action-evidence guidance;
* cMCP envelope: deterministic JSON used by cmcp_verify.verify_audit_bundle().

Do not collapse these into one serializer unless the upstream contracts converge.
"""

from __future__ import annotations

import base64
import binascii
import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .portable_evidence import RuntimeObservation, TrustKey, sha256_ref, verify_evidence

PROFILE = "agent-memory.trace-action-evidence.v1"
EVIDENCE_TYPE = "opaque-receipt"
TRACE_SDK_VERSION = "0.9.0"
TRACE_RELEASE_COMMIT = "94271a1630601c94e80a23263d9750cb8d39f1f4"
CMCP_RUNTIME_VERSION = "0.4.0"
CMCP_RELEASE_COMMIT = "a2e95151356c9ae6c545330c900f3d4af0e447c1"

TRACE_RECEIPT_VALID_ACCEPTED = "receipt_valid_accepted"
TRACE_RECEIPT_VALID_REJECTED = "receipt_valid_rejected"
TRACE_RECEIPT_MISSING_REQUIRED = "receipt_missing_required"
TRACE_RECEIPT_INVALID = "receipt_invalid"
TRACE_RECEIPT_UNVERIFIED = "receipt_unverified"

_OUTCOMES = {"accepted", "rejected"}
_ENVELOPE_FIELDS = {
    "issuer",
    "issuer_key_id",
    "signature",
    "evidence_hash",
    "evidence_type",
    "linked_call_id",
}


def _raw_public_key(public_key: Ed25519PublicKey) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def _key_id(public_key: Ed25519PublicKey) -> str:
    return hashlib.sha256(_raw_public_key(public_key)).hexdigest()


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def _parse_time(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("TRACE action-evidence timestamps must use RFC3339 UTC with Z")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("TRACE action-evidence timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def jcs_bytes(value: object) -> bytes:
    """RFC 8785/JCS bytes for the detached evidence payload."""
    return rfc8785.dumps(value)


def detached_payload_hash(payload: Mapping[str, object]) -> str:
    return "sha256:" + hashlib.sha256(jcs_bytes(dict(payload))).hexdigest()


def cmcp_envelope_signing_input(envelope: Mapping[str, object]) -> bytes:
    """Reproduce cMCP #301 envelope serialization exactly.

    cMCP's released verifier signs/verifies the envelope with sorted compact JSON
    and ``ensure_ascii=True``. The detached payload uses JCS separately.
    """
    body = {k: v for k, v in envelope.items() if k != "signature"}
    return json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


@dataclass(frozen=True)
class TraceReceiptIssuer:
    """Independent runtime/action-evidence issuer."""

    issuer_id: str
    private_key: Ed25519PrivateKey

    @property
    def key_id(self) -> str:
        return _key_id(self.private_key.public_key())

    def trust_key(self) -> "TraceReceiptTrustKey":
        return TraceReceiptTrustKey(
            issuer_id=self.issuer_id,
            public_key=self.private_key.public_key(),
        )


@dataclass(frozen=True)
class TraceReceiptTrustKey:
    """Pinned public key for an external action-evidence issuer."""

    issuer_id: str
    public_key: Ed25519PublicKey

    @property
    def key_id(self) -> str:
        return _key_id(self.public_key)

    @property
    def raw_public_key(self) -> bytes:
        return _raw_public_key(self.public_key)


def issue_trace_action_evidence(
    portable_evidence: Mapping[str, object],
    *,
    issuer: TraceReceiptIssuer,
    call_id: str,
    execution_outcome: str,
    execution_time: str,
) -> dict:
    """Issue a cMCP-compatible external execution-evidence envelope."""
    if execution_outcome not in _OUTCOMES:
        raise ValueError(f"unsupported external execution outcome: {execution_outcome}")
    if not isinstance(call_id, str) or not call_id:
        raise ValueError("call_id must be a non-empty string")
    _parse_time(execution_time)

    action_ref = portable_evidence.get("action_ref")
    canonical_receipt_ref = portable_evidence.get("canonical_receipt_ref")
    scope = portable_evidence.get("scope")
    if not isinstance(action_ref, str) or not action_ref:
        raise ValueError("portable evidence is missing action_ref")
    if not isinstance(canonical_receipt_ref, str) or not canonical_receipt_ref:
        raise ValueError("portable evidence is missing canonical_receipt_ref")
    if not isinstance(scope, Mapping):
        raise ValueError("portable evidence is missing scope")

    payload: dict[str, object] = {
        "profile": PROFILE,
        "call_id": call_id,
        "action_ref": action_ref,
        "portable_evidence_ref": sha256_ref(dict(portable_evidence)),
        "canonical_receipt_ref": canonical_receipt_ref,
        "execution_outcome": execution_outcome,
        "execution_time": execution_time,
    }
    for name in (
        "source_domain_ref",
        "destination_domain_ref",
        "domain_authorization_state_ref",
    ):
        value = scope.get(name)
        if value is not None:
            if not isinstance(value, str) or not value:
                raise ValueError(f"portable {name} must be a non-empty opaque reference")
            payload[name] = value

    envelope: dict[str, object] = {
        "issuer": issuer.issuer_id,
        "issuer_key_id": issuer.key_id,
        "evidence_hash": detached_payload_hash(payload),
        "evidence_type": EVIDENCE_TYPE,
        "linked_call_id": call_id,
    }
    signature = issuer.private_key.sign(cmcp_envelope_signing_input(envelope))
    envelope["signature"] = _b64url(signature)

    return {
        "external_execution_evidence": envelope,
        "detached_payload": payload,
    }


def _portable_scope_failures(payload: Mapping[str, object], portable_evidence: Mapping[str, object]) -> list[str]:
    scope = portable_evidence.get("scope")
    if not isinstance(scope, Mapping):
        return ["portable_scope_missing"]
    failures: list[str] = []
    for name in (
        "source_domain_ref",
        "destination_domain_ref",
        "domain_authorization_state_ref",
    ):
        signed = scope.get(name)
        detached = payload.get(name)
        if signed != detached:
            failures.append(f"{name}_mismatch")
    return failures


def verify_trace_action_evidence(
    bundle: Mapping[str, object] | None,
    portable_evidence: Mapping[str, object],
    agent_memory_trust_keys: Mapping[tuple[str, str], TrustKey],
    trace_trust_keys: Mapping[str, TraceReceiptTrustKey],
    *,
    canonical_receipt: Mapping[str, object] | None = None,
    observed_call_id: str | None = None,
    observed_action_ref: str | None = None,
    authority_valid_at_execution: bool | None = None,
    domain_authorization_valid_at_execution: bool | None = None,
) -> dict:
    """Verify TRACE/cMCP action evidence without importing Agent Memory semantics."""
    if bundle is None:
        portable_result = verify_evidence(
            portable_evidence,
            agent_memory_trust_keys,
            canonical_receipt=canonical_receipt,
        )
        return _result(
            TRACE_RECEIPT_MISSING_REQUIRED,
            "unverifiable",
            ["required_action_receipt_missing"],
            None,
            portable_result,
        )

    envelope = bundle.get("external_execution_evidence")
    payload = bundle.get("detached_payload")
    if not isinstance(envelope, Mapping) or not isinstance(payload, Mapping):
        portable_result = verify_evidence(
            portable_evidence,
            agent_memory_trust_keys,
            canonical_receipt=canonical_receipt,
        )
        return _result(
            TRACE_RECEIPT_INVALID,
            "invalid",
            ["missing_envelope_or_detached_payload"],
            None,
            portable_result,
        )

    failures: list[str] = []
    unknown_trust = False

    if set(envelope.keys()) != _ENVELOPE_FIELDS:
        failures.append("invalid_external_evidence_envelope_shape")
    if envelope.get("evidence_type") != EVIDENCE_TYPE:
        failures.append("unsupported_evidence_type")
    if payload.get("profile") != PROFILE:
        failures.append("unsupported_detached_payload_profile")

    call_id = payload.get("call_id")
    action_ref = payload.get("action_ref")
    execution_outcome = payload.get("execution_outcome")
    execution_time = payload.get("execution_time")
    if not all(isinstance(v, str) and v for v in (call_id, action_ref, execution_outcome, execution_time)):
        failures.append("missing_required_detached_payload_field")
    if execution_outcome not in _OUTCOMES:
        failures.append("invalid_execution_outcome")
    if isinstance(execution_time, str):
        try:
            _parse_time(execution_time)
        except ValueError:
            failures.append("invalid_execution_time")

    if envelope.get("linked_call_id") != call_id:
        failures.append("linked_call_id_mismatch")
    if observed_call_id is not None and observed_call_id != call_id:
        failures.append("wrong_call_id")

    if action_ref != portable_evidence.get("action_ref"):
        failures.append("portable_action_ref_mismatch")
    if observed_action_ref is not None and observed_action_ref != action_ref:
        failures.append("wrong_action_ref")

    if payload.get("portable_evidence_ref") != sha256_ref(dict(portable_evidence)):
        failures.append("portable_evidence_ref_mismatch")
    if payload.get("canonical_receipt_ref") != portable_evidence.get("canonical_receipt_ref"):
        failures.append("canonical_receipt_ref_mismatch")
    failures.extend(_portable_scope_failures(payload, portable_evidence))

    try:
        expected_hash = detached_payload_hash(payload)
    except Exception:
        expected_hash = ""
        failures.append("detached_payload_canonicalization_failed")
    if envelope.get("evidence_hash") != expected_hash:
        failures.append("detached_payload_hash_mismatch")

    issuer = envelope.get("issuer")
    key_id = envelope.get("issuer_key_id")
    signature = envelope.get("signature")
    if not all(isinstance(v, str) and v for v in (issuer, key_id, signature)):
        failures.append("missing_external_issuer_field")
    elif not isinstance(key_id, str) or len(key_id) != 64 or any(c not in "0123456789abcdef" for c in key_id):
        failures.append("invalid_issuer_key_id")
    else:
        trust_key = trace_trust_keys.get(key_id)
        if trust_key is None:
            unknown_trust = True
        else:
            if trust_key.issuer_id != issuer:
                failures.append("external_issuer_identity_mismatch")
            if trust_key.key_id != key_id:
                failures.append("external_issuer_key_binding_mismatch")
            try:
                trust_key.public_key.verify(
                    _b64url_decode(str(signature)),
                    cmcp_envelope_signing_input(envelope),
                )
            except (InvalidSignature, ValueError, TypeError, binascii.Error):
                failures.append("external_evidence_signature_invalid")

    runtime_action_ref = observed_action_ref if observed_action_ref is not None else action_ref
    runtime = RuntimeObservation(
        action_ref=str(runtime_action_ref) if isinstance(runtime_action_ref, str) else None,
        execution_time=str(execution_time) if isinstance(execution_time, str) else None,
        source_domain_ref=(
            str(payload.get("source_domain_ref")) if payload.get("source_domain_ref") is not None else None
        ),
        destination_domain_ref=(
            str(payload.get("destination_domain_ref")) if payload.get("destination_domain_ref") is not None else None
        ),
        domain_authorization_state_ref=(
            str(payload.get("domain_authorization_state_ref"))
            if payload.get("domain_authorization_state_ref") is not None
            else None
        ),
        authority_valid_at_execution=authority_valid_at_execution,
        domain_authorization_valid_at_execution=domain_authorization_valid_at_execution,
    )
    portable_result = verify_evidence(
        portable_evidence,
        agent_memory_trust_keys,
        canonical_receipt=canonical_receipt,
        runtime=runtime,
    )
    if portable_result["evidence_integrity"] != "valid":
        failures.append("agent_memory_portable_evidence_invalid")

    if failures:
        status = TRACE_RECEIPT_INVALID
        trace_binding = "invalid"
    elif unknown_trust:
        status = TRACE_RECEIPT_UNVERIFIED
        trace_binding = "unverifiable"
    elif execution_outcome == "accepted":
        status = TRACE_RECEIPT_VALID_ACCEPTED
        trace_binding = "valid"
    else:
        status = TRACE_RECEIPT_VALID_REJECTED
        trace_binding = "valid"

    return _result(
        status,
        trace_binding,
        failures,
        str(execution_outcome) if execution_outcome in _OUTCOMES else None,
        portable_result,
    )


def _result(
    receipt_status: str,
    trace_binding: str,
    failures: list[str],
    external_execution_outcome: str | None,
    portable_result: Mapping[str, object],
) -> dict:
    return {
        "trace_receipt_status": receipt_status,
        "trace_binding": trace_binding,
        "binding_failures": list(dict.fromkeys(failures)),
        "external_execution_outcome": external_execution_outcome,
        "agent_memory": copy.deepcopy(dict(portable_result)),
    }
