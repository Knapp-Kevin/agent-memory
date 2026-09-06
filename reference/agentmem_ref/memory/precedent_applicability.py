"""Deterministic precedent applicability consumer for issue #181.

The consumer accepts the existing Governance Context Projection produced by
``governance_projection.py`` and classifies whether historical governed decision
context is materially applicable to a current action. The result is advisory
only. It cannot create permission, a standing grant, or execution authority.
"""

from __future__ import annotations

from typing import Iterable

from ..core import receipts

SCHEMA_VERSION = "0.1.0"

EXACT_MATCH = "exact_match"
MATERIALLY_EQUIVALENT = "materially_equivalent"
MATERIALLY_DIFFERENT = "materially_different"
STALE = "stale"
CONFLICTING = "conflicting"
INSUFFICIENT_EVIDENCE = "insufficient_evidence"

REDUCE_REVIEW = "reduce_redundant_review"
NORMAL_REVIEW = "normal_review"
ESCALATE = "escalate"
BLOCK_PROPOSAL = "block_proposal_not_authority"

_CURRENT = "current"
_POSITIVE = "supportive"
_NEGATIVE = {"cautionary", "contradictory"}
_RELEVANT_RELATIONSHIPS = {"exact", "material_match"}
_DETERMINISTIC_MODES = {"exact_identity", "deterministic_condition_match"}
_DERIVED_SOURCE_TYPES = {
    "policy_outcome",
    "runtime_observation",
    "memory_inference",
    "external_evidence",
}


def _observation(precedent_ref: str, condition: dict) -> dict:
    return {
        "precedent_ref": precedent_ref,
        "condition": condition["name"],
        "comparison": condition["comparison"],
        "precedent_value": condition.get("precedent_value"),
        "current_value": condition.get("current_value"),
    }


def evaluate_projection(projection: dict) -> dict:
    """Return a deterministic advisory applicability result.

    Only exact identity and deterministic material-condition projections are
    accepted in V0.1. Probabilistic or hybrid retrieval is intentionally
    rejected so semantic similarity cannot quietly become authority.
    """

    receipts.validate("governance-context-projection.schema.json", projection)
    mode = projection["derivation"]["mode"]
    if mode not in _DETERMINISTIC_MODES:
        raise ValueError(
            "precedent applicability V0.1 accepts only exact_identity or "
            "deterministic_condition_match projections"
        )

    supporting_refs: list[str] = []
    cautionary_refs: list[str] = []
    material_matches: list[dict] = []
    material_differences: list[dict] = []
    unknown_conditions: list[dict] = []
    stale_reasons: list[str] = []

    current_support_relationships: list[str] = []
    independent_human_count = 0
    derived_count = 0
    relevant_negative_present = False
    current_support_seen = False
    historical_matching_support_seen = False

    for precedent in projection["precedents"]:
        ref = precedent["memory_ref"]
        polarity = precedent["polarity"]
        relationship = precedent["relationship"]
        validity = precedent["validity"]["status"]
        provenance = precedent["provenance"]

        if polarity == _POSITIVE:
            supporting_refs.append(ref)
        if polarity in _NEGATIVE:
            cautionary_refs.append(ref)

        for condition in precedent["material_conditions"]:
            item = _observation(ref, condition)
            comparison = condition["comparison"]
            if comparison == "match":
                material_matches.append(item)
            elif comparison == "mismatch":
                material_differences.append(item)
            else:
                unknown_conditions.append(item)

        relevant = relationship in _RELEVANT_RELATIONSHIPS
        current = validity == _CURRENT

        # Attribution counts describe current, materially relevant evidence of
        # any polarity. A relevant incident must not disappear merely because
        # it is cautionary instead of supportive.
        if relevant and current:
            if (
                provenance["source_type"] == "human_adjudication"
                and provenance.get("independent_adjudication") is True
            ):
                independent_human_count += 1
            elif provenance["source_type"] in _DERIVED_SOURCE_TYPES:
                derived_count += 1

        if polarity == _POSITIVE and relevant:
            historical_matching_support_seen = True
            if current:
                current_support_seen = True
                current_support_relationships.append(relationship)
            else:
                stale_reasons.append(f"{ref}:{validity}")

        if polarity in _NEGATIVE and relevant:
            if current:
                relevant_negative_present = True
            else:
                stale_reasons.append(f"{ref}:{validity}")

    # Scope is deliberately conservative. V0.1 may reduce review only when the
    # projection says the decision context is from the same governed scope.
    scope_relationship = projection["scope"]["relationship"]
    if scope_relationship != "same":
        applicability = MATERIALLY_DIFFERENT
        handling = ESCALATE
        stale_reasons.append(f"scope_relationship:{scope_relationship}")
    elif relevant_negative_present:
        applicability = CONFLICTING
        handling = ESCALATE
    elif unknown_conditions:
        applicability = INSUFFICIENT_EVIDENCE
        handling = NORMAL_REVIEW
    elif material_differences:
        applicability = MATERIALLY_DIFFERENT
        handling = NORMAL_REVIEW
    elif current_support_seen:
        if current_support_relationships and all(value == "exact" for value in current_support_relationships):
            applicability = EXACT_MATCH
        else:
            applicability = MATERIALLY_EQUIVALENT
        handling = REDUCE_REVIEW
    elif historical_matching_support_seen and stale_reasons:
        applicability = STALE
        handling = NORMAL_REVIEW
    else:
        applicability = INSUFFICIENT_EVIDENCE
        handling = NORMAL_REVIEW

    result = {
        "schema_version": SCHEMA_VERSION,
        "projection_id": projection["projection_id"],
        "applicability": applicability,
        "supporting_precedent_refs": list(dict.fromkeys(supporting_refs)),
        "cautionary_precedent_refs": list(dict.fromkeys(cautionary_refs)),
        "material_matches": material_matches,
        "material_differences": material_differences,
        "unknown_conditions": unknown_conditions,
        "stale_or_invalid_reasons": list(dict.fromkeys(stale_reasons)),
        "independent_human_evidence_count": independent_human_count,
        "policy_or_derived_evidence_count": derived_count,
        "incident_or_negative_evidence_present": relevant_negative_present,
        "recommended_handling": handling,
        "authority_effect": "none",
        "can_authorize_execution": False,
    }
    receipts.validate("precedent-applicability-result.schema.json", result)
    return result


