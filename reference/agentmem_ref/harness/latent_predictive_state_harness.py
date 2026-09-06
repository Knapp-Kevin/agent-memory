"""Representation-neutral opaque latent predictive-state pressure test for issue #137.

This harness does not implement JEPA and does not claim JEPA conformance. It tests
whether an opaque, probabilistically derived predictive state can remain useful
while source currentness or scope changes, without usefulness laundering itself
into currentness, recall admission, or downstream action authority.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from ..memory.derivation_currentness import evaluate_derivation_currentness
from ..memory.derivation_evidence import normalize_derivation
from .._paths import REPO_ROOT

ROOT = REPO_ROOT
FIXTURE = ROOT / "fixtures" / "opaque-latent-source-revocation.json"

SCOPE = {
    "scope_ref": "domain:project-a",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}
NARROW_SCOPE = {
    "scope_ref": "domain:project-a/private",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}


def _latent_derivation(confidence: float = 0.94) -> dict[str, Any]:
    return normalize_derivation(
        {
            "root_origin_refs": [
                "uor:test:latent-source-a",
                "uor:test:latent-source-b",
            ],
            "immediate_source_refs": [
                "uor:test:latent-source-a",
                "uor:test:latent-source-b",
            ],
            "source_trust": "bounded_trusted",
            "transformation": {
                "method": "opaque_latent_prediction",
                "transformer_ref": "model:opaque-predictor",
                "transformer_version": "fixture-v1",
                "transformer_trust": "bounded_trusted",
                "mode": "probabilistic",
                "status": "complete",
                "output_ref": "derived:latent:planner-state-v1",
            },
            "scope": SCOPE,
            "evidence_refs": [
                "evidence:latent-source-a",
                "evidence:latent-source-b",
            ],
            "confidence": {
                "signal_semantics": "predictive_quality",
                "estimator_ref": "model:opaque-predictor",
                "estimator_version": "fixture-v1",
                "value": confidence,
            },
            "created_at": "2026-08-13T06:20:00Z",
        },
        expected_scope=SCOPE,
    )


def _source_observations(state_b: str = "current") -> list[dict[str, Any]]:
    return [
        {
            "origin_ref": "uor:test:latent-source-a",
            "state": "current",
            "evidence_class": "ordinary",
            "evidence_refs": ["evidence:latent-source-a:current"],
        },
        {
            "origin_ref": "uor:test:latent-source-b",
            "state": state_b,
            "evidence_class": "ordinary",
            "evidence_refs": [f"evidence:latent-source-b:{state_b}"],
        },
    ]


def _scope(status: str = "unchanged", scope_ref: str = SCOPE["scope_ref"]) -> dict[str, Any]:
    return {
        "status": status,
        "current_scope_ref": scope_ref,
        "tenant_ref": "tenant-a",
        "project_ref": "project-a",
        "evidence_refs": [f"evidence:latent-scope:{status}"],
    }


def run_latent_predictive_state_harness() -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected = fixture["expected_behavior"]

    latent = _latent_derivation(confidence=0.94)
    before = copy.deepcopy(latent)

    current = evaluate_derivation_currentness(
        latent,
        source_observations=_source_observations(),
        scope_observation=_scope(),
        evaluated_at="2026-08-13T06:21:00Z",
    )
    revoked = evaluate_derivation_currentness(
        latent,
        source_observations=_source_observations("revoked"),
        scope_observation=_scope(),
        evaluated_at="2026-08-13T06:21:01Z",
    )
    deleted = evaluate_derivation_currentness(
        latent,
        source_observations=_source_observations("deleted"),
        scope_observation=_scope(),
        evaluated_at="2026-08-13T06:21:02Z",
    )
    scope_reduced = evaluate_derivation_currentness(
        latent,
        source_observations=_source_observations(),
        scope_observation=_scope("reduced", NARROW_SCOPE["scope_ref"]),
        evaluated_at="2026-08-13T06:21:03Z",
    )

    prediction_quality = latent["confidence"]["value"]
    governed = fixture["governed_uncertainty"]
    checks = {
        "opaque_probabilistic_derivation_representable": (
            latent["transformation"]["mode"] == "probabilistic"
            and latent["transformation"]["method"] == "opaque_latent_prediction"
        ),
        "initial_state_current": current["applicability"]["status"] == "current",
        "high_prediction_quality_preserved_in_evidence": prediction_quality == 0.94,
        "revocation_requires_revalidation": (
            revoked["applicability"]["status"] == "revalidation_required"
            and "source_revoked:uor:test:latent-source-b" in revoked["applicability"]["reasons"]
            and expected["revocation_requires_revalidation"] is True
        ),
        "deletion_requires_revalidation": (
            deleted["applicability"]["status"] == "revalidation_required"
            and "source_deleted:uor:test:latent-source-b" in deleted["applicability"]["reasons"]
            and expected["deleted_source_requires_revalidation"] is True
        ),
        "scope_reduction_requires_revalidation": (
            scope_reduced["applicability"]["status"] == "revalidation_required"
            and "source_scope_reduced" in scope_reduced["applicability"]["reasons"]
            and expected["scope_reduction_requires_revalidation"] is True
        ),
        "prediction_quality_does_not_restore_currentness": (
            prediction_quality == fixture["scenario"]["prediction_quality_after_revocation"]
            and revoked["applicability"]["status"] != "current"
            and expected["predictive_quality_preserves_authority"] is False
        ),
        "currentness_does_not_establish_admission": (
            revoked["interpretation"]["memory_admission"] == "not_established"
        ),
        "currentness_does_not_establish_authority": revoked["interpretation"]["authority_effect"] == "none",
        "planning_influence_separate_from_action_authority": (
            expected["planning_influence_equals_action_authority"] is False
            and governed["requested_action"] in governed["prohibited_actions"]
            and governed["selected_action"] in governed["permitted_actions"]
        ),
        "historical_derivation_unchanged": (
            latent == before
            and revoked["interpretation"]["historical_derivation_mutated"] is False
            and expected["historical_derivation_rewritten"] is False
        ),
        "prior_authorization_not_reusable": revoked["interpretation"]["prior_authorization_reusable"] is False,
    }

    return {
        "case_id": "opaque-latent-predictive-state-source-change",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "derivation_id": latent["derivation_id"],
            "prediction_quality": prediction_quality,
            "current": current["applicability"],
            "revoked": revoked["applicability"],
            "deleted": deleted["applicability"],
            "scope_reduced": scope_reduced["applicability"],
            "authority_interpretation_after_revocation": revoked["interpretation"],
        },
        "interpretation": {
            "jepa_implemented": False,
            "jepa_conformance_claim": "none",
            "capability_superiority_claim": "not_established",
            "representation_neutral_governance_pressure_test": "executed",
        },
    }
