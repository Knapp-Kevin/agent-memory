"""Vendor-neutral normalization of external trust and attestation evidence.

Issue #180 keeps four facts separate:

1. A peer payload parsed.
2. A verifier did or did not verify the peer claim.
3. The claim is or is not current and applicable to the requested context.
4. None of those facts creates Agent Memory authority by itself.

Peer-specific parsing and cryptographic verification stay outside this module. The
normalizer consumes a bounded adapter/verifier result, removes peer-only fields,
and emits a content-minimized Agent Memory evidence candidate.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping

import rfc8785

from ..core import receipts

PROFILE_VERSION = "0.1.0"
SCHEMA_VERSION = "1.0.0"

TRACE_PEER = "TRACE"
TRACE_VERSION = "agentrust-trace==0.9.0"
TRACE_RELEASE = "94271a1630601c94e80a23263d9750cb8d39f1f4"

CMCP_PEER = "cMCP"
CMCP_VERSION = "cmcp-runtime==0.4.0"
CMCP_RELEASE = "a2e95151356c9ae6c545330c900f3d4af0e447c1"

AGENT_MANIFEST_PEER = "Agent Manifest"
AGENT_MANIFEST_VERSION = "agent-manifest==0.11.2"
AGENT_MANIFEST_RELEASE = "9d26ac84461e829dba8ff97ca35748eeb874debe"

VERIFIED = "verified"
VERIFICATION_FAILED = "failed"
VERIFICATION_UNKNOWN = "unknown"
VERIFICATION_NOT_PERFORMED = "not_performed"
VERIFIER_UNAVAILABLE = "unavailable"

REVOCATION_NOT_REVOKED = "not_revoked"
REVOCATION_REVOKED = "revoked"
REVOCATION_UNKNOWN = "unknown"

FRESH_CURRENT = "current"
FRESH_EXPIRED = "expired"
FRESH_NOT_YET_VALID = "not_yet_valid"

APPLICABLE = "applicable"
MISMATCH = "mismatch"
STALE = "stale"
UNSUPPORTED = "unsupported"
INSUFFICIENT = "insufficient_evidence"
INVALID = "invalid"

SUPPORTED_CLAIM_TYPES = {
    "identity",
    "attestation",
    "runtime_configuration",
    "decision",
    "enforcement",
    "execution",
    "delegation",
}

SUPPORTED_SOURCE_TUPLES = {
    (TRACE_PEER, TRACE_VERSION, TRACE_RELEASE),
    (CMCP_PEER, CMCP_VERSION, CMCP_RELEASE),
    (AGENT_MANIFEST_PEER, AGENT_MANIFEST_VERSION, AGENT_MANIFEST_RELEASE),
}

_ALLOWED_VERIFICATION = {
    VERIFIED,
    VERIFICATION_FAILED,
    VERIFICATION_UNKNOWN,
    VERIFICATION_NOT_PERFORMED,
    VERIFIER_UNAVAILABLE,
}
_ALLOWED_REVOCATION = {
    REVOCATION_NOT_REVOKED,
    REVOCATION_REVOKED,
    REVOCATION_UNKNOWN,
}


@dataclass(frozen=True)
class EvidenceContext:
    """Current Agent Memory context against which evidence applicability is tested."""

    subject_ref: str
    scope: str
    tenant_ref: str | None = None
    resource_ref: str | None = None
    action_ref: str | None = None


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def _sha256_jcs(document: Mapping[str, object]) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(dict(document))).hexdigest()


def _require_string(record: Mapping[str, object], field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value:
        raise ValueError(f"external evidence adapter result requires non-empty {field!r}")
    return value


def _optional_string(record: Mapping[str, object], field: str) -> str | None:
    value = record.get(field)
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError(f"external evidence adapter result field {field!r} must be a non-empty string")
    return value


def _string_list(record: Mapping[str, object], field: str) -> list[str]:
    value = record.get(field, [])
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"external evidence adapter result field {field!r} must be a list of non-empty strings")
    return sorted(set(value))


def _freshness(issued_at: str, expires_at: str | None, observed_at: str) -> tuple[str, list[str]]:
    issued = _parse_time(issued_at)
    observed = _parse_time(observed_at)
    if issued > observed:
        return FRESH_NOT_YET_VALID, ["evidence_issued_in_future"]
    if expires_at is not None:
        expires = _parse_time(expires_at)
        if expires < issued:
            raise ValueError("external evidence expires_at precedes issued_at")
        if observed > expires:
            return FRESH_EXPIRED, ["evidence_expired"]
    return FRESH_CURRENT, []


def _binding_failures(record: Mapping[str, object], context: EvidenceContext) -> list[str]:
    failures: list[str] = []
    comparisons = (
        ("subject_ref", context.subject_ref, record.get("subject_ref")),
        ("scope", context.scope, record.get("claim_scope")),
        ("tenant_ref", context.tenant_ref, record.get("tenant_ref")),
        ("resource_ref", context.resource_ref, record.get("resource_ref")),
        ("action_ref", context.action_ref, record.get("action_ref")),
    )
    for field, expected, actual in comparisons:
        if expected is None:
            continue
        if actual is None:
            failures.append(f"missing_{field}_binding")
        elif actual != expected:
            failures.append(f"{field}_mismatch")
    return failures


def normalize_external_evidence(
    adapter_result: Mapping[str, object],
    *,
    context: EvidenceContext,
    observed_at: str,
) -> dict:
    """Normalize a peer adapter/verifier result without importing peer authority.

    The input is intentionally *not* a raw peer payload. A peer-specific adapter
    is responsible for parsing the peer record and for reporting verification
    state. This function never treats parsing as verification and never maps a
    verified peer claim into PAMA permission or canonical lifecycle state.
    """

    parse_status = _require_string(adapter_result, "parse_status")
    if parse_status != "parsed":
        raise ValueError("malformed/unparsed peer evidence cannot enter normalization")

    source_peer = _require_string(adapter_result, "source_peer")
    source_version = _require_string(adapter_result, "source_version")
    source_release_ref = _require_string(adapter_result, "source_release_ref")
    record_ref = _require_string(adapter_result, "record_ref")
    evidence_digest = _require_string(adapter_result, "evidence_digest")
    adapter_id = _require_string(adapter_result, "adapter_id")
    adapter_version = _require_string(adapter_result, "adapter_version")

    issuer_id = _require_string(adapter_result, "issuer_id")
    signer_id = _optional_string(adapter_result, "signer_id")
    verifier_id = _require_string(adapter_result, "verifier_id")
    verification_status = _require_string(adapter_result, "verification_status")
    if verification_status not in _ALLOWED_VERIFICATION:
        raise ValueError(f"unsupported verification_status {verification_status!r}")
    verification_method = _require_string(adapter_result, "verification_method")

    source_claim_type = _require_string(adapter_result, "claim_type")
    claim_type = source_claim_type if source_claim_type in SUPPORTED_CLAIM_TYPES else "other"
    claim_scope = _require_string(adapter_result, "claim_scope")
    subject_ref = _require_string(adapter_result, "subject_ref")

    issued_at = _require_string(adapter_result, "issued_at")
    expires_at = _optional_string(adapter_result, "expires_at")
    freshness_status, reasons = _freshness(issued_at, expires_at, observed_at)

    revocation_status = _require_string(adapter_result, "revocation_status")
    if revocation_status not in _ALLOWED_REVOCATION:
        raise ValueError(f"unsupported revocation_status {revocation_status!r}")
    revocation_evidence_ref = _optional_string(adapter_result, "revocation_evidence_ref")

    binding_failures = _binding_failures(adapter_result, context)
    reasons.extend(binding_failures)

    source_supported = (source_peer, source_version, source_release_ref) in SUPPORTED_SOURCE_TUPLES
    if not source_supported:
        reasons.append("unsupported_source_version")
    if source_claim_type not in SUPPORTED_CLAIM_TYPES:
        reasons.append("unsupported_claim_type")

    if verification_status == VERIFICATION_FAILED:
        reasons.append("verification_failed")
    elif verification_status in {VERIFICATION_UNKNOWN, VERIFICATION_NOT_PERFORMED, VERIFIER_UNAVAILABLE}:
        reasons.append(f"verification_{verification_status}")

    if revocation_status == REVOCATION_REVOKED:
        reasons.append("evidence_revoked")
    elif revocation_status == REVOCATION_UNKNOWN:
        reasons.append("revocation_unknown")

    if not source_supported or source_claim_type not in SUPPORTED_CLAIM_TYPES:
        applicability_status = UNSUPPORTED
    elif binding_failures:
        applicability_status = MISMATCH
    elif verification_status == VERIFICATION_FAILED:
        applicability_status = INVALID
    elif freshness_status != FRESH_CURRENT or revocation_status == REVOCATION_REVOKED:
        applicability_status = STALE
    elif verification_status != VERIFIED or revocation_status != REVOCATION_NOT_REVOKED:
        applicability_status = INSUFFICIENT
    else:
        applicability_status = APPLICABLE

    claim: dict[str, object] = {
        "type": claim_type,
        "source_claim_type": source_claim_type,
        "scope": claim_scope,
        "subject_ref": subject_ref,
        "limitations": _string_list(adapter_result, "limitations"),
    }
    for output_name, input_name in (
        ("tenant_ref", "tenant_ref"),
        ("resource_ref", "resource_ref"),
        ("action_ref", "action_ref"),
        ("runtime_ref", "runtime_ref"),
        ("configuration_ref", "configuration_ref"),
        ("policy_ref", "policy_ref"),
        ("decision_ref", "decision_ref"),
        ("decision_disposition", "decision_disposition"),
        ("enforcement_posture", "enforcement_posture"),
        ("execution_posture", "execution_posture"),
        ("attestation_mode", "attestation_mode"),
        ("delegation_ref", "delegation_ref"),
    ):
        value = _optional_string(adapter_result, input_name)
        if value is not None:
            claim[output_name] = value

    source = {
        "peer": source_peer,
        "version": source_version,
        "release_ref": source_release_ref,
        "record_ref": record_ref,
        "adapter_id": adapter_id,
        "adapter_version": adapter_version,
        "parse_status": parse_status,
    }
    verification = {
        "status": verification_status,
        "verifier_id": verifier_id,
        "method": verification_method,
    }
    issuer = {"id": issuer_id}
    if signer_id is not None:
        issuer["signer_id"] = signer_id

    normalized_body = {
        "schema_version": SCHEMA_VERSION,
        "profile_version": PROFILE_VERSION,
        "source": source,
        "issuer": issuer,
        "verification": verification,
        "claim": claim,
        "freshness": {
            "issued_at": issued_at,
            "observed_at": observed_at,
            "status": freshness_status,
        },
        "revocation": {
            "status": revocation_status,
        },
        "applicability": {
            "status": applicability_status,
            "reasons": sorted(set(reasons)),
        },
        "evidence_digest": evidence_digest,
        "evidence_refs": _string_list(adapter_result, "evidence_refs"),
        "interpretation": {
            "authority_effect": "none",
            "memory_authority": "not_established",
            "semantic_correctness": "not_established",
            "lifecycle_satisfaction": "not_established",
        },
    }
    if expires_at is not None:
        normalized_body["freshness"]["expires_at"] = expires_at
    if revocation_evidence_ref is not None:
        normalized_body["revocation"]["evidence_ref"] = revocation_evidence_ref

    normalized_body["evidence_id"] = "external-evidence:" + _sha256_jcs(normalized_body)
    receipts.validate("external-evidence-normalized.schema.json", normalized_body)
    return normalized_body
