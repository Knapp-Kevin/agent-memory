"""D/F/H/R/P registration for unsafe multi-memory composition, issue #206."""

from __future__ import annotations

from typing import Any

from . import receipts
from .security_evidence_depth import LEVELS, classify_evidence_levels
from .unsafe_composition_harness import run_unsafe_composition_harness

REPORT_TYPE = "agent-memory-security-evidence-depth"
REPORT_VERSION = "1.0.0"


def _exact_commit(value: str) -> str:
    commit = value.lower()
    if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
        raise ValueError("agent_memory_commit must be an exact 40-hex commit")
    return commit


def build_unsafe_composition_depth_report(agent_memory_commit: str) -> dict[str, Any]:
    commit = _exact_commit(agent_memory_commit)
    harness = run_unsafe_composition_harness()
    evidence = classify_evidence_levels(
        {
            "D": [
                "docs/26-governed-recall-planner.md",
                "docs/41-memory-isolation-domains-and-governed-crossing.md",
                "docs/profiles/unsafe-composition-evidence-profile.md",
            ],
            "F": ["fixtures/unsafe-multi-memory-composition.json"],
            "H": ["unsafe-composition-harness:set-level-admission"] if harness["passed"] else [],
            "R": [],
            "P": [],
        }
    )
    claim = {
        "claim_id": "poisoning:unsafe-multi-memory-composition",
        "title": "Individually admitted memories remain subject to set-level composition governance",
        "threat_family": "unsafe_context_composition",
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
        "behavioral_passed": harness["passed"],
        "non_certification_statement": "This claim records bounded evidence depth and does not assert external certification.",
    }
    report = {
        "report_type": REPORT_TYPE,
        "version": REPORT_VERSION,
        "agent_memory_commit": commit,
        "evidence_model": {
            "levels": list(LEVELS),
            "inference_policy": "no_level_may_be_inferred_from_another_level",
        },
        "claims": [claim],
        "required_behavioral_cases_passed": harness["passed"],
        "non_certification_statement": "Evidence mapping and demonstrated behavior do not constitute external certification.",
        "known_limits": [
            "V0.1 exercises explicit deterministic set-level composition constraints only.",
            "The harness proves bounded reference behavior and does not claim universal detection of semantically unsafe memory combinations.",
            "Behavioral H evidence does not self-promote to runtime R evidence.",
            "Production evidence P is not collected or inferred by this report.",
        ],
    }
    receipts.validate("security-evidence-depth-report.schema.json", report)
    return report
