"""Vendor-neutral adversarial/security finding evidence for issue #198.

The generic record is scanner-neutral. Vendor adapters may understand a pinned
source contract, but the normalized evidence cannot create memory authority,
standing policy, universal vulnerability/safety claims, admission, or external
certification.
"""

from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any

import rfc8785

from ..core import receipts

PROFILE_VERSION = "0.1.0"

GARAK_VERSION = "0.16.0"
GARAK_TAG = "v0.16.0"
GARAK_COMMIT = "dbe4515d12664f2e34ac2cea295f055c22fe82b4"
GARAK_SOURCE_REF = f"github://NVIDIA/garak/{GARAK_COMMIT}"

SNYK_AGENT_SCAN_VERSION = "0.5.17"
SNYK_AGENT_SCAN_TAG = "v0.5.17"
SNYK_AGENT_SCAN_COMMIT = "ea959964ce4728426fca9fa78c9e7809b972f313"
SNYK_AGENT_SCAN_SOURCE_REF = f"github://snyk/agent-scan/{SNYK_AGENT_SCAN_COMMIT}"

FINDING_FAMILIES = {"behavioral_probe", "supply_chain_configuration"}
SOURCE_CONTRACT_STATUSES = {"stable_pinned", "experimental_projection"}
RESULT_STATUSES = {
    "observed",
    "aborted",
    "declined",
    "partial",
    "target_unavailable",
    "evaluator_failure",
    "unknown_schema",
}
VERDICTS = {"hit", "no_hit", "mixed", "unknown", "error", "not_run"}
REPRODUCTION_STATES = {
    "not_attempted",
    "observed_once",
    "reproduced",
    "not_reproduced",
    "nondeterministic",
    "disputed",
}
FINDING_STATES = {
    "observed",
    "reproduced",
    "not_reproduced",
    "nondeterministic",
    "triaged",
    "remediation_proposed",
    "remediation_applied",
    "rescanned",
    "resolved",
    "residual",
    "disputed",
    "not_run",
}
CANDIDATE_CLASSES = {"threat_evidence", "correction_evidence", "incident_evidence", "conformance_evidence"}
TARGET_EXECUTION = {"observed", "possible", "not_observed", "not_applicable", "unknown"}
SANDBOX_STATES = {"isolated", "not_isolated", "not_applicable", "unknown"}
CONSENT_STATES = {"granted", "declined", "bypassed", "not_required", "unknown"}


