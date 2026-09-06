"""Pinned real-Cedar comparator for Agent Memory external policy composition.

Issue #216 proves the existing vendor-neutral external policy seam against the
real Cedar CLI. Cedar-specific request binding, policy-artifact custody, and
diagnostic parsing remain at this adapter edge. Valid results are normalized
through the existing external-policy-decision builder and composed by the
existing monotonic composition implementation.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..core import policy
from ..memory.enforcement_composition import (
    ALLOW,
    DENY,
    PROVIDER_ADVISORY,
    PROVIDER_AUTHORITATIVE,
    REQUIRE_APPROVAL,
    STATUS_AVAILABLE,
    STATUS_STALE_IDENTITY,
    STATUS_UNAVAILABLE,
    build_external_decision,
    build_projection,
    compose,
)
from ..state.substrate import InMemoryTemporalGraph
from .._paths import REPO_ROOT, REFERENCE_ROOT

CEDAR_VERSION = "4.12.0"
CEDAR_TAG = "v4.12.0"
CEDAR_SOURCE_COMMIT = "fdcbaed32bdb8c8d13e4eaf2b58db5555e9fb8c5"
CEDAR_PROVIDER_ID = "cedar-policy/cedar"
CEDAR_POLICY_PATH = REFERENCE_ROOT / "policies" / "cedar_agent_memory_v01.cedar"
CEDAR_POLICY_SHA256 = "sha256:a369c1423d48b6656e5e19f2589cc4660e00695e3b084c0a732b3f7f7ba6e18f"


@dataclass(frozen=True)
class CedarAdapterObservation:
    status: str
    external_decision: dict[str, Any] | None = None
    policy_sha256: str | None = None
    determining_policy_ids: tuple[str, ...] = ()
    request_digest: str | None = None
    error: str | None = None


def _proposal(
    *,
    proposal_id: str,
    purpose: str,
    operation: str = "promotion",
    risk_class: str = "low",
    target_class: str = policy.M2,
    downstream_authority: str = policy.A1,
    reversibility: str = "reversible",
) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="actor:cedar-comparator",
        charter_version="charter:cedar-comparator-v1",
        target_reference=f"mem:{proposal_id}",
        target_class=target_class,
        scope="scope:tenant-a/project-a",
        operation=operation,
        current_strength="promoted" if operation == "scope_expansion" else "reinforced",
        proposed_strength="canonical" if operation == "scope_expansion" else "promoted",
        downstream_authority=downstream_authority,
        reversibility=reversibility,
        risk_class=risk_class,
        evidence_refs=(f"evidence:{proposal_id}",),
        state_snapshot="v0",
        tenant_ref="tenant-a",
        purpose=purpose,
        isolation_domain_refs=("scope:tenant-a/project-a",),
        project_ref="project-a",
    )


def _projection(
    *,
    proposal_id: str,
    purpose: str,
    operation: str = "promotion",
    risk_class: str = "low",
    target_class: str = policy.M2,
    downstream_authority: str = policy.A1,
    reversibility: str = "reversible",
) -> tuple[policy.Proposal, policy.Decision, dict[str, Any]]:
    proposal = _proposal(
        proposal_id=proposal_id,
        purpose=purpose,
        operation=operation,
        risk_class=risk_class,
        target_class=target_class,
        downstream_authority=downstream_authority,
        reversibility=reversibility,
    )
    decision = policy.evaluate(proposal)
    return proposal, decision, build_projection(proposal, decision)


def minimized_cedar_context(projection: dict[str, Any]) -> dict[str, Any]:
    """Return the bounded Cedar request context, excluding raw memory payloads."""
    allowed = (
        "input_identity",
        "purpose",
        "risk_class",
        "scope",
        "tenant_ref",
        "pama_outcome",
        "policy_version",
    )
    return {field: projection[field] for field in allowed if field in projection}


def _uid(kind: str, value: str) -> str:
    return f"{kind}::{json.dumps(value, ensure_ascii=False)}"


def build_cedar_request(projection: dict[str, Any]) -> dict[str, Any]:
    return {
        "principal": _uid("Agent", projection["actor_id"]),
        "action": _uid("Action", projection["operation"]),
        "resource": _uid("Memory", projection["memory_id"]),
        "context": minimized_cedar_context(projection),
    }


def _sha256_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def policy_sha256(policy_path: Path = CEDAR_POLICY_PATH) -> str:
    """Digest of the policy text with line endings normalized, so the pin holds on any checkout."""
    return _sha256_bytes(policy_path.read_bytes().replace(b"\r\n", b"\n"))


def request_digest(request: dict[str, Any]) -> str:
    raw = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return _sha256_bytes(raw)


def parse_cedar_authorize_output(stdout: str, returncode: int) -> dict[str, Any]:
    """Parse Cedar v4.12.0 human output without treating DENY exit 2 as failure."""
    lines = [line.rstrip() for line in stdout.splitlines()]
    decision_lines = [line.strip() for line in lines if line.strip() in {"ALLOW", "DENY"}]
    if len(decision_lines) != 1:
        raise ValueError("Cedar authorize output must contain exactly one ALLOW or DENY decision")
    decision = decision_lines[0]
    expected_returncode = 0 if decision == "ALLOW" else 2
    if returncode != expected_returncode:
        raise ValueError(
            f"Cedar decision/exit mismatch: decision={decision}, returncode={returncode}, "
            f"expected={expected_returncode}"
        )

    policy_ids: list[str] = []
    marker = "note: this decision was due to the following policies:"
    for index, line in enumerate(lines):
        if line.strip() != marker:
            continue
        for candidate in lines[index + 1 :]:
            stripped = candidate.strip()
            if not stripped:
                break
            if stripped.startswith("note:"):
                break
            policy_ids.append(stripped)
        break

    return {
        "decision": decision.lower(),
        "determining_policy_ids": tuple(policy_ids),
    }


def detect_cedar_version(cedar_binary: str) -> str:
    try:
        completed = subprocess.run(
            [cedar_binary, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, OSError) as exc:
        raise RuntimeError(f"Cedar binary unavailable: {exc}") from exc
    if completed.returncode != 0:
        raise RuntimeError(
            f"Cedar version command failed: {completed.stderr.strip() or completed.stdout.strip()}"
        )
    text = completed.stdout.strip() or completed.stderr.strip()
    tokens = text.split()
    for token in reversed(tokens):
        if token == CEDAR_VERSION:
            return token
    raise RuntimeError(f"Cedar version output did not contain {CEDAR_VERSION!r}: {text!r}")


def evaluate_cedar(
    projection: dict[str, Any],
    *,
    cedar_binary: str,
    expected_policy_sha256: str = CEDAR_POLICY_SHA256,
    issued_at: str = "2026-08-13T04:50:00Z",
    policy_path: Path = CEDAR_POLICY_PATH,
) -> CedarAdapterObservation:
    """Run real Cedar and normalize only an exact-policy, exact-request result."""
    observed_policy_sha256 = policy_sha256(policy_path)
    if observed_policy_sha256 != expected_policy_sha256:
        return CedarAdapterObservation(
            status="stale_policy_artifact",
            policy_sha256=observed_policy_sha256,
            error=(
                f"Cedar policy digest mismatch: expected {expected_policy_sha256!r}, "
                f"observed {observed_policy_sha256!r}"
            ),
        )

    request = build_cedar_request(projection)
    req_digest = request_digest(request)
    with tempfile.TemporaryDirectory(prefix="agent-memory-cedar-") as tmpdir:
        tmp = Path(tmpdir)
        context_path = tmp / "context.json"
        entities_path = tmp / "entities.json"
        context_path.write_text(
            json.dumps(request["context"], sort_keys=True, separators=(",", ":")),
            encoding="utf-8",
        )
        entities_path.write_text("[]\n", encoding="utf-8")
        command = [
            cedar_binary,
            "authorize",
            "--principal",
            request["principal"],
            "--action",
            request["action"],
            "--resource",
            request["resource"],
            "--context",
            str(context_path),
            "--policies",
            str(policy_path),
            "--entities",
            str(entities_path),
            "--verbose",
        ]
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (FileNotFoundError, OSError) as exc:
            return CedarAdapterObservation(
                status="unavailable",
                policy_sha256=observed_policy_sha256,
                request_digest=req_digest,
                error=str(exc),
            )
        except subprocess.TimeoutExpired as exc:
            return CedarAdapterObservation(
                status="error",
                policy_sha256=observed_policy_sha256,
                request_digest=req_digest,
                error=f"Cedar evaluation timeout: {exc}",
            )

    if completed.returncode not in {0, 2}:
        return CedarAdapterObservation(
            status="error",
            policy_sha256=observed_policy_sha256,
            request_digest=req_digest,
            error=completed.stderr.strip() or completed.stdout.strip() or f"Cedar exited {completed.returncode}",
        )

    try:
        parsed = parse_cedar_authorize_output(completed.stdout, completed.returncode)
    except ValueError as exc:
        return CedarAdapterObservation(
            status="invalid",
            policy_sha256=observed_policy_sha256,
            request_digest=req_digest,
            error=str(exc),
        )

    reason = f"Cedar authorization {parsed['decision'].upper()}"
    if parsed["determining_policy_ids"]:
        reason += " via " + ",".join(parsed["determining_policy_ids"])

    try:
        external_decision = build_external_decision(
            provider_id=CEDAR_PROVIDER_ID,
            provider_version=CEDAR_VERSION,
            input_identity=projection["input_identity"],
            decision=parsed["decision"],
            reason=reason,
            issued_at=issued_at,
            evidence={
                "policy_engine": "cedar",
                "cedar_release": CEDAR_TAG,
                "cedar_source_commit": CEDAR_SOURCE_COMMIT,
                "policy_ref": str(policy_path.relative_to(REPO_ROOT)),
                "policy_sha256": observed_policy_sha256,
                "determining_policy_ids": list(parsed["determining_policy_ids"]),
                "request_digest": req_digest,
            },
        )
    except ValueError as exc:
        return CedarAdapterObservation(
            status="invalid",
            policy_sha256=observed_policy_sha256,
            determining_policy_ids=parsed["determining_policy_ids"],
            request_digest=req_digest,
            error=str(exc),
        )

    return CedarAdapterObservation(
        status="available",
        external_decision=external_decision,
        policy_sha256=observed_policy_sha256,
        determining_policy_ids=parsed["determining_policy_ids"],
        request_digest=req_digest,
    )


def _compose_observation(
    projection: dict[str, Any],
    observation: CedarAdapterObservation,
    provider_mode: str,
) -> dict[str, Any]:
    return compose(
        projection,
        provider_mode=provider_mode,
        external_decision=observation.external_decision if observation.status == "available" else None,
    )


def _matrix_case(
    *,
    case_id: str,
    proposal_id: str,
    purpose: str,
    expected_local: str,
    expected_cedar: str,
    expected_effective: str,
    cedar_binary: str,
    operation: str = "promotion",
    risk_class: str = "low",
    target_class: str = policy.M2,
    downstream_authority: str = policy.A1,
    reversibility: str = "reversible",
) -> dict[str, Any]:
    _, native, projection = _projection(
        proposal_id=proposal_id,
        purpose=purpose,
        operation=operation,
        risk_class=risk_class,
        target_class=target_class,
        downstream_authority=downstream_authority,
        reversibility=reversibility,
    )
    observation = evaluate_cedar(projection, cedar_binary=cedar_binary)
    if observation.status != "available" or observation.external_decision is None:
        raise AssertionError(f"{case_id}: real Cedar decision unavailable: {observation}")
    receipt = compose(
        projection,
        provider_mode=PROVIDER_AUTHORITATIVE,
        external_decision=observation.external_decision,
    )
    checks = {
        "local_expected": receipt["local_normalized_decision"] == expected_local,
        "cedar_expected": receipt.get("external_normalized_decision") == expected_cedar,
        "effective_expected": receipt["effective_decision"] == expected_effective,
        "provider_available": receipt["external_provider_status"] == STATUS_AVAILABLE,
        "execution_not_established": receipt["execution_status"] == "unknown",
        "projection_identity_preserved": observation.external_decision["input_identity"] == projection["input_identity"],
        "policy_digest_preserved": (
            observation.external_decision.get("evidence", {}).get("policy_sha256") == CEDAR_POLICY_SHA256
        ),
        "request_digest_preserved": (
            observation.external_decision.get("evidence", {}).get("request_digest") == observation.request_digest
        ),
        "pama_envelope_unchanged": (
            projection["permitted_actions"] == sorted(set(native.permitted_actions))
            and projection["prohibited_actions"] == sorted(set(native.prohibited_actions))
        ),
    }
    return {
        "case_id": case_id,
        "native_outcome": native.outcome,
        "projection": projection,
        "cedar_observation": observation,
        "composition": receipt,
        "checks": checks,
        "passed": all(checks.values()),
    }


def run_comparator(agent_memory_commit: str, *, cedar_binary: str = "cedar") -> dict[str, Any]:
    if len(agent_memory_commit) != 40 or any(ch not in "0123456789abcdef" for ch in agent_memory_commit):
        raise ValueError("agent_memory_commit must be an exact lowercase 40-hex commit")
    installed_version = detect_cedar_version(cedar_binary)
    if installed_version != CEDAR_VERSION:
        raise RuntimeError(f"expected Cedar {CEDAR_VERSION}, found {installed_version}")
    observed_policy_sha256 = policy_sha256()
    if observed_policy_sha256 != CEDAR_POLICY_SHA256:
        raise RuntimeError(
            f"checked-in Cedar policy digest mismatch: expected {CEDAR_POLICY_SHA256}, "
            f"observed {observed_policy_sha256}"
        )

    substrate = InMemoryTemporalGraph()
    initial_writes = len(substrate.write_log)

    matrix = [
        _matrix_case(
            case_id="native-allow-cedar-allow",
            proposal_id="cedar:allow-allow",
            purpose="cedar-allow",
            expected_local=ALLOW,
            expected_cedar=ALLOW,
            expected_effective=ALLOW,
            cedar_binary=cedar_binary,
        ),
        _matrix_case(
            case_id="native-allow-cedar-deny",
            proposal_id="cedar:allow-deny",
            purpose="cedar-deny",
            expected_local=ALLOW,
            expected_cedar=DENY,
            expected_effective=DENY,
            cedar_binary=cedar_binary,
        ),
        _matrix_case(
            case_id="native-require-approval-cedar-allow",
            proposal_id="cedar:review-allow",
            purpose="cedar-allow",
            risk_class="medium",
            expected_local=REQUIRE_APPROVAL,
            expected_cedar=ALLOW,
            expected_effective=REQUIRE_APPROVAL,
            cedar_binary=cedar_binary,
        ),
        _matrix_case(
            case_id="native-deny-cedar-allow",
            proposal_id="cedar:deny-allow",
            purpose="cedar-allow",
            operation="scope_expansion",
            risk_class="critical",
            target_class=policy.M5,
            downstream_authority=policy.A5,
            reversibility="irreversible",
            expected_local=DENY,
            expected_cedar=ALLOW,
            expected_effective=DENY,
            cedar_binary=cedar_binary,
        ),
    ]

    _, _, failure_projection = _projection(
        proposal_id="cedar:provider-failure",
        purpose="cedar-allow",
    )
    unavailable_observation = evaluate_cedar(
        failure_projection,
        cedar_binary="/definitely/missing/cedar",
    )
    advisory_unavailable = _compose_observation(
        failure_projection,
        unavailable_observation,
        PROVIDER_ADVISORY,
    )
    authoritative_unavailable = _compose_observation(
        failure_projection,
        unavailable_observation,
        PROVIDER_AUTHORITATIVE,
    )

    stale_policy_observation = evaluate_cedar(
        failure_projection,
        cedar_binary=cedar_binary,
        expected_policy_sha256="sha256:" + "0" * 64,
    )
    advisory_stale_policy = _compose_observation(
        failure_projection,
        stale_policy_observation,
        PROVIDER_ADVISORY,
    )
    authoritative_stale_policy = _compose_observation(
        failure_projection,
        stale_policy_observation,
        PROVIDER_AUTHORITATIVE,
    )

    _, _, projection_a = _projection(
        proposal_id="cedar:identity-a",
        purpose="cedar-allow",
    )
    _, _, projection_b = _projection(
        proposal_id="cedar:identity-b",
        purpose="cedar-allow",
    )
    identity_observation = evaluate_cedar(projection_a, cedar_binary=cedar_binary)
    if identity_observation.status != "available" or identity_observation.external_decision is None:
        raise AssertionError(f"identity Cedar evaluation unavailable: {identity_observation}")
    authoritative_stale_identity = compose(
        projection_b,
        provider_mode=PROVIDER_AUTHORITATIVE,
        external_decision=identity_observation.external_decision,
    )
    advisory_stale_identity = compose(
        projection_b,
        provider_mode=PROVIDER_ADVISORY,
        external_decision=identity_observation.external_decision,
    )

    final_writes = len(substrate.write_log)
    checks = {
        "real_cedar_version_exact": installed_version == CEDAR_VERSION,
        "policy_artifact_digest_exact": observed_policy_sha256 == CEDAR_POLICY_SHA256,
        "real_cedar_matrix_passed": all(case["passed"] for case in matrix),
        "cedar_can_tighten_native_allow": matrix[1]["composition"]["effective_decision"] == DENY,
        "cedar_allow_cannot_loosen_native_review": matrix[2]["composition"]["effective_decision"] == REQUIRE_APPROVAL,
        "cedar_allow_cannot_loosen_native_deny": matrix[3]["composition"]["effective_decision"] == DENY,
        "advisory_unavailable_preserves_native": (
            unavailable_observation.status == "unavailable"
            and advisory_unavailable["external_provider_status"] == STATUS_UNAVAILABLE
            and advisory_unavailable["effective_decision"] == ALLOW
        ),
        "authoritative_unavailable_fails_closed": (
            authoritative_unavailable["external_provider_status"] == STATUS_UNAVAILABLE
            and authoritative_unavailable["effective_decision"] == DENY
        ),
        "stale_policy_artifact_detected_at_adapter": stale_policy_observation.status == "stale_policy_artifact",
        "advisory_stale_policy_preserves_native": advisory_stale_policy["effective_decision"] == ALLOW,
        "authoritative_stale_policy_fails_closed": authoritative_stale_policy["effective_decision"] == DENY,
        "stale_input_identity_detected_by_generic_layer": (
            authoritative_stale_identity["external_provider_status"] == STATUS_STALE_IDENTITY
            and advisory_stale_identity["external_provider_status"] == STATUS_STALE_IDENTITY
        ),
        "authoritative_stale_identity_fails_closed": authoritative_stale_identity["effective_decision"] == DENY,
        "advisory_stale_identity_preserves_native": advisory_stale_identity["effective_decision"] == ALLOW,
        "cedar_success_not_execution_evidence": all(
            case["composition"]["execution_status"] == "unknown" for case in matrix
        ),
        "cedar_decision_did_not_create_memory_fact": final_writes == initial_writes == 0,
        "generic_composition_receipt_has_no_cedar_specific_core_fields": all(
            not any(key.startswith("cedar_") for key in case["composition"]) for case in matrix
        ),
        "minimized_policy_input_excludes_raw_payloads": all(
            "raw" not in key and "content" not in key and "prompt" not in key
            for key in minimized_cedar_context(matrix[0]["projection"])
        ),
    }
    passed = all(checks.values())
    result = {
        "schema_version": "1.0.0",
        "comparator": "cedar-external-policy-composition-v0.1",
        "agent_memory_commit": agent_memory_commit,
        "pinned_cedar": {
            "release": CEDAR_TAG,
            "source_commit": CEDAR_SOURCE_COMMIT,
            "installed_version": installed_version,
            "policy_ref": str(CEDAR_POLICY_PATH.relative_to(REPO_ROOT)),
            "policy_sha256": observed_policy_sha256,
        },
        "matrix": [
            {
                "case_id": case["case_id"],
                "native_outcome": case["native_outcome"],
                "input_identity": case["projection"]["input_identity"],
                "cedar_status": case["cedar_observation"].status,
                "cedar_decision": case["cedar_observation"].external_decision,
                "determining_policy_ids": list(case["cedar_observation"].determining_policy_ids),
                "request_digest": case["cedar_observation"].request_digest,
                "composition": case["composition"],
                "checks": case["checks"],
                "passed": case["passed"],
            }
            for case in matrix
        ],
        "failure_modes": {
            "unavailable": {
                "adapter_status": unavailable_observation.status,
                "advisory": advisory_unavailable,
                "authoritative": authoritative_unavailable,
            },
            "stale_policy_artifact": {
                "adapter_status": stale_policy_observation.status,
                "observed_policy_sha256": stale_policy_observation.policy_sha256,
                "advisory": advisory_stale_policy,
                "authoritative": authoritative_stale_policy,
            },
            "stale_input_identity": {
                "source_identity": projection_a["input_identity"],
                "current_identity": projection_b["input_identity"],
                "advisory": advisory_stale_identity,
                "authoritative": authoritative_stale_identity,
            },
        },
        "memory_write_count": final_writes,
        "checks": checks,
        "passed": passed,
        "non_claims": [
            "cedar_decision_is_not_agent_memory_authority",
            "cedar_allow_is_not_approval_or_standing_permission",
            "cedar_decision_is_not_enforcement_evidence",
            "cedar_authorization_success_is_not_execution_evidence",
            "cedar_policy_artifact_identity_is_adapter_evidence_not_canonical_memory_state",
            "cedar_policy_is_not_agent_memory_canonical_policy_storage",
        ],
    }
    if not passed:
        failed = [name for name, ok in checks.items() if not ok]
        raise AssertionError(f"Cedar external-policy comparator failed: {failed}; result={result}")
    return result
