#!/usr/bin/env python
"""Run a real cMCP v0.4.0 inbound external-evidence comparator."""

from __future__ import annotations

import argparse
import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from cmcp_runtime.audit.keys import SigningKey
from cmcp_runtime.audit.trace_claim import (
    AttestationReportInfo,
    CallGraphSummary,
    CallSummary,
    PolicyBundleInfo,
    ToolCatalogInfo,
    generate_trace_claim,
)
from cmcp_verify import ApprovedHashes, verify_trace_claim

from agentmem_ref.cmcp_external_evidence import normalize_cmcp_claim

CMCP_RELEASE = "v0.4.0"
CMCP_SOURCE_COMMIT = "a2e95151356c9ae6c545330c900f3d4af0e447c1"
POLICY_HASH = "sha256:" + "a" * 64
CATALOG_HASH = "sha256:" + "b" * 64
AUDIT_ROOT = "c" * 64
AUDIT_TIP = "d" * 64


def _observed_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _verification_dict(result) -> dict:
    return {
        "status": result.status.value,
        "verified_fields": list(result.verified_fields),
        "unverified_fields": list(result.unverified_fields),
        "failure_reason": result.failure_reason.value if result.failure_reason else None,
        "attestation_age_seconds": result.attestation_age_seconds,
        "is_attestation_fresh": result.is_attestation_fresh,
        "details": dict(result.details),
    }


def _claim(mode: str, *, generated_at: datetime | None = None) -> tuple[dict, SigningKey]:
    key = SigningKey()
    generated = generated_at or datetime.now(tz=UTC)
    claim = generate_trace_claim(
        session_id=f"agent-memory-{mode}",
        signing_key=key,
        attestation_report=AttestationReportInfo(
            provider="software-only",
            measurement="sha256:" + "0" * 64,
            report_data="",
            attestation_generated_at=generated.isoformat(),
            attestation_validity_seconds=3600,
        ),
        policy_bundle=PolicyBundleInfo(
            hash=POLICY_HASH,
            enforcement_mode={"enforce": "enforcing", "advisory": "advisory", "silent": "silent"}[mode],
            policy_version="cmcp-policy-v1",
        ),
        tool_catalog=ToolCatalogInfo(hash=CATALOG_HASH, drift_detected=False),
        call_summary=CallSummary(
            tool_calls_total=1,
            tool_calls_allowed=1,
            tool_calls_denied=0,
            tool_calls_faulted=0,
            tools_invoked=["memory.lookup"],
            session_max_sensitivity="internal",
            call_graph_summary=CallGraphSummary(
                compliance_domains_touched=["memory"],
                cross_boundary_events=[],
                edges_represent="temporal_adjacency",
            ),
        ),
        audit_chain_root=AUDIT_ROOT,
        audit_chain_tip=AUDIT_TIP,
        audit_chain_length=1,
    )
    return claim.model_dump(exclude_none=True), key


def _verify(claim: dict, key: SigningKey, *, approved_policy: str = POLICY_HASH, max_age: int = 3600):
    return verify_trace_claim(
        claim,
        ApprovedHashes(policy_bundle_hash=approved_policy, tool_catalog_hash=CATALOG_HASH),
        max_attestation_age_seconds=max_age,
        trusted_public_key_hex=key.public_key_hex,
    )


