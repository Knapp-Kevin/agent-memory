from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from agentmem_ref.runtime_config import (
    QualificationBinding,
    RuntimeConfigurationError,
    configuration_digest,
    validate_runtime_configuration,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "reference" / "fixtures" / "runtime-configuration" / "attached-existing-stack.json"


def _config() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _bindings() -> tuple[QualificationBinding, ...]:
    return (
        QualificationBinding(
            component_id="codegenome",
            component_version="43a6b7147ec78ec5c616723fa1dd30f342174860",
            capability_id="code_graph_traversal",
            capability_version="1.0",
            adapter_id="codegenome-cli",
            adapter_version="1.0.0",
            qualification_profile_id="code-graph-traversal-currentness",
            qualification_profile_version="1.1.0",
            applicability_digest="sha256:915a093171623702ea39df6e37a5588b7fdf2fb7bd88f81f7d3d41445a41af2e",
            qualification_current=True,
            earned_maturity="evidence_proven",
            source_rights_use_posture="runtime_allowed",
            record_ref="artifact:#300:codegenome",
        ),
        QualificationBinding(
            component_id="graphify",
            component_version="v0.9.43",
            capability_id="code_graph_traversal",
            capability_version="1.0",
            adapter_id="graphify-cli",
            adapter_version="1.0.0",
            qualification_profile_id="code-graph-traversal-currentness",
            qualification_profile_version="1.1.0",
            applicability_digest="sha256:5d7a051b579cc3bb914d664c2aff859426b48020d27c171fee6fe4930da14906",
            qualification_current=True,
            earned_maturity="evidence_proven",
            source_rights_use_posture="runtime_allowed",
            record_ref="artifact:#300:graphify",
        ),
    )


def _component(config: dict, component_id: str) -> dict:
    return next(
        item for item in config["components"]
        if item["declaration"]["component_id"] == component_id
    )


def _route(config: dict, route_id: str) -> dict:
    return next(item for item in config["routes"] if item["route_id"] == route_id)


class RuntimeConfigurationTests(unittest.TestCase):
    def test_attach_existing_stack_resolves_deterministically(self) -> None:
        config = _config()
        plan = validate_runtime_configuration(config, qualification_bindings=_bindings())
        self.assertEqual(plan.entry_mode, "attach_existing_stack")
        self.assertEqual(plan.canonical_owner_component_id, "existing-canonical-store")
        self.assertEqual(plan.required_projection_ids, ("code-graph",))
        self.assertEqual(plan.governance_peer_ids, ("dashclaw",))
        self.assertEqual(plan.authority_effect, "none")
        self.assertEqual(plan.configuration_digest, configuration_digest(config))

        routes = {route.route_id: route for route in plan.resolved_routes}
        self.assertEqual(routes["canonical-record-store"].primary.component_id, "existing-canonical-store")
        self.assertEqual(routes["derived-code-graph"].primary.component_id, "codegenome")
        self.assertEqual(routes["derived-code-graph"].fallback_component_id, "graphify")
        self.assertEqual(routes["derived-code-graph"].qualification_record_ref, "artifact:#300:codegenome")
        self.assertEqual(
            routes["derived-code-graph"].fallback_qualification_record_ref,
            "artifact:#300:graphify",
        )

    def test_configuration_digest_is_order_stable_for_object_keys(self) -> None:
        config = _config()
        reordered = {key: config[key] for key in reversed(list(config))}
        self.assertEqual(configuration_digest(config), configuration_digest(reordered))

    def test_missing_canonical_owner_fails_closed(self) -> None:
        config = _config()
        config["canonical_state"]["owner_component_id"] = "missing-store"
        with self.assertRaisesRegex(RuntimeConfigurationError, "canonical-state owner is missing"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_noncanonical_owner_capability_fails_closed(self) -> None:
        config = _config()
        _component(config, "existing-canonical-store")["declaration"]["capabilities"][0]["state_posture"] = "derived"
        with self.assertRaisesRegex(RuntimeConfigurationError, "must declare canonical state posture"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_stale_component_version_cannot_inherit_qualification(self) -> None:
        config = _config()
        _component(config, "codegenome")["declaration"]["component_version"] = "unverified-next-version"
        with self.assertRaisesRegex(RuntimeConfigurationError, "qualification is missing/stale"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_maturity_shortfall_refuses_preferred_provider(self) -> None:
        config = _config()
        _component(config, "codegenome")["declaration"]["capabilities"][0]["maturity"] = "runtime_wired"
        with self.assertRaisesRegex(RuntimeConfigurationError, "preferred provider"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_ambiguous_route_without_preference_fails(self) -> None:
        config = _config()
        _route(config, "derived-code-graph").pop("preferred_component")
        with self.assertRaisesRegex(RuntimeConfigurationError, "ambiguous providers"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_incompatible_fallback_fails_configuration(self) -> None:
        config = _config()
        graphify = _component(config, "graphify")
        graphify["declaration"]["capabilities"][0]["scope_posture"] = "external_scope_bridge"
        with self.assertRaisesRegex(RuntimeConfigurationError, "preferred provider|weaker/incompatible"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_runtime_disallowed_source_rights_fail(self) -> None:
        config = _config()
        _component(config, "graphify")["source_rights"]["use_posture"] = "comparator_only"
        with self.assertRaisesRegex(RuntimeConfigurationError, "not permitted for runtime use"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_noncurrent_qualification_fails(self) -> None:
        config = _config()
        bindings = list(_bindings())
        current = bindings[0]
        bindings[0] = QualificationBinding(
            **{**current.__dict__, "qualification_current": False}
        )
        with self.assertRaisesRegex(RuntimeConfigurationError, "qualification is non-current"):
            validate_runtime_configuration(config, qualification_bindings=bindings)

    def test_wrong_primary_applicability_digest_fails(self) -> None:
        config = _config()
        _route(config, "derived-code-graph")["qualification"]["applicability_digest"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(RuntimeConfigurationError, "qualification is missing/stale"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_evidence_maturity_requires_independent_qualification(self) -> None:
        config = _config()
        _route(config, "derived-code-graph")["qualification"] = {"required": False}
        with self.assertRaisesRegex(RuntimeConfigurationError, "requires evidence maturity"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_current_derived_route_requires_projection_identity(self) -> None:
        config = _config()
        _route(config, "derived-code-graph")["currentness"].pop("projection_id")
        with self.assertRaisesRegex(RuntimeConfigurationError, "has no projection_id"):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_literal_secret_material_is_not_a_portable_configuration_value(self) -> None:
        config = _config()
        _component(config, "existing-canonical-store")["adapter"]["secret_refs"]["connection"] = "postgres://user:literal-secret@db"
        with self.assertRaises(RuntimeConfigurationError):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_literal_secret_key_is_rejected_even_if_schema_shape_changes_later(self) -> None:
        config = _config()
        config["governance_peers"][0]["token"] = "literal-token"
        with self.assertRaises(RuntimeConfigurationError):
            validate_runtime_configuration(config, qualification_bindings=_bindings())

    def test_multiple_equivalent_fallbacks_are_ambiguous(self) -> None:
        config = _config()
        clone = copy.deepcopy(_component(config, "graphify"))
        clone["declaration"]["component_id"] = "graphify-second"
        clone["adapter"]["adapter_id"] = "graphify-second-cli"
        config["components"].append(clone)
        route = _route(config, "derived-code-graph")
        route["allowed_components"].append("graphify-second")
        route["fallback_components"].append("graphify-second")

        graphify_binding = _bindings()[1]
        second_binding = QualificationBinding(
            **{
                **graphify_binding.__dict__,
                "component_id": "graphify-second",
                "adapter_id": "graphify-second-cli",
                "record_ref": "artifact:#300:graphify-second",
            }
        )
        with self.assertRaisesRegex(RuntimeConfigurationError, "ambiguous equivalent fallbacks"):
            validate_runtime_configuration(
                config,
                qualification_bindings=(*_bindings(), second_binding),
            )


if __name__ == "__main__":
    unittest.main()
