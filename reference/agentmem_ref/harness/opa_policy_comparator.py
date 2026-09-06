"""Pinned real-OPA comparator for Agent Memory external policy composition.

Issue #214 proves the existing vendor-neutral external policy seam against the
real OPA CLI. OPA-specific parsing and policy-revision handling remain at this
adapter edge. Valid results are normalized through the existing
``external-policy-decision`` builder and composed by the existing monotonic
composition implementation.
"""

from __future__ import annotations

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

OPA_VERSION = "1.19.0"
OPA_TAG = "v1.19.0"
OPA_SOURCE_COMMIT = "1e32c796e8979b1bda2f768138500b1deb95ff24"
OPA_PROVIDER_ID = "open-policy-agent/opa"
OPA_POLICY_PACKAGE = "agentmemory"
OPA_POLICY_RULE = "decision"
OPA_POLICY_QUERY = f"data.{OPA_POLICY_PACKAGE}.{OPA_POLICY_RULE}"
OPA_POLICY_REVISION = "agent-memory-opa-policy-v0.1.0"
OPA_POLICY_PATH = REFERENCE_ROOT / "policies" / "opa_agent_memory_v01.rego"


@dataclass(frozen=True)
class OpaAdapterObservation:
    status: str
    external_decision: dict[str, Any] | None = None
    observed_policy_revision: str | None = None
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
        actor_id="actor:opa-comparator",
        charter_version="charter:opa-comparator-v1",
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


def minimized_opa_input(projection: dict[str, Any]) -> dict[str, Any]:
    """Return the explicit subset the OPA comparator is allowed to inspect."""
    allowed = (
        "input_identity",
        "proposal_id",
        "memory_id",
        "operation",
        "actor_id",
        "scope",
        "tenant_ref",
        "purpose",
        "state_snapshot",
        "risk_class",
        "reversibility",
        "pama_decision_ref",
        "pama_outcome",
        "permitted_actions",
        "prohibited_actions",
        "policy_version",
    )
    return {field: projection[field] for field in allowed if field in projection}


def parse_opa_eval_document(document: Any) -> dict[str, Any]:
    """Extract the value of one ``opa eval --format=json`` expression."""
    if not isinstance(document, dict):
        raise ValueError("OPA eval output must be a JSON object")
    results = document.get("result")
    if not isinstance(results, list) or len(results) != 1:
        raise ValueError("OPA eval output must contain exactly one result")
    expressions = results[0].get("expressions") if isinstance(results[0], dict) else None
    if not isinstance(expressions, list) or len(expressions) != 1:
        raise ValueError("OPA eval output must contain exactly one expression")
    expression = expressions[0]
    if not isinstance(expression, dict) or not isinstance(expression.get("value"), dict):
        raise ValueError("OPA eval expression must contain an object value")
    value = expression["value"]
    required = ("decision", "reason", "input_identity", "policy_revision")
    missing = [field for field in required if not isinstance(value.get(field), str) or not value.get(field)]
    if missing:
        raise ValueError(f"OPA decision missing required fields: {missing}")
    if value["decision"] not in {"allow", "warn", "escalate", "deny"}:
        raise ValueError(f"unsupported OPA decision {value['decision']!r}")
    return {
        "decision": value["decision"],
        "reason": value["reason"],
        "input_identity": value["input_identity"],
        "policy_revision": value["policy_revision"],
    }


