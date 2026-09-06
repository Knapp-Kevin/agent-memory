"""Versioned semantic compatibility for memory-derived policy projections.

The evaluator answers one narrow question: is this historical/derived projection
currently compatible with the exact external policy/temporal contract described
by the supplied target evidence? It does not make an authorization decision,
perform a schema migration, or mutate the historical projection.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from ..core import receipts

CURRENTNESS_STATES = {"current", "revalidation_required", "unknown"}
SEMANTIC_STATES = {"compatible", "migration_required", "incompatible", "unknown"}
POLICY_STATES = {"valid", "revalidation_required", "invalid", "unknown", "not_applicable"}
CONSUMER_KINDS = {"dogwood", "cedar", "cedarling", "other"}
ISOLATION_STRATEGIES = {
    "host_partition",
    "universal_symmetric_pin",
    "not_required",
    "unknown",
    "none",
}
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _digest(value: Any, field: str, *, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    value = _required_string(value, field)
    if not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field} must be a sha256 digest")
    return value


def _refs(value: Any, field: str, *, required: bool = False) -> list[str]:
    if value is None:
        value = []
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be an array")
    refs = list(dict.fromkeys(value))
    if not all(isinstance(item, str) and item for item in refs):
        raise ValueError(f"{field} must contain only non-empty strings")
    if required and not refs:
        raise ValueError(f"{field} must not be empty")
    return refs


def _optional_nonnegative_int(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer or null")
    return value


def _evaluation_id(body: dict[str, Any]) -> str:
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _normalize_projection(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("projection must be an object")
    return {
        "projection_ref": _required_string(value.get("projection_ref"), "projection.projection_ref"),
        "projection_profile": _required_string(value.get("projection_profile"), "projection.projection_profile"),
        "projection_version": _required_string(value.get("projection_version"), "projection.projection_version"),
        "projection_digest": _digest(value.get("projection_digest"), "projection.projection_digest"),
        "source_memory_refs": _refs(value.get("source_memory_refs"), "projection.source_memory_refs", required=True),
        "source_domain_schema_ref": _required_string(value.get("source_domain_schema_ref"), "projection.source_domain_schema_ref"),
        "source_domain_schema_digest": _digest(value.get("source_domain_schema_digest"), "projection.source_domain_schema_digest"),
    }


def _normalize_currentness(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("source_currentness must be an object")
    status = value.get("status")
    if status not in CURRENTNESS_STATES:
        raise ValueError("source_currentness.status is invalid")
    return {
        "evaluation_ref": _required_string(value.get("evaluation_ref"), "source_currentness.evaluation_ref"),
        "status": status,
        "evidence_refs": _refs(value.get("evidence_refs"), "source_currentness.evidence_refs"),
    }


def _normalize_target(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("target must be an object")
    consumer_kind = value.get("consumer_kind")
    if consumer_kind not in CONSUMER_KINDS:
        raise ValueError("target.consumer_kind is invalid")
    semantic_status = value.get("semantic_mapping_status")
    if semantic_status not in SEMANTIC_STATES:
        raise ValueError("target.semantic_mapping_status is invalid")
    policy_status = value.get("policy_validation_status")
    if policy_status not in POLICY_STATES:
        raise ValueError("target.policy_validation_status is invalid")

    isolation = value.get("isolation")
    if not isinstance(isolation, dict):
        raise ValueError("target.isolation must be an object")
    strategy = isolation.get("strategy")
    if strategy not in ISOLATION_STRATEGIES:
        raise ValueError("target.isolation.strategy is invalid")
    required = isolation.get("required")
    validated = isolation.get("validated")
    if not isinstance(required, bool) or not isinstance(validated, bool):
        raise ValueError("target.isolation required/validated must be booleans")

    policy_ref = value.get("policy_ref")
    if policy_ref is not None:
        policy_ref = _required_string(policy_ref, "target.policy_ref")
    policy_identity = value.get("policy_digest_or_version")
    if policy_identity is not None:
        policy_identity = _required_string(policy_identity, "target.policy_digest_or_version")

    return {
        "consumer_kind": consumer_kind,
        "consumer_version_or_source_pin": _required_string(value.get("consumer_version_or_source_pin"), "target.consumer_version_or_source_pin"),
        "action_schema_digest": _digest(value.get("action_schema_digest"), "target.action_schema_digest"),
        "event_schema_digest": _digest(value.get("event_schema_digest"), "target.event_schema_digest", optional=True),
        "policy_ref": policy_ref,
        "policy_digest_or_version": policy_identity,
        "semantic_mapping_status": semantic_status,
        "policy_validation_status": policy_status,
        "required_temporal_horizon_seconds": _optional_nonnegative_int(value.get("required_temporal_horizon_seconds"), "target.required_temporal_horizon_seconds"),
        "target_temporal_horizon_seconds": _optional_nonnegative_int(value.get("target_temporal_horizon_seconds"), "target.target_temporal_horizon_seconds"),
        "projected_context_digest": _digest(value.get("projected_context_digest"), "target.projected_context_digest", optional=True),
        "evaluated_context_digest": _digest(value.get("evaluated_context_digest"), "target.evaluated_context_digest", optional=True),
        "isolation": {
            "required": required,
            "strategy": strategy,
            "validated": validated,
            "evidence_refs": _refs(isolation.get("evidence_refs"), "target.isolation.evidence_refs"),
        },
        "evidence_refs": _refs(value.get("evidence_refs"), "target.evidence_refs"),
    }


def evaluate_policy_projection_compatibility(
    projection: dict[str, Any],
    *,
    source_currentness: dict[str, Any],
    target: dict[str, Any],
    evaluated_at: str,
) -> dict[str, Any]:
    """Emit append-only compatibility evidence without mutating the projection."""
    projection_norm = _normalize_projection(projection)
    currentness = _normalize_currentness(source_currentness)
    target_norm = _normalize_target(target)
    evaluated_at = _required_string(evaluated_at, "evaluated_at")

    reasons: list[str] = []
    incompatible = False
    migration_required = False
    unknown = False

    if currentness["status"] == "revalidation_required":
        reasons.append("source_currentness_revalidation_required")
        incompatible = True
    elif currentness["status"] == "unknown":
        reasons.append("source_currentness_unknown")
        unknown = True

    semantic_status = target_norm["semantic_mapping_status"]
    if semantic_status == "migration_required":
        reasons.append("semantic_mapping_migration_required")
        migration_required = True
    elif semantic_status == "incompatible":
        reasons.append("semantic_mapping_incompatible")
        incompatible = True
    elif semantic_status == "unknown":
        reasons.append("semantic_mapping_unknown")
        unknown = True
    elif semantic_status == "compatible" and not target_norm["evidence_refs"]:
        reasons.append("target_compatibility_evidence_missing")
        unknown = True

    policy_status = target_norm["policy_validation_status"]
    if policy_status == "revalidation_required":
        reasons.append("target_policy_revalidation_required")
        migration_required = True
    elif policy_status == "invalid":
        reasons.append("target_policy_invalid")
        incompatible = True
    elif policy_status == "unknown":
        reasons.append("target_policy_validation_unknown")
        unknown = True
    elif policy_status == "not_applicable" and target_norm["consumer_kind"] in {"dogwood", "cedar", "cedarling"}:
        reasons.append("target_policy_validation_not_applicable")
        incompatible = True

    if target_norm["consumer_kind"] == "dogwood" and target_norm["event_schema_digest"] is None:
        reasons.append("dogwood_event_schema_identity_missing")
        unknown = True

    if target_norm["consumer_kind"] in {"dogwood", "cedar", "cedarling"}:
        if target_norm["policy_ref"] is None or target_norm["policy_digest_or_version"] is None:
            reasons.append("target_policy_identity_missing")
            unknown = True

    required_horizon = target_norm["required_temporal_horizon_seconds"]
    target_horizon = target_norm["target_temporal_horizon_seconds"]
    if required_horizon is not None:
        if target_horizon is None:
            reasons.append("target_temporal_horizon_unknown")
            unknown = True
        elif target_horizon < required_horizon:
            reasons.append("target_temporal_horizon_insufficient")
            incompatible = True

    isolation = target_norm["isolation"]
    if isolation["required"]:
        if isolation["strategy"] == "none":
            reasons.append("target_isolation_absent")
            incompatible = True
        elif isolation["strategy"] == "unknown":
            reasons.append("target_isolation_unknown")
            unknown = True
        elif not isolation["validated"]:
            reasons.append("target_isolation_not_validated")
            unknown = True
        elif not isolation["evidence_refs"]:
            reasons.append("target_isolation_evidence_missing")
            unknown = True
    elif isolation["strategy"] == "not_required" and not isolation["validated"]:
        reasons.append("target_isolation_nonrequirement_not_validated")
        unknown = True

    projected_context = target_norm["projected_context_digest"]
    evaluated_context = target_norm["evaluated_context_digest"]
    if projected_context is not None:
        if evaluated_context is None:
            reasons.append("evaluated_context_identity_missing")
            unknown = True
        elif evaluated_context != projected_context:
            reasons.append("evaluated_context_differs_from_projected_context")
            incompatible = True

    if incompatible:
        status = "incompatible"
    elif migration_required:
        status = "migration_required"
    elif unknown:
        status = "unknown"
    else:
        status = "current"

    body = {
        "projection": projection_norm,
        "source_currentness": currentness,
        "target": target_norm,
        "compatibility": {
            "status": status,
            "consequential_use_current": status == "current",
            "revalidation_required": status != "current",
            "reason_codes": list(dict.fromkeys(reasons)),
        },
        "evaluated_at": evaluated_at,
        "interpretation": {
            "authority_effect": "none",
            "historical_projection_mutated": False,
            "memory_admission": "not_established",
            "external_policy_effect": "may_only_tighten_existing_boundary",
            "execution_evidence": "not_established",
            "human_adjudication": "not_established",
            "consumer_trace_role": "derived_noncanonical",
        },
    }
    result = {"schema_version": "1.0.0", "evaluation_id": _evaluation_id(body), **body}
    receipts.validate("policy-projection-compatibility.schema.json", result)
    return result
