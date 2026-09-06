"""Cryptographically bound temporal commitment reference for #259 / ADR-031.

The module keeps exact content identity, signer attestation, relative ordering,
external witness evidence, currentness, and authority as separate claims.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

import rfc8785
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from . import receipts

TEMPORAL_PROFILE = "agent-memory/temporal-commitment"
TEMPORAL_VERSION = "1.0.0"
ATTESTATION_PROFILE = "agent-memory/temporal-commitment-attestation"
ATTESTATION_VERSION = "1.0.0"
UOR_CONTENT_REFERENCE_PROFILE = "agent-memory/uor-addr-json-content-reference"
SIGNATURE_ALGORITHM = "Ed25519"
AUTHORITY_EFFECT = "none"
_LABEL_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TRUST_VALUES = {"trusted", "untrusted", "revoked", "unknown"}
_CURRENTNESS_VALUES = {"current", "superseded", "revoked", "disputed", "unknown"}
AddressFunction = Callable[[bytes], str]


def _parse_time(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("timestamp must be a non-empty string")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _validate_digest(value: str, field: str) -> str:
    if not isinstance(value, str) or not _LABEL_RE.fullmatch(value):
        raise ValueError(f"{field} must be lowercase sha256:<64hex>")
    return value


def _refs(value: Any, field: str, *, digests: bool = False) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be an array")
    result = list(dict.fromkeys(value))
    if not all(isinstance(item, str) and item for item in result):
        raise ValueError(f"{field} must contain only non-empty strings")
    if digests:
        for item in result:
            _validate_digest(item, field)
    return result


def canonical_json(value: Any) -> bytes:
    """RFC 8785 canonical bytes for Agent Memory temporal evidence."""
    return rfc8785.dumps(value)


def document_ref(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value)).hexdigest()


def build_temporal_commitment(
    *,
    event_type: str,
    subject_ref: str,
    payload_digest: str,
    temporal_claims: Mapping[str, Any],
    scope_ref: str,
    domain_schema_ref: str,
    domain_schema_digest: str,
    ordering_mode: str = "none",
    stream_ref: str | None = None,
    sequence: int | None = None,
    predecessor_reference_profile: str | None = None,
    predecessor_refs: tuple[str, ...] | list[str] = (),
    projection_profile: str | None = None,
    projection_version: str | None = None,
) -> dict[str, Any]:
    """Build a schema-valid temporal commitment before content addressing."""
    if not event_type or not subject_ref or not scope_ref or not domain_schema_ref:
        raise ValueError("event_type, subject_ref, scope_ref, and domain_schema_ref are required")
    _validate_digest(payload_digest, "payload_digest")
    _validate_digest(domain_schema_digest, "domain_schema_digest")

    claims = dict(temporal_claims)
    if not claims or not any(value is not None for value in claims.values()):
        raise ValueError("at least one non-null temporal claim is required")
    allowed_claims = {"event_time", "observed_at", "valid_from", "valid_to"}
    unknown = sorted(set(claims) - allowed_claims)
    if unknown:
        raise ValueError(f"unsupported temporal claims: {unknown}")
    for value in claims.values():
        if value is not None:
            _parse_time(value)
    if claims.get("valid_from") is not None and claims.get("valid_to") is not None:
        if _parse_time(claims["valid_from"]) > _parse_time(claims["valid_to"]):
            raise ValueError("valid_from cannot be after valid_to")

    predecessors = _refs(predecessor_refs, "predecessor_refs", digests=True)

    if ordering_mode == "none":
        if stream_ref is not None or sequence is not None or predecessor_reference_profile is not None or predecessors:
            raise ValueError("ordering mode none cannot carry stream, sequence, reference profile, or predecessors")
    elif ordering_mode == "linear_stream":
        _required_string(stream_ref, "stream_ref")
        _required_string(predecessor_reference_profile, "predecessor_reference_profile")
        if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
            raise ValueError("linear_stream requires a non-negative integer sequence")
        if sequence == 0 and predecessors:
            raise ValueError("linear_stream root cannot have a predecessor")
        if sequence > 0 and len(predecessors) != 1:
            raise ValueError("linear_stream sequence > 0 requires exactly one predecessor")
    else:
        raise ValueError(f"unsupported ordering mode: {ordering_mode}")

    commitment = {
        "schema_version": "1.0.0",
        "profile_id": TEMPORAL_PROFILE,
        "profile_version": TEMPORAL_VERSION,
        "event": {
            "event_type": event_type,
            "subject_ref": subject_ref,
            "payload_digest": payload_digest,
        },
        "temporal_claims": claims,
        "ordering": {
            "mode": ordering_mode,
            "stream_ref": stream_ref,
            "sequence": sequence,
            "predecessor_reference_profile": predecessor_reference_profile,
            "predecessor_refs": predecessors,
        },
        "semantics": {
            "domain_schema_ref": domain_schema_ref,
            "domain_schema_digest": domain_schema_digest,
            "projection_profile": projection_profile,
            "projection_version": projection_version,
        },
        "scope_ref": scope_ref,
    }
    receipts.validate("temporal-commitment.schema.json", commitment)
    return commitment


def address_temporal_commitment(commitment: Mapping[str, Any], *, address_fn: AddressFunction) -> str:
    """Return an exact content reference under an injected optional address profile."""
    material = dict(commitment)
    receipts.validate("temporal-commitment.schema.json", material)
    return _validate_digest(address_fn(canonical_json(material)), "content_ref")


def _attestation_transcript(
    *,
    content_ref: str,
    content_reference_profile: str,
    key_ref: str,
    algorithm: str = SIGNATURE_ALGORITHM,
) -> bytes:
    _validate_digest(content_ref, "content_ref")
    _required_string(content_reference_profile, "content_reference_profile")
    _required_string(key_ref, "key_ref")
    return canonical_json(
        {
            "domain": ATTESTATION_PROFILE,
            "version": ATTESTATION_VERSION,
            "content_reference_profile": content_reference_profile,
            "content_ref": content_ref,
            "signer_key_ref": key_ref,
            "algorithm": algorithm,
        }
    )


def sign_temporal_commitment(
    *,
    content_ref: str,
    private_key: Ed25519PrivateKey,
    key_ref: str,
    content_reference_profile: str = UOR_CONTENT_REFERENCE_PROFILE,
) -> dict[str, Any]:
    """Sign a domain-separated transcript that binds the exact content reference/profile."""
    transcript = _attestation_transcript(
        content_ref=content_ref,
        content_reference_profile=content_reference_profile,
        key_ref=key_ref,
    )
    signature = private_key.sign(transcript)
    attestation = {
        "schema_version": "1.0.0",
        "attestation_profile": ATTESTATION_PROFILE,
        "attestation_version": ATTESTATION_VERSION,
        "content_reference_profile": content_reference_profile,
        "content_ref": content_ref,
        "signer": {"key_ref": key_ref, "algorithm": SIGNATURE_ALGORITHM},
        "signature": base64.b64encode(signature).decode("ascii"),
        "interpretation": {
            "authority_effect": AUTHORITY_EFFECT,
            "trusted_time": "not_established",
            "currentness": "not_established",
            "execution_evidence": "not_established",
        },
    }
    receipts.validate("temporal-signer-attestation.schema.json", attestation)
    return attestation


def verify_temporal_attestation(
    attestation: Mapping[str, Any],
    *,
    public_key: Ed25519PublicKey,
    trust_status: str = "unknown",
) -> dict[str, Any]:
    """Verify signature integrity without laundering key trust into authority."""
    if trust_status not in _TRUST_VALUES:
        raise ValueError(f"unsupported trust_status: {trust_status}")
    material = dict(attestation)
    try:
        receipts.validate("temporal-signer-attestation.schema.json", material)
        signer = material["signer"]
        transcript = _attestation_transcript(
            content_ref=material["content_ref"],
            content_reference_profile=material["content_reference_profile"],
            key_ref=signer["key_ref"],
            algorithm=signer["algorithm"],
        )
        signature = base64.b64decode(material["signature"], validate=True)
        public_key.verify(signature, transcript)
        cryptographic_status = "valid"
        failure = None
    except (ValueError, TypeError, KeyError, binascii.Error, InvalidSignature) as exc:
        cryptographic_status = "invalid"
        failure = str(exc) or exc.__class__.__name__

    return {
        "cryptographic_status": cryptographic_status,
        "trust_status": trust_status,
        "trusted_signer": cryptographic_status == "valid" and trust_status == "trusted",
        "authority_effect": AUTHORITY_EFFECT,
        "currentness": "not_established",
        "trusted_time": "not_established",
        "event_truth": "not_established",
        "failure": failure,
    }


def build_external_witness_evidence(
    *,
    witness_profile: str,
    subject_kind: str,
    subject_reference_profile: str,
    subject_ref: str,
    claim_kind: str,
    verification_status: str,
    witnessed_at: str | None = None,
    proof_ref: str | None = None,
) -> dict[str, Any]:
    """Record already-verified external witness evidence without implementing the witness service."""
    _validate_digest(subject_ref, "subject_ref")
    _required_string(witness_profile, "witness_profile")
    _required_string(subject_reference_profile, "subject_reference_profile")
    if witnessed_at is not None:
        _parse_time(witnessed_at)
    if verification_status == "verified" and proof_ref is None:
        raise ValueError("verified witness evidence requires proof_ref")
    if verification_status == "verified" and claim_kind in {"existence_by_time", "freshness"} and witnessed_at is None:
        raise ValueError("verified time/freshness evidence requires witnessed_at")

    evidence = {
        "schema_version": "1.0.0",
        "witness_profile": witness_profile,
        "subject_kind": subject_kind,
        "subject_reference_profile": subject_reference_profile,
        "subject_ref": subject_ref,
        "claim_kind": claim_kind,
        "verification_status": verification_status,
        "witnessed_at": witnessed_at,
        "proof_ref": proof_ref,
        "interpretation": {
            "authority_effect": AUTHORITY_EFFECT,
            "event_occurrence_time_proven": False,
            "currentness": "not_established",
            "execution_evidence": "not_established",
        },
    }
    receipts.validate("temporal-external-witness.schema.json", evidence)
    return evidence


def verify_witness_binding(
    evidence: Mapping[str, Any],
    *,
    expected_subject_reference_profile: str,
    expected_subject_ref: str,
) -> dict[str, Any]:
    """Verify exact subject/profile binding, not what that subject semantically means."""
    _required_string(expected_subject_reference_profile, "expected_subject_reference_profile")
    _validate_digest(expected_subject_ref, "expected_subject_ref")
    material = dict(evidence)
    receipts.validate("temporal-external-witness.schema.json", material)
    bound = (
        material["verification_status"] == "verified"
        and material["subject_reference_profile"] == expected_subject_reference_profile
        and material["subject_ref"] == expected_subject_ref
    )
    return {
        "bound": bound,
        "verification_status": material["verification_status"],
        "claim_kind": material["claim_kind"],
        "witnessed_at": material["witnessed_at"],
        "event_occurrence_time_proven": False,
        "authority_effect": AUTHORITY_EFFECT,
    }


def evaluate_temporal_currentness(
    *,
    commitment_reference_profile: str,
    commitment_ref: str,
    status: str,
    evaluated_at: str,
    evidence_refs: tuple[str, ...] | list[str] = (),
    superseding_refs: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Emit append-only currentness evidence without altering historical commitment/signature validity."""
    _required_string(commitment_reference_profile, "commitment_reference_profile")
    _validate_digest(commitment_ref, "commitment_ref")
    if status not in _CURRENTNESS_VALUES:
        raise ValueError(f"unsupported temporal currentness status: {status}")
    _parse_time(evaluated_at)
    evidence = _refs(evidence_refs, "evidence_refs")
    superseding = _refs(superseding_refs, "superseding_refs", digests=True)
    if status in {"superseded", "revoked", "disputed"} and not evidence:
        raise ValueError(f"{status} currentness requires evidence_refs")
    if status == "superseded" and not superseding:
        raise ValueError("superseded currentness requires superseding_refs")
    if status != "superseded" and superseding:
        raise ValueError("superseding_refs are only valid for superseded status")

    body = {
        "commitment_reference_profile": commitment_reference_profile,
        "commitment_ref": commitment_ref,
        "status": status,
        "evidence_refs": evidence,
        "superseding_refs": superseding,
        "evaluated_at": evaluated_at,
        "interpretation": {
            "authority_effect": AUTHORITY_EFFECT,
            "historical_commitment_mutated": False,
            "cryptographic_validity_changed": False,
            "memory_admission": "not_established",
        },
    }
    result = {
        "schema_version": "1.0.0",
        "evaluation_id": document_ref(body),
        **body,
    }
    receipts.validate("temporal-currentness-evaluation.schema.json", result)
    return result


