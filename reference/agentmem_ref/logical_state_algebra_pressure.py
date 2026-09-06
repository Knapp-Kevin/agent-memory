"""Executable pressure test for issue #276.

This harness asks a deliberately narrow question: can the existing Agent Memory
contracts already express the governance-relevant consequence of the #276
cross-substrate scenarios without introducing a new logical state algebra?

It reuses existing executable evidence rather than re-encoding lifecycle,
currentness, PAMA, maintenance, or conditional-memory semantics in a new model.
A passing result is evidence for ``no_new_algebra`` at this bounded evidence
level. It is not evidence that future real module adapters cannot expose a
missing reusable transition contract.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .architecture_family_closeout import run_closeout_evidence
from .autonomous_maintenance_harness import run_autonomous_maintenance_harness
from .conditional_memory_harness import run_conditional_memory_harness

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / "docs" / "explorations" / "memory-architectures" / "logical-state-algebra-scenarios.json"
_HEX40 = re.compile(r"^[0-9a-f]{40}$")


def _scenario(
    scenario_id: str,
    *,
    family: str,
    checks: dict[str, bool],
    evidence_refs: list[str],
) -> dict[str, Any]:
    return {
        "id": scenario_id,
        "substrate_family": family,
        "checks": checks,
        "existing_contracts_express_scenario": all(checks.values()),
        "missing_generic_primitive_observed": False,
        "evidence_refs": evidence_refs,
    }


def _backend_replacement_case() -> dict[str, Any]:
    """Model logical continuity across physical backend replacement.

    The fixture intentionally gives the old and new stores different physical
    identifiers while preserving a stable logical memory reference and an
    explicit migration/rebuild receipt. Physical identifiers therefore remain
    implementation references rather than canonical memory identity.
    """

    before = {
        "logical_ref": "memory:project-a:procedure-17",
        "physical_backend": "sqlite",
        "physical_ref": "row:417",
        "content_ref": "sha256:" + "1" * 64,
        "module_profile": "explicit-document/0.1",
    }
    after = {
        "logical_ref": before["logical_ref"],
        "physical_backend": "graph-store",
        "physical_ref": "node:9f2a",
        "content_ref": before["content_ref"],
        "module_profile": "explicit-document/0.2",
    }
    migration = {
        "from_physical_ref": before["physical_ref"],
        "to_physical_ref": after["physical_ref"],
        "logical_ref": before["logical_ref"],
        "source_currentness": "current",
        "result": "rebuilt_current",
    }
    return {
        "before": before,
        "after": after,
        "migration": migration,
        "logical_identity_preserved": before["logical_ref"] == after["logical_ref"],
        "physical_identity_changed": before["physical_ref"] != after["physical_ref"],
        "content_identity_not_physical_identity": before["content_ref"] == after["content_ref"],
        "migration_binds_logical_identity": migration["logical_ref"] == before["logical_ref"],
    }


def run_logical_state_algebra_pressure(agent_memory_commit: str) -> dict[str, Any]:
    if not _HEX40.fullmatch(agent_memory_commit):
        raise ValueError("agent_memory_commit must be an exact lowercase 40-hex commit")

    scenario_contract = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    expected_ids = {item["id"] for item in scenario_contract["scenarios"]}

    architecture = run_closeout_evidence()
    by_family = {item["family"]: item for item in architecture["families"]}
    maintenance = run_autonomous_maintenance_harness()
    conditional = run_conditional_memory_harness()
    replacement = _backend_replacement_case()

    relational = by_family["relational_document_store"]
    graph = by_family["knowledge_graph_graphrag"]
    event = by_family["event_log_ledger"]
    hybrid = by_family["hybrid_composition"]
    shared = by_family["shared_distributed"]

    scenarios = [
        _scenario(
            "LSA-01",
            family="relational_document",
            checks={
                "exact_logical_identity_available": relational["exact_identity_available"] is True,
                "stale_projection_detected": relational["stale_derived_detected"] is True,
                "delete_residue_detected": relational["deletion_residue_detected"] is True,
                "transaction_not_derived_cleanup": relational["transaction_atomicity_is_derived_cleanup"] is False,
                "provenance_reconstructable": relational["provenance_reconstructable"] is True,
            },
            evidence_refs=["architecture_family_closeout:relational_document_store"],
        ),
        _scenario(
            "LSA-02",
            family="knowledge_temporal_graph",
            checks={
                "stale_derived_path_detected": graph["stale_derived_detected"] is True,
                "cached_reachability_not_admitted": graph["cached_reachability_admitted"] is False,
                "reachability_not_permission": graph["retrieval_or_reachability_is_permission"] is False,
                "provenance_reconstructable": graph["provenance_reconstructable"] is True,
            },
            evidence_refs=["architecture_family_closeout:knowledge_graph_graphrag"],
        ),
        _scenario(
            "LSA-03",
            family="event_log_ledger",
            checks={
                "current_truth_separate_from_history": event["current_truth_separate_from_history"] is True,
                "tombstone_not_forgetting_proof": event["tombstone_is_forgetting_proof"] is False,
                "historical_provenance_reconstructable": event["provenance_reconstructable"] is True,
                "history_not_authority": event["authority_effect"] == "none",
            },
            evidence_refs=["architecture_family_closeout:event_log_ledger"],
        ),
        _scenario(
            "LSA-04",
            family="hybrid",
            checks={
                "stale_cross_surface_state_detected": hybrid["stale_derived_detected"] is True,
                "residual_projection_detected": hybrid["deletion_residue_detected"] is True,
                "deletion_closure_names_canonical_source": "canonical_source" in hybrid["deletion_closure"],
                "derived_state_has_no_write_authority": hybrid["probabilistic_or_derived_state_has_write_authority"] is False,
            },
            evidence_refs=["architecture_family_closeout:hybrid_composition"],
        ),
        _scenario(
            "LSA-05",
            family="distributed_or_shared",
            checks={
                "conflicting_writer_detected": shared["conflicting_writer_detected"] is True,
                "shared_membership_not_mutation_authority": shared["shared_membership_is_mutation_authority"] is False,
                "stale_conflicting_write_not_committed": shared["stale_conflicting_write_committed"] is False,
                "provenance_reconstructable": shared["provenance_reconstructable"] is True,
            },
            evidence_refs=["architecture_family_closeout:shared_distributed"],
        ),
        _scenario(
            "LSA-06",
            family="hybrid_maintenance",
            checks={
                "maintenance_harness_passed": maintenance["passed"] is True,
                "cursor_requires_commit_and_validation": maintenance["finding"]["cursor_advance_requires_commit_and_validation"] is True,
                "constituent_pama_remains_authoritative": maintenance["finding"]["constituent_pama_operations_remain_authoritative"] is True,
                "broad_background_authority_not_required": maintenance["finding"]["broad_background_maintenance_authority_required"] is False,
            },
            evidence_refs=["autonomous_maintenance_harness"],
        ),
        _scenario(
            "LSA-07",
            family="learned_latent",
            checks={
                "conditional_memory_harness_passed": conditional["passed"] is True,
                "deterministic_address_not_admission": conditional["finding"]["deterministic_addressing_is_not_admission"] is True,
                "source_deletion_not_internal_forgetting": conditional["finding"]["external_source_deletion_is_not_internal_forgetting"] is True,
                "new_canonical_primitive_not_required": conditional["finding"]["new_canonical_memory_primitive_required"] is False,
            },
            evidence_refs=["conditional_memory_harness"],
        ),
        _scenario(
            "LSA-08",
            family="module_replacement",
            checks={
                "logical_identity_preserved": replacement["logical_identity_preserved"] is True,
                "physical_identity_changed": replacement["physical_identity_changed"] is True,
                "content_identity_separate_from_physical_identity": replacement["content_identity_not_physical_identity"] is True,
                "migration_binds_logical_identity": replacement["migration_binds_logical_identity"] is True,
            },
            evidence_refs=["logical_state_algebra_pressure:backend_replacement_fixture"],
        ),
    ]

    observed_ids = {item["id"] for item in scenarios}
    if observed_ids != expected_ids:
        raise AssertionError(
            f"scenario contract drift: expected {sorted(expected_ids)}, observed {sorted(observed_ids)}"
        )

    all_expressible = all(item["existing_contracts_express_scenario"] for item in scenarios)
    any_missing = any(item["missing_generic_primitive_observed"] for item in scenarios)
    recommendation = "no_new_algebra" if all_expressible and not any_missing else "further_contract_research_required"

    return {
        "schema_version": "0.1.0",
        "program": "issue-276-logical-state-algebra-pressure",
        "agent_memory_commit": agent_memory_commit,
        "scenario_contract_version": scenario_contract["schema_version"],
        "scenario_count": len(scenarios),
        "scenarios": scenarios,
        "aggregate": {
            "all_existing_contracts_express_scenarios": all_expressible,
            "missing_generic_primitive_observed": any_missing,
            "stronger_engine_evidence_observed": False,
            "current_recommendation": recommendation,
        },
        "cross_program_evidence": {
            "architecture_family_program": architecture["program"],
            "autonomous_maintenance_passed": maintenance["passed"],
            "conditional_memory_passed": conditional["passed"],
        },
        "limitations": [
            "This is representation-neutral executable evidence, not a real #275 product-comparator run.",
            "Passing does not prove future module adapters will not expose a repeated missing transition contract.",
            "No physical database engine, cross-module distributed transaction, or external module runtime is implemented here.",
            "A stronger-engine decision still requires repeated implementation evidence across materially different modules.",
        ],
    }
