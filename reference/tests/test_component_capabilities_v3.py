"""Capability Contract v3 tests for issue #343."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.capabilities import (  # noqa: E402
    AmbiguousCapabilityError,
    CapabilityBehaviorContract,
    CapabilityDeclaration,
    CapabilityOperationalContract,
    CapabilityOperationalRequirement,
    CapabilityRequirement,
    CapabilityResolutionError,
    ComponentDeclaration,
    ComponentRegistry,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas" / "component-capability-profile.schema.json"
FIXTURE = ROOT / "reference" / "fixtures" / "component-capabilities" / "frontier-v3-reference.json"


def behavior() -> CapabilityBehaviorContract:
    return CapabilityBehaviorContract(
        write=True,
        read=True,
        recall_candidate=True,
        currentness_model="basis_versioned",
        invalidation_model="version_relation",
        correction_model="invalidate_derived",
        deletion_model="derived_residue_then_purge",
        residue_model="scan_required",
        migration_rebuild_model="rebuild_from_canonical",
        structural_mutation_requirement="pama_required",
    )


def operational(*, durable: bool = True) -> CapabilityOperationalContract:
    if durable:
        return CapabilityOperationalContract(
            write_atomicity="single_record_atomic",
            concurrency_control="optimistic_revision",
            idempotency="durable_keyed",
            restart_recovery="reconstructable",
            reconciliation="deterministic_readback",
        )
    return CapabilityOperationalContract(
        write_atomicity="process_local",
        concurrency_control="process_local",
        idempotency="process_local",
        restart_recovery="process_local_only",
        reconciliation="process_local_only",
    )


def component(
    component_id: str,
    capability_id: str = "epistemic_belief_memory",
    *,
    maturity: str = "runtime_wired",
    durable: bool = True,
    authority_effect: str = "none",
    profile_version: str = "component-capability-v3",
) -> ComponentDeclaration:
    capability = CapabilityDeclaration(
        capability_id=capability_id,
        capability_version="1.0",
        maturity=maturity,
        state_posture="derived",
        scope_posture="enforces_agent_memory_scope",
        failure_posture="fail_closed",
        authority_effect=authority_effect,
        behavior_contract=behavior(),
        operational_contract=operational(durable=durable),
    )
    return ComponentDeclaration(
        component_id=component_id,
        component_version="1.0.0",
        profile_version=profile_version,
        failure_posture="fail_closed",
        capabilities=(capability,),
    )


class ComponentCapabilityV3Tests(unittest.TestCase):
    def test_v3_fixture_validates_and_frontier_capabilities_are_independent(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        value = json.loads(FIXTURE.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(value)
        parsed = ComponentDeclaration.from_dict(value)
        self.assertEqual(
            [item.capability_id for item in parsed.capabilities],
            ["epistemic_belief_memory", "predictive_counterfactual_memory"],
        )
        self.assertNotEqual(parsed.capabilities[0].maturity, parsed.capabilities[1].maturity)

    def test_schema_rejects_v3_without_behavior_or_operational_contract(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        source = json.loads(FIXTURE.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for required_contract in ("behavior_contract", "operational_contract"):
            value = json.loads(json.dumps(source))
            value["capabilities"][0].pop(required_contract)
            errors = list(validator.iter_errors(value))
            self.assertTrue(
                errors,
                f"component-capability-v3 unexpectedly accepted missing {required_contract}",
            )

    def test_v1_and_v2_remain_backwards_compatible(self):
        v1 = ComponentDeclaration(
            component_id="legacy-v1",
            component_version="9.0.0",
            profile_version="component-capability-v1",
            failure_posture="fail_closed",
            capabilities=(
                CapabilityDeclaration(
                    "procedural_skill_memory",
                    "1.0",
                    "declared",
                    "canonical",
                    "enforces_agent_memory_scope",
                    "fail_closed",
                ),
            ),
        )
        v2 = ComponentDeclaration(
            component_id="legacy-v2",
            component_version="1.0.0",
            profile_version="component-capability-v2",
            failure_posture="fail_closed",
            capabilities=(
                CapabilityDeclaration(
                    "procedural_skill_memory",
                    "1.0",
                    "implemented",
                    "canonical",
                    "enforces_agent_memory_scope",
                    "fail_closed",
                    behavior_contract=behavior(),
                ),
            ),
        )
        self.assertIsNone(v1.capabilities[0].behavior_contract)
        self.assertIsNone(v2.capabilities[0].operational_contract)

    def test_v3_requires_behavior_and_operational_contracts(self):
        with self.assertRaisesRegex(ValueError, "behavior_contract"):
            ComponentDeclaration(
                component_id="bad-v3-behavior",
                component_version="1.0.0",
                profile_version="component-capability-v3",
                failure_posture="fail_closed",
                capabilities=(
                    CapabilityDeclaration(
                        "epistemic_belief_memory",
                        "1.0",
                        "declared",
                        "derived",
                        "enforces_agent_memory_scope",
                        "fail_closed",
                        operational_contract=operational(),
                    ),
                ),
            )
        with self.assertRaisesRegex(ValueError, "operational_contract"):
            ComponentDeclaration(
                component_id="bad-v3-operational",
                component_version="1.0.0",
                profile_version="component-capability-v3",
                failure_posture="fail_closed",
                capabilities=(
                    CapabilityDeclaration(
                        "epistemic_belief_memory",
                        "1.0",
                        "declared",
                        "derived",
                        "enforces_agent_memory_scope",
                        "fail_closed",
                        behavior_contract=behavior(),
                    ),
                ),
            )

    def test_operational_requirement_filters_otherwise_valid_provider(self):
        requirement = CapabilityRequirement(
            "epistemic_belief_memory",
            "runtime_wired",
            operational_requirement=CapabilityOperationalRequirement(
                idempotency=("durable_keyed",),
                restart_recovery=("reconstructable", "checkpoint_replay"),
                reconciliation=("deterministic_readback", "authoritative_rebuild"),
            ),
        )
        registry = ComponentRegistry()
        registry.register(component("durable"))
        registry.register(component("process-local", durable=False))
        resolved = registry.resolve(requirement)
        self.assertEqual(resolved.component_id, "durable")

    def test_preferred_operationally_ineligible_provider_does_not_fallback(self):
        registry = ComponentRegistry(preferences={"epistemic_belief_memory": "preferred"})
        registry.register(component("preferred", durable=False))
        registry.register(component("eligible"))
        requirement = CapabilityRequirement(
            "epistemic_belief_memory",
            "runtime_wired",
            operational_requirement=CapabilityOperationalRequirement(
                restart_recovery=("reconstructable", "checkpoint_replay"),
            ),
        )
        with self.assertRaises(CapabilityResolutionError) as context:
            registry.resolve(requirement)
        self.assertIn("preferred provider", str(context.exception))

    def test_equally_qualified_providers_remain_explicitly_ambiguous(self):
        registry = ComponentRegistry()
        registry.register_many((component("a"), component("b")))
        requirement = CapabilityRequirement(
            "epistemic_belief_memory",
            "runtime_wired",
            operational_requirement=CapabilityOperationalRequirement(
                idempotency=("durable_keyed",),
            ),
        )
        with self.assertRaises(AmbiguousCapabilityError):
            registry.resolve(requirement)

    def test_process_local_provider_cannot_satisfy_restart_or_reconciliation_requirement(self):
        registry = ComponentRegistry()
        registry.register(component("process-local", durable=False))
        for operational_requirement in (
            CapabilityOperationalRequirement(restart_recovery=("reconstructable",)),
            CapabilityOperationalRequirement(reconciliation=("deterministic_readback",)),
        ):
            with self.assertRaises(CapabilityResolutionError):
                registry.resolve(
                    CapabilityRequirement(
                        "epistemic_belief_memory",
                        "runtime_wired",
                        operational_requirement=operational_requirement,
                    )
                )

    def test_provider_substitution_preserves_requested_semantics_and_authority(self):
        requirement = CapabilityRequirement(
            "epistemic_belief_memory",
            "runtime_wired",
            operational_requirement=CapabilityOperationalRequirement(
                idempotency=("durable_keyed",),
                restart_recovery=("reconstructable",),
            ),
        )
        first = ComponentRegistry()
        first.register(component("provider-a"))
        second = ComponentRegistry()
        second.register(component("provider-b"))

        resolved_a = first.resolve(requirement)
        resolved_b = second.resolve(requirement)
        self.assertEqual(resolved_a.capability_id, resolved_b.capability_id)
        self.assertEqual(resolved_a.capability_version, resolved_b.capability_version)
        self.assertEqual(resolved_a.state_posture, resolved_b.state_posture)
        self.assertEqual(resolved_a.scope_posture, resolved_b.scope_posture)
        self.assertEqual(resolved_a.behavior_contract, resolved_b.behavior_contract)
        self.assertTrue(requirement.operational_requirement.matches(resolved_a.operational_contract))
        self.assertTrue(requirement.operational_requirement.matches(resolved_b.operational_contract))
        self.assertEqual(resolved_a.authority_effect, "none")
        self.assertEqual(resolved_b.authority_effect, "none")
        self.assertNotEqual(resolved_a.component_id, resolved_b.component_id)

    def test_operational_quality_does_not_change_declared_authority_effect(self):
        registry = ComponentRegistry()
        registry.register(component("high-quality", authority_effect="proposal_only"))
        resolved = registry.resolve(
            CapabilityRequirement(
                "epistemic_belief_memory",
                "runtime_wired",
                operational_requirement=CapabilityOperationalRequirement(
                    write_atomicity=("single_record_atomic",),
                    concurrency_control=("optimistic_revision",),
                    idempotency=("durable_keyed",),
                    restart_recovery=("reconstructable",),
                    reconciliation=("deterministic_readback",),
                ),
            )
        )
        self.assertEqual(resolved.authority_effect, "proposal_only")

    def test_component_version_does_not_upgrade_capability_maturity(self):
        registry = ComponentRegistry()
        registry.register(component("new-component", maturity="declared"))
        with self.assertRaises(CapabilityResolutionError):
            registry.resolve(CapabilityRequirement("epistemic_belief_memory", "runtime_wired"))


if __name__ == "__main__":
    unittest.main()
