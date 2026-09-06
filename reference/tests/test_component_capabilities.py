"""Capability declaration and deterministic routing tests for #287/#290."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.capabilities import (  # noqa: E402
    AmbiguousCapabilityError,
    CapabilityDeclaration,
    CapabilityRequirement,
    CapabilityResolutionError,
    ComponentDeclaration,
    ComponentRegistry,
    maturity_satisfies,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "reference" / "fixtures" / "component-capabilities"


class ComponentCapabilityTests(unittest.TestCase):
    def _component(self, component_id: str, maturity: str, *, version: str = "1.0.0") -> ComponentDeclaration:
        return ComponentDeclaration(
            component_id=component_id,
            component_version=version,
            profile_version="component-capability-v1",
            failure_posture="fail_closed",
            capabilities=(
                CapabilityDeclaration(
                    capability_id="procedural_skill_memory",
                    capability_version="1.0",
                    maturity=maturity,
                    state_posture="canonical",
                    scope_posture="enforces_agent_memory_scope",
                    failure_posture="fail_closed",
                    authority_effect="none",
                ),
            ),
        )

    def test_machine_readable_schema_accepts_reference_fixtures(self):
        schema = json.loads((ROOT / "schemas" / "component-capability-profile.schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        files = sorted(FIXTURES.glob("*.json"))
        self.assertGreaterEqual(len(files), 3)
        for path in files:
            value = json.loads(path.read_text(encoding="utf-8"))
            errors = list(validator.iter_errors(value))
            self.assertEqual(errors, [], f"{path.name}: {[error.message for error in errors]}")
            component = ComponentDeclaration.from_dict(value)
            self.assertGreaterEqual(len(component.capabilities), 1)

    def test_maturity_order_is_explicit_and_enforced(self):
        self.assertTrue(maturity_satisfies("runtime_wired", "implemented"))
        self.assertFalse(maturity_satisfies("implemented", "runtime_wired"))
        registry = ComponentRegistry()
        registry.register(self._component("declared-only", "declared"))
        with self.assertRaises(CapabilityResolutionError):
            registry.resolve(CapabilityRequirement("procedural_skill_memory", "runtime_wired"))

    def test_ambiguous_overlap_fails_instead_of_using_registration_order(self):
        registry = ComponentRegistry()
        registry.register(self._component("provider-b", "runtime_wired"))
        registry.register(self._component("provider-a", "runtime_wired"))
        with self.assertRaises(AmbiguousCapabilityError) as context:
            registry.resolve(CapabilityRequirement("procedural_skill_memory", "runtime_wired"))
        self.assertIn("provider-a", str(context.exception))
        self.assertIn("provider-b", str(context.exception))

    def test_explicit_preference_resolves_overlap_without_downgrade(self):
        registry = ComponentRegistry(preferences={"procedural_skill_memory": "provider-b"})
        registry.register(self._component("provider-a", "runtime_wired"))
        registry.register(self._component("provider-b", "evidence_proven"))
        resolved = registry.resolve(CapabilityRequirement("procedural_skill_memory", "runtime_wired"))
        self.assertEqual(resolved.component_id, "provider-b")
        self.assertEqual(resolved.maturity, "evidence_proven")
        self.assertEqual(resolved.authority_effect, "none")

    def test_ineligible_preferred_provider_does_not_fallback_to_weaker_semantics(self):
        registry = ComponentRegistry(preferences={"procedural_skill_memory": "preferred"})
        registry.register(self._component("preferred", "implemented"))
        registry.register(self._component("eligible-but-not-preferred", "runtime_wired"))
        with self.assertRaises(CapabilityResolutionError) as context:
            registry.resolve(CapabilityRequirement("procedural_skill_memory", "runtime_wired"))
        self.assertIn("preferred provider", str(context.exception))

    def test_component_version_change_cannot_imply_capability_maturity_upgrade(self):
        registry = ComponentRegistry()
        registry.register(self._component("same-component", "declared", version="9.0.0"))
        with self.assertRaises(CapabilityResolutionError):
            registry.resolve(CapabilityRequirement("procedural_skill_memory", "runtime_wired"))

    def test_multi_capability_component_and_cross_component_composition(self):
        graph_and_lifecycle = ComponentDeclaration(
            component_id="multi",
            component_version="1.0.0",
            profile_version="component-capability-v1",
            failure_posture="fail_closed",
            capabilities=(
                CapabilityDeclaration(
                    "temporal_graph",
                    "1.0",
                    "runtime_wired",
                    "derived",
                    "enforces_agent_memory_scope",
                    "explicit_unavailable",
                ),
                CapabilityDeclaration(
                    "lifecycle_decay",
                    "1.0",
                    "runtime_wired",
                    "derived",
                    "enforces_agent_memory_scope",
                    "fail_closed",
                ),
            ),
        )
        vector = ComponentDeclaration(
            component_id="vector",
            component_version="1.0.0",
            profile_version="component-capability-v1",
            failure_posture="fail_closed",
            capabilities=(
                CapabilityDeclaration(
                    "vector_candidate_retrieval",
                    "1.0",
                    "runtime_wired",
                    "derived",
                    "enforces_agent_memory_scope",
                    "explicit_unavailable",
                ),
            ),
        )
        registry = ComponentRegistry()
        registry.register_many((graph_and_lifecycle, vector))
        resolved = registry.resolve_many(
            (
                CapabilityRequirement("temporal_graph", "runtime_wired"),
                CapabilityRequirement("lifecycle_decay", "runtime_wired"),
                CapabilityRequirement("vector_candidate_retrieval", "runtime_wired"),
            )
        )
        self.assertEqual([item.component_id for item in resolved], ["multi", "multi", "vector"])
        self.assertTrue(all(item.authority_effect == "none" for item in resolved))


if __name__ == "__main__":
    unittest.main()