def evaluate_linear_order(
    commitment: Mapping[str, Any],
    *,
    predecessor_commitment: Mapping[str, Any] | None = None,
    address_fn: AddressFunction | None = None,
    address_profile: str | None = None,
) -> dict[str, Any]:
    """Evaluate a linear-stream relation while making no completeness/non-equivocation claim."""
    current = dict(commitment)
    receipts.validate("temporal-commitment.schema.json", current)
    ordering = current["ordering"]
    if ordering["mode"] != "linear_stream":
        return {
            "status": "not_applicable",
            "local_order_valid": False,
            "complete_history_proven": False,
            "non_equivocation_proven": False,
            "authority_effect": AUTHORITY_EFFECT,
            "reason": "not_linear_stream",
        }

    sequence = ordering["sequence"]
    predecessors = ordering["predecessor_refs"]
    if sequence == 0:
        return {
            "status": "valid_root",
            "local_order_valid": True,
            "complete_history_proven": False,
            "non_equivocation_proven": False,
            "authority_effect": AUTHORITY_EFFECT,
            "reason": None,
        }

    if predecessor_commitment is None or address_fn is None or address_profile is None:
        return {
            "status": "missing_predecessor_evidence",
            "local_order_valid": False,
            "complete_history_proven": False,
            "non_equivocation_proven": False,
            "authority_effect": AUTHORITY_EFFECT,
            "reason": "predecessor_evidence_required",
        }

    predecessor = dict(predecessor_commitment)
    receipts.validate("temporal-commitment.schema.json", predecessor)
    predecessor_ref = address_temporal_commitment(predecessor, address_fn=address_fn)
    expected_ref = predecessors[0]
    reasons: list[str] = []
    if address_profile != ordering["predecessor_reference_profile"]:
        reasons.append("predecessor_reference_profile_mismatch")
    if predecessor_ref != expected_ref:
        reasons.append("predecessor_reference_mismatch")
    if predecessor["scope_ref"] != current["scope_ref"]:
        reasons.append("cross_scope_predecessor")
    previous_order = predecessor["ordering"]
    if previous_order["mode"] != "linear_stream":
        reasons.append("predecessor_not_linear_stream")
    else:
        if previous_order["stream_ref"] != ordering["stream_ref"]:
            reasons.append("stream_mismatch")
        if previous_order["predecessor_reference_profile"] != ordering["predecessor_reference_profile"]:
            reasons.append("stream_reference_profile_changed")
        if previous_order["sequence"] != sequence - 1:
            reasons.append("non_contiguous_sequence")

    return {
        "status": "valid" if not reasons else "invalid",
        "local_order_valid": not reasons,
        "complete_history_proven": False,
        "non_equivocation_proven": False,
        "authority_effect": AUTHORITY_EFFECT,
        "reason": reasons[0] if reasons else None,
        "reason_codes": reasons,
    }


