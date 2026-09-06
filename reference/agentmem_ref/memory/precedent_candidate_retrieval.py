"""Estimator-mediated precedent candidate retrieval for issue #233.

This module deliberately stops at candidate discovery. Estimator output is evidence
about retrieval usefulness, never evidence of authority. Every candidate must still
pass through ``precedent_applicability.evaluate_projection`` before governance may
use its advisory applicability context.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Iterable, Mapping, Protocol, Sequence

from ..core import receipts
from .precedent_applicability import evaluate_projection

SCHEMA_VERSION = "0.1.0"

COMPLETED = "completed"
UNAVAILABLE = "unavailable"
UNSUPPORTED = "unsupported"

AUTHORITY_EFFECT = "none"

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_DEFAULT_ALIASES = {
    "upload": "push",
    "publish": "push",
    "send": "push",
    "featurebranch": "feature_branch",
    "feature": "feature_branch",
    "nonprotected": "unprotected",
    "normal": "ordinary",
    "regular": "ordinary",
    "prod": "production",
    "credential": "sensitive",
    "credentials": "sensitive",
    "secret": "sensitive",
    "secrets": "sensitive",
}


class EstimatorUnavailable(RuntimeError):
    """Raised when an estimator cannot execute at all."""


class UnsupportedEstimatorVersion(RuntimeError):
    """Raised when an estimator implementation/version is unsupported."""


class CandidateEstimator(Protocol):
    """Small estimator interface. Scores are retrieval evidence, not truth."""

    estimator_id: str
    estimator_version: str
    configuration_ref: str
    threshold_ref: str
    score_semantics: str
    calibration_posture: str

    def score(self, query_features: Sequence[str], candidate_features: Sequence[str]) -> float:
        """Return a bounded candidate score."""


@dataclass(frozen=True)
class CandidatePrecedent:
    precedent_ref: str
    projection_identity: str
    features: tuple[str, ...]
    evidence_class: str = "unspecified"
    rationale_summary: str | None = None


@dataclass(frozen=True)
class RetrievalRequest:
    run_ref: str
    query_projection_identity: str
    query_features: tuple[str, ...]
    candidates: tuple[CandidatePrecedent, ...]
    executed_at: str
    threshold: float
    privacy_minimized: bool = True


class DeterministicReferenceEstimator:
    """Deterministic fixture estimator for repository conformance.

    It canonicalizes a deliberately tiny alias table and uses Jaccard overlap.
    This is not a claim that lexical overlap is a production semantic model.
    It exists so the estimator/governance boundary is executable without pinning
    canonical Agent Memory to embeddings, a model vendor, or a programming language.
    """

    estimator_id = "agent-memory/reference-token-jaccard"
    estimator_version = "0.1.0"
    configuration_ref = "config:precedent-candidate-reference-estimator:v1"
    threshold_ref = "threshold:precedent-candidate-reference-estimator:v1"
    score_semantics = "canonicalized_token_jaccard_similarity_0_to_1"
    calibration_posture = "uncalibrated_reference_fixture"

    def __init__(self, aliases: Mapping[str, str] | None = None) -> None:
        self._aliases = dict(_DEFAULT_ALIASES)
        if aliases:
            self._aliases.update(aliases)

    def _tokens(self, features: Sequence[str]) -> set[str]:
        tokens: set[str] = set()
        for feature in features:
            normalized = feature.lower().replace("-", " ").replace("_", " ")
            for token in _TOKEN_RE.findall(normalized):
                tokens.add(self._aliases.get(token, token))
        return tokens

    def score(self, query_features: Sequence[str], candidate_features: Sequence[str]) -> float:
        query = self._tokens(query_features)
        candidate = self._tokens(candidate_features)
        if not query and not candidate:
            return 1.0
        if not query or not candidate:
            return 0.0
        return len(query & candidate) / len(query | candidate)


class UnavailableReferenceEstimator(DeterministicReferenceEstimator):
    estimator_id = "agent-memory/reference-unavailable"
    estimator_version = "0.1.0"

    def score(self, query_features: Sequence[str], candidate_features: Sequence[str]) -> float:
        raise EstimatorUnavailable("reference estimator unavailable")


class UnsupportedReferenceEstimator(DeterministicReferenceEstimator):
    estimator_id = "agent-memory/reference-unsupported"
    estimator_version = "999.0.0"

    def score(self, query_features: Sequence[str], candidate_features: Sequence[str]) -> float:
        raise UnsupportedEstimatorVersion("reference estimator version unsupported")


def _non_authority_fields() -> dict:
    return {
        "authority_effect": AUTHORITY_EFFECT,
        "can_authorize_execution": False,
        "can_change_permitted_actions": False,
        "can_create_grant_or_policy": False,
    }


def _base_evidence(request: RetrievalRequest, estimator: CandidateEstimator, status: str) -> dict:
    if not request.run_ref or not request.query_projection_identity or not request.executed_at:
        raise ValueError("retrieval request requires run_ref, query projection identity, and timestamp")
    if not 0.0 <= request.threshold <= 1.0:
        raise ValueError("retrieval threshold must be between 0 and 1")
    if not request.query_features:
        raise ValueError("retrieval request requires minimized query features")

    document = {
        "schema_version": SCHEMA_VERSION,
        "run_ref": request.run_ref,
        "status": status,
        "estimator": {
            "estimator_id": estimator.estimator_id,
            "estimator_version": estimator.estimator_version,
            "configuration_ref": estimator.configuration_ref,
            "threshold_ref": estimator.threshold_ref,
            "score_semantics": estimator.score_semantics,
            "calibration_posture": estimator.calibration_posture,
            "threshold": request.threshold,
        },
        "input_projection": {
            "identity": request.query_projection_identity,
            "privacy_minimized": request.privacy_minimized,
        },
        "candidates": [],
        "executed_at": request.executed_at,
        **_non_authority_fields(),
    }
    return document


def retrieve_candidates(request: RetrievalRequest, estimator: CandidateEstimator) -> dict:
    """Retrieve candidate precedent refs while preserving estimator evidence.

    All candidates are scored independently. Frequency never boosts a score, and
    no evidence class is suppressed merely because another class is more common.
    Historical rationale is never evaluated or executed by this reference matcher.
    """

    evidence = _base_evidence(request, estimator, COMPLETED)
    scored: list[dict] = []

    try:
        for candidate in request.candidates:
            if not candidate.precedent_ref or not candidate.projection_identity:
                raise ValueError("candidate requires precedent_ref and projection identity")
            if not candidate.features:
                raise ValueError("candidate requires minimized features")
            raw_score = estimator.score(request.query_features, candidate.features)
            if not math.isfinite(raw_score) or not 0.0 <= raw_score <= 1.0:
                raise ValueError("estimator score must be finite and between 0 and 1")
            scored.append(
                {
                    "candidate_precedent_ref": candidate.precedent_ref,
                    "candidate_projection_identity": candidate.projection_identity,
                    "score": round(float(raw_score), 6),
                    "score_semantics": estimator.score_semantics,
                    "above_threshold": raw_score >= request.threshold,
                    "evidence_class": candidate.evidence_class,
                    "historical_rationale_treatment": "data_not_instruction",
                    **_non_authority_fields(),
                }
            )
    except EstimatorUnavailable as exc:
        evidence["status"] = UNAVAILABLE
        evidence["failure"] = {
            "kind": "estimator_unavailable",
            "message": str(exc),
            "fail_open": False,
        }
        receipts.validate("precedent-candidate-retrieval.schema.json", evidence)
        return evidence
    except UnsupportedEstimatorVersion as exc:
        evidence["status"] = UNSUPPORTED
        evidence["failure"] = {
            "kind": "unsupported_estimator_version",
            "message": str(exc),
            "fail_open": False,
        }
        receipts.validate("precedent-candidate-retrieval.schema.json", evidence)
        return evidence

    scored.sort(
        key=lambda item: (
            -item["score"],
            item["candidate_precedent_ref"],
        )
    )
    for rank, item in enumerate(scored, start=1):
        item["rank"] = rank

    evidence["candidates"] = scored
    receipts.validate("precedent-candidate-retrieval.schema.json", evidence)
    return evidence


def selected_candidate_refs(evidence: dict) -> tuple[str, ...]:
    """Return above-threshold refs only when retrieval completed.

    An unavailable or unsupported estimator yields no semantic candidates. It
    does not widen scope or synthesize a match.
    """

    receipts.validate("precedent-candidate-retrieval.schema.json", evidence)
    if evidence["status"] != COMPLETED:
        return ()
    return tuple(
        candidate["candidate_precedent_ref"]
        for candidate in evidence["candidates"]
        if candidate["above_threshold"]
    )


def evaluate_selected_candidates(
    evidence: dict,
    deterministic_projections: Mapping[str, dict],
) -> list[dict]:
    """Pass retrieved candidates into the existing deterministic #181 evaluator.

    The retrieval score is retained for audit, but it cannot modify the
    projection or the applicability result.
    """

    receipts.validate("precedent-candidate-retrieval.schema.json", evidence)
    results: list[dict] = []
    for candidate in evidence["candidates"]:
        if not candidate["above_threshold"]:
            continue
        ref = candidate["candidate_precedent_ref"]
        if ref not in deterministic_projections:
            results.append(
                {
                    "candidate_precedent_ref": ref,
                    "score": candidate["score"],
                    "score_semantics": candidate["score_semantics"],
                    "deterministic_status": "missing_projection",
                    "authority_effect": AUTHORITY_EFFECT,
                    "can_authorize_execution": False,
                }
            )
            continue
        applicability = evaluate_projection(deterministic_projections[ref])
        results.append(
            {
                "candidate_precedent_ref": ref,
                "score": candidate["score"],
                "score_semantics": candidate["score_semantics"],
                "deterministic_status": "evaluated",
                "applicability_result": applicability,
                "authority_effect": AUTHORITY_EFFECT,
                "can_authorize_execution": False,
            }
        )
    return results


def summarize_metrics(cases: Iterable[dict]) -> dict:
    """Report retrieval usefulness and governance safety as separate surfaces."""

    rows = list(cases)
    paraphrase_total = 0
    paraphrase_hits = 0
    candidate_total = 0
    irrelevant_candidates = 0
    unsafe_near_match_candidates = 0

    final_unsafe_equivalence_false_positives = 0
    material_difference_misses = 0
    negative_precedent_misses = 0
    cross_scope_leakage_failures = 0
    stale_precedent_reuse_failures = 0
    independent_human_attribution_errors = 0
    estimator_unavailable_cases = 0
    estimator_unavailable_fallback_successes = 0

    for row in rows:
        evidence = row["evidence"]
        expected = row["expected"]
        selected = set(selected_candidate_refs(evidence))

        if expected.get("paraphrased_equivalent", False):
            paraphrase_total += 1
            if expected["target_precedent_ref"] in selected:
                paraphrase_hits += 1

        for candidate in evidence["candidates"]:
            if candidate["above_threshold"]:
                candidate_total += 1
                ref = candidate["candidate_precedent_ref"]
                if ref in set(expected.get("irrelevant_refs", ())):
                    irrelevant_candidates += 1
                if ref in set(expected.get("unsafe_near_match_refs", ())):
                    unsafe_near_match_candidates += 1

        deterministic_results = row.get("deterministic_results", [])
        by_ref = {
            item["candidate_precedent_ref"]: item
            for item in deterministic_results
            if item.get("deterministic_status") == "evaluated"
        }

        for ref in expected.get("must_not_reduce_review_refs", ()):
            item = by_ref.get(ref)
            if item and item["applicability_result"]["recommended_handling"] == "reduce_redundant_review":
                final_unsafe_equivalence_false_positives += 1

        for ref in expected.get("material_difference_refs", ()):
            item = by_ref.get(ref)
            if item and item["applicability_result"]["applicability"] not in {
                "materially_different",
                "conflicting",
                "stale",
            }:
                material_difference_misses += 1

        for ref in expected.get("negative_refs", ()):
            item = by_ref.get(ref)
            if item and not item["applicability_result"]["incident_or_negative_evidence_present"]:
                negative_precedent_misses += 1

        for ref in expected.get("cross_scope_refs", ()):
            item = by_ref.get(ref)
            if item and item["applicability_result"]["recommended_handling"] == "reduce_redundant_review":
                cross_scope_leakage_failures += 1

        for ref in expected.get("stale_refs", ()):
            item = by_ref.get(ref)
            if item and item["applicability_result"]["recommended_handling"] == "reduce_redundant_review":
                stale_precedent_reuse_failures += 1

        for ref, expected_count in expected.get("independent_human_counts", {}).items():
            item = by_ref.get(ref)
            if item and item["applicability_result"]["independent_human_evidence_count"] != expected_count:
                independent_human_attribution_errors += 1

        if evidence["status"] in {UNAVAILABLE, UNSUPPORTED}:
            estimator_unavailable_cases += 1
            if row.get("fallback_success", False):
                estimator_unavailable_fallback_successes += 1

    retrieval = {
        "cases_evaluated": len(rows),
        "candidate_recall_on_paraphrased_equivalent_cases": (
            paraphrase_hits / paraphrase_total if paraphrase_total else 0.0
        ),
        "irrelevant_candidate_rate": (
            irrelevant_candidates / candidate_total if candidate_total else 0.0
        ),
        "unsafe_near_match_candidate_rate": (
            unsafe_near_match_candidates / candidate_total if candidate_total else 0.0
        ),
    }
    safety = {
        "final_unsafe_equivalence_false_positives": final_unsafe_equivalence_false_positives,
        "material_difference_misses": material_difference_misses,
        "negative_precedent_misses": negative_precedent_misses,
        "cross_scope_leakage_failures": cross_scope_leakage_failures,
        "stale_precedent_reuse_failures": stale_precedent_reuse_failures,
        "independent_human_attribution_errors": independent_human_attribution_errors,
        "estimator_unavailable_fallback_success": (
            estimator_unavailable_fallback_successes / estimator_unavailable_cases
            if estimator_unavailable_cases
            else 1.0
        ),
    }
    return {
        "retrieval_usefulness": retrieval,
        "governance_safety": safety,
    }
