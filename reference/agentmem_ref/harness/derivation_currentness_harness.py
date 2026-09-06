"""Behavioral derived-state currentness and scope propagation proof for #210."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from ..memory.derivation_currentness import evaluate_derivation_currentness
from ..memory.derivation_evidence import derive_from, normalize_derivation
from .._paths import REPO_ROOT

ROOT = REPO_ROOT
SCOPE_REDUCTION_FIXTURE = ROOT / "fixtures" / "scope-reduction-propagates-to-derived-state.json"
SHARED_REVOCATION_FIXTURE = ROOT / "fixtures" / "shared-memory-revocation-propagation.json"

BASE_SCOPE = {
    "scope_ref": "domain:shared-derived",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}
NARROW_SCOPE = {
    "scope_ref": "domain:project-a-only",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}
SHARED_SCOPE = {
    "scope_ref": "domain:shared-security",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}


def _source_derivation(*, confidence: float = 0.82, transformer_trust: str = "trusted") -> dict[str, Any]:
    return normalize_derivation(
        {
            "root_origin_refs": ["uor:test:source-a", "uor:test:source-b"],
            "immediate_source_refs": ["uor:test:source-a", "uor:test:source-b"],
            "source_trust": "bounded_trusted",
            "transformation": {
                "method": "summary",
                "transformer_ref": "transformer:summary-v1",
                "transformer_version": "v1",
                "transformer_trust": transformer_trust,
                "output_ref": "derived:summary:shared",
            },
            "scope": BASE_SCOPE,
            "evidence_refs": ["evidence:source-a", "evidence:source-b"],
            "confidence": {
                "signal_semantics": "summary_confidence",
                "estimator_ref": "estimator:summary",
                "estimator_version": "v1",
                "value": confidence,
            },
            "created_at": "2026-08-12T20:00:00Z",
        },
        expected_scope=BASE_SCOPE,
    )


def _second_derivation(first: dict[str, Any]) -> dict[str, Any]:
    return derive_from(
        first,
        {
            "method": "compression",
            "transformer_ref": "transformer:compress-v2",
            "transformer_version": "v2",
            "transformer_trust": "trusted",
            "output_ref": "derived:summary:compressed",
            "evidence_refs": ["evidence:compression"],
            "confidence": {
                "signal_semantics": "compression_confidence",
                "estimator_ref": "estimator:compression",
                "estimator_version": "v2",
                "value": 0.97,
            },
            "created_at": "2026-08-12T20:01:00Z",
            # Arbitrary transformer-provided scope is ignored by derive_from.
            "scope": {
                "scope_ref": "domain:everything",
                "tenant_ref": "tenant-b",
                "project_ref": "project-b",
            },
        },
        expected_scope=BASE_SCOPE,
    )


def _observations(state_a: str = "current", state_b: str = "current", *, evidence_a: str = "ordinary") -> list[dict[str, Any]]:
    return [
        {
            "origin_ref": "uor:test:source-a",
            "state": state_a,
            "evidence_class": evidence_a,
            "evidence_refs": [f"evidence:source-a:{state_a}"],
        },
        {
            "origin_ref": "uor:test:source-b",
            "state": state_b,
            "evidence_class": "ordinary",
            "evidence_refs": [f"evidence:source-b:{state_b}"],
        },
    ]


def _scope(status: str, scope_ref: str, evidence_ref: str) -> dict[str, Any]:
    return {
        "status": status,
        "current_scope_ref": scope_ref,
        "tenant_ref": "tenant-a",
        "project_ref": "project-a",
        "evidence_refs": [evidence_ref],
    }


def _shared_derivation() -> dict[str, Any]:
    return normalize_derivation(
        {
            "root_origin_refs": ["uor:test:shared-source"],
            "immediate_source_refs": ["uor:test:shared-source"],
            "source_trust": "bounded_trusted",
            "transformation": {
                "method": "summary",
                "transformer_ref": "transformer:shared-summary",
                "transformer_version": "v1",
                "transformer_trust": "trusted",
                "output_ref": "derived:shared-summary",
            },
            "scope": SHARED_SCOPE,
            "evidence_refs": ["evidence:shared-source"],
            "created_at": "2026-08-12T20:02:00Z",
        },
        expected_scope=SHARED_SCOPE,
    )


def run_derivation_currentness_harness() -> dict[str, Any]:
    scope_fixture = json.loads(SCOPE_REDUCTION_FIXTURE.read_text(encoding="utf-8"))
    shared_fixture = json.loads(SHARED_REVOCATION_FIXTURE.read_text(encoding="utf-8"))

    first = _source_derivation()
    second = _second_derivation(first)
    first_before = copy.deepcopy(first)
    second_before = copy.deepcopy(second)

    current_first = evaluate_derivation_currentness(
        first,
        source_observations=_observations(),
        scope_observation=_scope("unchanged", BASE_SCOPE["scope_ref"], "evidence:scope:current"),
        evaluated_at="2026-08-12T21:00:00Z",
    )
    current_second = evaluate_derivation_currentness(
        second,
        source_observations=_observations(),
        scope_observation=_scope("unchanged", BASE_SCOPE["scope_ref"], "evidence:scope:current"),
        evaluated_at="2026-08-12T21:00:01Z",
    )

    scope_reduced = evaluate_derivation_currentness(
        second,
        source_observations=_observations(),
        scope_observation=_scope(
            "reduced",
            NARROW_SCOPE["scope_ref"],
            "fixture://scope-reduction/source-a",
        ),
        evaluated_at="2026-08-12T21:01:00Z",
    )
    narrowed = derive_from(
        second,
        {
            "method": "rebuild-under-current-scope",
            "transformer_ref": "transformer:scope-reconciler",
            "transformer_version": "v1",
            "transformer_trust": "bounded_trusted",
            "output_ref": "derived:summary:narrowed",
            "evidence_refs": ["evidence:scope-reduction"],
            "created_at": "2026-08-12T21:01:30Z",
        },
        expected_scope=NARROW_SCOPE,
        narrowed_scope=NARROW_SCOPE,
        scope_basis_refs=("fixture://scope-reduction/source-a",),
    )
    narrowed_current = evaluate_derivation_currentness(
        narrowed,
        source_observations=_observations(),
        scope_observation=_scope("unchanged", NARROW_SCOPE["scope_ref"], "evidence:narrowed-scope-current"),
        evaluated_at="2026-08-12T21:02:00Z",
    )

    revoked_first = evaluate_derivation_currentness(
        first,
        source_observations=_observations(state_a="revoked"),
        scope_observation=_scope("unchanged", BASE_SCOPE["scope_ref"], "evidence:scope:current"),
        evaluated_at="2026-08-12T21:03:00Z",
    )
    revoked_second = evaluate_derivation_currentness(
        second,
        source_observations=_observations(state_a="revoked"),
        scope_observation=_scope("unchanged", BASE_SCOPE["scope_ref"], "evidence:scope:current"),
        evaluated_at="2026-08-12T21:03:01Z",
    )
    tombstoned_second = evaluate_derivation_currentness(
        second,
        source_observations=_observations(state_a="tombstoned"),
        scope_observation=_scope("unchanged", BASE_SCOPE["scope_ref"], "evidence:scope:current"),
        evaluated_at="2026-08-12T21:03:02Z",
    )
    deleted_second = evaluate_derivation_currentness(
        second,
        source_observations=_observations(state_a="deleted"),
        scope_observation=_scope("unchanged", BASE_SCOPE["scope_ref"], "evidence:scope:current"),
        evaluated_at="2026-08-12T21:03:03Z",
    )
    adversarial_second = evaluate_derivation_currentness(
        second,
        source_observations=_observations(evidence_a="adversarial"),
        scope_observation=_scope("unchanged", BASE_SCOPE["scope_ref"], "evidence:scope:current"),
        evaluated_at="2026-08-12T21:03:04Z",
    )

    shared = _shared_derivation()
    shared_before = copy.deepcopy(shared)
    shared_current = evaluate_derivation_currentness(
        shared,
        source_observations=[
            {
                "origin_ref": "uor:test:shared-source",
                "state": "current",
                "evidence_class": "ordinary",
                "evidence_refs": ["evidence:shared-source:current"],
            }
        ],
        scope_observation=_scope("unchanged", SHARED_SCOPE["scope_ref"], "evidence:shared-membership:current"),
        evaluated_at="2026-08-12T21:04:00Z",
    )
    shared_revoked = evaluate_derivation_currentness(
        shared,
        source_observations=[
            {
                "origin_ref": "uor:test:shared-source",
                "state": "current",
                "evidence_class": "ordinary",
                "evidence_refs": ["evidence:shared-source:current"],
            }
        ],
        scope_observation=_scope(
            "revoked",
            SHARED_SCOPE["scope_ref"],
            "fixture://shared-membership/revoked-user-alice",
        ),
        evaluated_at="2026-08-12T21:04:01Z",
    )

    missing_with_extra = evaluate_derivation_currentness(
        second,
        source_observations=[
            {
                "origin_ref": "uor:test:source-a",
                "state": "current",
                "evidence_class": "ordinary",
                "evidence_refs": ["evidence:source-a:current"],
            },
            {
                "origin_ref": "uor:test:unrelated-source",
                "state": "current",
                "evidence_class": "ordinary",
                "evidence_refs": ["evidence:unrelated"],
            },
        ],
        scope_observation=_scope("unchanged", BASE_SCOPE["scope_ref"], "evidence:scope:current"),
        evaluated_at="2026-08-12T21:05:00Z",
    )

    scope_expected = scope_fixture["expected_behavior"]
    shared_expected = shared_fixture["expected_behavior"]
    checks = {
        "initial_first_derivation_current": current_first["applicability"]["status"] == "current",
        "initial_second_derivation_current": current_second["applicability"]["status"] == "current",
        "scope_fixture_source_scope_reduced": scope_expected["source_scope_reduced"] is True,
        "scope_fixture_old_scope_not_current": scope_expected["old_derived_scope_current"] is False,
        "scope_reduction_requires_revalidation": (
            scope_reduced["applicability"]["status"] == "revalidation_required"
            and "source_scope_reduced" in scope_reduced["applicability"]["reasons"]
        ),
        "explicit_narrowed_derivation_created": (
            narrowed["scope"]["relation"] == "narrowed"
            and narrowed["scope"]["scope_ref"] == NARROW_SCOPE["scope_ref"]
            and narrowed["scope"]["basis_refs"] == ["fixture://scope-reduction/source-a"]
        ),
        "narrowed_derivation_can_be_current": narrowed_current["applicability"]["status"] == "current",
        "multi_hop_root_lineage_preserved": second["root_origin_refs"] == first["root_origin_refs"],
        "root_revocation_invalidates_first_currentness": revoked_first["applicability"]["status"] == "revalidation_required",
        "root_revocation_propagates_to_second": (
            revoked_second["applicability"]["status"] == "revalidation_required"
            and "source_revoked:uor:test:source-a" in revoked_second["applicability"]["reasons"]
        ),
        "tombstone_reason_distinct": "source_tombstoned:uor:test:source-a" in tombstoned_second["applicability"]["reasons"],
        "deletion_reason_distinct": "source_deleted:uor:test:source-a" in deleted_second["applicability"]["reasons"],
        "negative_adversarial_character_survives": adversarial_second["evidence_character"] == "negative_or_adversarial",
        "shared_fixture_membership_revoked": shared_expected["shared_membership_revoked"] is True,
        "shared_fixture_old_scope_not_current": shared_expected["old_downstream_scope_current"] is False,
        "shared_revocation_requires_revalidation": (
            shared_current["applicability"]["status"] == "current"
            and shared_revoked["applicability"]["status"] == "revalidation_required"
            and "source_scope_or_membership_revoked" in shared_revoked["applicability"]["reasons"]
        ),
        "shared_revocation_is_not_remote_mutation": shared_revoked["interpretation"]["remote_mutation"] == "not_established",
        "prior_authorization_not_reusable": shared_revoked["interpretation"]["prior_authorization_reusable"] is False,
        "missing_root_remains_unknown_despite_extra_observation": (
            missing_with_extra["applicability"]["status"] == "unknown"
            and "uor:test:unrelated-source" in missing_with_extra["unexpected_source_refs"]
            and "missing_source_observation:uor:test:source-b" in missing_with_extra["applicability"]["reasons"]
        ),
        "historical_first_derivation_unchanged": first == first_before,
        "historical_second_derivation_unchanged": second == second_before,
        "historical_shared_derivation_unchanged": shared == shared_before,
        "currentness_has_no_authority_effect": revoked_second["interpretation"]["authority_effect"] == "none",
        "currentness_does_not_establish_admission": revoked_second["interpretation"]["memory_admission"] == "not_established",
    }

    return {
        "case_id": "derivation-currentness-and-scope-propagation",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "first_derivation_id": first["derivation_id"],
            "second_derivation_id": second["derivation_id"],
            "narrowed_derivation_id": narrowed["derivation_id"],
            "scope_reduction_status": scope_reduced["applicability"],
            "revoked_second_status": revoked_second["applicability"],
            "tombstoned_second_status": tombstoned_second["applicability"],
            "deleted_second_status": deleted_second["applicability"],
            "shared_revocation_status": shared_revoked["applicability"],
            "missing_with_extra_status": missing_with_extra["applicability"],
        },
    }
