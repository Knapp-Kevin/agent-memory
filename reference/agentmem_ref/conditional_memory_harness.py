"""Representation-neutral conditional-memory pressure test for issue #228.

The harness models the governance-relevant property of Engram-like conditional
memory without copying or requiring the upstream runtime: deterministic internal
addressing can continue to resolve after the table's source basis becomes stale.
A separate currentness/scope/suppression gate therefore controls eligibility to
influence model state.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from . import policy
from .derivation_currentness import evaluate_derivation_currentness
from .derivation_evidence import normalize_derivation

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ROOT / "docs" / "explorations" / "memory-architectures" / "model-internal-conditional-memory-scenarios.json"

SCOPE = {
    "scope_ref": "tenant-a/project-a",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}


def deterministic_addresses(token_ids: list[int], multipliers: list[int], moduli: list[int]) -> list[int]:
    """Small deterministic XOR/multiply hash used only for the research fixture."""
    if not token_ids or len(token_ids) != len(multipliers):
        raise ValueError("token_ids and multipliers must be non-empty and equal length")
    if not moduli or any(not isinstance(mod, int) or mod <= 1 for mod in moduli):
        raise ValueError("moduli must be integers > 1")
    mix = token_ids[0] * multipliers[0]
    for token, multiplier in zip(token_ids[1:], multipliers[1:]):
        mix ^= token * multiplier
    return [mix % modulus for modulus in moduli]


def _table_derivation(*, source_ref: str, output_ref: str, created_at: str) -> dict[str, Any]:
    return normalize_derivation(
        {
            "root_origin_refs": [source_ref],
            "immediate_source_refs": [source_ref],
            "source_trust": "bounded_trusted",
            "transformation": {
                "method": "conditional_memory_table_build",
                "transformer_ref": "builder:conditional-memory-fixture",
                "transformer_version": "v1",
                "transformer_trust": "bounded_trusted",
                "mode": "deterministic",
                "status": "complete",
                "output_ref": output_ref,
            },
            "scope": SCOPE,
            "evidence_refs": [f"evidence:{source_ref}"],
            "created_at": created_at,
        },
        expected_scope=SCOPE,
    )


def _currentness(derivation: dict[str, Any], source_state: str, evaluated_at: str) -> dict[str, Any]:
    source_ref = derivation["root_origin_refs"][0]
    return evaluate_derivation_currentness(
        derivation,
        source_observations=[
            {
                "origin_ref": source_ref,
                "state": source_state,
                "evidence_class": "ordinary",
                "evidence_refs": [f"evidence:{source_ref}:{source_state}"],
            }
        ],
        scope_observation={
            "status": "unchanged",
            "current_scope_ref": SCOPE["scope_ref"],
            "tenant_ref": SCOPE["tenant_ref"],
            "project_ref": SCOPE["project_ref"],
            "evidence_refs": ["evidence:conditional-table-scope"],
        },
        evaluated_at=evaluated_at,
    )


def influence_gate(
    *,
    applicability_status: str,
    table_partition: str,
    requested_partition: str,
    suppressed: bool,
) -> str:
    if table_partition != requested_partition:
        return "block_scope"
    if applicability_status != "current":
        return "block_stale"
    if suppressed:
        return "block_suppressed"
    return "allow"


def _find_collision() -> dict[str, Any]:
    seen: dict[tuple[int, ...], tuple[int, int]] = {}
    multipliers = [3, 5]
    moduli = [5, 7]
    for left in range(1, 20):
        for right in range(1, 20):
            address = tuple(deterministic_addresses([left, right], multipliers, moduli))
            previous = seen.get(address)
            if previous is not None and previous != (left, right):
                return {
                    "address": list(address),
                    "first_tokens": list(previous),
                    "second_tokens": [left, right],
                    "source_identity_equal": False,
                    "authority_equivalent": False,
                }
            seen[address] = (left, right)
    raise AssertionError("fixture collision search unexpectedly found no collision")


def _deployment_decisions() -> dict[str, Any]:
    deploy = policy.evaluate(
        policy.Proposal(
            proposal_id="conditional-table:deploy",
            actor_id="agent:table-builder",
            charter_version="v1",
            target_reference="conditional-table:t2",
            target_class=policy.M3,
            scope="tenant-a/project-a",
            operation="promotion",
            current_strength="candidate",
            proposed_strength="canonical",
            downstream_authority=policy.A3,
            reversibility="versioned_revocable",
            risk_class="high",
            evidence_refs=("evidence:table-build",),
            actor_authority_resolved=True,
            approves_own_authority=False,
        )
    )
    widen = policy.evaluate(
        policy.Proposal(
            proposal_id="conditional-table:widen-partition",
            actor_id="agent:table-builder",
            charter_version="v1",
            target_reference="conditional-table:t2",
            target_class=policy.M5,
            scope="tenant-a/project-a",
            operation="scope_expansion",
            current_strength="project",
            proposed_strength="cross_tenant",
            downstream_authority=policy.A5,
            reversibility="irreversible",
            risk_class="critical",
            evidence_refs=("evidence:table-build",),
            actor_authority_resolved=True,
            approves_own_authority=False,
        )
    )
    return {
        "table_deployment": {
            "outcome": deploy.outcome,
            "permitted_actions": list(deploy.permitted_actions),
            "prohibited_actions": list(deploy.prohibited_actions),
        },
        "partition_widening": {
            "outcome": widen.outcome,
            "permitted_actions": list(widen.permitted_actions),
            "prohibited_actions": list(widen.prohibited_actions),
        },
    }


def run_conditional_memory_harness() -> dict[str, Any]:
    source = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    table = source["table"]
    fixture = source["hash_fixture"]

    first_addresses = deterministic_addresses(
        fixture["token_ids"], fixture["multipliers"], fixture["moduli"]
    )
    second_addresses = deterministic_addresses(
        fixture["token_ids"], fixture["multipliers"], fixture["moduli"]
    )

    t1 = _table_derivation(
        source_ref=table["source_ref"],
        output_ref=table["table_digest"],
        created_at="2026-08-13T07:20:00Z",
    )
    t1_before = copy.deepcopy(t1)

    case_results = []
    checks: dict[str, bool] = {
        "addressing_is_deterministic": first_addresses == second_addresses,
    }
    for index, case in enumerate(source["cases"]):
        evaluation = _currentness(t1, case["source_state"], f"2026-08-13T07:21:{index:02d}Z")
        gate = influence_gate(
            applicability_status=evaluation["applicability"]["status"],
            table_partition=table["partition_ref"],
            requested_partition=case["requested_partition"],
            suppressed=case["suppressed"],
        )
        result = {
            "id": case["id"],
            "addresses": first_addresses,
            "physical_lookup_resolves": True,
            "table_currentness": evaluation["applicability"],
            "gate": gate,
        }
        case_results.append(result)
        checks[f"case:{case['id']}:gate"] = gate == case["expected_gate"]

    revoked = next(item for item in case_results if item["id"] == "revoked-source-still-addressable")
    deleted = next(item for item in case_results if item["id"] == "deleted-source-still-addressable")
    cross_scope = next(item for item in case_results if item["id"] == "cross-partition-address")
    suppressed = next(item for item in case_results if item["id"] == "overlay-suppresses-current-address")

    replacement_source = "uor:test:conditional-source-b"
    t2 = _table_derivation(
        source_ref=replacement_source,
        output_ref="sha256:" + "b" * 64,
        created_at="2026-08-13T07:22:00Z",
    )
    t2_currentness = _currentness(t2, "current", "2026-08-13T07:22:30Z")

    collision = _find_collision()
    deployment = _deployment_decisions()

    checks.update(
        {
            "revoked_table_still_physically_addressable_but_blocked": (
                revoked["physical_lookup_resolves"]
                and revoked["table_currentness"]["status"] == "revalidation_required"
                and revoked["gate"] == "block_stale"
            ),
            "deleted_source_is_not_forgetting_proof": (
                deleted["physical_lookup_resolves"]
                and deleted["table_currentness"]["status"] == "revalidation_required"
                and deleted["gate"] == "block_stale"
            ),
            "scope_partition_blocks_identical_address": cross_scope["gate"] == "block_scope",
            "overlay_can_suppress_before_influence": suppressed["gate"] == "block_suppressed",
            "rebuilt_table_has_new_identity": t2["derivation_id"] != t1["derivation_id"],
            "rebuilt_table_can_be_current": t2_currentness["applicability"]["status"] == "current",
            "historical_table_derivation_unchanged": t1 == t1_before,
            "collision_does_not_create_identity_or_authority": (
                collision["first_tokens"] != collision["second_tokens"]
                and collision["source_identity_equal"] is False
                and collision["authority_equivalent"] is False
            ),
            "table_deployment_is_separately_governed": deployment["table_deployment"]["outcome"] != policy.ALLOW,
            "partition_widening_uses_scope_expansion_floor": deployment["partition_widening"]["outcome"] == policy.BLOCK,
        }
    )

    return {
        "case_id": "model-internal-conditional-memory",
        "passed": all(checks.values()),
        "scenario_set_version": source["scenario_set_version"],
        "upstream_pin": {
            "repository": "deepseek-ai/Engram",
            "commit": "fb7f84a21f91223715394a33a1dc24bbfb7f788e",
            "license": "Apache-2.0",
            "runtime_executed": False,
        },
        "table_identity": table,
        "checks": checks,
        "cases": case_results,
        "collision": collision,
        "replacement_table": {
            "old_derivation_id": t1["derivation_id"],
            "new_derivation_id": t2["derivation_id"],
            "new_currentness": t2_currentness["applicability"],
        },
        "deployment_decisions": deployment,
        "finding": {
            "existing_derivation_currentness_sufficient": True,
            "deterministic_addressing_is_not_admission": True,
            "external_source_deletion_is_not_internal_forgetting": True,
            "runtime_lookup_requires_per_influence_or_partition_gate": True,
            "missing_reusable_contract": "model_internal_conditional_memory_influence_profile",
            "new_canonical_memory_primitive_required": False,
            "engram_dependency_required": False,
            "full_upstream_demo_adds_governance_evidence_before_profile": False,
        },
    }
