"""Representation-neutral progressive domain-schema pressure test for issue #226.

This is exploratory evidence, not a canonical domain-ontology implementation. It
classifies domain-model proposals using existing PAMA dimensions and makes one
specific gap visible: durable domain-schema mutation is now a known operation
class, but the canonical PAMA operation enum has no exact name for it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core import policy
from .._paths import REPO_ROOT

ROOT = REPO_ROOT
SCENARIOS = ROOT / "docs" / "explorations" / "memory-architectures" / "progressive-domain-schema-scenarios.json"


def _pama_for_domain_case(case: dict[str, Any]) -> tuple[policy.Decision | None, str | None]:
    if case["kind"] == "derived_projection_maintenance":
        return None, None

    evidence_refs = tuple(dict.fromkeys(case.get("root_source_refs", [])))
    if case.get("widens_scope"):
        operation = "scope_expansion"
        target_class = policy.M5
        authority = policy.A5
        risk = "critical"
        reversibility = "irreversible"
    elif case.get("privileged_semantics"):
        operation = "policy_mutation"
        target_class = policy.M5
        authority = policy.A5
        risk = "critical"
        reversibility = "versioned_revocable"
    else:
        # `other` is a temporary fail-closed projection for this exploratory
        # harness only. Repository doctrine explicitly says `other` must not
        # hide a known consequential class merely to avoid schema evolution.
        operation = "other"
        target_class = policy.M4 if case.get("affects_existing_objects") else policy.M3
        authority = policy.A3
        risk = "high" if case.get("affects_existing_objects") else "medium"
        reversibility = "versioned_revocable"

    decision = policy.evaluate(
        policy.Proposal(
            proposal_id=f"schema-proposal:{case['id']}",
            actor_id="agent:schema-discovery",
            charter_version="v1",
            target_reference=f"domain-schema:{case['scope']}",
            target_class=target_class,
            scope=case["scope"],
            operation=operation,
            current_strength="promoted",
            proposed_strength="canonical",
            downstream_authority=authority,
            reversibility=reversibility,
            risk_class=risk,
            evidence_refs=evidence_refs,
            estimator_refs=(case.get("estimator_ref", "estimator:unknown"),),
            estimator_versions=("fixture-v1",),
            actor_authority_resolved=True,
            approves_own_authority=False,
        )
    )
    return decision, operation


def evaluate_domain_schema_case(case: dict[str, Any]) -> dict[str, Any]:
    roots = list(dict.fromkeys(case.get("root_source_refs", [])))
    source_state = case.get("source_state", "current")
    currentness = "current" if source_state == "current" else "revalidation_required"

    if case["kind"] == "derived_projection_maintenance":
        return {
            "id": case["id"],
            "proposal_allowed": True,
            "self_commit_allowed": None,
            "classification": "derived_projection_maintenance",
            "operation_gap": False,
            "minimum_posture": "separate_maintenance_governance",
            "independent_root_count": len(roots),
            "currentness": currentness,
            "commit_complete": True,
            "last_writer_wins_allowed": False,
            "pama_operation": None,
            "pama_outcome": None,
            "interpretation": {
                "domain_schema_changed": False,
                "canonical_doctrine_schema_changed": False,
                "estimator_authority": "none",
            },
        }

    if case.get("widens_scope"):
        classification = "scope_expanding_schema_mutation"
    elif case.get("privileged_semantics"):
        classification = "authority_bearing_schema_mutation"
    elif case.get("conflict"):
        classification = "semantic_conflict"
    elif case.get("affects_existing_objects"):
        classification = "semantic_reinterpretation"
    else:
        classification = "domain_schema_mutation"

    decision, operation = _pama_for_domain_case(case)
    assert decision is not None
    operation_gap = operation == "other"
    commit_complete = not (
        case.get("requires_migration", False) and case.get("derived_projection_residue", False)
    )

    return {
        "id": case["id"],
        "proposal_allowed": True,
        "self_commit_allowed": False,
        "classification": classification,
        "operation_gap": operation_gap,
        "minimum_posture": decision.outcome,
        "independent_root_count": len(roots),
        "currentness": currentness,
        "commit_complete": commit_complete,
        "last_writer_wins_allowed": False,
        "pama_operation": operation,
        "pama_outcome": decision.outcome,
        "pama_permitted_actions": list(decision.permitted_actions),
        "pama_prohibited_actions": list(decision.prohibited_actions),
        "interpretation": {
            "domain_schema_changed": False,
            "canonical_doctrine_schema_changed": False,
            "estimator_authority": "none",
            "historical_objects_rewritten": False,
            "repeated_proposals_create_independent_roots": False,
            "generic_other_is_final_operation_contract": False,
        },
    }


def run_domain_schema_discovery_harness() -> dict[str, Any]:
    source = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    observed = [evaluate_domain_schema_case(case) for case in source["scenarios"]]
    by_id = {item["id"]: item for item in observed}

    checks: dict[str, bool] = {}
    for case in source["scenarios"]:
        actual = by_id[case["id"]]
        for field, expected in case["expected"].items():
            checks[f"{case['id']}:{field}"] = actual.get(field) == expected

    cross_case_checks = {
        "estimator_never_self_commits_domain_schema": all(
            item["self_commit_allowed"] is False
            for item in observed
            if item["classification"] != "derived_projection_maintenance"
        ),
        "scope_expansion_uses_existing_blocking_path": (
            by_id["cross-tenant-relation-widening"]["pama_operation"] == "scope_expansion"
            and by_id["cross-tenant-relation-widening"]["pama_outcome"] == policy.BLOCK
        ),
        "privileged_semantics_use_governance_floor": (
            by_id["privileged-entity-from-untrusted-input"]["pama_operation"] == "policy_mutation"
            and by_id["privileged-entity-from-untrusted-input"]["pama_outcome"]
            == policy.REQUIRE_EXTERNAL_VERIFICATION
        ),
        "ordinary_domain_schema_change_exposes_operation_gap": all(
            item["operation_gap"] is True
            for item in observed
            if item["id"]
            in {
                "additive-local-entity-type",
                "semantic-merge-by-similarity",
                "replayed-proposal-not-corroboration",
                "revoked-source-basis",
                "migration-with-stale-projection-residue",
                "concurrent-incompatible-proposals",
            }
        ),
        "repetition_does_not_create_corroboration": (
            by_id["replayed-proposal-not-corroboration"]["independent_root_count"] == 1
        ),
        "revoked_basis_requires_revalidation": (
            by_id["revoked-source-basis"]["currentness"] == "revalidation_required"
        ),
        "migration_not_complete_with_stale_projection": (
            by_id["migration-with-stale-projection-residue"]["commit_complete"] is False
        ),
        "conflict_not_last_writer_wins": (
            by_id["concurrent-incompatible-proposals"]["last_writer_wins_allowed"] is False
        ),
        "index_maintenance_not_schema_mutation": (
            by_id["index-only-rebuild"]["classification"] == "derived_projection_maintenance"
            and by_id["index-only-rebuild"]["operation_gap"] is False
        ),
    }
    checks.update(cross_case_checks)

    return {
        "case_id": "progressive-domain-schema-discovery",
        "passed": all(checks.values()),
        "scenario_set_version": source["scenario_set_version"],
        "checks": checks,
        "observed": observed,
        "finding": {
            "existing_pama_dimensions_sufficient_for_authority_bounding": True,
            "existing_scope_and_policy_operations_cover_high_consequence_special_cases": True,
            "canonical_operation_gap": "domain_schema_mutation",
            "generic_other_is_not_recommended_as_final_contract": True,
            "new_domain_ontology_core_schema_required": False,
            "cognee_dependency_required": False,
        },
    }
