from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import jsonschema

from agentmem_ref.capabilities import (
    AmbiguousCapabilityError,
    CapabilityBehaviorContract,
    CapabilityBehaviorRequirement,
    CapabilityDeclaration,
    CapabilityRequirement,
    ComponentDeclaration,
    ComponentRegistry,
)
from agentmem_ref.runtime_behavior import (
    RuntimeBehaviorContractError,
    validate_runtime_behavior_contract,
)


ROOT = Path(__file__).resolve().parents[2]
COMPONENT_SCHEMA = ROOT / "schemas" / "component-capability-profile.schema.json"
RUNTIME_COMPOSED = ROOT / "reference" / "fixtures" / "runtime-configuration" / "reference-composed-runtime.json"
LEGACY_RUNTIME = ROOT / "reference" / "fixtures" / "runtime-configuration" / "attached-existing-stack.json"
LEGACY_COMPONENT = ROOT / "reference" / "fixtures" / "component-capabilities" / "procedural-reference.json"


def _behavior(*, currentness: str = "basis_versioned", correction: str = "invalidate_derived"):
    return CapabilityBehaviorContract(
        write=True,
        read=True,
        recall_candidate=False,
        currentness_model=currentness,
        invalidation_model="version_relation",
        correction_model=correction,
        deletion_model="derived_residue_then_purge",
        residue_model="derived_residual",
        migration_rebuild_model="rebuild_from_canonical",
        structural_mutation_requirement="none",
    )


def _component(component_id: str, behavior: CapabilityBehaviorContract | None):
    return ComponentDeclaration(
        component_id=component_id,
        component_version="1.0.0",
        profile_version="component-capability-v2" if behavior else "component-capability-v1",
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
                behavior_contract=behavior,
            ),
        ),
    )


class CapabilityBehaviorContractTests(unittest.TestCase):
    def test_legacy_v1_component_schema_remains_valid(self) -> None:
        schema = json.loads(COMPONENT_SCHEMA.read_text(encoding="utf-8"))
        legacy = json.loads(LEGACY_COMPONENT.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(legacy)
        declaration = ComponentDeclaration.from_dict(legacy)
        self.assertEqual(declaration.profile_version, "component-capability-v1")
        self.assertTrue(all(capability.behavior_contract is None for capability in declaration.capabilities))

    def test_v2_requires_behavior_contract_on_every_capability(self) -> None:
        config = json.loads(RUNTIME_COMPOSED.read_text(encoding="utf-8"))
        declaration = copy.deepcopy(config["components"][0]["declaration"])
        declaration["capabilities"][0].pop("behavior_contract")
        schema = json.loads(COMPONENT_SCHEMA.read_text(encoding="utf-8"))
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(schema).validate(declaration)
        with self.assertRaisesRegex(ValueError, "requires behavior_contract"):
            ComponentDeclaration.from_dict(declaration)

    def test_behavior_requirement_can_disambiguate_providers(self) -> None:
        registry = ComponentRegistry()
        registry.register_many(
            (
                _component("basis-provider", _behavior()),
                _component("external-provider", _behavior(currentness="external_asserted")),
            )
        )

        with self.assertRaises(AmbiguousCapabilityError):
            registry.resolve(
                CapabilityRequirement(
                    capability_id="rebuild_projection",
                    capability_version="1.0",
                    minimum_maturity="runtime_wired",
                )
            )

        resolved = registry.resolve(
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
        self.assertEqual(resolved.component_id, "basis-provider")
        self.assertIsNotNone(resolved.behavior_contract)
        self.assertEqual(resolved.behavior_contract.currentness_model, "basis_versioned")
        self.assertEqual(resolved.authority_effect, "none")

    def test_legacy_provider_is_ineligible_when_behavior_is_required(self) -> None:
        registry = ComponentRegistry()
        registry.register(_component("legacy-provider", None))
        with self.assertRaisesRegex(ValueError, "no eligible provider"):
            registry.resolve(
                CapabilityRequirement(
                    capability_id="rebuild_projection",
                    capability_version="1.0",
                    minimum_maturity="runtime_wired",
                    behavior_requirement=CapabilityBehaviorRequirement(
                        migration_rebuild_models=("rebuild_from_canonical",),
                    ),
                )
            )

    def test_v2_composed_runtime_satisfies_declared_behavior_routes(self) -> None:
        config = json.loads(RUNTIME_COMPOSED.read_text(encoding="utf-8"))
        plan = validate_runtime_behavior_contract(config)
        self.assertEqual(plan.required_projection_ids, ("reference-derived-index",))
        routes = {route.route_id: route for route in plan.resolved_routes}
        projection = routes["derived-projection-rebuild"].primary
        self.assertEqual(projection.profile_version, "component-capability-v2")
        self.assertEqual(projection.behavior_contract.currentness_model, "basis_versioned")
        self.assertEqual(projection.behavior_contract.correction_model, "invalidate_derived")
        self.assertEqual(projection.behavior_contract.deletion_model, "derived_residue_then_purge")
        self.assertEqual(projection.behavior_contract.residue_model, "derived_residual")
        self.assertEqual(projection.behavior_contract.migration_rebuild_model, "rebuild_from_canonical")
        self.assertEqual(projection.authority_effect, "none")

    def test_runtime_route_refuses_behavior_mismatch(self) -> None:
        config = json.loads(RUNTIME_COMPOSED.read_text(encoding="utf-8"))
        projection = next(
            component for component in config["components"]
            if component["declaration"]["component_id"] == "reference-projection-sidecar"
        )
        projection["declaration"]["capabilities"][0]["behavior_contract"]["correction_model"] = "not_applicable"
        with self.assertRaisesRegex(RuntimeBehaviorContractError, "behavior requirements are not satisfied"):
            validate_runtime_behavior_contract(config)

    def test_structural_mutation_requirement_is_metadata_not_authority(self) -> None:
        contract = _behavior()
        payload = contract.to_dict()
        payload["structural_mutation_requirement"] = "pama_required"
        parsed = CapabilityBehaviorContract.from_dict(payload)
        declaration = CapabilityDeclaration(
            capability_id="schema_mutation_candidate",
            capability_version="1.0",
            maturity="runtime_wired",
            state_posture="derived",
            scope_posture="inherits_agent_memory_scope",
            failure_posture="fail_closed",
            authority_effect="proposal_only",
            behavior_contract=parsed,
        )
        self.assertEqual(parsed.structural_mutation_requirement, "pama_required")
        self.assertEqual(declaration.authority_effect, "proposal_only")
        self.assertNotEqual(declaration.authority_effect, "pama_required")

    def test_legacy_runtime_without_behavior_requirements_remains_valid(self) -> None:
        config = json.loads(LEGACY_RUNTIME.read_text(encoding="utf-8"))
        # The legacy attach fixture requires external qualification evidence and
        # is covered by its existing tests. Remove the evidence-level route here
        # so this test isolates behavior-contract backward compatibility.
        config["routes"] = [
            route for route in config["routes"]
            if route["route_id"] == "canonical-record-store"
        ]
        config["components"] = [
            component for component in config["components"]
            if component["declaration"]["component_id"] == "existing-canonical-store"
        ]
        plan = validate_runtime_behavior_contract(config)
        self.assertEqual(plan.canonical_owner_component_id, "existing-canonical-store")
        self.assertEqual(plan.resolved_routes[0].primary.profile_version, "component-capability-v1")
        self.assertIsNone(plan.resolved_routes[0].primary.behavior_contract)


if __name__ == "__main__":
    unittest.main()