def _sha256_ref(value: dict[str, Any]) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _ref(name: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _digest(name: str, value: object) -> str:
    text = _ref(name, value)
    if len(text) != 71 or not text.startswith("sha256:") or any(ch not in "0123456789abcdef" for ch in text[7:]):
        raise ValueError(f"{name} must be a lowercase sha256 digest reference")
    return text


def _refs(name: str, value: object) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{name} must be a list of non-empty strings")
    return list(dict.fromkeys(value))


def _optional_int(name: str, value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _binding(target: dict[str, str], expected_context: dict[str, str] | None) -> tuple[str, list[str]]:
    if expected_context is None:
        return "not_evaluated", []
    if not isinstance(expected_context, dict):
        raise ValueError("expected_context must be an object")
    reasons: list[str] = []
    for field in ("target_ref", "scope_ref", "tenant_ref", "project_ref", "environment_ref"):
        expected = expected_context.get(field)
        if expected is None:
            continue
        actual = target.get(field)
        if actual is None:
            reasons.append(f"{field}_missing")
        elif actual != expected:
            reasons.append(f"{field}_mismatch")
    return ("mismatch", reasons) if reasons else ("exact", [])


def normalize_security_finding(adapter_result: dict[str, Any], expected_context: dict[str, str] | None = None) -> dict[str, Any]:
    """Normalize one scanner finding/projection into the generic evidence contract."""
    if not isinstance(adapter_result, dict):
        raise ValueError("adapter_result must be an object")

    family = adapter_result.get("finding_family")
    if family not in FINDING_FAMILIES:
        raise ValueError(f"invalid finding_family {family!r}")
    contract_status = adapter_result.get("source_contract_status")
    if contract_status not in SOURCE_CONTRACT_STATUSES:
        raise ValueError(f"invalid source_contract_status {contract_status!r}")
    result_status = adapter_result.get("result_status")
    if result_status not in RESULT_STATUSES:
        raise ValueError(f"invalid result_status {result_status!r}")
    verdict = adapter_result.get("verdict")
    if verdict not in VERDICTS:
        raise ValueError(f"invalid verdict {verdict!r}")
    if result_status == "declined" and verdict != "not_run":
        raise ValueError("declined scan must use verdict='not_run'")
    if result_status == "target_unavailable" and verdict not in {"not_run", "unknown", "error"}:
        raise ValueError("target_unavailable cannot claim a substantive finding verdict")

    reproduction_state = adapter_result.get("reproduction_state")
    if reproduction_state not in REPRODUCTION_STATES:
        raise ValueError(f"invalid reproduction_state {reproduction_state!r}")
    finding_state = adapter_result.get("finding_state")
    if finding_state not in FINDING_STATES:
        raise ValueError(f"invalid finding_state {finding_state!r}")
    candidate_classification = adapter_result.get("candidate_classification")
    if candidate_classification not in CANDIDATE_CLASSES:
        raise ValueError(f"invalid candidate_classification {candidate_classification!r}")

    target: dict[str, str] = {
        "target_ref": _ref("target_ref", adapter_result.get("target_ref")),
        "scope_ref": _ref("scope_ref", adapter_result.get("scope_ref")),
    }
    for field in ("target_configuration_ref", "tenant_ref", "project_ref", "environment_ref"):
        value = adapter_result.get(field)
        if value is not None:
            target[field] = _ref(field, value)

    test: dict[str, Any] = {"check_ref": _ref("check_ref", adapter_result.get("check_ref"))}
    for field in ("check_version", "case_ref", "evaluator_ref", "evaluator_version", "seed_ref"):
        value = adapter_result.get(field)
        if value is not None:
            test[field] = _ref(field, value)
    if adapter_result.get("case_digest") is not None:
        test["case_digest"] = _digest("case_digest", adapter_result["case_digest"])
    for field in ("sample_size", "repetitions"):
        value = _optional_int(field, adapter_result.get(field))
        if value is not None:
            test[field] = value

    result: dict[str, Any] = {"status": result_status, "verdict": verdict}
    counts = {}
    for field in ("passed", "fails", "total_evaluated"):
        value = _optional_int(field, adapter_result.get(field))
        if value is not None:
            counts[field] = value
            result[field] = value
    if {"passed", "fails", "total_evaluated"}.issubset(counts) and counts["passed"] + counts["fails"] != counts["total_evaluated"]:
        raise ValueError("passed + fails must equal total_evaluated")

    source_metric = adapter_result.get("source_metric")
    if source_metric is not None:
        if not isinstance(source_metric, dict):
            raise ValueError("source_metric must be an object")
        metric = {
            "name": _ref("source_metric.name", source_metric.get("name")),
            "value": source_metric.get("value"),
        }
        if isinstance(metric["value"], bool) or not isinstance(metric["value"], (int, float)):
            raise ValueError("source_metric.value must be numeric")
        for bound in ("lower_bound", "upper_bound"):
            if source_metric.get(bound) is not None:
                value = source_metric[bound]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(f"source_metric.{bound} must be numeric")
                metric[bound] = value
        result["source_metric"] = metric
    if adapter_result.get("source_severity") is not None:
        result["source_severity"] = _ref("source_severity", adapter_result["source_severity"])

    target_execution = adapter_result.get("target_execution")
    sandbox = adapter_result.get("sandbox")
    consent = adapter_result.get("consent")
    if target_execution not in TARGET_EXECUTION:
        raise ValueError(f"invalid target_execution {target_execution!r}")
    if sandbox not in SANDBOX_STATES:
        raise ValueError(f"invalid sandbox {sandbox!r}")
    if consent not in CONSENT_STATES:
        raise ValueError(f"invalid consent {consent!r}")
    execution_context = {
        "target_execution": target_execution,
        "sandbox": sandbox,
        "consent": consent,
    }
    if adapter_result.get("scanner_privilege_ref") is not None:
        execution_context["scanner_privilege_ref"] = _ref("scanner_privilege_ref", adapter_result["scanner_privilege_ref"])

    lineage = {
        "prior_finding_refs": _refs("prior_finding_refs", adapter_result.get("prior_finding_refs")),
        "remediation_refs": _refs("remediation_refs", adapter_result.get("remediation_refs")),
        "rescan_refs": _refs("rescan_refs", adapter_result.get("rescan_refs")),
        "conflict_refs": _refs("conflict_refs", adapter_result.get("conflict_refs")),
    }

    body: dict[str, Any] = {
        "finding_family": family,
        "source": {
            "tool": _ref("source_tool", adapter_result.get("source_tool")),
            "version": _ref("source_version", adapter_result.get("source_version")),
            "source_ref": _ref("source_ref", adapter_result.get("source_ref")),
            "source_commit": _ref("source_commit", adapter_result.get("source_commit")),
            "adapter_id": _ref("adapter_id", adapter_result.get("adapter_id")),
            "adapter_version": _ref("adapter_version", adapter_result.get("adapter_version")),
            "source_contract_status": contract_status,
        },
        "target": target,
        "test": test,
        "result": result,
        "reproduction_state": reproduction_state,
        "finding_state": finding_state,
        "candidate_classification": candidate_classification,
        "execution_context": execution_context,
        "raw_evidence_digest": _digest("raw_evidence_digest", adapter_result.get("raw_evidence_digest")),
        "known_limitations": _refs("known_limitations", adapter_result.get("known_limitations")),
        "lineage": lineage,
        "observed_at": _ref("observed_at", adapter_result.get("observed_at")),
        "interpretation": {
            "authority_effect": "none",
            "universal_vulnerability": "not_established",
            "safety_claim": "not_established",
            "standing_policy": "not_established",
            "memory_admission": "not_established",
            "certification_claim": "none",
        },
    }
    if adapter_result.get("raw_evidence_ref") is not None:
        body["raw_evidence_ref"] = _ref("raw_evidence_ref", adapter_result["raw_evidence_ref"])

    binding_status, binding_reasons = _binding(target, expected_context)
    body["binding_status"] = binding_status
    body["binding_reasons"] = binding_reasons

    identity_body = deepcopy(body)
    document = {
        "schema_version": "1.0.0",
        "profile_version": PROFILE_VERSION,
        "finding_id": f"security-finding:{_sha256_ref(identity_body)}",
        **body,
    }
    receipts.validate("security-finding-evidence.schema.json", document)
    return document


def normalize_garak_eval(source: dict[str, Any], expected_context: dict[str, str] | None = None) -> dict[str, Any]:
    """Project one exact garak v0.16.0 eval record into generic evidence."""
    if source.get("garak_version") != GARAK_VERSION:
        raise ValueError(f"unsupported garak version {source.get('garak_version')!r}")
    if source.get("garak_source_commit") != GARAK_COMMIT:
        raise ValueError("garak source commit does not match pinned v0.16.0")
    record = source.get("eval_record")
    if not isinstance(record, dict) or record.get("entry_type") != "eval":
        raise ValueError("garak adapter requires an eval report.jsonl record")

    passed = _optional_int("eval_record.passed", record.get("passed"))
    fails = _optional_int("eval_record.fails", record.get("fails"))
    total = _optional_int("eval_record.total_evaluated", record.get("total_evaluated"))
    if passed is None or fails is None or total is None:
        raise ValueError("garak eval requires passed, fails, and total_evaluated")
    if passed + fails != total:
        raise ValueError("garak passed + fails must equal total_evaluated")
    if total == 0:
        verdict = "unknown"
    elif fails == 0:
        verdict = "no_hit"
    elif passed == 0:
        verdict = "hit"
    else:
        verdict = "mixed"

    metric: dict[str, Any] = {
        "name": "garak_pass_rate",
        "value": (passed / total) if total else 0.0,
    }
    if record.get("confidence_lower") is not None:
        metric["lower_bound"] = record["confidence_lower"]
    if record.get("confidence_upper") is not None:
        metric["upper_bound"] = record["confidence_upper"]

    adapter_result = {
        "finding_family": "behavioral_probe",
        "source_tool": "NVIDIA garak",
        "source_version": GARAK_TAG,
        "source_ref": GARAK_SOURCE_REF,
        "source_commit": GARAK_COMMIT,
        "adapter_id": "agent-memory:garak-eval-v01",
        "adapter_version": PROFILE_VERSION,
        "source_contract_status": "stable_pinned",
        "target_ref": source.get("target_ref"),
        "target_configuration_ref": source.get("target_configuration_ref"),
        "scope_ref": source.get("scope_ref"),
        "tenant_ref": source.get("tenant_ref"),
        "project_ref": source.get("project_ref"),
        "environment_ref": source.get("environment_ref"),
        "check_ref": f"garak-probe:{_ref('eval_record.probe', record.get('probe'))}",
        "check_version": GARAK_TAG,
        "case_ref": source.get("run_ref"),
        "evaluator_ref": f"garak-detector:{_ref('eval_record.detector', record.get('detector'))}",
        "evaluator_version": GARAK_TAG,
        "sample_size": total,
        "repetitions": source.get("repetitions"),
        "seed_ref": source.get("seed_ref"),
        "result_status": "observed",
        "verdict": verdict,
        "passed": passed,
        "fails": fails,
        "total_evaluated": total,
        "source_metric": metric,
        "reproduction_state": source.get("reproduction_state", "observed_once"),
        "finding_state": source.get("finding_state", "observed"),
        "candidate_classification": source.get("candidate_classification", "threat_evidence"),
        "target_execution": "observed",
        "sandbox": source.get("sandbox", "unknown"),
        "consent": source.get("consent", "not_required"),
        "scanner_privilege_ref": source.get("scanner_privilege_ref"),
        "raw_evidence_ref": source.get("raw_evidence_ref"),
        "raw_evidence_digest": source.get("raw_evidence_digest"),
        "known_limitations": [
            "Observed garak result is bounded to the pinned target, probe, detector, configuration, and sampling conditions.",
            "A no-hit result is not proof of safety outside the evaluated scope.",
        ] + _refs("known_limitations", source.get("known_limitations")),
        "prior_finding_refs": source.get("prior_finding_refs"),
        "remediation_refs": source.get("remediation_refs"),
        "rescan_refs": source.get("rescan_refs"),
        "conflict_refs": source.get("conflict_refs"),
        "observed_at": source.get("observed_at"),
    }
    return normalize_security_finding(adapter_result, expected_context)


def normalize_snyk_agent_scan_projection(source: dict[str, Any], expected_context: dict[str, str] | None = None) -> dict[str, Any]:
    """Normalize a bounded Snyk Agent Scan v0.5.17 projection.

    This adapter intentionally does not parse or expose unstable raw CLI field
    names. A caller maps the current upstream output into this stable projection
    at the adapter edge, and the generic Agent Memory schema remains unchanged.
    """
    if source.get("source_version") != SNYK_AGENT_SCAN_TAG:
        raise ValueError(f"unsupported Snyk Agent Scan version {source.get('source_version')!r}")
    if source.get("source_commit") != SNYK_AGENT_SCAN_COMMIT:
        raise ValueError("Snyk Agent Scan source commit does not match pinned v0.5.17")

    result_status = source.get("result_status")
    verdict = source.get("verdict")
    if result_status not in RESULT_STATUSES or verdict not in VERDICTS:
        raise ValueError("Snyk projection requires a generic result_status and verdict")

    consent = source.get("consent", "unknown")
    mcp_execution = source.get("mcp_server_execution")
    if mcp_execution not in {"executed", "could_execute", "not_executed", "not_applicable", "unknown"}:
        raise ValueError("invalid mcp_server_execution")
    target_execution = {
        "executed": "observed",
        "could_execute": "possible",
        "not_executed": "not_observed",
        "not_applicable": "not_applicable",
        "unknown": "unknown",
    }[mcp_execution]
    if consent == "declined" and mcp_execution == "executed":
        raise ValueError("declined Snyk MCP scan cannot claim server execution")

    limitations = [
        "Snyk Agent Scan CLI/JSON field names, issue codes, severity labels, and response structure are treated as experimental adapter-local details.",
        "Scanning stdio MCP configurations may execute configured commands; execution, consent, and sandbox context are preserved separately.",
    ] + _refs("known_limitations", source.get("known_limitations"))

    adapter_result = {
        "finding_family": "supply_chain_configuration",
        "source_tool": "Snyk Agent Scan",
        "source_version": SNYK_AGENT_SCAN_TAG,
        "source_ref": SNYK_AGENT_SCAN_SOURCE_REF,
        "source_commit": SNYK_AGENT_SCAN_COMMIT,
        "adapter_id": "agent-memory:snyk-agent-scan-projection-v01",
        "adapter_version": PROFILE_VERSION,
        "source_contract_status": "experimental_projection",
        "target_ref": source.get("component_ref"),
        "target_configuration_ref": source.get("configuration_ref"),
        "scope_ref": source.get("scope_ref"),
        "tenant_ref": source.get("tenant_ref"),
        "project_ref": source.get("project_ref"),
        "environment_ref": source.get("environment_ref"),
        "check_ref": source.get("check_ref"),
        "check_version": source.get("check_version"),
        "case_ref": source.get("scan_ref"),
        "case_digest": source.get("case_digest"),
        "evaluator_ref": source.get("evaluator_ref", "snyk-agent-scan:analysis"),
        "evaluator_version": SNYK_AGENT_SCAN_TAG,
        "sample_size": source.get("sample_size"),
        "result_status": result_status,
        "verdict": verdict,
        "source_metric": source.get("source_metric"),
        "source_severity": source.get("source_severity"),
        "reproduction_state": source.get("reproduction_state", "not_attempted"),
        "finding_state": source.get("finding_state", "not_run" if result_status == "declined" else "observed"),
        "candidate_classification": source.get("candidate_classification", "conformance_evidence" if result_status == "declined" else "threat_evidence"),
        "target_execution": target_execution,
        "sandbox": source.get("sandbox", "unknown"),
        "consent": consent,
        "scanner_privilege_ref": source.get("scanner_privilege_ref"),
        "raw_evidence_ref": source.get("raw_evidence_ref"),
        "raw_evidence_digest": source.get("raw_evidence_digest"),
        "known_limitations": limitations,
        "prior_finding_refs": source.get("prior_finding_refs"),
        "remediation_refs": source.get("remediation_refs"),
        "rescan_refs": source.get("rescan_refs"),
        "conflict_refs": source.get("conflict_refs"),
        "observed_at": source.get("observed_at"),
    }
    return normalize_security_finding(adapter_result, expected_context)
