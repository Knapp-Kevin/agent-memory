"""D/F/H/R/P evidence-depth report for sleeper-poisoning recall re-evaluation."""

from __future__ import annotations

from typing import Any

from ..core import receipts
from .security_evidence_depth import LEVELS, REPORT_TYPE, REPORT_VERSION, _claim, _exact_commit
from .sleeper_poisoning_harness import run_sleeper_poisoning_harness


def build_sleeper_poisoning_depth_report(agent_memory_commit: str) -> dict[str, Any]:
    commit = _exact_commit(agent_memory_commit)
    harness = run_sleeper_poisoning_harness()
    claim = _claim(
        agent_memory_commit=commit,
        claim_id="poisoning:sleeper-delayed-trigger-recall",
        title="Retained memory is re-evaluated under changed current recall context before activation",
        threat_family="delayed_sleeper_memory_poisoning",
        doctrine_refs=[
            "docs/15-memory-threat-model.md",
            "docs/26-governed-recall-planner.md",
            "docs/profiles/contextual-recall-admission-profile.md",
        ],
        fixture_refs=["fixtures/sleeper-memory-poisoning.json"],
        harness_ref="sleeper-poisoning-harness:delayed-trigger-recall",
        behavioral_passed=harness["passed"],
        scope_profiles=["L", "T", "E", "H"],
    )
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
            "The V0.1 harness demonstrates reference behavioral re-evaluation of one delayed-trigger sleeper scenario; it does not discover sleeper triggers semantically.",
            "The contextual recall harness earns H evidence only; no independent live-runtime R evidence is claimed.",
            "Long-horizon consolidation, production workloads, and production sleeper resistance remain untested.",
            "Production evidence P is explicitly unproven.",
            "No composite security or maturity score is emitted.",
        ],
    }
    receipts.validate("security-evidence-depth-report.schema.json", report)
    return report