def run(agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40 or any(ch not in "0123456789abcdef" for ch in agent_memory_commit):
        raise ValueError("agent_memory_commit must be exact lowercase 40-hex")

    mode_cases = []
    for mode in ("enforce", "advisory", "silent"):
        claim, key = _claim(mode)
        projected = _verification_dict(_verify(claim, key))
        enforcement, attestation = normalize_cmcp_claim(
            claim, projected, observed_at=_observed_now()
        )
        checks = {
            "real_verifier_is_partial_without_hardware": projected["status"] == "partially_verified",
            "enforcement_posture_preserved": enforcement["claim"]["enforcement_posture"] == mode,
            "enforcement_integrity_applicable": enforcement["applicability"]["status"] == "applicable",
            "hardware_not_overreported": attestation["verification"]["status"] == "unknown",
            "attestation_not_applicable_as_verified": attestation["applicability"]["status"] == "insufficient_evidence",
            "authority_nonclaim": enforcement["interpretation"]["authority_effect"] == "none",
            "execution_not_claimed": "execution_posture" not in enforcement["claim"],
        }
        mode_cases.append(
            {
                "mode": mode,
                "cMCP_verification": projected,
                "enforcement": enforcement,
                "attestation": attestation,
                "checks": checks,
                "passed": all(checks.values()),
            }
        )

    stale_claim, stale_key = _claim(
        "enforce", generated_at=datetime.now(tz=UTC) - timedelta(hours=2)
    )
    stale_result = _verification_dict(_verify(stale_claim, stale_key, max_age=3600))
    stale_enforcement, stale_attestation = normalize_cmcp_claim(
        stale_claim, stale_result, observed_at=_observed_now()
    )

    mismatch_claim, mismatch_key = _claim("enforce")
    mismatch_result = _verification_dict(
        _verify(mismatch_claim, mismatch_key, approved_policy="sha256:" + "f" * 64)
    )
    mismatch_enforcement, _ = normalize_cmcp_claim(
        mismatch_claim, mismatch_result, observed_at=_observed_now()
    )

    tampered_claim, tampered_key = _claim("enforce")
    tampered = copy.deepcopy(tampered_claim)
    tampered["signature"] = "A" * max(1, len(tampered["signature"]))
    tampered_result = _verification_dict(_verify(tampered, tampered_key))
    tampered_enforcement, _ = normalize_cmcp_claim(
        tampered, tampered_result, observed_at=_observed_now()
    )

    privacy_claim, privacy_key = _claim("enforce")
    privacy_claim["gateway"]["attestation_evidence"] = {
        "raw_evidence": "c2VjcmV0LWhhcmR3YXJlLWJsb2I=",
        "quote_signature": "c2lnbmF0dXJl",
        "cert_chain": "Y2VydGlmaWNhdGUtY2hhaW4=",
    }
    from cmcp_runtime.audit.trace_claim import RuntimeClaim, sign_trace_claim
    privacy_model = RuntimeClaim.model_validate(privacy_claim)
    privacy_model.signature = sign_trace_claim(privacy_model, privacy_key)
    privacy_claim = privacy_model.model_dump(exclude_none=True)
    privacy_result = _verification_dict(_verify(privacy_claim, privacy_key))
    privacy_enforcement, privacy_attestation = normalize_cmcp_claim(
        privacy_claim, privacy_result, observed_at=_observed_now()
    )
    normalized_render = json.dumps(
        [privacy_enforcement, privacy_attestation], sort_keys=True
    )

    checks = {
        "all_enforcement_modes_real_and_distinct": all(case["passed"] for case in mode_cases),
        "stale_attestation_is_scoped_to_attestation_record": (
            stale_result["is_attestation_fresh"] is False
            and stale_enforcement["freshness"]["status"] == "current"
            and stale_enforcement["applicability"]["status"] == "applicable"
            and stale_attestation["freshness"]["status"] == "expired"
            and stale_attestation["applicability"]["status"] == "stale"
        ),
        "wrong_policy_hash_invalidates_enforcement": (
            mismatch_result["failure_reason"] == "POLICY_HASH_MISMATCH"
            and mismatch_enforcement["applicability"]["status"] == "invalid"
        ),
        "tampered_signature_invalidates_enforcement": (
            tampered_result["failure_reason"] == "SIGNATURE_INVALID"
            and tampered_enforcement["applicability"]["status"] == "invalid"
        ),
        "raw_attestation_blob_not_persisted": "c2VjcmV0LWhhcmR3YXJlLWJsb2I=" not in normalized_render,
        "cert_chain_not_persisted": "Y2VydGlmaWNhdGUtY2hhaW4=" not in normalized_render,
    }
    result = {
        "schema_version": "1.0.0",
        "comparator": "cmcp-inbound-external-evidence-v0.1",
        "agent_memory_commit": agent_memory_commit,
        "cmcp": {
            "release": CMCP_RELEASE,
            "source_commit": CMCP_SOURCE_COMMIT,
            "runtime_package": "cmcp-runtime==0.4.0",
            "trace_package": "agentrust-trace==0.9.0",
        },
        "mode_cases": mode_cases,
        "stale_case": {
            "verification": stale_result,
            "enforcement": stale_enforcement,
            "attestation": stale_attestation,
        },
        "policy_mismatch_case": {
            "verification": mismatch_result,
            "enforcement": mismatch_enforcement,
        },
        "tampered_signature_case": {
            "verification": tampered_result,
            "enforcement": tampered_enforcement,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "non_claims": [
            "cmcp_enforcement_posture_is_not_agent_memory_authority",
            "cmcp_policy_allow_is_not_approval",
            "cmcp_decision_log_is_not_execution_witness",
            "software_only_verification_is_not_hardware_attestation",
            "audit_chain_integrity_is_not_lifecycle_satisfaction",
            "gateway_identity_is_not_semantic_correctness",
        ],
    }
    if not result["passed"]:
        failed = [key for key, value in checks.items() if not value]
        failed_modes = {
            case["mode"]: [name for name, ok in case["checks"].items() if not ok]
            for case in mode_cases
            if not case["passed"]
        }
        raise AssertionError(
            f"cMCP inbound external-evidence comparator failed: {failed}; mode_failures={failed_modes}"
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(args.agent_memory_commit)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
