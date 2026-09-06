"""External trust evidence for temporal signer attestations (#265).

This module deliberately separates possession of a signing key from evidence that
an exact public key is trusted for a logical signer key reference. Neither claim
creates Agent Memory currentness or PAMA authority.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Mapping

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from ..core import receipts
from .temporal_commitment import verify_temporal_attestation

AUTHORITY_EFFECT = "none"
TRUST_PROFILE = "agent-memory/temporal-signer-trust"
_TRUST_VALUES = {"trusted", "untrusted", "revoked", "unknown"}
_VERIFICATION_VALUES = {"verified", "invalid", "unknown"}


def _parse_time(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _required(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def public_key_digest(public_key: Ed25519PublicKey) -> str:
    """Return an exact digest for the raw Ed25519 public-key material."""
    if not isinstance(public_key, Ed25519PublicKey):
        raise ValueError("public_key must be Ed25519PublicKey")
    raw = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def build_signer_trust_evidence(
    *,
    key_ref: str,
    public_key: Ed25519PublicKey,
    trust_status: str,
    verification_status: str,
    trust_source_ref: str,
    verified_at: str,
    evidence_refs: list[str] | tuple[str, ...],
    valid_from: str | None = None,
    valid_to: str | None = None,
) -> dict[str, Any]:
    """Build trust evidence bound to both logical key identity and key material."""
    key_ref = _required(key_ref, "key_ref")
    trust_source_ref = _required(trust_source_ref, "trust_source_ref")
    if trust_status not in _TRUST_VALUES:
        raise ValueError(f"unsupported trust_status: {trust_status}")
    if verification_status not in _VERIFICATION_VALUES:
        raise ValueError(f"unsupported verification_status: {verification_status}")
    _parse_time(verified_at, "verified_at")
    if valid_from is not None:
        _parse_time(valid_from, "valid_from")
    if valid_to is not None:
        _parse_time(valid_to, "valid_to")
    if valid_from is not None and valid_to is not None:
        if _parse_time(valid_from, "valid_from") > _parse_time(valid_to, "valid_to"):
            raise ValueError("valid_from cannot be after valid_to")

    refs = list(dict.fromkeys(evidence_refs))
    if not all(isinstance(item, str) and item for item in refs):
        raise ValueError("evidence_refs must contain non-empty strings")
    if verification_status == "verified" and not refs:
        raise ValueError("verified signer trust requires evidence_refs")

    evidence = {
        "schema_version": "1.0.0",
        "profile_id": TRUST_PROFILE,
        "key_ref": key_ref,
        "public_key_digest": public_key_digest(public_key),
        "trust_status": trust_status,
        "verification_status": verification_status,
        "trust_source_ref": trust_source_ref,
        "verified_at": verified_at,
        "evidence_refs": refs,
        "valid_from": valid_from,
        "valid_to": valid_to,
        "interpretation": {
            "authority_effect": AUTHORITY_EFFECT,
            "currentness": "not_established",
            "trusted_time": "not_established",
            "event_truth": "not_established",
        },
    }
    receipts.validate("temporal-signer-trust.schema.json", evidence)
    return evidence


def evaluate_attestation_trust(
    attestation: Mapping[str, Any],
    *,
    public_key: Ed25519PublicKey,
    trust_evidence: Mapping[str, Any],
    evaluated_at: str,
) -> dict[str, Any]:
    """Combine key-possession verification with separately verified trust evidence."""
    now = _parse_time(evaluated_at, "evaluated_at")
    evidence = dict(trust_evidence)
    receipts.validate("temporal-signer-trust.schema.json", evidence)

    possession = verify_temporal_attestation(
        attestation,
        public_key=public_key,
        trust_status="unknown",
    )
    signer = attestation.get("signer", {})
    key_ref_matches = signer.get("key_ref") == evidence["key_ref"]
    key_material_matches = public_key_digest(public_key) == evidence["public_key_digest"]

    within_validity = True
    if evidence.get("valid_from") is not None:
        within_validity = within_validity and now >= _parse_time(evidence["valid_from"], "valid_from")
    if evidence.get("valid_to") is not None:
        within_validity = within_validity and now <= _parse_time(evidence["valid_to"], "valid_to")

    evidence_verified = evidence["verification_status"] == "verified"
    trusted_status = evidence["trust_status"] == "trusted"
    trusted_signer = all(
        [
            possession["cryptographic_status"] == "valid",
            key_ref_matches,
            key_material_matches,
            evidence_verified,
            trusted_status,
            within_validity,
        ]
    )

    reasons: list[str] = []
    if possession["cryptographic_status"] != "valid":
        reasons.append("attestation_invalid")
    if not key_ref_matches:
        reasons.append("key_ref_mismatch")
    if not key_material_matches:
        reasons.append("public_key_mismatch")
    if not evidence_verified:
        reasons.append("trust_evidence_not_verified")
    if not trusted_status:
        reasons.append(f"trust_status_{evidence['trust_status']}")
    if not within_validity:
        reasons.append("trust_evidence_outside_validity")

    return {
        "trusted_signer": trusted_signer,
        "key_possession_status": possession["cryptographic_status"],
        "key_ref_matches": key_ref_matches,
        "key_material_matches": key_material_matches,
        "trust_evidence_status": evidence["verification_status"],
        "trust_status": evidence["trust_status"],
        "within_validity": within_validity,
        "reason_codes": reasons,
        "authority_effect": AUTHORITY_EFFECT,
        "currentness": "not_established",
        "trusted_time": "not_established",
        "event_truth": "not_established",
    }
