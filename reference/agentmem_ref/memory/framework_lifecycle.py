"""Vendor-neutral framework lifecycle evidence for issue #189.

Framework runtimes may persist checkpoints, sessions, messages, or workflow
state because execution needs them.  This module preserves those facts as
runtime evidence without letting persistence become Agent Memory admission,
authority, or rollback power.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import rfc8785

from ..core import receipts

PROFILE_VERSION = "0.1.0"

EVENT_TYPES = {
    "run_started",
    "recall_requested",
    "recall_admitted",
    "mutation_proposed",
    "mutation_committed",
    "mutation_denied",
    "checkpoint_saved",
    "checkpoint_write_failed",
    "retry",
    "resume",
}
PERSISTENCE_CLASSES = {
    "execution_state",
    "evidence",
    "memory_candidate",
    "explicit_non_memory",
}
CHECKPOINT_RELATIONS = {"current", "stale", "divergent", "unknown"}


def _sha256_ref(value: dict) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _require_ref(name: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def classify_checkpoint_relation(
    checkpoint_ref: str,
    latest_checkpoint_ref: str,
    previous_by_checkpoint: dict[str, str | None],
) -> str:
    """Classify a checkpoint by explicit lineage, never iteration counters.

    A checkpoint that is an ancestor of the latest checkpoint is stale.  A
    checkpoint on another lineage is divergent.  Missing lineage information
    is unknown rather than optimistically current.
    """

    _require_ref("checkpoint_ref", checkpoint_ref)
    _require_ref("latest_checkpoint_ref", latest_checkpoint_ref)
    if checkpoint_ref == latest_checkpoint_ref:
        return "current"
    if latest_checkpoint_ref not in previous_by_checkpoint:
        return "unknown"

    seen: set[str] = set()
    cursor: str | None = latest_checkpoint_ref
    while cursor is not None:
        if cursor in seen:
            raise ValueError("checkpoint lineage contains a cycle")
        seen.add(cursor)
        if cursor == checkpoint_ref:
            return "stale"
        if cursor not in previous_by_checkpoint:
            return "unknown"
        cursor = previous_by_checkpoint[cursor]

    if checkpoint_ref in previous_by_checkpoint:
        return "divergent"
    return "unknown"


@dataclass
class MutationReplayGuard:
    """Small deterministic idempotency ledger for framework retry/resume seams."""

    _receipts: dict[str, str] = field(default_factory=dict)

    def prior_receipt(self, idempotency_key: str) -> str | None:
        _require_ref("idempotency_key", idempotency_key)
        return self._receipts.get(idempotency_key)

    def record(self, idempotency_key: str, receipt_ref: str) -> str:
        key = _require_ref("idempotency_key", idempotency_key)
        receipt = _require_ref("receipt_ref", receipt_ref)
        existing = self._receipts.get(key)
        if existing is not None and existing != receipt:
            raise ValueError("idempotency key is already bound to a different receipt")
        self._receipts[key] = receipt
        return "replay" if existing is not None else "recorded"


def build_framework_lifecycle_event(
    *,
    framework_id: str,
    framework_version: str,
    framework_source_ref: str,
    framework_source_commit: str | None,
    event_type: str,
    run_ref: str,
    workflow_ref: str,
    persistence_classification: str,
    occurred_at: str,
    expected_context: dict | None = None,
    session_ref: str | None = None,
    checkpoint_ref: str | None = None,
    previous_checkpoint_ref: str | None = None,
    checkpoint_relation: str | None = None,
    checkpoint_format_version: str | None = None,
    iteration_count: int | None = None,
    action_ref: str | None = None,
    input_identity: str | None = None,
    pama_decision_ref: str | None = None,
    decision_receipt_ref: str | None = None,
    composition_ref: str | None = None,
    approval_evidence_ref: str | None = None,
    execution_witness_ref: str | None = None,
    trace_correlation_ref: str | None = None,
    scope_ref: str | None = None,
    tenant_ref: str | None = None,
    project_ref: str | None = None,
    memory_state_ref: str | None = None,
    idempotency_key: str | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> dict:
    """Build one minimized, reconstructable framework lifecycle event."""

    if event_type not in EVENT_TYPES:
        raise ValueError(f"invalid event_type {event_type!r}")
    if persistence_classification not in PERSISTENCE_CLASSES:
        raise ValueError(f"invalid persistence_classification {persistence_classification!r}")
    if checkpoint_relation is not None and checkpoint_relation not in CHECKPOINT_RELATIONS:
        raise ValueError(f"invalid checkpoint_relation {checkpoint_relation!r}")
    if iteration_count is not None and iteration_count < 0:
        raise ValueError("iteration_count cannot be negative")
    if checkpoint_ref is None and any(
        value is not None
        for value in (previous_checkpoint_ref, checkpoint_relation, checkpoint_format_version, iteration_count)
    ):
        raise ValueError("checkpoint metadata requires checkpoint_ref")

    framework = {
        "framework_id": _require_ref("framework_id", framework_id),
        "version": _require_ref("framework_version", framework_version),
        "source_ref": _require_ref("framework_source_ref", framework_source_ref),
    }
    if framework_source_commit is not None:
        if len(framework_source_commit) != 40 or any(ch not in "0123456789abcdef" for ch in framework_source_commit):
            raise ValueError("framework_source_commit must be a lowercase 40-hex commit")
        framework["source_commit"] = framework_source_commit

    body: dict = {
        "framework": framework,
        "event_type": event_type,
        "run_ref": _require_ref("run_ref", run_ref),
        "workflow_ref": _require_ref("workflow_ref", workflow_ref),
        "persistence_classification": persistence_classification,
        "occurred_at": _require_ref("occurred_at", occurred_at),
        "evidence_refs": list(dict.fromkeys(evidence_refs)),
        "interpretation": {
            "authority_effect": "none",
            "memory_admission": "not_established",
            "lifecycle_satisfaction": "not_established",
            "checkpoint_rollback_authority": "not_established",
        },
    }

    optional = {
        "session_ref": session_ref,
        "action_ref": action_ref,
        "input_identity": input_identity,
        "pama_decision_ref": pama_decision_ref,
        "decision_receipt_ref": decision_receipt_ref,
        "composition_ref": composition_ref,
        "approval_evidence_ref": approval_evidence_ref,
        "execution_witness_ref": execution_witness_ref,
        "trace_correlation_ref": trace_correlation_ref,
        "scope_ref": scope_ref,
        "tenant_ref": tenant_ref,
        "project_ref": project_ref,
        "memory_state_ref": memory_state_ref,
        "idempotency_key": idempotency_key,
    }
    for name, value in optional.items():
        if value is not None:
            body[name] = _require_ref(name, value)

    if checkpoint_ref is not None:
        checkpoint = {
            "checkpoint_ref": _require_ref("checkpoint_ref", checkpoint_ref),
            "relation_to_latest": checkpoint_relation or "unknown",
        }
        if previous_checkpoint_ref is not None:
            checkpoint["previous_checkpoint_ref"] = _require_ref(
                "previous_checkpoint_ref", previous_checkpoint_ref
            )
        if checkpoint_format_version is not None:
            checkpoint["checkpoint_format_version"] = _require_ref(
                "checkpoint_format_version", checkpoint_format_version
            )
        if iteration_count is not None:
            checkpoint["iteration_count"] = iteration_count
        body["checkpoint"] = checkpoint

    binding_reasons: list[str] = []
    if expected_context:
        for field_name in ("action_ref", "input_identity", "scope_ref", "tenant_ref", "project_ref"):
            expected = expected_context.get(field_name)
            if expected is None:
                continue
            actual = body.get(field_name)
            if actual is None:
                binding_reasons.append(f"{field_name}_missing")
            elif actual != expected:
                binding_reasons.append(f"{field_name}_mismatch")
        body["binding_status"] = "mismatch" if binding_reasons else "exact"
    else:
        body["binding_status"] = "not_evaluated"
    body["binding_reasons"] = binding_reasons

    identity_body = {key: value for key, value in body.items() if key != "occurred_at"}
    document = {
        "schema_version": "1.0.0",
        "profile_version": PROFILE_VERSION,
        "event_id": f"framework-event:{_sha256_ref(identity_body)}",
        **body,
    }
    receipts.validate("framework-lifecycle-event.schema.json", document)
    return document