def summarize_metrics(evaluated_cases: Iterable[dict]) -> dict:
    """Aggregate fixture metrics without hiding safety failures in one score.

    Each item contains ``result`` plus an ``expected`` mapping from the fixture.
    This is intentionally explicit: the point is to expose false reductions and
    attribution errors instead of rewarding prompt count.
    """

    cases = list(evaluated_cases)
    reductions = 0
    unsafe_false_positives = 0
    material_difference_misses = 0
    negative_precedent_misses = 0
    cross_scope_leakage_failures = 0
    stale_precedent_reuse_failures = 0
    attribution_errors = 0
    novel_cases = 0
    novel_escalations = 0

    for item in cases:
        result = item["result"]
        expected = item["expected"]
        reduced = result["recommended_handling"] == REDUCE_REVIEW
        if reduced:
            reductions += 1
        if reduced and not expected.get("review_reduction_safe", False):
            unsafe_false_positives += 1
        if expected.get("material_difference", False) and result["applicability"] not in {
            MATERIALLY_DIFFERENT,
            CONFLICTING,
            STALE,
        }:
            material_difference_misses += 1
        if expected.get("negative_present", False) and not result["incident_or_negative_evidence_present"]:
            negative_precedent_misses += 1
        if expected.get("cross_scope", False) and reduced:
            cross_scope_leakage_failures += 1
        if expected.get("stale", False) and reduced:
            stale_precedent_reuse_failures += 1
        if result["independent_human_evidence_count"] != expected.get(
            "independent_human_evidence_count",
            result["independent_human_evidence_count"],
        ):
            attribution_errors += 1
        if result["policy_or_derived_evidence_count"] != expected.get(
            "policy_or_derived_evidence_count",
            result["policy_or_derived_evidence_count"],
        ):
            attribution_errors += 1
        if expected.get("novel", False):
            novel_cases += 1
            if result["recommended_handling"] in {NORMAL_REVIEW, ESCALATE, BLOCK_PROPOSAL}:
                novel_escalations += 1

    return {
        "cases_evaluated": len(cases),
        "redundant_review_reductions_proposed": reductions,
        "unsafe_equivalence_false_positives": unsafe_false_positives,
        "material_difference_misses": material_difference_misses,
        "negative_precedent_misses": negative_precedent_misses,
        "cross_scope_leakage_failures": cross_scope_leakage_failures,
        "stale_precedent_reuse_failures": stale_precedent_reuse_failures,
        "independent_human_derived_evidence_attribution_errors": attribution_errors,
        "novel_case_escalation_rate": (novel_escalations / novel_cases) if novel_cases else 0.0,
    }
