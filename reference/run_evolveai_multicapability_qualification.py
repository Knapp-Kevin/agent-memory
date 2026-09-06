#!/usr/bin/env python3
"""Normalize EvolveAI public-facade evidence into #298 qualification records."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from agentmem_ref.evolveai_profile import (
    ADAPTER_ID,
    ADAPTER_VERSION,
    EVOLVEAI_COMMIT,
    EXPECTED_MATURITY,
    IMPLEMENTATION_REF,
    QUALIFICATION_PROFILE_ID,
    QUALIFICATION_PROFILE_VERSION,
    QUALIFIED_CAPABILITIES,
    assert_scope_binding,
    build_profile_report,
    build_scope_binding,
    load_profile,
    profile_digest,
)
from agentmem_ref.qualification import (
    AdapterResult,
    QualificationRuntime,
    QualificationSubject,
    qualification_from_adapter_results,
)


MaturityBefore = dict[str, str]
MATURITY_BEFORE: MaturityBefore = {
    "vector_representation": "runtime_wired",
    "vector_candidate_retrieval": "runtime_wired",
    "temporal_graph": "runtime_wired",
    "graph_traversal": "implemented",
    "content_addressed_exact_retrieval": "runtime_wired",
    "tier_routing": "runtime_wired",
    "lifecycle_decay": "runtime_wired",
    "lifecycle_orchestration": "implemented",
    "rem_synthesis_consolidation": "implemented",
    "negative_failure_memory": "implemented",
    "persistent_snapshot_restart": "runtime_wired",
    "audited_deletion": "runtime_wired",
    "l3_provenance_audit": "implemented",
}

CAPABILITY_OBSERVATIONS: dict[str, tuple[str, ...]] = {
    "vector_representation": ("vector_scan_runtime",),
    "vector_candidate_retrieval": ("vector_scan_runtime",),
    "temporal_graph": ("l2_routing", "temporal_graph_association"),
    "graph_traversal": ("temporal_graph_association",),
    "content_addressed_exact_retrieval": (
        "exact_retrieval",
        "restart_preserved_current",
        "deleted_not_current",
    ),
    "tier_routing": ("l2_routing", "l3_routing"),
    "lifecycle_decay": ("lifecycle_synthesis",),
    "lifecycle_orchestration": ("lifecycle_synthesis",),
    "rem_synthesis_consolidation": ("lifecycle_synthesis",),
    "negative_failure_memory": ("shadow_candidate_block",),
    "persistent_snapshot_restart": (
        "pre_restart_health",
        "restart_preserved_current",
        "deletion_history_survives_restart",
    ),
    "audited_deletion": (
        "audited_delete",
        "deleted_not_current",
        "deletion_history_survives_restart",
    ),
    "l3_provenance_audit": (
        "pre_restart_health",
        "audited_delete",
        "deletion_history_survives_restart",
    ),
}

OPERATIONS = {
    "vector_representation": "represent",
    "vector_candidate_retrieval": "recall_candidate",
    "temporal_graph": "graph_store",
    "graph_traversal": "traverse",
    "content_addressed_exact_retrieval": "exact_retrieve",
    "tier_routing": "route",
    "lifecycle_decay": "maintenance",
    "lifecycle_orchestration": "orchestrate",
    "rem_synthesis_consolidation": "consolidate",
    "negative_failure_memory": "risk_candidate",
    "persistent_snapshot_restart": "save_load",
    "audited_deletion": "delete",
    "l3_provenance_audit": "verify_audit",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=Path, required=True)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--agent-memory-commit", required=True)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_digest(value: object) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(rendered).hexdigest()


def subject(capability_id: str) -> QualificationSubject:
    return QualificationSubject(
        component_id="evolveai",
        component_version=EVOLVEAI_COMMIT,
        implementation_ref=IMPLEMENTATION_REF,
        capability_id=capability_id,
        capability_version="1.0",
        adapter_id=ADAPTER_ID,
        adapter_version=ADAPTER_VERSION,
        qualification_profile_id=QUALIFICATION_PROFILE_ID,
        qualification_profile_version=QUALIFICATION_PROFILE_VERSION,
    )


def main() -> int:
    args = parse_args()
    profile = load_profile(args.profile)
    fixture = json.loads(args.fixture.read_text(encoding="utf-8"))
    raw = json.loads(args.raw.read_text(encoding="utf-8"))

    if raw.get("provider") != "evolveai" or raw.get("provider_version") != EVOLVEAI_COMMIT:
        raise SystemExit("native EvolveAI evidence is not bound to the repaired exact commit")
    expected_runtime = fixture["runtime"]
    if raw.get("runtime") != expected_runtime:
        raise SystemExit(
            f"native EvolveAI runtime identity drifted: observed={raw.get('runtime')} expected={expected_runtime}"
        )
    observations = raw.get("observations")
    if not isinstance(observations, dict):
        raise SystemExit("native EvolveAI evidence is missing observations")

    required_observations = sorted({item for items in CAPABILITY_OBSERVATIONS.values() for item in items})
    missing = [name for name in required_observations if observations.get(name) is not True]
    if missing:
        raise SystemExit(f"EvolveAI workload did not prove required observations: {missing}")

    fixture_provider = fixture["provider"]
    if fixture_provider["component_version"] != EVOLVEAI_COMMIT:
        raise SystemExit("fixture component pin drifted")
    if fixture_provider["implementation_ref"] != IMPLEMENTATION_REF:
        raise SystemExit("fixture implementation ref drifted")
    fixture_adapter = fixture["adapter"]
    expected_adapter = {
        "adapter_id": ADAPTER_ID,
        "adapter_version": ADAPTER_VERSION,
        "qualification_profile_id": QUALIFICATION_PROFILE_ID,
        "qualification_profile_version": QUALIFICATION_PROFILE_VERSION,
    }
    if fixture_adapter != expected_adapter:
        raise SystemExit("fixture adapter/profile identity drifted")

    profile_sha = profile_digest(profile)
    scope_spec = fixture["scope_binding"]
    binding = build_scope_binding(
        agent_memory_scope=scope_spec["agent_memory_scope"],
        provider_scope=scope_spec["provider_scope"],
        profile_sha256=profile_sha,
    )
    assert_scope_binding(
        binding,
        requested_scope=scope_spec["agent_memory_scope"],
        profile_sha256=profile_sha,
    )

    configuration = {
        "runtime": expected_runtime,
        "scope_binding": binding,
        "claim_boundaries": fixture["claim_boundaries"],
    }
    runtime = QualificationRuntime(
        configuration_digest=canonical_digest(configuration),
        fixture_id=fixture["fixture_id"],
        fixture_digest=sha256_file(args.fixture),
        dependency_refs=(
            f"MythologIQ-Labs-LLC/EvolveAI@{EVOLVEAI_COMMIT}",
            "rust:stable",
            "engine:EvolveAI::MockEngine@384",
        ),
        runtime_refs=(
            f"driver:{ADAPTER_ID}@{ADAPTER_VERSION}",
            f"qualification-profile:{QUALIFICATION_PROFILE_ID}@{QUALIFICATION_PROFILE_VERSION}",
            f"component-profile:{profile_sha}",
        ),
    )

    raw_digest = sha256_file(args.raw)
    profile_file_digest = sha256_file(args.profile)
    fixture_digest = sha256_file(args.fixture)
    artifact_digests = (raw_digest, profile_file_digest, fixture_digest)

    normalized = {
        "schema_version": "1.0.0",
        "provider": "evolveai",
        "provider_version": EVOLVEAI_COMMIT,
        "profile_digest": profile_sha,
        "scope_binding": binding,
        "vector": {
            "provider_engine": "MockEngine",
            "runtime_path_proven": True,
            "real_embedding_quality_proven": False,
            "agent_memory_recall_authority": False,
        },
        "graph": {
            "temporal_association_proven": True,
            "direct_neighbor_traversal_proven": True,
            "graph_augmented_context_assembly_proven": False,
        },
        "lifecycle": {
            "orchestration_proven": True,
            "rem_synthesis_path_proven": True,
            "all_decay_threshold_semantics_proven": False,
            "repetition_is_independent_corroboration": False,
        },
        "shadow": {
            "provider_native_block_observed": True,
            "agent_memory_interpretation": "risk_candidate_only",
            "agent_memory_pass_block_authority": False,
        },
        "persistence": {
            "current_state_survives_explicit_save_load": True,
            "delete_history_survives_explicit_save_load": True,
            "l1_restart_persistence_proven": False,
        },
        "deletion": {
            "native_l3_live_removal_proven": True,
            "native_delete_ledger_event_proven": True,
            "deleted_value_not_current_after_delete": True,
            "delete_history_survives_restart": True,
            "transitive_forgetting_proven": False,
            "external_derived_residue_absence_proven": False,
        },
        "correction": {
            "agent_memory_supersession_semantics_proven": False,
            "provider_revalidation_required": True,
        },
        "authority_effect": "none",
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    normalized_path = args.output_dir / "evolveai-normalized-evidence.json"
    normalized_path.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    normalized_ref = "artifact://evolveai-normalized-evidence.json"
    raw_ref = "artifact://evolveai-native-observation.json"

    records = []
    for capability_id in sorted(QUALIFIED_CAPABILITIES):
        expected_maturity = EXPECTED_MATURITY[capability_id]
        cap_subject = subject(capability_id)
        observation_names = CAPABILITY_OBSERVATIONS[capability_id]
        checks = [
            (f"native.{name}", observations[name] is True, raw_ref)
            for name in observation_names
        ]
        checks.extend(
            [
                ("exact_component_pin", raw["provider_version"] == EVOLVEAI_COMMIT, raw_ref),
                ("external_scope_bridge_bound", binding["agent_memory_scope"] == scope_spec["agent_memory_scope"], normalized_ref),
                ("profile_digest_bound", binding["component_profile_digest"] == profile_sha, normalized_ref),
                ("no_agent_memory_authority", normalized["authority_effect"] == "none", normalized_ref),
            ]
        )
        if capability_id in {"vector_representation", "vector_candidate_retrieval"}:
            checks.extend(
                [
                    ("mock_engine_explicit", raw["runtime"]["engine"] == "MockEngine", raw_ref),
                    ("real_embedding_quality_not_overclaimed", not normalized["vector"]["real_embedding_quality_proven"], normalized_ref),
                ]
            )
        if capability_id == "negative_failure_memory":
            checks.append(
                ("native_block_not_policy_authority", not normalized["shadow"]["agent_memory_pass_block_authority"], normalized_ref)
            )
        if capability_id in {"audited_deletion", "l3_provenance_audit"}:
            checks.extend(
                [
                    ("transitive_forgetting_not_overclaimed", not normalized["deletion"]["transitive_forgetting_proven"], normalized_ref),
                    ("external_residue_not_overclaimed", not normalized["deletion"]["external_derived_residue_absence_proven"], normalized_ref),
                ]
            )
        if capability_id == "content_addressed_exact_retrieval":
            checks.append(
                ("post_delete_currentness_absent", normalized["deletion"]["deleted_value_not_current_after_delete"], normalized_ref)
            )

        result = AdapterResult(
            subject=cap_subject,
            operation=OPERATIONS[capability_id],
            runtime_identity=f"EvolveAI@{EVOLVEAI_COMMIT};MockEngine:{expected_runtime['dimensions']}",
            input_refs=(f"fixture://{fixture['fixture_id']}",),
            raw_provider_refs=(raw_ref,),
            normalized_refs=(f"{normalized_ref}#{capability_id}",),
            currentness="current",
            failure_result="none",
            trace_ref=f"trace://evolveai/{capability_id}/1.0.0",
        )
        record = qualification_from_adapter_results(
            subject=cap_subject,
            runtime=runtime,
            license_id="Apache-2.0",
            license_ref=f"MythologIQ-Labs-LLC/EvolveAI/LICENSE@{EVOLVEAI_COMMIT}",
            use_posture="runtime_allowed",
            results=(result,),
            checks=checks,
            artifact_digests=artifact_digests,
            maturity_before=MATURITY_BEFORE[capability_id],
            profile_maturity_ceiling=expected_maturity,
            earned_maturity=expected_maturity,
            limitations=tuple(
                next(
                    capability["limitations"]
                    for capability in profile["capabilities"]
                    if capability["capability_id"] == capability_id
                )
            ),
        )
        record_path = args.output_dir / f"qualification-{capability_id}.json"
        record_path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        records.append(
            {
                "capability_id": capability_id,
                "earned_maturity": expected_maturity,
                "applicability_digest": record.applicability_digest,
                "record": record_path.name,
            }
        )

    profile_report = build_profile_report(profile, agent_memory_commit=args.agent_memory_commit)
    profile_report_path = args.output_dir / "evolveai-profile-report.json"
    profile_report_path.write_text(
        json.dumps(profile_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    invariants = {
        "all_native_observations_true": all(observations[name] is True for name in required_observations),
        "exact_repaired_pin": raw["provider_version"] == EVOLVEAI_COMMIT,
        "scope_binding_exact": binding["agent_memory_scope"] == scope_spec["agent_memory_scope"],
        "scope_binding_version_bound": binding["component_version"] == EVOLVEAI_COMMIT,
        "scope_binding_profile_bound": binding["component_profile_digest"] == profile_sha,
        "mock_vector_boundary_explicit": raw["runtime"]["engine"] == "MockEngine" and not normalized["vector"]["real_embedding_quality_proven"],
        "graphrag_not_inferred": not normalized["graph"]["graph_augmented_context_assembly_proven"],
        "shadow_block_not_authority": not normalized["shadow"]["agent_memory_pass_block_authority"],
        "deletion_currentness_proven": normalized["deletion"]["deleted_value_not_current_after_delete"],
        "delete_history_restart_proven": normalized["deletion"]["delete_history_survives_restart"],
        "transitive_forgetting_not_claimed": not normalized["deletion"]["transitive_forgetting_proven"],
        "external_residue_not_claimed_absent": not normalized["deletion"]["external_derived_residue_absence_proven"],
        "qualification_records_independent": len(records) == len(QUALIFIED_CAPABILITIES) and len({item["applicability_digest"] for item in records}) == len(records),
        "authority_effect_none": normalized["authority_effect"] == "none" and profile_report["authority_effect"] == "none",
    }
    if not all(invariants.values()):
        raise SystemExit(f"EvolveAI qualification invariants failed: {invariants}")

    summary = {
        "schema_version": "1.0.0",
        "agent_memory_commit": args.agent_memory_commit,
        "provider_commit": EVOLVEAI_COMMIT,
        "profile_digest": profile_sha,
        "raw_provider_digest": raw_digest,
        "fixture_digest": fixture_digest,
        "normalized_digest": sha256_file(normalized_path),
        "records": records,
        "invariants": invariants,
        "authority_effect": "none",
    }
    (args.output_dir / "evolveai-qualification-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
