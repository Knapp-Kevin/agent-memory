"""D/F/H/R/P evidence-depth report for P2-B scanner finding adapters."""

from __future__ import annotations

from typing import Any

from ..core import receipts
from .security_evidence_depth import LEVELS, REPORT_TYPE, REPORT_VERSION, _claim, _exact_commit
from .security_finding_harness import run_security_finding_harness


def build_security_finding_depth_report(agent_memory_commit: str) -> dict[str, Any]:
    commit = _exact_commit(agent_memory_commit)
    harness = run_security_finding_harness()
    claims = [
        _claim(
            agent_memory_commit=commit,
            claim_id="security-finding:garak-normalization",
            title="Pinned garak v0.16.0 eval results normalize as scoped non-authoritative security evidence",
            threat_family="adversarial_scanner_evidence",
            doctrine_refs=[
                "docs/15-memory-threat-model.md",
                "docs/profiles/security-finding-evidence-profile.md",
            ],
            fixture_refs=["fixtures/security-finding-evidence-matrix.json"],
            harness_ref="security-finding-harness:garak-v0.16.0",
            behavioral_passed=harness["cases"]["garak"]["passed"],
            scope_profiles=["L", "T", "E", "H"],
        ),
        _claim(
            agent_memory_commit=commit,
            claim_id="security-finding:snyk-agent-scan-projection",
            title="Snyk Agent Scan v0.5.17 experimental output projects into stable scoped non-authoritative evidence",
            threat_family="supply_chain_configuration_evidence",
            doctrine_refs=[
                "docs/15-memory-threat-model.md",
                "docs/profiles/security-finding-evidence-profile.md",
            ],
            fixture_refs=["fixtures/security-finding-evidence-matrix.json"],
            harness_ref="security-finding-harness:snyk-agent-scan-v0.5.17",
            behavioral_passed=harness["cases"]["snyk_agent_scan"]["passed"],
            scope_profiles=["L", "T", "E", "H"],
        ),
    ]
    report = {
        "report_type": REPORT_TYPE,
        "version": REPORT_VERSION,
        "agent_memory_commit": commit,
        "evidence_model": {
            "levels": list(LEVELS),
            "inference_policy": "no_level_may_be_inferred_from_another_level",
        },
        "claims": claims,
        "required_behavioral_cases_passed": harness["passed"],
        "non_certification_statement": "Evidence mapping and demonstrated behavior do not constitute external certification.",
        "known_limits": [
            "The garak adapter is behaviorally validated against pinned v0.16.0 eval-record semantics but this report does not execute a live garak scan; R remains unproven.",
            "The Snyk Agent Scan adapter consumes an Agent Memory-facing experimental projection rather than stabilizing upstream CLI/JSON fields; R remains unproven.",
            "Scanner findings remain scoped evidence candidates and do not establish universal vulnerability, safety, standing policy, memory admission, or certification.",
            "Production evidence P is not collected or inferred and remains explicitly unproven.",
            "No composite security or scanner-confidence score is emitted.",
        ],
    }
    receipts.validate("security-evidence-depth-report.schema.json", report)
    return report
