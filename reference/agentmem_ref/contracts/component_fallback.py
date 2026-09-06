"""Explicit capability fallback evaluation for #300/#280.

Fallback is a routing decision after an already-selected provider becomes
unavailable. It is never implicit registration-order behavior and never grants
memory, recall, structural, or action authority.

The evaluator is deliberately conservative. A fallback candidate must be
explicitly allowed and must preserve the selected capability's version,
maturity floor, state posture, scope posture, failure posture, authority effect,
qualification profile, qualification currentness, and runtime source-rights
posture. Otherwise the operation remains explicitly unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .capabilities import ResolvedCapability, maturity_satisfies
from .qualification import QualificationRecord


class FallbackError(ValueError):
    """Fallback evidence or configuration is internally inconsistent."""


@dataclass(frozen=True)
class ProviderFailure:
    component_id: str
    capability_id: str
    failure_result: str
    evidence_ref: str
    trace_ref: str

    def __post_init__(self) -> None:
        for name, value in (
            ("component_id", self.component_id),
            ("capability_id", self.capability_id),
            ("failure_result", self.failure_result),
            ("evidence_ref", self.evidence_ref),
            ("trace_ref", self.trace_ref),
        ):
            if not value:
                raise ValueError(f"{name} is required")
        if self.failure_result == "none":
            raise ValueError("fallback requires an actual provider failure result")

    def to_dict(self) -> dict[str, str]:
        return {
            "component_id": self.component_id,
            "capability_id": self.capability_id,
            "failure_result": self.failure_result,
            "evidence_ref": self.evidence_ref,
            "trace_ref": self.trace_ref,
        }


@dataclass(frozen=True)
class QualifiedCapability:
    resolved: ResolvedCapability
    qualification: QualificationRecord

    def __post_init__(self) -> None:
        subject = self.qualification.subject
        if subject.component_id != self.resolved.component_id:
            raise FallbackError("qualification component does not match resolved component")
        if subject.component_version != self.resolved.component_version:
            raise FallbackError("qualification component version does not match resolved component")
        if subject.capability_id != self.resolved.capability_id:
            raise FallbackError("qualification capability does not match resolved capability")
        if subject.capability_version != self.resolved.capability_version:
            raise FallbackError("qualification capability version does not match resolved capability")
        if self.qualification.authority_effect != "none":
            raise FallbackError("qualification cannot grant fallback authority")


@dataclass(frozen=True)
class FallbackDecision:
    status: str
    primary_component_id: str
    capability_id: str
    failure_result: str
    selected_component_id: str = ""
    reason: str = ""
    rejected_candidates: tuple[tuple[str, tuple[str, ...]], ...] = ()

    @property
    def authority_effect(self) -> str:
        return "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "primary_component_id": self.primary_component_id,
            "capability_id": self.capability_id,
            "failure_result": self.failure_result,
            "selected_component_id": self.selected_component_id or None,
            "reason": self.reason,
            "rejected_candidates": [
                {"component_id": component_id, "reasons": list(reasons)}
                for component_id, reasons in self.rejected_candidates
            ],
            "authority_effect": "none",
        }


def _qualification_reasons(
    primary: QualifiedCapability,
    candidate: QualifiedCapability,
) -> list[str]:
    reasons: list[str] = []
    left = primary.resolved
    right = candidate.resolved
    left_q = primary.qualification
    right_q = candidate.qualification

    if right.capability_id != left.capability_id:
        reasons.append("capability_id_mismatch")
    if right.capability_version != left.capability_version:
        reasons.append("capability_version_mismatch")
    if not maturity_satisfies(right.maturity, left.maturity):
        reasons.append("weaker_maturity")
    if right.state_posture != left.state_posture:
        reasons.append("state_posture_mismatch")
    if right.scope_posture != left.scope_posture:
        reasons.append("scope_posture_mismatch")
    if right.failure_posture != left.failure_posture:
        reasons.append("failure_posture_mismatch")
    if right.authority_effect != left.authority_effect:
        reasons.append("authority_effect_mismatch")

    left_subject = left_q.subject
    right_subject = right_q.subject
    if right_subject.qualification_profile_id != left_subject.qualification_profile_id:
        reasons.append("qualification_profile_mismatch")
    if right_subject.qualification_profile_version != left_subject.qualification_profile_version:
        reasons.append("qualification_profile_version_mismatch")
    if not right_q.qualification_current:
        reasons.append("qualification_not_current")
    if right_q.use_posture != "runtime_allowed":
        reasons.append("source_rights_not_runtime_allowed")
    if not maturity_satisfies(right_q.earned_maturity, left.maturity):
        reasons.append("qualification_maturity_below_primary")

    return reasons


def evaluate_explicit_fallback(
    *,
    primary: QualifiedCapability,
    failure: ProviderFailure,
    candidates: Iterable[QualifiedCapability],
    allowed_components: Iterable[str],
) -> FallbackDecision:
    """Select one explicitly configured equivalent fallback or remain unavailable."""

    if failure.component_id != primary.resolved.component_id:
        raise FallbackError("failure component does not match selected primary")
    if failure.capability_id != primary.resolved.capability_id:
        raise FallbackError("failure capability does not match selected primary")

    if primary.qualification.use_posture != "runtime_allowed":
        raise FallbackError("primary runtime selection lacks runtime-allowed source rights")
    if not primary.qualification.qualification_current:
        raise FallbackError("primary runtime selection lacks a current qualification")

    allowed = tuple(dict.fromkeys(allowed_components))
    if not allowed:
        return FallbackDecision(
            status="unavailable",
            primary_component_id=primary.resolved.component_id,
            capability_id=primary.resolved.capability_id,
            failure_result=failure.failure_result,
            reason="fallback_not_configured",
        )

    candidate_by_id = {candidate.resolved.component_id: candidate for candidate in candidates}
    compatible: list[QualifiedCapability] = []
    rejected: list[tuple[str, tuple[str, ...]]] = []

    for component_id in allowed:
        candidate = candidate_by_id.get(component_id)
        if candidate is None:
            rejected.append((component_id, ("configured_fallback_not_available",)))
            continue
        reasons = _qualification_reasons(primary, candidate)
        if reasons:
            rejected.append((component_id, tuple(reasons)))
            continue
        compatible.append(candidate)

    if not compatible:
        return FallbackDecision(
            status="unavailable",
            primary_component_id=primary.resolved.component_id,
            capability_id=primary.resolved.capability_id,
            failure_result=failure.failure_result,
            reason="no_equivalent_fallback",
            rejected_candidates=tuple(rejected),
        )

    if len(compatible) > 1:
        return FallbackDecision(
            status="unavailable",
            primary_component_id=primary.resolved.component_id,
            capability_id=primary.resolved.capability_id,
            failure_result=failure.failure_result,
            reason="ambiguous_equivalent_fallbacks",
            rejected_candidates=tuple(rejected),
        )

    selected = compatible[0]
    return FallbackDecision(
        status="fallback_selected",
        primary_component_id=primary.resolved.component_id,
        capability_id=primary.resolved.capability_id,
        failure_result=failure.failure_result,
        selected_component_id=selected.resolved.component_id,
        reason="explicit_equivalent_fallback",
        rejected_candidates=tuple(rejected),
    )
