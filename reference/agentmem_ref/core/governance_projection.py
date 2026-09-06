"""Deterministic reference builder for vendor-neutral governance context.

This module implements the first executable slice of ADR-029. It deliberately
builds remembered context, not a governance verdict. Consumer-specific policy,
risk, approval, and enforcement semantics belong downstream.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_POLARITIES = {"supportive", "cautionary", "contradictory", "neutral"}
VALID_VALIDITY = {"current", "stale", "expired", "superseded", "revoked", "disputed", "historical"}
VALID_SOURCE_TYPES = {
    "human_adjudication",
    "policy_outcome",
    "runtime_observation",
    "memory_inference",
    "external_evidence",
}
NEGATIVE_POLARITIES = {"cautionary", "contradictory"}


@dataclass(frozen=True)
class MaterialCondition:
    name: str
    precedent_value: Any
    current_value: Any
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class PrecedentInput:
    memory_ref: str
    polarity: str
    conditions: tuple[MaterialCondition, ...]
    source_type: str
    source_ref: str
    validity_status: str = "current"
    rationale_ref: str | None = None
    rationale_summary: str | None = None
    outcome_refs: tuple[str, ...] = ()
    authority_ref: str | None = None
    independent_adjudication: bool = False
    policy_version_ref: str | None = None


@dataclass(frozen=True)
class ProjectionRequest:
    projection_id: str
    current_context_ref: str
    domain_refs: tuple[str, ...]
    scope_relationship: str
    precedents: tuple[PrecedentInput, ...]
    source_snapshot_ref: str
    generated_at: str
    purpose_ref: str | None = None
    sensitivity_labels: tuple[str, ...] = ()
    privacy_minimized: bool = True


def _validate_precedent(precedent: PrecedentInput) -> None:
    if not precedent.memory_ref or not precedent.source_ref:
        raise ValueError("precedent requires memory_ref and source_ref")
    if precedent.polarity not in VALID_POLARITIES:
        raise ValueError(f"invalid precedent polarity: {precedent.polarity!r}")
    if precedent.validity_status not in VALID_VALIDITY:
        raise ValueError(f"invalid precedent validity: {precedent.validity_status!r}")
    if precedent.source_type not in VALID_SOURCE_TYPES:
        raise ValueError(f"invalid precedent source_type: {precedent.source_type!r}")
    if not precedent.conditions:
        raise ValueError("precedent requires at least one material condition")
    if precedent.independent_adjudication and precedent.source_type != "human_adjudication":
        raise ValueError(
            "independent_adjudication may only be true for human_adjudication; "
            "derived or policy outcomes must not launder themselves into human precedent"
        )
    for condition in precedent.conditions:
        if not condition.name:
            raise ValueError("material condition requires a name")


def _compare_condition(condition: MaterialCondition) -> str:
    if condition.precedent_value is None or condition.current_value is None:
        return "unknown"
    return "match" if condition.precedent_value == condition.current_value else "mismatch"


def _relationship(comparisons: tuple[str, ...]) -> str:
    if any(comparison == "mismatch" for comparison in comparisons):
        return "material_mismatch"
    if comparisons and all(comparison == "match" for comparison in comparisons):
        return "material_match"
    return "unknown"


def build_governance_projection(request: ProjectionRequest) -> dict[str, Any]:
    """Build deterministic governance context from explicit precedent inputs.

    The output intentionally conforms to the V0.1 projection shape without
    emitting a consumer verdict, standing permission, or risk score.
    """
    if not request.projection_id or not request.current_context_ref:
        raise ValueError("projection requires projection_id and current_context_ref")
    if not request.domain_refs:
        raise ValueError("projection requires at least one scope domain_ref")
    if request.scope_relationship not in {"same", "crossing_authorized", "mismatch", "unknown"}:
        raise ValueError(f"invalid scope relationship: {request.scope_relationship!r}")
    if not request.precedents:
        raise ValueError("projection requires at least one precedent")
    if not request.source_snapshot_ref or not request.generated_at:
        raise ValueError("projection requires source_snapshot_ref and generated_at")

    seen: set[str] = set()
    source_memory_refs: list[str] = []
    projected_precedents: list[dict[str, Any]] = []
    negative_precedent_refs: list[str] = []

    for precedent in request.precedents:
        _validate_precedent(precedent)
        if precedent.memory_ref in seen:
            raise ValueError(f"duplicate precedent memory_ref: {precedent.memory_ref!r}")
        seen.add(precedent.memory_ref)
        source_memory_refs.append(precedent.memory_ref)

        conditions: list[dict[str, Any]] = []
        comparison_values: list[str] = []
        for condition in precedent.conditions:
            comparison = _compare_condition(condition)
            comparison_values.append(comparison)
            item: dict[str, Any] = {
                "name": condition.name,
                "precedent_value": condition.precedent_value,
                "current_value": condition.current_value,
                "comparison": comparison,
            }
            if condition.evidence_refs:
                item["evidence_refs"] = list(condition.evidence_refs)
            conditions.append(item)

        projected: dict[str, Any] = {
            "memory_ref": precedent.memory_ref,
            "polarity": precedent.polarity,
            "relationship": _relationship(tuple(comparison_values)),
            "material_conditions": conditions,
            "validity": {"status": precedent.validity_status},
            "provenance": {
                "source_type": precedent.source_type,
                "source_ref": precedent.source_ref,
                "independent_adjudication": precedent.independent_adjudication,
            },
        }

        if precedent.rationale_ref:
            projected["rationale_ref"] = precedent.rationale_ref
        if precedent.rationale_summary:
            projected["rationale_summary"] = precedent.rationale_summary
        if precedent.outcome_refs:
            projected["outcome_refs"] = list(precedent.outcome_refs)
        if precedent.authority_ref:
            projected["provenance"]["authority_ref"] = precedent.authority_ref
        if precedent.policy_version_ref:
            projected["validity"]["policy_version_ref"] = precedent.policy_version_ref

        if precedent.polarity in NEGATIVE_POLARITIES:
            negative_precedent_refs.append(precedent.memory_ref)

        projected_precedents.append(projected)

    projection: dict[str, Any] = {
        "schema_version": "0.1.0",
        "projection_id": request.projection_id,
        "purpose": "governance_decision_context",
        "current_context_ref": request.current_context_ref,
        "source_memory_refs": source_memory_refs,
        "scope": {
            "domain_refs": list(request.domain_refs),
            "relationship": request.scope_relationship,
        },
        "precedents": projected_precedents,
        "derivation": {
            "mode": "deterministic_condition_match",
            "reconstructable": True,
            "source_snapshot_ref": request.source_snapshot_ref,
        },
        "sensitivity": {
            "privacy_minimized": request.privacy_minimized,
            "labels": list(request.sensitivity_labels),
        },
        "generated_at": request.generated_at,
    }

    if request.purpose_ref:
        projection["scope"]["purpose_ref"] = request.purpose_ref
    if negative_precedent_refs:
        projection["negative_precedent_refs"] = negative_precedent_refs

    return projection
