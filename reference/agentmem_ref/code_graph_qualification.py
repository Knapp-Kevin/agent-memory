"""Provider-neutral CodeGenome/Graphify qualification normalizer for #300.

The module preserves provider-native outputs as separate artifacts and normalizes
only the tiny factual surface shared by the qualification fixture. It does not
rank products and cannot grant Agent Memory authority.
"""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

from .capabilities import ResolvedCapability
from .component_fallback import (
    ProviderFailure,
    QualifiedCapability,
    evaluate_explicit_fallback,
)
from .qualification import (
    AdapterResult,
    QualificationRuntime,
    QualificationSubject,
    qualification_from_adapter_results,
)

CODEGENOME_COMMIT = "43a6b7147ec78ec5c616723fa1dd30f342174860"
GRAPHIFY_RELEASE = "v0.9.43"
GRAPHIFY_COMMIT = "7281f27eac568f77f50910f59f84543458f5dfd1"
PROFILE_ID = "code-graph-traversal-currentness"
PROFILE_VERSION = "1.1.0"

_LINE = re.compile(r"^line (\d+):(\d+)$")


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def fixture_digest(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: str(item)):
        digest.update(str(path).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return "sha256:" + digest.hexdigest()


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def codegenome_subject() -> QualificationSubject:
    return QualificationSubject(
        component_id="codegenome",
        component_version=CODEGENOME_COMMIT,
        implementation_ref=f"MythologIQ-Labs-LLC/CodeGenome@{CODEGENOME_COMMIT}",
        capability_id="code_graph_traversal",
        capability_version="1.0",
        adapter_id="codegenome-cli",
        adapter_version="1.0.0",
        qualification_profile_id=PROFILE_ID,
        qualification_profile_version=PROFILE_VERSION,
    )


def graphify_subject() -> QualificationSubject:
    return QualificationSubject(
        component_id="graphify",
        component_version=GRAPHIFY_RELEASE,
        implementation_ref=f"Graphify-Labs/graphify@{GRAPHIFY_COMMIT}",
        capability_id="code_graph_traversal",
        capability_version="1.0",
        adapter_id="graphify-cli",
        adapter_version="1.0.0",
        qualification_profile_id=PROFILE_ID,
        qualification_profile_version=PROFILE_VERSION,
    )


def _codegenome_start_lines(path: Path) -> set[int]:
    payload = _load(path)
    if not isinstance(payload, list):
        raise ValueError(f"CodeGenome query output must be a list: {path}")
    lines: set[int] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        location = item.get("node")
        if not isinstance(location, str):
            continue
        match = _LINE.fullmatch(location)
        if match:
            lines.add(int(match.group(1)))
    return lines


def _clean_label(label: str) -> str:
    value = label.strip()
    if value.startswith("."):
        value = value[1:]
    if value.endswith("()"):
        value = value[:-2]
    return value


def _graphify_call_facts(path: Path) -> set[tuple[str, str, str]]:
    payload = _load(path)
    if not isinstance(payload, dict):
        raise ValueError(f"Graphify graph output must be an object: {path}")
    nodes = {
        node.get("id"): node
        for node in payload.get("nodes", [])
        if isinstance(node, dict) and node.get("id")
    }
    relationships = payload.get("links")
    if relationships is None:
        relationships = payload.get("edges", [])
    facts: set[tuple[str, str, str]] = set()
    for edge in relationships:
        if not isinstance(edge, dict) or edge.get("relation") != "calls":
            continue
        source = nodes.get(edge.get("source"))
        target = nodes.get(edge.get("target"))
        if not source or not target:
            continue
        source_file = str(edge.get("source_file") or source.get("source_file") or "")
        facts.add(
            (
                Path(source_file).name,
                _clean_label(str(source.get("label", ""))),
                _clean_label(str(target.get("label", ""))),
            )
        )
    return facts


def _checks(mapping: dict[str, bool], evidence_ref: str) -> tuple[tuple[str, bool, str], ...]:
    return tuple((name, passed, evidence_ref) for name, passed in mapping.items())


def _runtime(agent_memory_commit: str, all_fixture_paths: list[Path]) -> QualificationRuntime:
    configuration = {
        "profile": f"{PROFILE_ID}@{PROFILE_VERSION}",
        "codegenome": CODEGENOME_COMMIT,
        "graphify": f"{GRAPHIFY_RELEASE}@{GRAPHIFY_COMMIT}",
        "update_posture": "full_rebuild",
        "failure_posture": "explicit_unavailable",
        "fallback_posture": "explicit_equivalent_only",
    }
    configuration_digest = sha256_bytes(
        json.dumps(configuration, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )
    return QualificationRuntime(
        configuration_digest=configuration_digest,
        fixture_id="component-qualification-code-graph-v1-v2-failure",
        fixture_digest=fixture_digest(all_fixture_paths),
        dependency_refs=(
            f"CodeGenome@{CODEGENOME_COMMIT}",
            f"Graphify@{GRAPHIFY_RELEASE}:{GRAPHIFY_COMMIT}",
        ),
        runtime_refs=(f"agent-memory@{agent_memory_commit}", "python:3.12", "rust:stable"),
    )


def _failure_result(
    *,
    subject: QualificationSubject,
    raw_path: Path,
    normalized_path: Path,
) -> tuple[AdapterResult, ProviderFailure]:
    raw = _load(raw_path)
    normalized = _load(normalized_path)
    if not isinstance(raw, dict) or raw.get("exception_type") != "FileNotFoundError":
        raise ValueError(f"provider unavailable raw evidence is not a FileNotFoundError: {raw_path}")
    if not isinstance(normalized, dict):
        raise ValueError(f"provider unavailable normalized evidence must be an object: {normalized_path}")
    if normalized.get("component_id") != subject.component_id:
        raise ValueError("provider unavailable evidence component does not match qualification subject")
    if normalized.get("capability_id") != subject.capability_id:
        raise ValueError("provider unavailable evidence capability does not match qualification subject")
    if normalized.get("failure_result") != "provider_unavailable":
        raise ValueError("provider unavailable evidence has the wrong failure result")
    if normalized.get("currentness") != "unavailable":
        raise ValueError("provider unavailable evidence has the wrong currentness posture")
    if normalized.get("authority_effect") != "none":
        raise ValueError("provider unavailable evidence cannot grant authority")
    runtime_identity = normalized.get("runtime_identity")
    trace_ref = normalized.get("trace_ref")
    if not isinstance(runtime_identity, str) or not runtime_identity:
        raise ValueError("provider unavailable runtime identity is required")
    if not isinstance(trace_ref, str) or not trace_ref:
        raise ValueError("provider unavailable trace reference is required")

    adapter = AdapterResult(
        subject=subject,
        operation="provider_availability_probe",
        runtime_identity=runtime_identity,
        input_refs=(f"executable:{runtime_identity}",),
        raw_provider_refs=(str(raw_path),),
        normalized_refs=(str(normalized_path),),
        currentness="unavailable",
        failure_result="provider_unavailable",
        trace_ref=trace_ref,
    )
    failure = ProviderFailure(
        component_id=subject.component_id,
        capability_id=subject.capability_id,
        failure_result="provider_unavailable",
        evidence_ref=str(raw_path),
        trace_ref=trace_ref,
    )
    return adapter, failure


def _resolved_capability(component_id: str, component_version: str, maturity: str) -> ResolvedCapability:
    return ResolvedCapability(
        component_id=component_id,
        component_version=component_version,
        profile_version="component-profile-v1",
        capability_id="code_graph_traversal",
        capability_version="1.0",
        maturity=maturity,
        state_posture="derived",
        scope_posture="inherits_agent_memory_scope",
        failure_posture="explicit_unavailable",
        authority_effect="none",
        evidence_refs=(f"qualification:{component_id}:{PROFILE_ID}:{PROFILE_VERSION}",),
    )


def build_qualification_report(
    *,
    agent_memory_commit: str,
    fixture_paths: list[Path],
    codegenome_v1_main_downstream: Path,
    codegenome_v1_main_upstream: Path,
    codegenome_v1_decoy_downstream: Path,
    codegenome_v2_main_downstream: Path,
    codegenome_v2_main_upstream: Path,
    codegenome_v2_decoy_downstream: Path,
    codegenome_unavailable_raw: Path,
    codegenome_unavailable_normalized: Path,
    graphify_v1: Path,
    graphify_v2: Path,
    graphify_unavailable_raw: Path,
    graphify_unavailable_normalized: Path,
) -> dict[str, Any]:
    runtime = _runtime(agent_memory_commit, fixture_paths)

    cg_v1_down = _codegenome_start_lines(codegenome_v1_main_downstream)
    cg_v1_up = _codegenome_start_lines(codegenome_v1_main_upstream)
    cg_v1_decoy = _codegenome_start_lines(codegenome_v1_decoy_downstream)
    cg_v2_down = _codegenome_start_lines(codegenome_v2_main_downstream)
    cg_v2_up = _codegenome_start_lines(codegenome_v2_main_upstream)
    cg_v2_decoy = _codegenome_start_lines(codegenome_v2_decoy_downstream)

    codegenome_checks = {
        "v1_main_target_identity": 5 in cg_v1_down,
        "v1_main_downstream_leaf": 1 in cg_v1_down,
        "v1_main_downstream_excludes_top": 9 not in cg_v1_down,
        "v1_main_downstream_excludes_decoy_leaf": 12 not in cg_v1_down,
        "v1_main_upstream_top": 9 in cg_v1_up,
        "v1_main_upstream_excludes_leaf": 1 not in cg_v1_up,
        "v1_decoy_downstream_decoy_leaf": 12 in cg_v1_decoy,
        "v1_decoy_excludes_main_leaf": 1 not in cg_v1_decoy,
        "v2_main_target_identity": 5 in cg_v2_down,
        "v2_main_downstream_replacement_leaf": 13 in cg_v2_down,
        "v2_main_downstream_excludes_old_leaf": 1 not in cg_v2_down,
        "v2_main_downstream_excludes_decoy_leaf": 12 not in cg_v2_down,
        "v2_main_upstream_top": 9 in cg_v2_up,
        "v2_main_upstream_excludes_replacement_leaf": 13 not in cg_v2_up,
        "v2_decoy_downstream_decoy_leaf": 12 in cg_v2_decoy,
        "v2_decoy_excludes_replacement_leaf": 13 not in cg_v2_decoy,
        "full_rebuild_currentness": 1 in cg_v1_down and 1 not in cg_v2_down and 13 in cg_v2_down,
        "provider_unavailable_explicit": True,
    }

    graphify_v1_facts = _graphify_call_facts(graphify_v1)
    graphify_v2_facts = _graphify_call_facts(graphify_v2)
    graphify_checks = {
        "v1_main_middle_calls_leaf": ("main.rs", "middle", "leaf") in graphify_v1_facts,
        "v1_main_top_calls_middle": ("main.rs", "top", "middle") in graphify_v1_facts,
        "v1_decoy_middle_calls_decoy_leaf": ("decoy.rs", "middle", "decoy_leaf") in graphify_v1_facts,
        "v2_main_middle_calls_replacement_leaf": ("main.rs", "middle", "replacement_leaf") in graphify_v2_facts,
        "v2_main_top_calls_middle": ("main.rs", "top", "middle") in graphify_v2_facts,
        "v2_decoy_middle_calls_decoy_leaf": ("decoy.rs", "middle", "decoy_leaf") in graphify_v2_facts,
        "v2_excludes_old_main_edge": ("main.rs", "middle", "leaf") not in graphify_v2_facts,
        "full_rebuild_currentness": (
            ("main.rs", "middle", "leaf") in graphify_v1_facts
            and ("main.rs", "middle", "leaf") not in graphify_v2_facts
            and ("main.rs", "middle", "replacement_leaf") in graphify_v2_facts
        ),
        "provider_unavailable_explicit": True,
    }

    cg_subject = codegenome_subject()
    graphify_subject_value = graphify_subject()
    cg_failure_result, cg_failure = _failure_result(
        subject=cg_subject,
        raw_path=codegenome_unavailable_raw,
        normalized_path=codegenome_unavailable_normalized,
    )
    graphify_failure_result, _graphify_failure = _failure_result(
        subject=graphify_subject_value,
        raw_path=graphify_unavailable_raw,
        normalized_path=graphify_unavailable_normalized,
    )

    cg_raw = (
        codegenome_v1_main_downstream,
        codegenome_v1_main_upstream,
        codegenome_v1_decoy_downstream,
        codegenome_v2_main_downstream,
        codegenome_v2_main_upstream,
        codegenome_v2_decoy_downstream,
    )
    graphify_raw = (graphify_v1, graphify_v2)

    cg_result = AdapterResult(
        subject=cg_subject,
        operation="code_graph_traversal_v1_v2_full_rebuild",
        runtime_identity=f"CodeGenome@{CODEGENOME_COMMIT}",
        input_refs=("fixture:v1", "fixture:v2"),
        raw_provider_refs=tuple(str(path) for path in cg_raw),
        normalized_refs=("normalized:codegenome-code-graph",),
        currentness="v1_historical_v2_current_full_rebuild",
        failure_result="none",
        trace_ref="qualification:codegenome",
    )
    graphify_result = AdapterResult(
        subject=graphify_subject_value,
        operation="code_graph_traversal_v1_v2_full_rebuild",
        runtime_identity=f"Graphify@{GRAPHIFY_RELEASE}:{GRAPHIFY_COMMIT}",
        input_refs=("fixture:v1", "fixture:v2"),
        raw_provider_refs=tuple(str(path) for path in graphify_raw),
        normalized_refs=("normalized:graphify-code-graph",),
        currentness="v1_historical_v2_current_full_rebuild",
        failure_result="none",
        trace_ref="qualification:graphify",
    )

    cg_passed = all(codegenome_checks.values())
    graphify_passed = all(graphify_checks.values())
    cg_artifacts = (*cg_raw, codegenome_unavailable_raw, codegenome_unavailable_normalized)
    graphify_artifacts = (*graphify_raw, graphify_unavailable_raw, graphify_unavailable_normalized)
    cg_record = qualification_from_adapter_results(
        subject=cg_subject,
        runtime=runtime,
        license_id="MIT",
        license_ref=f"MythologIQ-Labs-LLC/CodeGenome/LICENSE@{CODEGENOME_COMMIT}",
        use_posture="runtime_allowed",
        results=(cg_result, cg_failure_result),
        checks=_checks(codegenome_checks, "normalized:codegenome-code-graph"),
        artifact_digests=tuple(sha256_file(path) for path in cg_artifacts),
        maturity_before="runtime_wired",
        profile_maturity_ceiling="evidence_proven",
        earned_maturity="runtime_wired" if not cg_passed else "evidence_proven",
        limitations=("Currentness in this slice is proven through explicit full rebuild, not incremental update.",),
    )
    graphify_record = qualification_from_adapter_results(
        subject=graphify_subject_value,
        runtime=runtime,
        license_id="Apache-2.0",
        license_ref=f"Graphify-Labs/graphify/LICENSE@{GRAPHIFY_COMMIT}",
        use_posture="runtime_allowed",
        results=(graphify_result, graphify_failure_result),
        checks=_checks(graphify_checks, "normalized:graphify-code-graph"),
        artifact_digests=tuple(sha256_file(path) for path in graphify_artifacts),
        maturity_before="runtime_wired",
        profile_maturity_ceiling="evidence_proven",
        earned_maturity="runtime_wired" if not graphify_passed else "evidence_proven",
        limitations=("Currentness in this slice is proven through explicit full rebuild, not incremental update.",),
    )

    cg_resolved = _resolved_capability("codegenome", CODEGENOME_COMMIT, cg_record.earned_maturity)
    graphify_resolved = _resolved_capability("graphify", GRAPHIFY_RELEASE, graphify_record.earned_maturity)
    primary = QualifiedCapability(cg_resolved, cg_record)
    graphify_candidate = QualifiedCapability(graphify_resolved, graphify_record)

    no_fallback = evaluate_explicit_fallback(
        primary=primary,
        failure=cg_failure,
        candidates=(graphify_candidate,),
        allowed_components=(),
    )
    explicit_graphify = evaluate_explicit_fallback(
        primary=primary,
        failure=cg_failure,
        candidates=(graphify_candidate,),
        allowed_components=("graphify",),
    )
    weaker_graphify = QualifiedCapability(
        replace(graphify_resolved, maturity="runtime_wired"),
        graphify_record,
    )
    weaker_refused = evaluate_explicit_fallback(
        primary=primary,
        failure=cg_failure,
        candidates=(weaker_graphify,),
        allowed_components=("graphify",),
    )

    return {
        "schema_version": "1.1.0",
        "profile": {"id": PROFILE_ID, "version": PROFILE_VERSION},
        "update_posture": "full_rebuild",
        "failure_posture": "explicit_unavailable",
        "providers": {
            "codegenome": {
                "checks": codegenome_checks,
                "v1_start_lines": {
                    "main_downstream": sorted(cg_v1_down),
                    "main_upstream": sorted(cg_v1_up),
                    "decoy_downstream": sorted(cg_v1_decoy),
                },
                "v2_start_lines": {
                    "main_downstream": sorted(cg_v2_down),
                    "main_upstream": sorted(cg_v2_up),
                    "decoy_downstream": sorted(cg_v2_decoy),
                },
                "qualification": cg_record.to_dict(),
                "passed": cg_passed,
            },
            "graphify": {
                "checks": graphify_checks,
                "v1_call_facts": [list(item) for item in sorted(graphify_v1_facts)],
                "v2_call_facts": [list(item) for item in sorted(graphify_v2_facts)],
                "qualification": graphify_record.to_dict(),
                "passed": graphify_passed,
            },
        },
        "failure_fallback": {
            "primary_failure": cg_failure.to_dict(),
            "no_fallback_configured": no_fallback.to_dict(),
            "explicit_graphify": explicit_graphify.to_dict(),
            "weaker_graphify_refused": weaker_refused.to_dict(),
            "authority_effect": "none",
        },
        "matched_result": {
            "both_passed": cg_passed and graphify_passed,
            "winner": None,
            "authority_effect": "none",
            "unrelated_capabilities_promoted": [],
        },
    }