def detect_linear_forks(
    nodes: list[Mapping[str, Any]],
    *,
    address_fn: AddressFunction,
    content_reference_profile: str,
) -> list[dict[str, Any]]:
    """Return explicit fork evidence after verifying each content-ref/commitment binding."""
    _required_string(content_reference_profile, "content_reference_profile")
    children: dict[tuple[str, str, str], list[str]] = {}
    for node in nodes:
        content_ref = _validate_digest(node["content_ref"], "content_ref")
        commitment = dict(node["commitment"])
        receipts.validate("temporal-commitment.schema.json", commitment)
        generated_ref = address_temporal_commitment(commitment, address_fn=address_fn)
        if generated_ref != content_ref:
            raise ValueError("node content_ref does not match commitment content")
        ordering = commitment["ordering"]
        if ordering["mode"] != "linear_stream" or ordering["sequence"] == 0:
            continue
        if ordering["predecessor_reference_profile"] != content_reference_profile:
            raise ValueError("node predecessor reference profile does not match detector profile")
        key = (
            ordering["stream_ref"],
            ordering["predecessor_reference_profile"],
            ordering["predecessor_refs"][0],
        )
        children.setdefault(key, []).append(content_ref)

    forks = []
    for (stream_ref, reference_profile, predecessor_ref), child_refs in sorted(children.items()):
        unique = sorted(set(child_refs))
        if len(unique) > 1:
            forks.append(
                {
                    "stream_ref": stream_ref,
                    "predecessor_reference_profile": reference_profile,
                    "predecessor_ref": predecessor_ref,
                    "child_refs": unique,
                    "canonical_child": None,
                    "authority_effect": AUTHORITY_EFFECT,
                }
            )
    return forks
