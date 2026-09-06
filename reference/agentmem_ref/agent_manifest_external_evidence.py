"""Agent Manifest v0.11.0 adapter into Agent Memory's generic external-evidence seam.

One signed manifest can establish several different facts with different evidence
strength. This adapter keeps three of them separate:

1. signed agent identity / manifest identity;
2. deployment/runtime artifact configuration binding;
3. hardware/runtime attestation posture.

A valid manifest, matching tool catalog, HITL record, delegation chain, or memory
baseline never becomes Agent Memory action authority merely because the peer
verifier accepts it.
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

import rfc8785

from .external_evidence import (
    EvidenceContext,
    REVOCATION_NOT_REVOKED,
    REVOCATION_REVOKED,
    VERIFIED,
    VERIFICATION_FAILED,
    VERIFICATION_UNKNOWN,
    normalize_external_evidence,
)

AGENT_MANIFEST_PEER = "Agent Manifest"
AGENT_MANIFEST_VERSION = "agent-manifest==0.11.2"
AGENT_MANIFEST_RELEASE = "9d26ac84461e829dba8ff97ca35748eeb874debe"
AGENT_MANIFEST_VERIFIER_ID = "agent_manifest.verify_manifest==0.11.0"
ADAPTER_ID = "agent-memory-agent-manifest-external-evidence"
ADAPTER_VERSION = "0.1.0"

_VALID = "VALID"
_MISMATCH = "MISMATCH"
_EXPIRED = "EXPIRED"
_REVOKED = "REVOKED"
_INCOMPATIBLE = "INCOMPATIBLE_VERSION"
_SIGNATURE_MISSING = "SIGNATURE_MISSING"
_UNVERIFIABLE = "UNVERIFIABLE"
_ATTESTATION_UNAVAILABLE = "ATTESTATION_UNAVAILABLE"

_MATCH = "MATCH"
_FIELD_EXPIRED = "EXPIRED"
_FIELD_MISMATCH = "MISMATCH"

_CONFIGURATION_FIELDS = (
    "system_prompt",
    "policy_bundle",
    "tool_manifest",
    "model_identity",
    "rag_corpus",
    "memory_baseline",
    "decision_trace",
    "supply_chain",
)


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _sha256_jcs(document: Mapping[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(dict(document))).hexdigest()


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"Agent Manifest requires non-empty {field}")
    return value


def _enum_string(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _verification_projection(result: Mapping[str, Any]) -> tuple[str, bool, bool, Mapping[str, Any]]:
    overall = _enum_string(result.get("result", ""))
    signature_verified = bool(result.get("signature_verified", False))
    attestation_verified = bool(result.get("attestation_verified", False))
    fields = result.get("fields_verified", {})
    if not isinstance(fields, Mapping):
        raise ValueError("Agent Manifest verifier result requires fields_verified")
    return overall, signature_verified, attestation_verified, fields


def _identity_verification_status(result: Mapping[str, Any]) -> str:
    overall, signature_verified, _, _ = _verification_projection(result)
    if signature_verified:
        return VERIFIED
    if overall in {_MISMATCH, _INCOMPATIBLE, _SIGNATURE_MISSING}:
        return VERIFICATION_FAILED
    return VERIFICATION_UNKNOWN


def _configuration_verification_status(
    manifest: Mapping[str, Any], result: Mapping[str, Any]
) -> str:
    overall, signature_verified, _, fields = _verification_projection(result)
    if not signature_verified:
        if overall in {_MISMATCH, _INCOMPATIBLE, _SIGNATURE_MISSING}:
            return VERIFICATION_FAILED
        return VERIFICATION_UNKNOWN

    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        raise ValueError("Agent Manifest artifacts must be an object")

    for field in _CONFIGURATION_FIELDS:
        if field not in artifacts:
            continue
        status = _enum_string(fields.get(field, ""))
        if status in {_FIELD_MISMATCH, _FIELD_EXPIRED}:
            return VERIFICATION_FAILED
        if status != _MATCH:
            return VERIFICATION_UNKNOWN
    return VERIFIED


def _attestation_verification_status(result: Mapping[str, Any]) -> str:
    overall, _, attestation_verified, _ = _verification_projection(result)
    if attestation_verified:
        return VERIFIED
    if overall == _ATTESTATION_UNAVAILABLE:
        return VERIFICATION_UNKNOWN
    return VERIFICATION_UNKNOWN


def _revocation_status(result: Mapping[str, Any]) -> str:
    overall, _, _, _ = _verification_projection(result)
    return REVOCATION_REVOKED if overall == _REVOKED else REVOCATION_NOT_REVOKED


def _artifact_refs(manifest: Mapping[str, Any]) -> list[str]:
    artifacts = manifest.get("artifacts", {})
    if not isinstance(artifacts, Mapping):
        raise ValueError("Agent Manifest artifacts must be an object")

    refs: list[str] = []
    mappings = (
        ("system_prompt", "hash", "agent-manifest:system-prompt"),
        ("policy_bundle", "hash", "agent-manifest:policy-bundle"),
        ("tool_manifest", "catalog_hash", "agent-manifest:tool-catalog"),
        ("rag_corpus", "merkle_root", "agent-manifest:rag-corpus"),
        ("memory_baseline", "snapshot_hash", "agent-manifest:memory-baseline"),
        ("decision_trace", "audit_chain_root", "agent-manifest:decision-trace"),
        ("supply_chain", "container_image_digest", "agent-manifest:container-image"),
    )
    for artifact_name, field, prefix in mappings:
        artifact = artifacts.get(artifact_name)
        if isinstance(artifact, Mapping):
            value = artifact.get(field)
            if isinstance(value, str) and value:
                refs.append(f"{prefix}:{value}")

    model = artifacts.get("model_identity")
    if isinstance(model, Mapping):
        version = model.get("version")
        provider = model.get("provider")
        model_id = model.get("model_id")
        if isinstance(version, str) and version:
            identity = ":".join(
                str(part) for part in (provider, model_id, version) if isinstance(part, str) and part
            )
            refs.append(f"agent-manifest:model:{identity or version}")
    return sorted(set(refs))


def _configuration_ref(manifest: Mapping[str, Any]) -> str:
    refs = _artifact_refs(manifest)
    payload = {"artifact_refs": refs}
    return "agent-manifest:configuration:" + _sha256_jcs(payload)


def _common_adapter_fields(
    manifest: Mapping[str, Any],
    result: Mapping[str, Any],
    *,
    envelope_digest: str | None,
    signer_id: str | None,
) -> dict[str, Any]:
    manifest_id = _string(manifest.get("manifest_id"), "manifest_id")
    agent_id = _string(manifest.get("agent_id"), "agent_id")
    issued_at = _string(manifest.get("issued_at"), "issued_at")
    expires_at = manifest.get("expires_at")
    if expires_at is not None:
        expires_at = _string(expires_at, "expires_at")

    result_id = result.get("verification_id")
    if not isinstance(result_id, str) or not result_id:
        result_id = "unidentified-verification"

    evidence_refs = [
        f"agent-manifest:manifest:{manifest_id}",
        f"agent-manifest:verification:{result_id}",
        *_artifact_refs(manifest),
    ]
    if envelope_digest:
        evidence_refs.append(f"agent-manifest:cose:{envelope_digest}")

    fields: dict[str, Any] = {
        "parse_status": "parsed",
        "source_peer": AGENT_MANIFEST_PEER,
        "source_version": AGENT_MANIFEST_VERSION,
        "source_release_ref": AGENT_MANIFEST_RELEASE,
        "record_ref": f"agent-manifest:{manifest_id}:{result_id}",
        "evidence_digest": envelope_digest or _sha256_jcs(manifest),
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "issuer_id": str(manifest.get("issuer") or agent_id),
        "verifier_id": AGENT_MANIFEST_VERIFIER_ID,
        "verification_method": "agent_manifest.verify_manifest",
        "claim_scope": f"agent-manifest:{manifest_id}",
        "subject_ref": agent_id,
        "issued_at": issued_at,
        "revocation_status": _revocation_status(result),
        "evidence_refs": sorted(set(evidence_refs)),
    }
    if signer_id:
        fields["signer_id"] = signer_id
    if expires_at:
        fields["expires_at"] = expires_at
    if fields["revocation_status"] == REVOCATION_REVOKED:
        fields["revocation_evidence_ref"] = f"agent-manifest:revocation:{manifest_id}"
    return fields


def build_agent_manifest_adapter_results(
    manifest: Mapping[str, Any],
    verifier_result: Mapping[str, Any],
    *,
    envelope_digest: str | None = None,
    signer_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Build separate identity, configuration, and attestation evidence records."""
    common = _common_adapter_fields(
        manifest,
        verifier_result,
        envelope_digest=envelope_digest,
        signer_id=signer_id,
    )
    overall, _, attestation_verified, _ = _verification_projection(verifier_result)

    identity = {
        **common,
        "verification_status": _identity_verification_status(verifier_result),
        "claim_type": "identity",
        "configuration_ref": _configuration_ref(manifest),
        "limitations": [
            "signed_manifest_identity_is_not_action_authority",
            "manifest_validity_is_not_execution_evidence",
            "agent_identity_is_not_memory_lifecycle_satisfaction",
            f"agent_manifest_overall_result:{overall}",
        ],
    }

    configuration = {
        **common,
        "verification_status": _configuration_verification_status(manifest, verifier_result),
        "claim_type": "runtime_configuration",
        "configuration_ref": _configuration_ref(manifest),
        "limitations": [
            "matching_tool_catalog_does_not_authorize_a_specific_invocation",
            "memory_baseline_digest_is_not_canonical_or_current_agent_memory",
            "manifest_hitl_record_is_not_agent_memory_approval",
            "manifest_delegation_chain_is_not_reusable_agent_memory_authority",
            "configuration_match_is_not_execution_evidence",
            f"agent_manifest_overall_result:{overall}",
        ],
    }

    attestation = {
        **common,
        "verification_status": _attestation_verification_status(verifier_result),
        "claim_type": "attestation",
        "attestation_mode": "hardware_verified" if attestation_verified else "not_established",
        "limitations": [
            "runtime_attestation_does_not_create_agent_memory_authority",
            "runtime_attestation_does_not_establish_semantic_correctness",
            "hardware_attestation_not_established" if not attestation_verified else "hardware_attestation_scope_remains_bounded",
            f"agent_manifest_overall_result:{overall}",
        ],
    }
    return identity, configuration, attestation


def normalize_agent_manifest_evidence(
    manifest: Mapping[str, Any],
    verifier_result: Mapping[str, Any],
    *,
    observed_at: str,
    envelope_digest: str | None = None,
    signer_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Normalize Agent Manifest evidence against its exact manifest identity scope."""
    identity_adapter, configuration_adapter, attestation_adapter = build_agent_manifest_adapter_results(
        manifest,
        verifier_result,
        envelope_digest=envelope_digest,
        signer_id=signer_id,
    )
    context = EvidenceContext(
        subject_ref=identity_adapter["subject_ref"],
        scope=identity_adapter["claim_scope"],
    )
    return tuple(
        normalize_external_evidence(adapter, context=context, observed_at=observed_at)
        for adapter in (identity_adapter, configuration_adapter, attestation_adapter)
    )
