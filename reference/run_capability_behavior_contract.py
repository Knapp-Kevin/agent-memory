#!/usr/bin/env python3
"""Emit exact-head evidence for the #280 capability behavior declaration contract."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.capabilities import (  # noqa: E402
    CapabilityBehaviorContract,
    CapabilityBehaviorRequirement,
    CapabilityDeclaration,
    CapabilityRequirement,
    ComponentDeclaration,
    ComponentRegistry,
)
from agentmem_ref.runtime_behavior import (  # noqa: E402
    RuntimeBehaviorContractError,
    validate_runtime_behavior_contract,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "reference" / "fixtures"
COMPOSED = FIXTURES / "runtime-configuration" / "reference-composed-runtime.json"
LEGACY = FIXTURES / "component-capabilities" / "procedural-reference.json"


def _provider(component_id: str, *, currentness: str) -> ComponentDeclaration:
    return ComponentDeclaration(
        component_id=component_id,
        component_version="1.0.0",
        profile_version="component-capability-v2",
        failure_posture="explicit_unavailable",
        capabilities=(
            CapabilityDeclaration(
                capability_id="rebuild_projection",
                capability_version="1.0",
                maturity="runtime_wired",
                state_posture="derived",
                scope_posture="inherits_agent_memory_scope",
                failure_posture="explicit_unavailable",
                authority_effect="none",
                behavior_contract=CapabilityBehaviorContract(
                    write=True,
                    read=True,
                    recall_candidate=False,
                    currentness_model=currentness,
                    invalidation_model="version_relation",
                    correction_model="invalidate_derived",
                    deletion_model="derived_residue_then_purge",
                    residue_model="derived_residual",
                    migration_rebuild_model="rebuild_from_canonical",
                    structural_mutation_requirement="none",
                ),
            ),
        ),
    )


def build_report(agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent-memory commit must be an exact 40-character SHA")

    composed = json.loads(COMPOSED.read_text(encoding="utf-8"))
    plan = validate_runtime_behavior_contract(composed)
    routes = {route.route_id: route for route in plan.resolved_routes}
    projection = routes["derived-projection-rebuild"].primary
    semantic = routes["canonical-semantic-fact"].primary
    retrieval = routes["governed-exact-retrieval"].primary

    mismatch = copy.deepcopy(composed)
    sidecar = next(
        component for component in mismatch["components"]
        if component["declaration"]["component_id"] == "reference-projection-sidecar"
    )
    sidecar["declaration"]["capabilities"][0]["behavior_contract"]["migration_rebuild_model"] = "unsupported"
    mismatch_refused = False
    try:
        validate_runtime_behavior_contract(mismatch)
    except RuntimeBehaviorContractError:
        mismatch_refused = True

    legacy = ComponentDeclaration.from_dict(json.loads(LEGACY.read_text(encoding="utf-8")))

    registry = ComponentRegistry()
    registry.register_many(
        (
            _provider("basis-provider", currentness="basis_versioned"),
            _provider("external-provider", currentness="external_asserted"),
        )
    )
    behavior_selected = registry.resolve(
        CapabilityRequirement(
            capability_id="rebuild_projection",
            capability_version="1.0",
            minimum_maturity="runtime_wired",
            behavior_requirement=CapabilityBehaviorRequirement(
                currentness_models=("basis_versioned",),
                migration_rebuild_models=("rebuild_from_canonical",),
            ),
        )
    )

    structural_contract = CapabilityBehaviorContract(
        write=False,
        read=True,
        recall_candidate=True,
        currentness_model="provider_revalidated",
        invalidation_model="provider_revalidation",
        correction_model="candidate_only",
        deletion_model="candidate_drop",
        residue_model="provider_managed",
        migration_rebuild_model="requires_requalification",
        structural_mutation_requirement="pama_required",
    )
    structural_declaration = CapabilityDeclaration(
        capability_id="schema_mutation_candidate",
        capability_version="1.0",
        maturity="runtime_wired",
        state_posture="derived",
        scope_posture="inherits_agent_memory_scope",
        failure_posture="fail_closed",
        authority_effect="proposal_only",
        behavior_contract=structural_contract,
    )

    invariants = {
        "legacy_v1_remains_readable": (
            legacy.profile_version == "component-capability-v1"
            and all(capability.behavior_contract is None for capability in legacy.capabilities)
        ),
        "v2_semantic_memory_behavior_explicit": (
            semantic.behavior_contract is not None
            and semantic.behavior_contract.write
            and semantic.behavior_contract.currentness_model == "canonical_version"
            and semantic.behavior_contract.correction_model == "canonical_supersession"
            and semantic.behavior_contract.deletion_model == "canonical_delete"
        ),
        "v2_retrieval_behavior_explicit": (
            retrieval.behavior_contract is not None
            and retrieval.behavior_contract.read
            and retrieval.behavior_contract.recall_candidate
            and not retrieval.behavior_contract.write
        ),
        "v2_projection_lifecycle_explicit": (
            projection.behavior_contract is not None
            and projection.behavior_contract.currentness_model == "basis_versioned"
            and projection.behavior_contract.invalidation_model == "version_relation"
            and projection.behavior_contract.correction_model == "invalidate_derived"
            and projection.behavior_contract.deletion_model == "derived_residue_then_purge"
            and projection.behavior_contract.residue_model == "derived_residual"
            and projection.behavior_contract.migration_rebuild_model == "rebuild_from_canonical"
        ),
        "runtime_route_behavior_mismatch_refused": mismatch_refused,
        "behavior_requirement_can_disambiguate_provider": (
            behavior_selected.component_id == "basis-provider"
            and behavior_selected.behavior_contract is not None
            and behavior_selected.behavior_contract.currentness_model == "basis_versioned"
        ),
        "behavior_metadata_does_not_grant_authority": (
            behavior_selected.authority_effect == "none"
            and structural_contract.structural_mutation_requirement == "pama_required"
            and structural_declaration.authority_effect == "proposal_only"
        ),
        "composed_runtime_requires_behavior_v2": all(
            route.primary.profile_version == "component-capability-v2"
            for route in plan.resolved_routes
        ),
    }
    invariants = {name: bool(value) for name, value in invariants.items()}
    if not all(type(value) is bool for value in invariants.values()):
        raise TypeError("every structural invariant must be a JSON boolean")

    return {
        "schema_version": "1.0.0",
        "agent_memory_commit": agent_memory_commit,
        "component_profile_contract": "component-capability-v2",
        "legacy_profile_contract": "component-capability-v1",
        "runtime_configuration_digest": plan.configuration_digest,
        "resolved_behavior": {
            route_id: route.primary.behavior_contract.to_dict()
            for route_id, route in routes.items()
        },
        "structural_invariants": invariants,
        "structural_invariants_passed": all(invariants.values()),
        "authority_effect": "none",
        "limitations": [
            "Behavior metadata is descriptive and does not replace PAMA, recall admission, policy, or external authorization.",
            "Legacy v1 declarations remain valid but cannot satisfy a route that explicitly requires v2 behavior semantics.",
            "The behavior vocabulary is intentionally bounded to #280 lifecycle dimensions and does not introduce a new logical memory state algebra.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report(args.agent_memory_commit)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    if not report["structural_invariants_passed"]:
        failed = [name for name, passed in report["structural_invariants"].items() if not passed]
        print(f"capability behavior invariants failed: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
