"""Non-authority-bearing Agent2Agent collaboration evidence for issue #194.

A2A supplies peer discovery, message, task, context, and artifact facts. This
module normalizes those facts without letting transport/task identity become
Agent Memory authority, durable admission, semantic correctness, execution
proof, or lifecycle satisfaction.
"""

from __future__ import annotations

import hashlib
import re

import rfc8785

from ..core import receipts

PROFILE_VERSION = "0.1.0"
A2A_RELEASE = "v1.0.1"
A2A_SOURCE_COMMIT = "3303592588e388e62e0f69f701af531d2f4e3991"
A2A_SOURCE_REF = f"github://a2aproject/A2A/{A2A_SOURCE_COMMIT}/specification/a2a.proto"

DIRECTIONS = {"outbound", "inbound"}
INTERACTION_KINDS = {"task_request", "task_status", "message", "artifact"}
EXPORT_CLASSES = {"explicit_non_memory", "context_projection", "memory_candidate"}
MEMORY_EVIDENCE_STATUSES = {"current", "historical", "stale", "revoked", "unknown", "not_applicable"}
TASK_STATES = {
    "unspecified",
    "submitted",
    "working",
    "completed",
    "failed",
    "canceled",
    "input_required",
    "rejected",
    "auth_required",
    "unavailable",
    "not_observed",
}
GOVERNANCE_STATUSES = {"available", "unavailable", "not_required"}
EFFECTIVE_DECISIONS = {"allow", "warn", "require_approval", "deny"}
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _sha256_ref(value: dict) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _require_ref(name: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_digest(name: str, value: object) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase sha256 digest reference")
    return value


def _string_list(name: str, value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{name} must be a list of non-empty strings")
    return list(dict.fromkeys(value))


def _binding(adapter_result: dict, expected_context: dict | None, export_classification: str) -> tuple[str, list[str]]:
    if expected_context is None:
        if export_classification == "context_projection":
            return "mismatch", ["expected_context_missing"]
        return "not_evaluated", []
    if not isinstance(expected_context, dict):
        raise ValueError("expected_context must be an object when provided")

    reasons: list[str] = []
    for field in ("action_ref", "input_identity", "scope_ref", "tenant_ref", "project_ref"):
        expected = expected_context.get(field)
        if expected is None:
            continue
        actual = adapter_result.get(field)
        if actual is None:
            reasons.append(f"{field}_missing")
        elif actual != expected:
            reasons.append(f"{field}_mismatch")

    if export_classification == "context_projection":
        for required in ("action_ref", "input_identity", "scope_ref"):
            if expected_context.get(required) is None:
                reasons.append(f"expected_{required}_missing")
            elif adapter_result.get(required) is None and f"{required}_missing" not in reasons:
                reasons.append(f"{required}_missing")

    return ("mismatch", reasons) if reasons else ("exact", [])


def _alignment(
    *,
    direction: str,
    export_classification: str,
    memory_evidence_status: str,
    governance_status: str,
    effective_decision: str | None,
    task_state: str,
    binding_status: str,
) -> str:
    if binding_status == "mismatch" and governance_status != "not_required":
        return "binding_mismatch"

    # A remote protocol result may be governance-relevant even when the content
    # itself is explicit non-memory. Export/memory classification and action
    # governance are deliberately separate axes.
    if governance_status == "available" and effective_decision == "deny":
        if direction == "inbound" and task_state not in {"unavailable", "not_observed", "rejected"}:
            return "remote_result_under_deny"
        if export_classification == "context_projection":
            return "within_governance"

    if export_classification == "context_projection":
        if memory_evidence_status in {"historical", "stale", "revoked"}:
            return "historical_only"
        if governance_status != "available":
            return "blocked_governance_unavailable"
        assert effective_decision is not None
        if effective_decision == "require_approval":
            return "approval_not_established"
        return "within_governance"

    return "not_applicable" if governance_status == "not_required" else "not_evaluated"


def normalize_a2a_collaboration(adapter_result: dict, expected_context: dict | None = None) -> dict:
    """Normalize one bounded A2A collaboration event.

    The adapter may inspect raw Agent Cards, Messages, Tasks, or Artifacts long
    enough to compute stable refs/digests. This function intentionally accepts
    and emits only minimized evidence fields.
    """

    if not isinstance(adapter_result, dict):
        raise ValueError("adapter_result must be an object")
    if adapter_result.get("protocol_release") != A2A_RELEASE:
        raise ValueError(f"unsupported A2A release {adapter_result.get('protocol_release')!r}")
    if adapter_result.get("protocol_source_commit") != A2A_SOURCE_COMMIT:
        raise ValueError("A2A protocol source commit does not match the pinned stable release")

    direction = adapter_result.get("direction")
    if direction not in DIRECTIONS:
        raise ValueError(f"invalid direction {direction!r}")
    interaction_kind = adapter_result.get("interaction_kind")
    if interaction_kind not in INTERACTION_KINDS:
        raise ValueError(f"invalid interaction_kind {interaction_kind!r}")
    if interaction_kind == "task_request" and direction != "outbound":
        raise ValueError("task_request must be outbound")
    if interaction_kind == "artifact" and direction != "inbound":
        raise ValueError("artifact observation must be inbound in V0.1")

    export_classification = adapter_result.get("export_classification")
    if export_classification not in EXPORT_CLASSES:
        raise ValueError(f"invalid export_classification {export_classification!r}")
    if export_classification == "context_projection" and direction != "outbound":
        raise ValueError("context_projection must be outbound in V0.1")
    if export_classification == "memory_candidate" and direction != "inbound":
        raise ValueError("memory_candidate must be inbound in V0.1")

    memory_evidence_status = adapter_result.get("memory_evidence_status")
    if memory_evidence_status not in MEMORY_EVIDENCE_STATUSES:
        raise ValueError(f"invalid memory_evidence_status {memory_evidence_status!r}")
    if export_classification != "context_projection" and memory_evidence_status not in {"not_applicable", "unknown"}:
        raise ValueError("memory evidence currentness only applies to outbound context projections")

    task_state = adapter_result.get("task_state")
    if task_state not in TASK_STATES:
        raise ValueError(f"invalid task_state {task_state!r}")

    governance_status = adapter_result.get("governance_status")
    if governance_status not in GOVERNANCE_STATUSES:
        raise ValueError(f"invalid governance_status {governance_status!r}")
    effective_decision = adapter_result.get("effective_decision")
    if governance_status == "available":
        if effective_decision not in EFFECTIVE_DECISIONS:
            raise ValueError("available governance requires a valid effective_decision")
    elif effective_decision is not None:
        raise ValueError("effective_decision requires governance_status='available'")
    if export_classification == "context_projection" and governance_status == "not_required":
        raise ValueError("outbound memory-derived context cannot declare governance not required")

    body: dict = {
        "protocol": {
            "name": "a2a",
            "release": A2A_RELEASE,
            "source_ref": _require_ref(
                "protocol_source_ref",
                adapter_result.get("protocol_source_ref", A2A_SOURCE_REF),
            ),
            "source_commit": A2A_SOURCE_COMMIT,
        },
        "direction": direction,
        "interaction_kind": interaction_kind,
        "local_agent_ref": _require_ref("local_agent_ref", adapter_result.get("local_agent_ref")),
        "remote_agent_ref": _require_ref("remote_agent_ref", adapter_result.get("remote_agent_ref")),
        "agent_card_digest": _require_digest("agent_card_digest", adapter_result.get("agent_card_digest")),
        "export_classification": export_classification,
        "memory_evidence_status": memory_evidence_status,
        "task_state": task_state,
        "governance_status": governance_status,
        "payload_digest": _require_digest("payload_digest", adapter_result.get("payload_digest")),
        "observed_at": _require_ref("observed_at", adapter_result.get("observed_at")),
        "evidence_refs": _string_list("evidence_refs", adapter_result.get("evidence_refs")),
        "interpretation": {
            "authority_effect": "none",
            "delegated_memory_authority": "not_established",
            "memory_admission": "not_established",
            "semantic_correctness": "not_established",
            "execution_claim": "not_established",
            "lifecycle_satisfaction": "not_established",
            "agent_card_authority": "none",
            "task_completion_authority": "none",
        },
    }

    if effective_decision is not None:
        body["effective_decision"] = effective_decision

    optional_refs = (
        "agent_card_ref",
        "task_ref",
        "context_ref",
        "message_ref",
        "artifact_ref",
        "action_ref",
        "scope_ref",
        "tenant_ref",
        "project_ref",
        "pama_decision_ref",
        "composition_ref",
        "approval_evidence_ref",
        "execution_witness_ref",
        "trace_correlation_ref",
    )
    for name in optional_refs:
        value = adapter_result.get(name)
        if value is not None:
            body[name] = _require_ref(name, value)

    if adapter_result.get("input_identity") is not None:
        body["input_identity"] = _require_digest("input_identity", adapter_result["input_identity"])

    for name in ("external_evidence_refs", "correction_refs", "revocation_refs"):
        values = _string_list(name, adapter_result.get(name))
        if values:
            body[name] = values

    if interaction_kind == "message" and "message_ref" not in body:
        raise ValueError("message interaction requires message_ref")
    if interaction_kind == "artifact" and "artifact_ref" not in body:
        raise ValueError("artifact interaction requires artifact_ref")

    binding_status, binding_reasons = _binding(adapter_result, expected_context, export_classification)
    body["binding_status"] = binding_status
    body["binding_reasons"] = binding_reasons
    body["governance_alignment"] = _alignment(
        direction=direction,
        export_classification=export_classification,
        memory_evidence_status=memory_evidence_status,
        governance_status=governance_status,
        effective_decision=effective_decision,
        task_state=task_state,
        binding_status=binding_status,
    )

    identity_body = {key: value for key, value in body.items() if key != "observed_at"}
    document = {
        "schema_version": "1.0.0",
        "profile_version": PROFILE_VERSION,
        "collaboration_id": f"a2a-collaboration:{_sha256_ref(identity_body)}",
        **body,
    }
    receipts.validate("a2a-collaboration-evidence.schema.json", document)
    return document
