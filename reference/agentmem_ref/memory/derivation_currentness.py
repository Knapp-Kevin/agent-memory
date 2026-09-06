"""Append-only currentness evaluation for historical derivations, issue #210.

A derivation record says what was transformed, from which root sources, under
which scope, at a historical point in time. Later source revocation, dispute,
supersession, deletion, tombstoning, or scope reduction must not rewrite that
history. This module emits a separate currentness evaluation instead.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ..core import receipts

SOURCE_STATES = {
    "current",
    "disputed",
    "revoked",
    "superseded",
    "tombstoned",
    "deleted",
    "unknown",
}
EVIDENCE_CLASSES = {"ordinary", "negative", "adversarial", "correction", "incident"}
SCOPE_STATES = {"unchanged", "reduced", "revoked", "unknown"}
NONCURRENT_STATES = {"disputed", "revoked", "superseded", "tombstoned", "deleted"}


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _refs(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{field} must be an array")
    refs = list(dict.fromkeys(value))
    if not all(isinstance(item, str) and item for item in refs):
        raise ValueError(f"{field} must contain only non-empty strings")
    return refs


def _normalize_source_observation(value: dict[str, Any], index: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"source_observations[{index}] must be an object")
    origin_ref = _required_string(value.get("origin_ref"), f"source_observations[{index}].origin_ref")
    state = value.get("state")
    if state not in SOURCE_STATES:
        raise ValueError(f"source_observations[{index}].state is invalid")
    evidence_class = value.get("evidence_class", "ordinary")
    if evidence_class not in EVIDENCE_CLASSES:
        raise ValueError(f"source_observations[{index}].evidence_class is invalid")
    return {
        "origin_ref": origin_ref,
        "observed": True,
        "state": state,
        "evidence_class": evidence_class,
        "evidence_refs": _refs(value.get("evidence_refs"), f"source_observations[{index}].evidence_refs"),
    }


def _missing_observation(origin_ref: str) -> dict[str, Any]:
    return {
        "origin_ref": origin_ref,
        "observed": False,
        "state": "unknown",
        "evidence_class": "ordinary",
        "evidence_refs": [],
    }


def _normalize_scope_observation(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("scope_observation must be an object")
    status = value.get("status")
    if status not in SCOPE_STATES:
        raise ValueError("scope_observation.status is invalid")
    return {
        "status": status,
        "current_scope_ref": _required_string(value.get("current_scope_ref"), "scope_observation.current_scope_ref"),
        "tenant_ref": _required_string(value.get("tenant_ref"), "scope_observation.tenant_ref"),
        "project_ref": _required_string(value.get("project_ref"), "scope_observation.project_ref"),
        "evidence_refs": _refs(value.get("evidence_refs"), "scope_observation.evidence_refs"),
    }


def _evidence_character(observations: list[dict[str, Any]]) -> str:
    classes = {item["evidence_class"] for item in observations if item["observed"]}
    if classes.intersection({"negative", "adversarial"}):
        return "negative_or_adversarial"
    if classes.intersection({"correction", "incident"}):
        return "correction_or_incident"
    return "ordinary"


def _evaluation_id(body: dict[str, Any]) -> str:
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def evaluate_derivation_currentness(
    derivation: dict[str, Any],
    *,
    source_observations: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    scope_observation: dict[str, Any],
    evaluated_at: str,
) -> dict[str, Any]:
    """Evaluate current applicability without mutating historical derivation evidence.

    Every root origin named by the derivation is evaluated independently. Extra
    observations are retained only as unexpected refs and cannot substitute for
    a missing root. Multi-hop child derivations naturally inherit the same root
    list, so currentness propagates from original sources rather than only the
    immediate parent derivation.
    """
    receipts.validate("derivation-evidence.schema.json", derivation)
    evaluated_at = _required_string(evaluated_at, "evaluated_at")
    if not isinstance(source_observations, (list, tuple)):
        raise ValueError("source_observations must be an array")

    normalized_input = [
        _normalize_source_observation(item, index)
        for index, item in enumerate(source_observations)
    ]
    by_origin: dict[str, dict[str, Any]] = {}
    for item in normalized_input:
        if item["origin_ref"] in by_origin:
            raise ValueError(f"duplicate source observation for {item['origin_ref']}")
        by_origin[item["origin_ref"]] = item

    root_refs = list(derivation["root_origin_refs"])
    root_set = set(root_refs)
    unexpected = sorted(set(by_origin) - root_set)
    ordered: list[dict[str, Any]] = []
    reasons: list[str] = []
    definite_revalidation = False
    unknown = False

    for root_ref in root_refs:
        observation = by_origin.get(root_ref)
        if observation is None:
            observation = _missing_observation(root_ref)
            reasons.append(f"missing_source_observation:{root_ref}")
            unknown = True
        elif observation["state"] in NONCURRENT_STATES:
            reasons.append(f"source_{observation['state']}:{root_ref}")
            definite_revalidation = True
        elif observation["state"] == "unknown":
            reasons.append(f"source_state_unknown:{root_ref}")
            unknown = True
        ordered.append(observation)

    transformation_status = derivation["transformation"].get("status", "complete")
    if transformation_status in {"partial", "failed"}:
        reasons.append(f"transformation_{transformation_status}")
        definite_revalidation = True

    current_scope = _normalize_scope_observation(scope_observation)
    historical_scope = derivation["scope"]
    if current_scope["tenant_ref"] != historical_scope["tenant_ref"]:
        reasons.append("scope_tenant_mismatch")
        definite_revalidation = True
    if current_scope["project_ref"] != historical_scope["project_ref"]:
        reasons.append("scope_project_mismatch")
        definite_revalidation = True

    scope_status = current_scope["status"]
    if scope_status == "unchanged":
        if current_scope["current_scope_ref"] != historical_scope["scope_ref"]:
            reasons.append("scope_changed_without_reduction_evidence")
            definite_revalidation = True
    elif scope_status == "reduced":
        if current_scope["current_scope_ref"] == historical_scope["scope_ref"]:
            reasons.append("scope_reduction_not_demonstrated")
        else:
            reasons.append("source_scope_reduced")
        definite_revalidation = True
    elif scope_status == "revoked":
        reasons.append("source_scope_or_membership_revoked")
        definite_revalidation = True
    elif scope_status == "unknown":
        reasons.append("scope_state_unknown")
        unknown = True

    if definite_revalidation:
        status = "revalidation_required"
    elif unknown:
        status = "unknown"
    else:
        status = "current"

    body = {
        "derivation_id": derivation["derivation_id"],
        "root_origin_refs": root_refs,
        "source_observations": ordered,
        "unexpected_source_refs": unexpected,
        "scope_observation": current_scope,
        "applicability": {
            "status": status,
            "revalidation_required": status != "current",
            "reasons": list(dict.fromkeys(reasons)),
        },
        "evidence_character": _evidence_character(ordered),
        "evaluated_at": evaluated_at,
        "interpretation": {
            "authority_effect": "none",
            "memory_admission": "not_established",
            "certification_claim": "none",
            "remote_mutation": "not_established",
            "historical_derivation_mutated": False,
            "prior_authorization_reusable": False,
            "currentness_evidence_authority": "none",
        },
    }
    result = {
        "schema_version": "1.0.0",
        "evaluation_id": _evaluation_id(body),
        **body,
    }
    receipts.validate("derivation-currentness-evaluation.schema.json", result)
    return result
