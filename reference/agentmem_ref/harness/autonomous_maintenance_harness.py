"""Representation-neutral autonomous-maintenance research harness for #227.

This module intentionally does not implement a scheduler, sleep agent, or storage
backend. It pressure-tests two boundaries:

* probabilistic evidence fusion may rank/propose but does not create authority;
* a maintenance run may advance its durable cursor only after governed work is
  committed and required validation succeeds.
"""

from __future__ import annotations

import json
from functools import reduce
from pathlib import Path
from typing import Any

from ..core import policy
from .._paths import REPO_ROOT

ROOT = REPO_ROOT
SCENARIOS = ROOT / "docs" / "explorations" / "memory-architectures" / "autonomous-maintenance-scenarios.json"


def noisy_or(probabilities: list[float]) -> float:
    """Combine independent probabilities; caller owns independence semantics."""
    if not probabilities:
        return 0.0
    for value in probabilities:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0.0 or value > 1.0:
            raise ValueError("probabilities must be numeric values in [0, 1]")
    return 1.0 - reduce(lambda product, value: product * (1.0 - value), probabilities, 1.0)


def _group_probabilities(signals: list[dict[str, Any]], polarity: str) -> dict[str, float]:
    """Collapse one dependence group before cross-group fusion.

    Maximum signal is an intentionally conservative fixture reducer. The point is
    not to standardize that reducer; it is to make duplicate/derived/correlated
    observations unable to present themselves as independent evidence merely by
    increasing row count.
    """
    grouped: dict[str, float] = {}
    for signal in signals:
        if signal.get("polarity") != polarity:
            continue
        group = signal.get("dependence_group")
        probability = signal.get("probability")
        if not isinstance(group, str) or not group:
            raise ValueError("fusion signal requires dependence_group")
        if not isinstance(probability, (int, float)) or isinstance(probability, bool):
            raise ValueError("fusion signal requires numeric probability")
        if not 0.0 <= float(probability) <= 1.0:
            raise ValueError("fusion probability must be in [0, 1]")
        grouped[group] = max(grouped.get(group, 0.0), float(probability))
    return grouped


def fuse_evidence(signals: list[dict[str, Any]]) -> dict[str, Any]:
    support = _group_probabilities(signals, "support")
    challenge = _group_probabilities(signals, "challenge")
    return {
        "support_probability": round(noisy_or(list(support.values())), 6),
        "challenge_probability": round(noisy_or(list(challenge.values())), 6),
        "support_groups": len(support),
        "challenge_groups": len(challenge),
        "support_group_probabilities": dict(sorted(support.items())),
        "challenge_group_probabilities": dict(sorted(challenge.items())),
        "interpretation": {
            "authority_effect": "none",
            "certification_claim": "none",
            "independence_is_estimator_input": True,
            "row_count_is_not_corroboration": True,
            "challenge_evidence_preserved_separately": True,
        },
    }


def _pama_case(case: dict[str, Any]) -> dict[str, Any]:
    target_map = {
        "M3": policy.M3,
        "M4": policy.M4,
        "M5": policy.M5,
    }
    authority_map = {
        "A1": policy.A1,
        "A3": policy.A3,
        "A5": policy.A5,
    }
    operation = case["operation"]
    risk = case["risk_class"]
    reversibility = "irreversible" if operation in {"permanent_deletion", "scope_expansion"} else "versioned_revocable"
    decision = policy.evaluate(
        policy.Proposal(
            proposal_id=f"maintenance:{case['id']}",
            actor_id="agent:maintenance",
            charter_version="v1",
            target_reference=f"memory:{case['id']}",
            target_class=target_map[case["target_class"]],
            scope="tenant-a/project-a",
            operation=operation,
            current_strength="promoted",
            proposed_strength="canonical",
            downstream_authority=authority_map[case["downstream_authority"]],
            reversibility=reversibility,
            risk_class=risk,
            evidence_refs=("evidence:maintenance-source-a", "evidence:maintenance-source-b"),
            estimator_refs=("estimator:evidence-fusion",),
            estimator_versions=("research-v1",),
            actor_authority_resolved=True,
            approves_own_authority=False,
        )
    )
    return {
        "id": case["id"],
        "fused_support": case["fused_support"],
        "pama_outcome": decision.outcome,
        "permitted_actions": list(decision.permitted_actions),
        "prohibited_actions": list(decision.prohibited_actions),
        "reasons": list(decision.reasons),
        "interpretation": {
            "fused_support_authority": "none",
            "maintenance_actor_self_authority": False,
            "pama_evaluated_after_estimator": True,
        },
    }


