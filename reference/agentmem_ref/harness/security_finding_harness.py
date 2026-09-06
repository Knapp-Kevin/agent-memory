"""Behavioral harness for the two P2-B scanner evidence families."""

from __future__ import annotations

from typing import Any

from ..memory.security_finding import normalize_garak_eval, normalize_snyk_agent_scan_projection


def _garak_case() -> dict[str, Any]:
    expected = {
        "target_ref": "target:scanner-harness",
        "scope_ref": "scope:tenant-a/project-a",
        "tenant_ref": "tenant-a",
        "project_ref": "project-a",
        "environment_ref": "env:test",
    }
    source = {
        "garak_version": "0.16.0",
        "garak_source_commit": "dbe4515d12664f2e34ac2cea295f055c22fe82b4",
        **expected,
        "target_configuration_ref": "config:scanner-harness:v1",
        "run_ref": "garak-run:harness",
        "repetitions": 4,
        "sandbox": "isolated",
        "raw_evidence_digest": "sha256:" + "a" * 64,
        "observed_at": "2026-08-12T22:55:00Z",
        "eval_record": {
            "entry_type": "eval",
            "probe": "probes.promptinject.HijackHateHumans",
            "detector": "detector.mitigation.MitigationBypass",
            "passed": 1,
            "fails": 3,
            "nones": 0,
            "total_evaluated": 4,
            "total_processed": 4,
        },
        "pama_outcome": "allow",
        "standing_policy": "global-block",
        "raw_attack_prompt": "must-not-copy",
    }
    finding = normalize_garak_eval(source, expected)
    checks = {
        "generic_family": finding["finding_family"] == "behavioral_probe",
        "stable_pin": finding["source"]["source_contract_status"] == "stable_pinned",
        "source_counts_preserved": (
            finding["result"]["passed"] == 1
            and finding["result"]["fails"] == 3
            and finding["result"]["total_evaluated"] == 4
        ),
        "mixed_finding_preserved": finding["result"]["verdict"] == "mixed",
        "binding_exact": finding["binding_status"] == "exact",
        "authority_none": finding["interpretation"]["authority_effect"] == "none",
        "universal_vulnerability_not_established": finding["interpretation"]["universal_vulnerability"] == "not_established",
        "standing_policy_not_established": finding["interpretation"]["standing_policy"] == "not_established",
        "hostile_fields_discarded": all(
            key not in finding for key in ("pama_outcome", "standing_policy", "raw_attack_prompt")
        ),
    }
    return {"case_id": "garak-pinned-eval-normalization", "passed": all(checks.values()), "checks": checks}


def _snyk_case() -> dict[str, Any]:
    expected = {
        "target_ref": "target:scanner-harness",
        "scope_ref": "scope:tenant-a/project-a",
        "tenant_ref": "tenant-a",
        "project_ref": "project-a",
        "environment_ref": "env:test",
    }
    source = {
        "source_version": "v0.5.17",
        "source_commit": "ea959964ce4728426fca9fa78c9e7809b972f313",
        "component_ref": expected["target_ref"],
        "configuration_ref": "config:mcp:scanner-harness",
        "scope_ref": expected["scope_ref"],
        "tenant_ref": expected["tenant_ref"],
        "project_ref": expected["project_ref"],
        "environment_ref": expected["environment_ref"],
        "check_ref": "snyk-agent-scan:tool-poisoning",
        "scan_ref": "snyk-agent-scan:harness",
        "result_status": "observed",
        "verdict": "hit",
        "mcp_server_execution": "executed",
        "sandbox": "isolated",
        "consent": "granted",
        "scanner_privilege_ref": "privilege:test-user",
        "raw_evidence_digest": "sha256:" + "b" * 64,
        "observed_at": "2026-08-12T22:56:00Z",
        "experimental_issue_code": "must-not-copy",
        "experimental_raw_response": {"secret": "must-not-copy"},
        "pama_outcome": "allow",
    }
    finding = normalize_snyk_agent_scan_projection(source, expected)
    checks = {
        "generic_family": finding["finding_family"] == "supply_chain_configuration",
        "experimental_projection_is_explicit": finding["source"]["source_contract_status"] == "experimental_projection",
        "binding_exact": finding["binding_status"] == "exact",
        "active_target_execution_preserved": finding["execution_context"]["target_execution"] == "observed",
        "sandbox_preserved": finding["execution_context"]["sandbox"] == "isolated",
        "consent_preserved": finding["execution_context"]["consent"] == "granted",
        "authority_none": finding["interpretation"]["authority_effect"] == "none",
        "memory_admission_not_established": finding["interpretation"]["memory_admission"] == "not_established",
        "experimental_fields_discarded": all(
            key not in finding for key in ("experimental_issue_code", "experimental_raw_response", "pama_outcome")
        ),
    }
    return {"case_id": "snyk-experimental-projection-normalization", "passed": all(checks.values()), "checks": checks}


def run_security_finding_harness() -> dict[str, Any]:
    cases = {"garak": _garak_case(), "snyk_agent_scan": _snyk_case()}
    return {"cases": cases, "passed": all(case["passed"] for case in cases.values())}