def detect_opa_version(opa_binary: str) -> str:
    try:
        completed = subprocess.run(
            [opa_binary, "version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (FileNotFoundError, OSError) as exc:
        raise RuntimeError(f"OPA binary unavailable: {exc}") from exc
    if completed.returncode != 0:
        raise RuntimeError(f"OPA version command failed: {completed.stderr.strip() or completed.stdout.strip()}")
    for line in completed.stdout.splitlines():
        if line.startswith("Version:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("OPA version output did not contain Version:")


def evaluate_opa(
    projection: dict[str, Any],
    *,
    opa_binary: str,
    expected_policy_revision: str = OPA_POLICY_REVISION,
    issued_at: str = "2026-08-13T03:35:00Z",
    policy_path: Path = OPA_POLICY_PATH,
) -> OpaAdapterObservation:
    """Evaluate the pinned OPA policy and normalize only a compatible result."""
    input_document = minimized_opa_input(projection)
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as handle:
        json.dump(input_document, handle, sort_keys=True, separators=(",", ":"))
        input_path = Path(handle.name)
    try:
        try:
            completed = subprocess.run(
                [
                    opa_binary,
                    "eval",
                    "--format=json",
                    "--data",
                    str(policy_path),
                    "--input",
                    str(input_path),
                    OPA_POLICY_QUERY,
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (FileNotFoundError, OSError) as exc:
            return OpaAdapterObservation(status="unavailable", error=str(exc))
        except subprocess.TimeoutExpired as exc:
            return OpaAdapterObservation(status="error", error=f"OPA evaluation timeout: {exc}")
    finally:
        input_path.unlink(missing_ok=True)

    if completed.returncode != 0:
        return OpaAdapterObservation(
            status="error",
            error=completed.stderr.strip() or completed.stdout.strip() or f"OPA exited {completed.returncode}",
        )
    try:
        document = json.loads(completed.stdout)
        value = parse_opa_eval_document(document)
    except (json.JSONDecodeError, ValueError) as exc:
        return OpaAdapterObservation(status="invalid", error=str(exc))

    observed_revision = value["policy_revision"]
    if observed_revision != expected_policy_revision:
        return OpaAdapterObservation(
            status="stale_policy_revision",
            observed_policy_revision=observed_revision,
            error=(
                f"OPA policy revision mismatch: expected {expected_policy_revision!r}, "
                f"observed {observed_revision!r}"
            ),
        )

    try:
        decision = build_external_decision(
            provider_id=OPA_PROVIDER_ID,
            provider_version=OPA_VERSION,
            input_identity=value["input_identity"],
            decision=value["decision"],
            reason=value["reason"],
            issued_at=issued_at,
            evidence={
                "policy_engine": "opa",
                "policy_package": OPA_POLICY_PACKAGE,
                "policy_rule": OPA_POLICY_RULE,
                "policy_revision": observed_revision,
                "policy_ref": str(policy_path.relative_to(REPO_ROOT)),
                "opa_release": OPA_TAG,
                "opa_source_commit": OPA_SOURCE_COMMIT,
            },
        )
    except ValueError as exc:
        return OpaAdapterObservation(status="invalid", observed_policy_revision=observed_revision, error=str(exc))
    return OpaAdapterObservation(
        status="available",
        external_decision=decision,
        observed_policy_revision=observed_revision,
    )


def _compose_observation(projection: dict[str, Any], observation: OpaAdapterObservation, provider_mode: str) -> dict[str, Any]:
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
    expected_opa: str,
    expected_effective: str,
    opa_binary: str,
    operation: str = "promotion",
    risk_class: str = "low",
    target_class: str = policy.M2,
    downstream_authority: str = policy.A1,
    reversibility: str = "reversible",
) -> dict[str, Any]:
    proposal, native, projection = _projection(
        proposal_id=proposal_id,
        purpose=purpose,
        operation=operation,
        risk_class=risk_class,
        target_class=target_class,
        downstream_authority=downstream_authority,
        reversibility=reversibility,
    )
    observation = evaluate_opa(projection, opa_binary=opa_binary)
    if observation.status != "available" or observation.external_decision is None:
        raise AssertionError(f"{case_id}: real OPA decision unavailable: {observation}")
    receipt = compose(
        projection,
        provider_mode=PROVIDER_AUTHORITATIVE,
        external_decision=observation.external_decision,
    )
    checks = {
        "local_expected": receipt["local_normalized_decision"] == expected_local,
        "opa_expected": receipt.get("external_normalized_decision") == expected_opa,
        "effective_expected": receipt["effective_decision"] == expected_effective,
        "provider_available": receipt["external_provider_status"] == STATUS_AVAILABLE,
        "execution_not_established": receipt["execution_status"] == "unknown",
        "projection_identity_preserved": observation.external_decision["input_identity"] == projection["input_identity"],
        "policy_revision_preserved": (
            observation.external_decision.get("evidence", {}).get("policy_revision") == OPA_POLICY_REVISION
        ),
        "pama_envelope_unchanged": (
            projection["permitted_actions"] == sorted(set(native.permitted_actions))
            and projection["prohibited_actions"] == sorted(set(native.prohibited_actions))
        ),
    }
    return {
        "case_id": case_id,
        "proposal": proposal,
        "native_outcome": native.outcome,
        "projection": projection,
        "opa_observation": observation,
        "composition": receipt,
        "checks": checks,
        "passed": all(checks.values()),
    }


def run_comparator(agent_memory_commit: str, *, opa_binary: str = "opa") -> dict[str, Any]:
    if len(agent_memory_commit) != 40 or any(ch not in "0123456789abcdef" for ch in agent_memory_commit):
        raise ValueError("agent_memory_commit must be an exact lowercase 40-hex commit")
    installed_version = detect_opa_version(opa_binary)
    if installed_version != OPA_VERSION:
        raise RuntimeError(f"expected OPA {OPA_VERSION}, found {installed_version}")

    substrate = InMemoryTemporalGraph()
    initial_writes = len(substrate.write_log)

    matrix = [
        _matrix_case(
            case_id="native-allow-opa-allow",
            proposal_id="opa:allow-allow",
            purpose="opa-allow",
            expected_local=ALLOW,
            expected_opa=ALLOW,
            expected_effective=ALLOW,
            opa_binary=opa_binary,
        ),
        _matrix_case(
            case_id="native-allow-opa-deny",
            proposal_id="opa:allow-deny",
            purpose="opa-deny",
            expected_local=ALLOW,
            expected_opa=DENY,
            expected_effective=DENY,
            opa_binary=opa_binary,
        ),
        _matrix_case(
            case_id="native-require-approval-opa-allow",
            proposal_id="opa:review-allow",
            purpose="opa-allow",
            risk_class="medium",
            expected_local=REQUIRE_APPROVAL,
            expected_opa=ALLOW,
            expected_effective=REQUIRE_APPROVAL,
            opa_binary=opa_binary,
        ),
        _matrix_case(
            case_id="native-deny-opa-allow",
            proposal_id="opa:deny-allow",
            purpose="opa-allow",
            operation="scope_expansion",
            risk_class="critical",
            target_class=policy.M5,
            downstream_authority=policy.A5,
            reversibility="irreversible",
            expected_local=DENY,
            expected_opa=ALLOW,
            expected_effective=DENY,
            opa_binary=opa_binary,
        ),
    ]

    # Provider-unavailable semantics are generic and must remain mode-specific.
    _, _, failure_projection = _projection(
        proposal_id="opa:provider-failure",
        purpose="opa-allow",
    )
    unavailable_observation = evaluate_opa(
        failure_projection,
        opa_binary="/definitely/missing/opa",
    )
    advisory_unavailable = _compose_observation(failure_projection, unavailable_observation, PROVIDER_ADVISORY)
    authoritative_unavailable = _compose_observation(
        failure_projection,
        unavailable_observation,
        PROVIDER_AUTHORITATIVE,
    )

    # Adapter-specific policy revision staleness is rejected before generic
    # composition. The generic layer then applies configured peer-failure mode.
    stale_revision_observation = evaluate_opa(
        failure_projection,
        opa_binary=opa_binary,
        expected_policy_revision="agent-memory-opa-policy-stale-test",
    )
    advisory_stale_revision = _compose_observation(
        failure_projection,
        stale_revision_observation,
        PROVIDER_ADVISORY,
    )
    authoritative_stale_revision = _compose_observation(
        failure_projection,
        stale_revision_observation,
        PROVIDER_AUTHORITATIVE,
    )

    # A valid real OPA decision for one exact projection cannot be replayed
    # against another Agent Memory input identity.
    _, _, projection_a = _projection(
        proposal_id="opa:identity-a",
        purpose="opa-allow",
    )
    _, _, projection_b = _projection(
        proposal_id="opa:identity-b",
        purpose="opa-allow",
    )
    identity_observation = evaluate_opa(projection_a, opa_binary=opa_binary)
    if identity_observation.status != "available" or identity_observation.external_decision is None:
        raise AssertionError(f"identity OPA evaluation unavailable: {identity_observation}")
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
    matrix_passed = all(case["passed"] for case in matrix)
    checks = {
        "real_opa_version_exact": installed_version == OPA_VERSION,
        "real_opa_matrix_passed": matrix_passed,
        "opa_can_tighten_native_allow": matrix[1]["composition"]["effective_decision"] == DENY,
        "opa_allow_cannot_loosen_native_review": matrix[2]["composition"]["effective_decision"] == REQUIRE_APPROVAL,
        "opa_allow_cannot_loosen_native_deny": matrix[3]["composition"]["effective_decision"] == DENY,
        "advisory_unavailable_preserves_native": (
            unavailable_observation.status == "unavailable"
            and advisory_unavailable["external_provider_status"] == STATUS_UNAVAILABLE
            and advisory_unavailable["effective_decision"] == ALLOW
        ),
        "authoritative_unavailable_fails_closed": (
            authoritative_unavailable["external_provider_status"] == STATUS_UNAVAILABLE
            and authoritative_unavailable["effective_decision"] == DENY
        ),
        "stale_policy_revision_detected_at_adapter": stale_revision_observation.status == "stale_policy_revision",
        "advisory_stale_revision_preserves_native": advisory_stale_revision["effective_decision"] == ALLOW,
        "authoritative_stale_revision_fails_closed": authoritative_stale_revision["effective_decision"] == DENY,
        "stale_input_identity_detected_by_generic_layer": (
            authoritative_stale_identity["external_provider_status"] == STATUS_STALE_IDENTITY
            and advisory_stale_identity["external_provider_status"] == STATUS_STALE_IDENTITY
        ),
        "authoritative_stale_identity_fails_closed": authoritative_stale_identity["effective_decision"] == DENY,
        "advisory_stale_identity_preserves_native": advisory_stale_identity["effective_decision"] == ALLOW,
        "opa_success_not_execution_evidence": all(
            case["composition"]["execution_status"] == "unknown" for case in matrix
        ),
        "opa_decision_did_not_create_memory_fact": final_writes == initial_writes == 0,
        "generic_composition_receipt_has_no_opa_specific_core_fields": all(
            not any(key.startswith("opa_") for key in case["composition"]) for case in matrix
        ),
        "minimized_policy_input_excludes_raw_payloads": all(
            "raw" not in key and "content" not in key and "prompt" not in key
            for key in minimized_opa_input(matrix[0]["projection"])
        ),
    }
    passed = all(checks.values())
    result = {
        "schema_version": "1.0.0",
        "comparator": "opa-external-policy-composition-v0.1",
        "agent_memory_commit": agent_memory_commit,
        "pinned_opa": {
            "release": OPA_TAG,
            "source_commit": OPA_SOURCE_COMMIT,
            "installed_version": installed_version,
            "policy_ref": str(OPA_POLICY_PATH.relative_to(REPO_ROOT)),
            "policy_package": OPA_POLICY_PACKAGE,
            "policy_rule": OPA_POLICY_RULE,
            "expected_policy_revision": OPA_POLICY_REVISION,
        },
        "matrix": [
            {
                "case_id": case["case_id"],
                "native_outcome": case["native_outcome"],
                "input_identity": case["projection"]["input_identity"],
                "opa_status": case["opa_observation"].status,
                "opa_decision": case["opa_observation"].external_decision,
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
            "stale_policy_revision": {
                "adapter_status": stale_revision_observation.status,
                "observed_policy_revision": stale_revision_observation.observed_policy_revision,
                "advisory": advisory_stale_revision,
                "authoritative": authoritative_stale_revision,
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
            "opa_decision_is_not_agent_memory_authority",
            "opa_allow_is_not_approval_or_standing_permission",
            "opa_decision_is_not_enforcement_evidence",
            "opa_evaluation_success_is_not_execution_evidence",
            "opa_policy_revision_is_adapter_evidence_not_canonical_memory_state",
            "opa_policy_is_not_agent_memory_canonical_policy_storage",
        ],
    }
    if not passed:
        failed = [name for name, ok in checks.items() if not ok]
        raise AssertionError(f"OPA external-policy comparator failed: {failed}; result={result}")
    return result
