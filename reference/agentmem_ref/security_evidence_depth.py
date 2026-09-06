"""Security evidence-depth ledger and poisoning-boundary harness for issue #196.

The D/F/H/R/P levels are independent evidence claims:

D = documented doctrine
F = structural fixture/scenario
H = behavioral/conformance harness
R = runtime implementation evidence
P = production evidence

No level is inferred from another. In particular, executing this module proves
behavioral coverage only; runtime evidence is counted only when separately
supplied and bound to the exact Agent Memory head, and production evidence is
never manufactured by the reference implementation.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import policy, receipts
from .a2a_collaboration import normalize_a2a_collaboration
from .adapter import Clock, GovernedMemoryAdapter
from .mcp_interaction import normalize_mcp_interaction
from .substrate import InMemoryTemporalGraph

LEVELS = ("D", "F", "H", "R", "P")
LEVEL_RANK = {level: index for index, level in enumerate(LEVELS)}
REPORT_TYPE = "agent-memory-security-evidence-depth"
REPORT_VERSION = "1.0.0"


def _exact_commit(value: str) -> str:
    commit = value.lower()
    if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
        raise ValueError("agent_memory_commit must be an exact 40-hex commit")
    return commit


def _dedupe_refs(values: list[str] | tuple[str, ...] | None) -> list[str]:
    if not values:
        return []
    if not all(isinstance(value, str) and value for value in values):
        raise ValueError("evidence references must be non-empty strings")
    return list(dict.fromkeys(values))


def classify_evidence_levels(evidence_by_level: dict[str, list[str] | tuple[str, ...]]) -> dict[str, Any]:
    """Classify exactly the levels with evidence refs, without gap filling.

    A claim with D and H evidence remains D+H. F is not inferred merely because
    behavioral evidence exists. This intentionally permits non-contiguous
    evidence sets because the report describes evidence, not an ordinal badge.
    """
    unknown = set(evidence_by_level) - set(LEVELS)
    if unknown:
        raise ValueError(f"unknown evidence levels: {sorted(unknown)}")
    normalized = {level: _dedupe_refs(evidence_by_level.get(level, [])) for level in LEVELS}
    demonstrated = [level for level in LEVELS if normalized[level]]
    unproven = [level for level in LEVELS if not normalized[level]]
    highest = max(demonstrated, key=lambda level: LEVEL_RANK[level]) if demonstrated else "none"
    return {
        "evidence": normalized,
        "demonstrated_levels": demonstrated,
        "highest_demonstrated_level": highest,
        "explicitly_unproven_levels": unproven,
    }


def _direct_external_write_case() -> dict[str, Any]:
    """Exercise an untrusted/high-confidence poisoning proposal on the real adapter."""
    common = dict(
        actor_id="external:untrusted-source",
        charter_version="charter:external-ingest-v1",
        target_reference="mem:poisoning:direct-external-write",
        target_class=policy.M4,
        scope="scope:tenant-a/project-a",
        operation="promotion",
        current_strength="observed",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="high",
        evidence_refs=(
            "evidence:external-untrusted:source-1",
            "evidence:derived-repeat:source-1:copy-1",
            "evidence:derived-repeat:source-1:copy-2",
        ),
        estimator_refs=("estimator:semantic-confidence",),
        estimator_versions=("estimator:semantic-confidence:v1",),
        tenant_ref="tenant-a",
        project_ref="project-a",
        purpose="poisoning-boundary-harness",
    )

    high_substrate = InMemoryTemporalGraph()
    low_substrate = InMemoryTemporalGraph()
    high_adapter = GovernedMemoryAdapter(high_substrate, tenant="tenant-a", clock=Clock())
    low_adapter = GovernedMemoryAdapter(low_substrate, tenant="tenant-a", clock=Clock())

    high = high_adapter.commit_proposal(
        policy.Proposal(proposal_id="poison:direct:high-confidence", confidence=0.99, **common),
        "untrusted external content attempting durable promotion",
    )
    low = low_adapter.commit_proposal(
        policy.Proposal(proposal_id="poison:direct:low-confidence", confidence=0.01, **common),
        "untrusted external content attempting durable promotion",
    )

    high_writes = [entry for entry in high_substrate.write_log if entry[0] == "write_fact"]
    low_writes = [entry for entry in low_substrate.write_log if entry[0] == "write_fact"]
    expected_evidence = list(common["evidence_refs"])
    preserved = high.pama_decision["basis"]["evidence_refs"] == expected_evidence

    checks = {
        "high_confidence_not_committed": not high.committed and not high_writes,
        "low_confidence_not_committed": not low.committed and not low_writes,
        "confidence_did_not_change_outcome": high.decision.outcome == low.decision.outcome,
        "confidence_did_not_change_permitted_actions": high.decision.permitted_actions == low.decision.permitted_actions,
        "confidence_did_not_change_prohibited_actions": high.decision.prohibited_actions == low.decision.prohibited_actions,
        "promotion_remained_prohibited": "promotion" in high.decision.prohibited_actions,
        "provenance_evidence_refs_preserved": preserved,
        "repeated_derived_refs_did_not_discharge_review": high.decision.outcome in {
            policy.REQUIRE_REVIEW,
            policy.REQUIRE_EXTERNAL_VERIFICATION,
            policy.BLOCK,
        },
    }
    return {
        "case_id": "direct-external-write-poisoning",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "high_confidence": 0.99,
            "low_confidence": 0.01,
            "high_outcome": high.decision.outcome,
            "low_outcome": low.decision.outcome,
            "high_selected_action": high.receipt["selected_action"],
            "low_selected_action": low.receipt["selected_action"],
            "evidence_refs": expected_evidence,
            "substrate_write_count": len(high_writes) + len(low_writes),
        },
    }


def _mcp_ingestion_case() -> dict[str, Any]:
    """Exercise merged MCP resource ingestion as a non-authoritative candidate."""
    value = {
        "protocol_revision": "2026-07-28",
        "protocol_source_commit": "5f5440bb26a62e2cf3440b92da5a667efa03b267",
        "interaction_kind": "resource_read",
        "method": "resources/read",
        "client_ref": "mcp-client:poisoning-harness",
        "server_ref": "mcp-server:untrusted-peer",
        "request_id": "poisoning-resource-1",
        "target_ref": "mcp-resource:untrusted:1",
        "memory_effect": "memory_candidate",
        "request_status": "observed",
        "result_status": "complete",
        "result_classification": "success",
        "governance_status": "not_required",
        "request_digest": "sha256:" + "a" * 64,
        "result_digest": "sha256:" + "b" * 64,
        "observed_at": "2026-08-12T22:41:00Z",
        "evidence_refs": ["evidence:mcp:untrusted-resource"],
        # Hostile peer-only fields must be discarded.
        "pama_outcome": "allow",
        "lifecycle_state": "canonical",
        "memory_authority": "owner",
        "permitted_actions": ["everything"],
        "resource_content": "poisoned raw content must not be copied",
    }
    result = normalize_mcp_interaction(value, None)
    hostile = ("pama_outcome", "lifecycle_state", "memory_authority", "permitted_actions", "resource_content")
    checks = {
        "resource_is_memory_candidate_only": result["memory_effect"] == "memory_candidate",
        "memory_admission_not_established": result["interpretation"]["memory_admission"] == "not_established",
        "authority_effect_none": result["interpretation"]["authority_effect"] == "none",
        "execution_not_established": result["interpretation"]["execution_claim"] == "not_established",
        "hostile_fields_discarded": all(key not in result for key in hostile),
        "protocol_result_does_not_require_governance_for_candidate": result["governance_alignment"] == "not_applicable",
    }
    return {
        "case_id": "mcp-ingestion-poisoning",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "interaction_id": result["interaction_id"],
            "binding_status": result["binding_status"],
            "governance_alignment": result["governance_alignment"],
            "result_classification": result["result_classification"],
        },
    }


def _a2a_ingestion_case() -> dict[str, Any]:
    """Exercise merged A2A artifact ingestion plus cross-tenant mismatch."""
    candidate = {
        "protocol_release": "v1.0.1",
        "protocol_source_commit": "3303592588e388e62e0f69f701af531d2f4e3991",
        "direction": "inbound",
        "interaction_kind": "artifact",
        "local_agent_ref": "agent:local:poisoning-harness",
        "remote_agent_ref": "agent:remote:untrusted-peer",
        "agent_card_digest": "sha256:" + "c" * 64,
        "task_ref": "a2a-task:poisoning-1",
        "context_ref": "a2a-context:poisoning-1",
        "artifact_ref": "a2a-artifact:poisoning-1:artifact-1",
        "export_classification": "memory_candidate",
        "memory_evidence_status": "not_applicable",
        "task_state": "completed",
        "governance_status": "not_required",
        "external_evidence_refs": ["external-evidence:remote-identity-verified"],
        "payload_digest": "sha256:" + "d" * 64,
        "observed_at": "2026-08-12T22:42:00Z",
        "evidence_refs": ["evidence:a2a:untrusted-artifact"],
        # Hostile peer-only fields must be discarded.
        "pama_outcome": "allow",
        "lifecycle_state": "canonical",
        "authority_transition": "standing_grant",
        "artifact_body": "poisoned raw content must not be copied",
    }
    normalized_candidate = normalize_a2a_collaboration(candidate, None)

    expected_context = {
        "action_ref": "action:a2a:known-local-action",
        "input_identity": "sha256:" + "e" * 64,
        "scope_ref": "scope:tenant-a/project-a",
        "tenant_ref": "tenant-a",
        "project_ref": "project-a",
    }
    cross_tenant = deepcopy(candidate)
    cross_tenant.update(
        {
            "interaction_kind": "task_status",
            "export_classification": "explicit_non_memory",
            "memory_evidence_status": "not_applicable",
            "governance_status": "available",
            "effective_decision": "allow",
            "action_ref": expected_context["action_ref"],
            "input_identity": expected_context["input_identity"],
            "scope_ref": "scope:tenant-b/project-b",
            "tenant_ref": "tenant-b",
            "project_ref": "project-b",
        }
    )
    cross_tenant.pop("artifact_ref", None)
    normalized_cross_tenant = normalize_a2a_collaboration(cross_tenant, expected_context)

    hostile = ("pama_outcome", "lifecycle_state", "authority_transition", "artifact_body")
    checks = {
        "artifact_is_memory_candidate_only": normalized_candidate["export_classification"] == "memory_candidate",
        "memory_admission_not_established": normalized_candidate["interpretation"]["memory_admission"] == "not_established",
        "peer_identity_not_authority": normalized_candidate["interpretation"]["delegated_memory_authority"] == "not_established",
        "peer_identity_not_semantic_correctness": normalized_candidate["interpretation"]["semantic_correctness"] == "not_established",
        "hostile_fields_discarded": all(key not in normalized_candidate for key in hostile),
        "cross_tenant_binding_mismatch": normalized_cross_tenant["binding_status"] == "mismatch",
        "cross_tenant_governance_mismatch": normalized_cross_tenant["governance_alignment"] == "binding_mismatch",
    }
    return {
        "case_id": "a2a-ingestion-poisoning",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "collaboration_id": normalized_candidate["collaboration_id"],
            "candidate_classification": normalized_candidate["export_classification"],
            "cross_tenant_binding_reasons": normalized_cross_tenant["binding_reasons"],
        },
    }


def run_poisoning_harness() -> dict[str, Any]:
    cases = {
        "direct_external_write": _direct_external_write_case(),
        "mcp_ingestion": _mcp_ingestion_case(),
        "a2a_ingestion": _a2a_ingestion_case(),
    }
    return {
        "cases": cases,
        "passed": all(case["passed"] for case in cases.values()),
    }


def _runtime_direct_evidence(agent_memory_commit: str, benchmark_security: dict[str, Any] | None) -> tuple[list[str], list[str]]:
    """Return current and stale direct-poisoning runtime evidence refs.

    The same-head P5 scorecard is accepted as R evidence only if its hard gates
    pass and the confidence-authority metric is exactly zero. A scorecard bound
    to another head remains useful historical evidence but cannot prove current R.
    """
    if benchmark_security is None:
        return [], []
    if not isinstance(benchmark_security, dict):
        raise ValueError("benchmark_security must be an object")
    benchmark_commit = benchmark_security.get("agent_memory_commit")
    ref = f"ci-artifact:p5-benchmark-security-scorecard@{benchmark_commit}#authority_from_confidence_count"
    valid_behavior = (
        benchmark_security.get("hard_gates_passed") is True
        and benchmark_security.get("metrics", {}).get("authority_from_confidence_count") == 0
        and benchmark_security.get("cases", {}).get("authority_from_confidence", {}).get("passed") is True
    )
    if not valid_behavior:
        return [], []
    if benchmark_commit == agent_memory_commit:
        return [ref], []
    return [], [ref]


def _claim(
    *,
    agent_memory_commit: str,
    claim_id: str,
    title: str,
    threat_family: str,
    doctrine_refs: list[str],
    fixture_refs: list[str],
    harness_ref: str,
    behavioral_passed: bool,
    runtime_evidence_refs: list[str] | None = None,
    stale_runtime_evidence_refs: list[str] | None = None,
    runtime_evidence_head: str | None = None,
    production_evidence_refs: list[str] | None = None,
    external_mappings: list[dict[str, str]] | None = None,
    scope_profiles: list[str] | None = None,
) -> dict[str, Any]:
    runtime_refs = _dedupe_refs(runtime_evidence_refs)
    production_refs = _dedupe_refs(production_evidence_refs)
    stale_runtime_refs = _dedupe_refs(stale_runtime_evidence_refs)
    mappings = deepcopy(external_mappings or [])
    for mapping in mappings:
        if mapping.get("certification_claim") != "none":
            raise ValueError("external mappings must set certification_claim='none'")
        for required in ("source", "version", "control_ref"):
            if not isinstance(mapping.get(required), str) or not mapping[required]:
                raise ValueError(f"external mapping requires {required}")

    evidence = {
        "D": _dedupe_refs(doctrine_refs),
        "F": _dedupe_refs(fixture_refs),
        "H": [harness_ref] if behavioral_passed else [],
        "R": runtime_refs,
        "P": production_refs,
    }
    depth = classify_evidence_levels(evidence)
    claim = {
        "claim_id": claim_id,
        "title": title,
        "threat_family": threat_family,
        "doctrine_refs": depth["evidence"]["D"],
        "fixture_refs": depth["evidence"]["F"],
        "behavioral_harness_refs": depth["evidence"]["H"],
        "runtime_evidence_refs": depth["evidence"]["R"],
        "production_evidence_refs": depth["evidence"]["P"],
        "external_mappings": mappings,
        "demonstrated_levels": depth["demonstrated_levels"],
        "highest_demonstrated_level": depth["highest_demonstrated_level"],
        "explicitly_unproven_levels": depth["explicitly_unproven_levels"],
        "scope_profiles": list(dict.fromkeys(scope_profiles or ["L", "T", "E", "H"])),
        "evaluated_head": agent_memory_commit,
        "behavioral_passed": behavioral_passed,
        "non_certification_statement": "This claim records bounded evidence depth and does not assert external certification.",
    }
    if runtime_evidence_head is not None and runtime_refs:
        claim["runtime_evidence_head"] = _exact_commit(runtime_evidence_head)
    if stale_runtime_refs:
        claim["stale_runtime_evidence_refs"] = stale_runtime_refs
    return claim


def build_report(
    agent_memory_commit: str,
    *,
    benchmark_security: dict[str, Any] | None = None,
) -> dict[str, Any]:
    commit = _exact_commit(agent_memory_commit)
    harness = run_poisoning_harness()
    direct_runtime_refs, stale_direct_refs = _runtime_direct_evidence(commit, benchmark_security)

    claims = [
        _claim(
            agent_memory_commit=commit,
            claim_id="poisoning:direct-external-write",
            title="Direct untrusted external content cannot self-authorize durable promotion",
            threat_family="memory_poisoning",
            doctrine_refs=["docs/15-memory-threat-model.md", "docs/04-governance-and-pama.md"],
            fixture_refs=["fixtures/security-evidence-depth-matrix.json"],
            harness_ref="security-poisoning-harness:direct-external-write",
            behavioral_passed=harness["cases"]["direct_external_write"]["passed"],
            runtime_evidence_refs=direct_runtime_refs,
            stale_runtime_evidence_refs=stale_direct_refs,
            runtime_evidence_head=commit if direct_runtime_refs else None,
        ),
        _claim(
            agent_memory_commit=commit,
            claim_id="poisoning:mcp-ingestion",
            title="MCP tool/resource output remains evidence or a memory candidate under normal admission",
            threat_family="protocol_ingestion_poisoning",
            doctrine_refs=["docs/15-memory-threat-model.md", "docs/profiles/mcp-interaction-evidence-profile.md"],
            fixture_refs=["fixtures/mcp-interaction-evidence-matrix.json", "fixtures/security-evidence-depth-matrix.json"],
            harness_ref="security-poisoning-harness:mcp-ingestion",
            behavioral_passed=harness["cases"]["mcp_ingestion"]["passed"],
        ),
        _claim(
            agent_memory_commit=commit,
            claim_id="poisoning:a2a-ingestion",
            title="A2A peer Message/Artifact content remains evidence or a memory candidate under normal admission",
            threat_family="cross_agent_ingestion_poisoning",
            doctrine_refs=["docs/15-memory-threat-model.md", "docs/profiles/a2a-collaboration-evidence-profile.md"],
            fixture_refs=["fixtures/a2a-collaboration-evidence-matrix.json", "fixtures/security-evidence-depth-matrix.json"],
            harness_ref="security-poisoning-harness:a2a-ingestion",
            behavioral_passed=harness["cases"]["a2a_ingestion"]["passed"],
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
            "The V0.1 poisoning harness covers direct external writes, MCP ingestion, and non-authority-bearing A2A ingestion only.",
            "MCP and A2A cases demonstrate behavioral H evidence against reference normalizers, not live-host runtime R evidence.",
            "Direct-write R evidence is claimed only when a same-head passing P5 benchmark-security artifact is supplied to the report generator.",
            "Production evidence P is not collected or inferred by this report and remains explicitly unproven unless separately supplied by a future governed process.",
            "No composite security, maturity, coverage, or certification score is emitted.",
        ],
    }
    receipts.validate("security-evidence-depth-report.schema.json", report)
    return report


def with_behavioral_failure(report: dict[str, Any], claim_id: str) -> dict[str, Any]:
    """Test helper proving a failed behavioral case cannot remain H."""
    mutated = deepcopy(report)
    target = next((claim for claim in mutated["claims"] if claim["claim_id"] == claim_id), None)
    if target is None:
        raise ValueError(f"unknown claim_id {claim_id!r}")
    target["behavioral_passed"] = False
    target["behavioral_harness_refs"] = []
    evidence = {
        "D": target["doctrine_refs"],
        "F": target["fixture_refs"],
        "H": [],
        "R": target["runtime_evidence_refs"],
        "P": target["production_evidence_refs"],
    }
    depth = classify_evidence_levels(evidence)
    target["demonstrated_levels"] = depth["demonstrated_levels"]
    target["highest_demonstrated_level"] = depth["highest_demonstrated_level"]
    target["explicitly_unproven_levels"] = depth["explicitly_unproven_levels"]
    mutated["required_behavioral_cases_passed"] = all(claim["behavioral_passed"] for claim in mutated["claims"])
    receipts.validate("security-evidence-depth-report.schema.json", mutated)
    return mutated