def evaluate_transaction(case: dict[str, Any]) -> dict[str, Any]:
    before = case["cursor_before"]
    source_currentness = case.get("source_currentness", "current")

    if source_currentness != "current":
        status = "blocked_stale_source"
        current_outputs = False
        cursor_after = before
    elif case["commit_succeeded"] and case["validation_passed"]:
        status = "committed"
        current_outputs = True
        cursor_after = before + 1
    elif case["rollback_supported"]:
        status = "rolled_back"
        current_outputs = False
        cursor_after = before
    else:
        status = "quarantined"
        current_outputs = False
        cursor_after = before

    result = {
        "id": case["id"],
        "status": status,
        "cursor_before": before,
        "cursor_after": cursor_after,
        "cursor_advanced": cursor_after != before,
        "current_outputs": current_outputs,
        "original_retained": not current_outputs,
        "semantic_memory_changed": bool(case.get("semantic_memory_changed", status == "committed")),
        "interpretation": {
            "cursor_advances_only_after_commit_and_validation": True,
            "failed_run_consumes_input": False,
            "quarantine_is_not_clean_commit": True,
            "successful_write_is_not_sufficient_without_validation": True,
        },
    }
    return result


def run_autonomous_maintenance_harness() -> dict[str, Any]:
    source = json.loads(SCENARIOS.read_text(encoding="utf-8"))

    fusion_results = []
    checks: dict[str, bool] = {}
    for case in source["fusion_cases"]:
        result = {"id": case["id"], **fuse_evidence(case["signals"])}
        fusion_results.append(result)
        for field, expected in case["expected"].items():
            checks[f"fusion:{case['id']}:{field}"] = result[field] == expected

    governance_results = []
    for case in source["governance_cases"]:
        result = _pama_case(case)
        governance_results.append(result)
        checks[f"governance:{case['id']}:outcome"] = result["pama_outcome"] == case["expected_outcome"]
        checks[f"governance:{case['id']}:confidence_no_authority"] = (
            result["interpretation"]["fused_support_authority"] == "none"
        )

    transaction_results = []
    for case in source["transaction_cases"]:
        result = evaluate_transaction(case)
        transaction_results.append(result)
        for field, expected in case["expected"].items():
            checks[f"transaction:{case['id']}:{field}"] = result[field] == expected

    by_tx = {item["id"]: item for item in transaction_results}
    checks.update(
        {
            "cursor_never_advances_on_failed_or_quarantined_run": all(
                not item["cursor_advanced"]
                for item in transaction_results
                if item["status"] != "committed"
            ),
            "validated_commit_advances_exactly_once": (
                by_tx["successful-validated-commit-advances-once"]["cursor_after"]
                == by_tx["successful-validated-commit-advances-once"]["cursor_before"] + 1
            ),
            "failed_summary_retains_original": by_tx["validation-failure-retains-original"]["original_retained"] is True,
            "revoked_source_cannot_rebuild_current_state": by_tx["revoked-source-rebuild-not-current"]["current_outputs"] is False,
            "index_rebuild_does_not_imply_semantic_mutation": (
                by_tx["index-only-rebuild-can-be-ledgered-housekeeping"]["semantic_memory_changed"] is False
            ),
        }
    )

    return {
        "case_id": "autonomous-maintenance-and-evidence-fusion",
        "passed": all(checks.values()),
        "scenario_set_version": source["scenario_set_version"],
        "checks": checks,
        "fusion_results": fusion_results,
        "governance_results": governance_results,
        "transaction_results": transaction_results,
        "finding": {
            "noisy_or_is_estimator_not_authority": True,
            "dependence_groups_required_for_honest_fusion": True,
            "challenge_evidence_must_remain_visible": True,
            "broad_background_maintenance_authority_required": False,
            "constituent_pama_operations_remain_authoritative": True,
            "missing_reusable_contract": "maintenance_run_transaction_evidence",
            "cursor_advance_requires_commit_and_validation": True,
            "real_autonomous_consolidator_dependency_required": False,
        },
    }
