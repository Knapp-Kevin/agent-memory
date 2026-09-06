"""D/F/H/R/P registration for derivation currentness propagation, issue #210."""

from __future__ import annotations

from typing import Any

from ..core import receipts
from .derivation_currentness_harness import run_derivation_currentness_harness
from .security_evidence_depth import LEVELS, classify_evidence_levels

REPORT_TYPE = "agent-memory-security-evidence-depth"
REPORT_VERSION = "1.0.0"


def _exact_commit(value: str) -> str:
    commit = value.lower()
    if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
        raise ValueError("agent_memory_commit must be an exact 40-hex commit")
    return commit


def _claim(
    *,
    claim_id: str,
    title: str,
    threat_family: str,
    fixture_refs: list[str],
    harness_ref: str,
    commit: str,
    harness_passed: bool,
) -> dict[str, Any]:
    evidence = classify_evidence_levels(
        {
            "D": [
                "docs/profiles/derivation-provenance-profile.md",
                "docs/profiles/derivation-currentness-profile.md",
                "docs/26-governed-recall-planner.md",
            ],
            "F": fixture_refs,
            "H": [harness_ref] if harness_passed else [],
            "R": [],
            "P": [],
        }
    )
    return {
        "claim_id": claim_id,
        "title": title,
        "threat_family": threat_family,
        "doctrine_refs": evidence["evidence"]["D"],
        "fixture_refs": evidence["evidence"]["F"],
        "behavioral_harness_refs": evidence["evidence"]["H"],
        "runtime_evidence_refs": evidence["evidence"]["R"],
        "production_evidence_refs": evidence["evidence"]["P"],
        "external_mappings": [],
        "demonstrated_levels": evidence["demonstrated_levels"],
        "highest_demonstrated_level": evidence["highest_demonstrated_level"],
        "explicitly_unproven_levels": evidence["explicitly_unproven_levels"],
        "scope_profiles": ["L", "T", "E", "H"],
        "evaluated_head": commit,
        "behavioral_passed": harness_passed,
        "non_certification_statement": "This claim records bounded evidence depth and does not assert external certification.",
    }


def build_derivation_currentness_depth_report(agent_memory_commit: str) -> dict[str, Any]:
    commit = _exact_commit(agent_memory_commit)
    harness = run_derivation_currentness_harness()
    passed = harness["passed"]
    report = {
        "report_type": REPORT_TYPE,
        "version": REPORT_VERSION,
        "agent_memory_commit": commit,
        "evidence_model": {
            "levels": list(LEVELS),
            "inference_policy": "no_level_may_be_inferred_from_another_level",
        },
        "claims": [
            _claim(
                claim_id="derived-state:root-currentness-propagation",
                title="Current applicability of multi-hop derived state is re-evaluated against original root-source state",
                threat_family="derived_state_currentness",
                fixture_refs=[
                    "fixtures/scope-reduction-propagates-to-derived-state.json",
                    "fixtures/shared-memory-revocation-propagation.json",
                ],
                harness_ref="derivation-currentness-harness:root-state-propagation",
                commit=commit,
                harness_passed=passed,
            ),
            _claim(
                claim_id="derived-state:scope-reduction-propagation",
                title="Source scope reduction invalidates stale derived applicability until explicitly narrowed or rebuilt",
                threat_family="derived_scope_currentness",
                fixture_refs=["fixtures/scope-reduction-propagates-to-derived-state.json"],
                harness_ref="derivation-currentness-harness:scope-reduction",
                commit=commit,
                harness_passed=passed,
            ),
            _claim(
                claim_id="derived-state:shared-revocation-propagation",
                title="Shared authority revocation requires derived applicability re-evaluation without fabricating remote mutation",
                threat_family="shared_revocation_currentness",
                fixture_refs=["fixtures/shared-memory-revocation-propagation.json"],
                harness_ref="derivation-currentness-harness:shared-revocation",
                commit=commit,
                harness_passed=passed,
            ),
        ],
        "required_behavioral_cases_passed": passed,
        "non_certification_statement": "Evidence mapping and demonstrated behavior do not constitute external certification.",
        "known_limits": [
            "V0.1 evaluates currentness from explicitly supplied source/scope observations; it does not discover source-state changes automatically.",
            "Scope narrowing is explicit and does not infer hierarchy from scope names.",
            "Behavioral H evidence does not self-promote to runtime R evidence.",
            "Production evidence P is not collected or inferred by this report.",
            "Currentness evaluation does not itself authorize memory admission, mutation, certification, or remote cleanup.",
        ],
    }
    receipts.validate("security-evidence-depth-report.schema.json", report)
    return report
