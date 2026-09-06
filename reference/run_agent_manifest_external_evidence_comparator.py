#!/usr/bin/env python
"""Run the real pinned Agent Manifest inbound evidence comparator for #223.

The pinned version is AGENT_MANIFEST_SDK_VERSION; it is not duplicated here.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from agent_manifest import (
    RevocationRecord,
    RevocationStore,
    VerificationContext,
    generate_ed25519,
    sign_manifest_cose,
    verify_manifest,
)

from agentmem_ref import policy
from agentmem_ref.agent_manifest_external_evidence import (
    AGENT_MANIFEST_RELEASE,
    AGENT_MANIFEST_VERSION,
    normalize_agent_manifest_evidence,
)
from agentmem_ref.agent_manifest_correlation import AGENT_MANIFEST_SDK_VERSION


SYSTEM_PROMPT_HASH = "sha256:" + "a" * 64
POLICY_BUNDLE_HASH = "sha256:" + "b" * 64
TOOL_CATALOG_HASH = "sha256:" + "c" * 64
MEMORY_BASELINE_HASH = "sha256:" + "d" * 64
MODEL_VERSION = "fixture-model-v1"
MANIFEST_ID = "018f4a3b-2c1d-7e5f-a8b9-0d1e2f3a4b5c"
AGENT_ID = "spiffe://trust.example/agent/memory/prod"
ISSUER_ID = "spiffe://trust.example/issuer/security"


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _manifest(now: datetime, *, expired: bool = False, version: str = "0.2") -> dict:
    if expired:
        issued = now - timedelta(days=2)
        expires = now - timedelta(days=1)
    else:
        issued = now - timedelta(minutes=1)
        expires = now + timedelta(days=30)
    return {
        "manifest_id": MANIFEST_ID,
        "agent_id": AGENT_ID,
        "issuer": ISSUER_ID,
        "version": version,
        "issued_at": _iso(issued),
        "expires_at": _iso(expires),
        "crypto_profile": "standard",
        "artifacts": {
            "system_prompt": {"hash": SYSTEM_PROMPT_HASH},
            "policy_bundle": {"hash": POLICY_BUNDLE_HASH},
            "tool_manifest": {"catalog_hash": TOOL_CATALOG_HASH},
            "model_identity": {
                "model_hash": None,
                "version": MODEL_VERSION,
                "deployment_type": "api",
            },
            "memory_baseline": {
                "snapshot_hash": MEMORY_BASELINE_HASH,
            },
        },
    }


def _context(keypair, *, memory_hash: str = MEMORY_BASELINE_HASH, trusted: bool = True) -> VerificationContext:
    return VerificationContext(
        system_prompt_hash=SYSTEM_PROMPT_HASH,
        policy_bundle_hash=POLICY_BUNDLE_HASH,
        tool_catalog_hash=TOOL_CATALOG_HASH,
        model_version=MODEL_VERSION,
        memory_snapshot_hash=memory_hash,
        trusted_keys={keypair.key_id: keypair.public_b64url()} if trusted else {},
        strict_artifact_verification=True,
    )


def _result_dict(result) -> dict:
    return result.model_dump(mode="json")


def _digest(envelope: bytes) -> str:
    return "sha256:" + hashlib.sha256(envelope).hexdigest()


def _pama_checks(evidence_refs: tuple[str, ...]) -> tuple[dict, dict]:
    low = policy.evaluate(
        policy.Proposal(
            proposal_id="proposal:manifest-low-read",
            actor_id="agent:manifest-fixture",
            charter_version="v1",
            target_reference="memory:manifest-low",
            target_class=policy.M0,
            scope="scope:project-a",
            operation="runtime_assembly",
            current_strength="transient",
            proposed_strength="transient",
            downstream_authority=policy.A0,
            reversibility="reversible",
            risk_class="low",
            evidence_refs=evidence_refs,
        )
    )
    high = policy.evaluate(
        policy.Proposal(
            proposal_id="proposal:manifest-critical-scope-expansion",
            actor_id="agent:manifest-fixture",
            charter_version="v1",
            target_reference="memory:manifest-high",
            target_class=policy.M5,
            scope="scope:project-a",
            operation="scope_expansion",
            current_strength="project",
            proposed_strength="cross_tenant",
            downstream_authority=policy.A5,
            reversibility="irreversible",
            risk_class="critical",
            evidence_refs=evidence_refs,
        )
    )
    return (
        {
            "outcome": low.outcome,
            "permitted_actions": list(low.permitted_actions),
            "prohibited_actions": list(low.prohibited_actions),
            "reasons": list(low.reasons),
        },
        {
            "outcome": high.outcome,
            "permitted_actions": list(high.permitted_actions),
            "prohibited_actions": list(high.prohibited_actions),
            "reasons": list(high.reasons),
        },
    )


def run(agent_memory_commit: str) -> dict:
    package_version = importlib.metadata.version("agent-manifest")
    if package_version != AGENT_MANIFEST_SDK_VERSION:
        raise RuntimeError(
            f"expected agent-manifest=={AGENT_MANIFEST_SDK_VERSION}, got {package_version}"
        )

    now = datetime.now(timezone.utc).replace(microsecond=0)
    observed_at = _iso(now)
    keypair = generate_ed25519()
    manifest = _manifest(now)
    envelope = sign_manifest_cose(manifest, keypair)
    envelope_digest = _digest(envelope)

    valid_result = verify_manifest(envelope, _context(keypair), RevocationStore())
    valid_dict = _result_dict(valid_result)
    normalized = normalize_agent_manifest_evidence(
        manifest,
        valid_dict,
        observed_at=observed_at,
        envelope_digest=envelope_digest,
        signer_id=keypair.key_id,
    )
    identity, configuration, attestation = normalized

    mismatch_result = verify_manifest(
        envelope,
        _context(keypair, memory_hash="sha256:" + "0" * 64),
        RevocationStore(),
    )
    mismatch_normalized = normalize_agent_manifest_evidence(
        manifest,
        _result_dict(mismatch_result),
        observed_at=observed_at,
        envelope_digest=envelope_digest,
        signer_id=keypair.key_id,
    )

    untrusted_result = verify_manifest(envelope, _context(keypair, trusted=False), RevocationStore())
    untrusted_normalized = normalize_agent_manifest_evidence(
        manifest,
        _result_dict(untrusted_result),
        observed_at=observed_at,
        envelope_digest=envelope_digest,
        signer_id=keypair.key_id,
    )

    tampered = bytearray(envelope)
    tampered[-1] ^= 0x01
    tampered_result = verify_manifest(bytes(tampered), _context(keypair), RevocationStore())

    expired_manifest = _manifest(now, expired=True)
    expired_envelope = sign_manifest_cose(expired_manifest, keypair)
    expired_result = verify_manifest(expired_envelope, _context(keypair), RevocationStore())
    expired_normalized = normalize_agent_manifest_evidence(
        expired_manifest,
        _result_dict(expired_result),
        observed_at=observed_at,
        envelope_digest=_digest(expired_envelope),
        signer_id=keypair.key_id,
    )

    revocations = RevocationStore()
    revocations.revoke(
        RevocationRecord(
            manifest_id=MANIFEST_ID,
            revoked_at=now,
            reason="fixture revocation",
            revoked_by="security@example.test",
        )
    )
    revoked_result = verify_manifest(envelope, _context(keypair), revocations)
    revoked_normalized = normalize_agent_manifest_evidence(
        manifest,
        _result_dict(revoked_result),
        observed_at=observed_at,
        envelope_digest=envelope_digest,
        signer_id=keypair.key_id,
    )

    unsupported_manifest = _manifest(now, version="9.9")
    unsupported_result = verify_manifest(unsupported_manifest, _context(keypair), RevocationStore())

    low_pama, high_pama = _pama_checks((identity["evidence_id"], configuration["evidence_id"]))

    raw_render = json.dumps(normalized, sort_keys=True)
    checks = {
        "exact_agent_manifest_package": package_version == AGENT_MANIFEST_SDK_VERSION,
        "exact_source_release_pin_recorded": AGENT_MANIFEST_RELEASE == "9d26ac84461e829dba8ff97ca35748eeb874debe",
        "cose_manifest_valid": valid_dict["result"] == "VALID" and valid_dict["signature_verified"] is True,
        "identity_evidence_applicable": identity["applicability"]["status"] == "applicable",
        "configuration_evidence_applicable": configuration["applicability"]["status"] == "applicable",
        "hardware_attestation_not_inherited": (
            valid_dict["attestation_verified"] is False
            and attestation["applicability"]["status"] == "insufficient_evidence"
            and attestation["claim"]["attestation_mode"] == "not_established"
        ),
        "memory_baseline_mismatch_invalidates_configuration_not_identity": (
            mismatch_normalized[0]["applicability"]["status"] == "applicable"
            and mismatch_normalized[1]["applicability"]["status"] == "invalid"
        ),
        "untrusted_key_never_creates_applicable_identity": untrusted_normalized[0]["applicability"]["status"] != "applicable",
        "tampered_cose_not_valid": _result_dict(tampered_result)["result"] != "VALID",
        "expired_manifest_stale": (
            _result_dict(expired_result)["result"] == "EXPIRED"
            and expired_normalized[0]["applicability"]["status"] == "stale"
        ),
        "revoked_manifest_stale": (
            _result_dict(revoked_result)["result"] == "REVOKED"
            and revoked_normalized[0]["applicability"]["status"] == "stale"
        ),
        "unsupported_manifest_not_valid": _result_dict(unsupported_result)["result"] != "VALID",
        "same_valid_manifest_does_not_widen_pama": (
            valid_dict["result"] == "VALID"
            and low_pama["outcome"] == "allow_with_ledger"
            and high_pama["outcome"] == "block"
            and "scope_expansion" in high_pama["prohibited_actions"]
        ),
        "raw_artifacts_not_normalized": (
            "system prompt content" not in raw_render.lower()
            and "tool schema" not in raw_render.lower()
            and "memory contents" not in raw_render.lower()
        ),
        "normalized_authority_remains_none": all(
            record["interpretation"]["authority_effect"] == "none" for record in normalized
        ),
    }

    return {
        "case_id": "agent-manifest-v0.11.0-external-evidence",
        "passed": all(checks.values()),
        "agent_memory_commit": agent_memory_commit,
        "peer": {
            "package": AGENT_MANIFEST_VERSION,
            "source_release_ref": AGENT_MANIFEST_RELEASE,
            "manifest_version": "0.2",
            "envelope": "COSE_Sign1/Ed25519",
        },
        "checks": checks,
        "observed": {
            "valid_result": valid_dict,
            "mismatch_result": _result_dict(mismatch_result),
            "untrusted_result": _result_dict(untrusted_result),
            "tampered_result": _result_dict(tampered_result),
            "expired_result": _result_dict(expired_result),
            "revoked_result": _result_dict(revoked_result),
            "unsupported_result": _result_dict(unsupported_result),
            "identity_evidence_id": identity["evidence_id"],
            "configuration_evidence_id": configuration["evidence_id"],
            "attestation_evidence_id": attestation["evidence_id"],
            "attestation_applicability": attestation["applicability"],
            "pama_low_risk": low_pama,
            "pama_high_risk": high_pama,
        },
        "interpretation": {
            "agent_manifest_valid_means": "signed identity/configuration evidence within verified bindings",
            "action_authority": "not_established",
            "execution_evidence": "not_established",
            "hardware_attestation": "not_established_without_verified_attestation",
            "memory_baseline": "bound_snapshot_evidence_not_canonical_or_current_agent_memory",
            "hitl_record": "not_agent_memory_approval_without_separate_binding",
            "delegation_chain": "not_reusable_agent_memory_authority_without_separate_governed_transition",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run(args.agent_memory_commit)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise SystemExit("Agent Manifest comparator failed")


if __name__ == "__main__":
    main()
