"""Portable Agent Memory governance evidence, P4.5a reference profile.

This module projects a canonical Agent Memory decision receipt into a content-free,
portable evidence object. The canonical receipt remains authoritative; the
portable object binds that receipt to governance, authority, domain, runtime, and
lifecycle references so an independent verifier can check what happened without
receiving raw memory content or a signing secret.
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

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

EVIDENCE_TYPE = "agent-memory-governance-evidence"
EVIDENCE_VERSION = "1.0.0"
ALGORITHM = "Ed25519"

INTEGRITY_VALID = "valid"
INTEGRITY_INVALID = "invalid"
INTEGRITY_UNVERIFIABLE = "unverifiable"

GOVERNANCE_VALUES = {
    "permitted",
    "denied",
    "deferred",
    "review_required",
    "committed",
}
LIFECYCLE_VALUES = {
    "satisfied",
    "residual",
    "incomplete",
    "unverifiable",
    "not_applicable",
}


def canonical_json(value: object) -> bytes:
    """Return the deterministic v1 canonical JSON byte representation."""
    _reject_floats(value)
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _reject_floats(value: object) -> None:
    if isinstance(value, float):
        raise TypeError("portable evidence v1 does not permit floating-point values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_floats(item)


def sha256_ref(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class IssuerKey:
    """Private signing key and its issuance-validity metadata."""

    issuer_id: str
    key_id: str
    private_key: Ed25519PrivateKey
    valid_from: str
    valid_until: str | None = None
    revoked_at: str | None = None

    def usable_at(self, timestamp: str) -> bool:
        return _usable_at(timestamp, self.valid_from, self.valid_until, self.revoked_at)

    def trust_key(self) -> "TrustKey":
        return TrustKey(
            issuer_id=self.issuer_id,
            key_id=self.key_id,
            public_key=self.private_key.public_key(),
            valid_from=self.valid_from,
            valid_until=self.valid_until,
            revoked_at=self.revoked_at,
        )


@dataclass(frozen=True)
class TrustKey:
    """Public verification key configured as a verifier trust anchor."""

    issuer_id: str
    key_id: str
    public_key: Ed25519PublicKey
    valid_from: str
    valid_until: str | None = None
    revoked_at: str | None = None

    def usable_at(self, timestamp: str) -> bool:
        return _usable_at(timestamp, self.valid_from, self.valid_until, self.revoked_at)


def _usable_at(timestamp: str, valid_from: str, valid_until: str | None, revoked_at: str | None) -> bool:
    point = _parse_time(timestamp)
    if point < _parse_time(valid_from):
        return False
    if valid_until and point > _parse_time(valid_until):
        return False
    if revoked_at and point >= _parse_time(revoked_at):
        return False
    return True


@dataclass(frozen=True)
class RuntimeObservation:
    """Optional execution-time facts supplied independently by a verifier.

    Generic actor/PAMA authority continuity and isolation-domain membership
    continuity are separate facts. A verifier must not infer that one remained
    valid merely because the other did.
    """

    action_ref: str | None = None
    execution_time: str | None = None
    policy_ref: str | None = None
    authority_state_ref: str | None = None
    source_domain_ref: str | None = None
    destination_domain_ref: str | None = None
    domain_authorization_state_ref: str | None = None
    authority_valid_at_execution: bool | None = None
    domain_authorization_valid_at_execution: bool | None = None


def issue_evidence(
    canonical_receipt: Mapping[str, object],
    *,
    issuer_id: str,
    key: IssuerKey,
    issued_at: str,
    action_ref: str,
    memory_action: str,
    governance_disposition: str,
    policy_ref: str,
    authority_state_ref: str,
    decision_time: str,
    scope_ref: str,
    before_state_ref: str,
    after_state_ref: str,
    lifecycle_result: str = "not_applicable",
    source_domain_ref: str | None = None,
    destination_domain_ref: str | None = None,
    domain_authorization_state_ref: str | None = None,
) -> dict:
    """Create and sign a portable projection of a canonical decision receipt."""
    if issuer_id != key.issuer_id:
        raise ValueError("issuer_id must match the configured issuer key")
    if governance_disposition not in GOVERNANCE_VALUES:
        raise ValueError(f"unsupported governance disposition: {governance_disposition}")
    if lifecycle_result not in LIFECYCLE_VALUES:
        raise ValueError(f"unsupported lifecycle result: {lifecycle_result}")
    if not key.usable_at(issued_at):
        raise ValueError("issuer key is not valid at evidence issuance time")
    if _parse_time(decision_time) > _parse_time(issued_at):
        raise ValueError("decision_time cannot be after evidence issuance")

    scope = {"scope_ref": scope_ref}
    for name, value in (
        ("source_domain_ref", source_domain_ref),
        ("destination_domain_ref", destination_domain_ref),
        ("domain_authorization_state_ref", domain_authorization_state_ref),
    ):
        if value is not None:
            scope[name] = value

    evidence = {
        "evidence_type": EVIDENCE_TYPE,
        "version": EVIDENCE_VERSION,
        "canonicalization": "agent-memory-canonical-json-v1",
        "issuer": {
            "id": issuer_id,
            "key_id": key.key_id,
            "algorithm": ALGORITHM,
        },
        "issued_at": issued_at,
        "action_ref": action_ref,
        "memory_action": memory_action,
        "canonical_receipt_ref": sha256_ref(dict(canonical_receipt)),
        "governance": {
            "disposition": governance_disposition,
            "policy_ref": policy_ref,
            "authority_state_ref": authority_state_ref,
            "decision_time": decision_time,
        },
        "scope": scope,
        "state": {
            "before_ref": before_state_ref,
            "after_ref": after_state_ref,
        },
        "lifecycle_result": lifecycle_result,
    }
    signature = key.private_key.sign(canonical_json(_signable(evidence)))
    evidence["authentication"] = {
        "algorithm": ALGORITHM,
        "key_id": key.key_id,
        "value": base64.b64encode(signature).decode("ascii"),
    }
    return evidence


def _signable(evidence: Mapping[str, object]) -> dict:
    payload = copy.deepcopy(dict(evidence))
    payload.pop("authentication", None)
    return payload


def verify_evidence(
    evidence: Mapping[str, object],
    trust_keys: Mapping[tuple[str, str], TrustKey],
    *,
    canonical_receipt: Mapping[str, object] | None = None,
    runtime: RuntimeObservation | None = None,
) -> dict:
    """Verify evidence while keeping all semantic outcome dimensions separate."""
    runtime = runtime or RuntimeObservation()
    failures = _structural_failures(evidence)
    if failures:
        return _result(INTEGRITY_INVALID, failures, evidence, "unresolved", runtime)

    issuer = evidence["issuer"]
    auth = evidence["authentication"]
    issuer_id = issuer["id"]
    key_id = issuer["key_id"]

    key = trust_keys.get((issuer_id, key_id))
    if key is None:
        return _result(
            INTEGRITY_UNVERIFIABLE,
            ["unknown_or_untrusted_issuer_key"],
            evidence,
            "unresolved",
            runtime,
        )

    issued_at = evidence["issued_at"]
    if not key.usable_at(issued_at):
        return _result(
            INTEGRITY_UNVERIFIABLE,
            ["issuer_key_not_valid_at_issuance"],
            evidence,
            "unresolved",
            runtime,
        )

    try:
        signature = base64.b64decode(auth["value"], validate=True)
        key.public_key.verify(signature, canonical_json(_signable(evidence)))
    except (InvalidSignature, ValueError, TypeError, binascii.Error):
        return _result(
            INTEGRITY_INVALID,
            ["signature_verification_failed"],
            evidence,
            "unresolved",
            runtime,
        )

    failures = []
    receipt_resolution = "detached"
    if canonical_receipt is not None:
        if sha256_ref(dict(canonical_receipt)) != evidence["canonical_receipt_ref"]:
            failures.append("canonical_receipt_hash_mismatch")
            receipt_resolution = "mismatch"
        else:
            receipt_resolution = "resolved"

    governance = evidence["governance"]
    scope = evidence["scope"]
    for observed, signed, failure in (
        (runtime.action_ref, evidence["action_ref"], "wrong_action_ref"),
        (runtime.policy_ref, governance["policy_ref"], "stale_or_wrong_policy_ref"),
        (runtime.authority_state_ref, governance["authority_state_ref"], "stale_or_wrong_authority_state_ref"),
        (runtime.source_domain_ref, scope.get("source_domain_ref"), "wrong_source_domain"),
        (runtime.destination_domain_ref, scope.get("destination_domain_ref"), "wrong_destination_domain"),
        (
            runtime.domain_authorization_state_ref,
            scope.get("domain_authorization_state_ref"),
            "stale_or_wrong_domain_authorization_state_ref",
        ),
    ):
        if observed is not None and observed != signed:
            failures.append(failure)

    if runtime.execution_time is not None:
        try:
            if _parse_time(runtime.execution_time) < _parse_time(governance["decision_time"]):
                failures.append("execution_precedes_decision")
        except ValueError:
            failures.append("invalid_execution_time")

    integrity = INTEGRITY_VALID if not failures else INTEGRITY_INVALID
    return _result(integrity, failures, evidence, receipt_resolution, runtime)


def _structural_failures(evidence: Mapping[str, object]) -> list[str]:
    failures: list[str] = []
    if evidence.get("evidence_type") != EVIDENCE_TYPE or evidence.get("version") != EVIDENCE_VERSION:
        failures.append("unsupported_evidence_profile")
    if evidence.get("canonicalization") != "agent-memory-canonical-json-v1":
        failures.append("unsupported_canonicalization")

    issuer = evidence.get("issuer")
    auth = evidence.get("authentication")
    governance = evidence.get("governance")
    scope = evidence.get("scope")
    state = evidence.get("state")
    if not all(isinstance(item, dict) for item in (issuer, auth, governance, scope, state)):
        failures.append("missing_required_object")
        return failures

    if issuer.get("algorithm") != ALGORITHM or auth.get("algorithm") != ALGORITHM:
        failures.append("unsupported_signature_algorithm")
    if issuer.get("key_id") != auth.get("key_id"):
        failures.append("key_binding_mismatch")
    if governance.get("disposition") not in GOVERNANCE_VALUES:
        failures.append("invalid_governance_disposition")
    if evidence.get("lifecycle_result") not in LIFECYCLE_VALUES:
        failures.append("invalid_lifecycle_result")

    required_strings = (
        issuer.get("id"),
        issuer.get("key_id"),
        auth.get("value"),
        evidence.get("issued_at"),
        evidence.get("action_ref"),
        evidence.get("memory_action"),
        evidence.get("canonical_receipt_ref"),
        governance.get("policy_ref"),
        governance.get("authority_state_ref"),
        governance.get("decision_time"),
        scope.get("scope_ref"),
        state.get("before_ref"),
        state.get("after_ref"),
    )
    if any(not isinstance(value, str) or not value for value in required_strings):
        failures.append("missing_required_string")

    try:
        if isinstance(evidence.get("issued_at"), str) and isinstance(governance.get("decision_time"), str):
            if _parse_time(governance["decision_time"]) > _parse_time(evidence["issued_at"]):
                failures.append("decision_after_issuance")
    except ValueError:
        failures.append("invalid_evidence_timestamp")

    receipt_ref = evidence.get("canonical_receipt_ref")
    if isinstance(receipt_ref, str):
        digest = receipt_ref.removeprefix("sha256:")
        if not receipt_ref.startswith("sha256:") or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            failures.append("invalid_canonical_receipt_ref")

    return failures


def _cross_domain(scope: Mapping[str, object]) -> bool:
    source = scope.get("source_domain_ref")
    destination = scope.get("destination_domain_ref")
    return (
        isinstance(source, str)
        and isinstance(destination, str)
        and bool(source)
        and bool(destination)
        and source != destination
    )


def _result(
    integrity: str,
    failures: list[str],
    evidence: Mapping[str, object],
    receipt_resolution: str,
    runtime: RuntimeObservation,
) -> dict:
    governance = evidence.get("governance") if isinstance(evidence.get("governance"), dict) else {}
    scope = evidence.get("scope") if isinstance(evidence.get("scope"), dict) else {}
    disposition = governance.get("disposition", "unverifiable")
    lifecycle = evidence.get("lifecycle_result", "unverifiable")
    cross_domain = _cross_domain(scope)
    signed_domain_state = scope.get("domain_authorization_state_ref")

    if runtime.action_ref is None:
        execution = "not_executed"
    elif "wrong_action_ref" in failures:
        execution = "execution_mismatch"
    elif disposition in {"denied", "deferred", "review_required"}:
        execution = "unauthorized_execution"
    elif runtime.authority_valid_at_execution is False:
        execution = "unauthorized_execution"
    elif cross_domain and runtime.domain_authorization_valid_at_execution is False:
        execution = "unauthorized_execution"
    elif runtime.authority_valid_at_execution is None:
        execution = "unverifiable"
    elif cross_domain and (
        not isinstance(signed_domain_state, str)
        or not signed_domain_state
        or runtime.domain_authorization_state_ref is None
        or runtime.domain_authorization_valid_at_execution is None
    ):
        # A boundary-crossing action needs execution-time membership/authorization
        # continuity. Absence of that evidence never becomes optimistic permission.
        execution = "unverifiable"
    elif integrity == INTEGRITY_VALID:
        execution = "executed_as_authorized"
    else:
        execution = "unverifiable"

    return {
        "evidence_integrity": integrity,
        "binding_failures": failures,
        "receipt_resolution": receipt_resolution,
        "governance_disposition": disposition,
        "runtime_execution": execution,
        "lifecycle_satisfaction": lifecycle,
    }
