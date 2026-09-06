"""Behavior-aware extension of the portable Agent Memory runtime contract.

The original runtime configuration validator remains the compatibility boundary
for component-capability-v1 configurations. This module layers the v2 behavior
contract on the same validated plan. It does not create a second routing model:
component behavior matching uses the same ``CapabilityBehaviorRequirement``
semantics implemented by ``ComponentRegistry``.

A behavior declaration is descriptive evidence about an implementation surface.
It never grants mutation, recall-admission, structural, or action authority.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

from .capabilities import (
    CapabilityBehaviorRequirement,
    CapabilityDeclaration,
    ComponentDeclaration,
)
from .runtime_config import (
    QualificationBinding,
    RuntimeConfigurationError,
    RuntimeConfigurationPlan,
    load_runtime_configuration,
    validate_runtime_configuration,
)


class RuntimeBehaviorContractError(RuntimeConfigurationError):
    """A resolved runtime route does not satisfy its declared behavior contract."""


def _component_declarations(value: Mapping[str, object]) -> dict[str, ComponentDeclaration]:
    rows = value.get("components", ())
    if not isinstance(rows, list):
        raise RuntimeBehaviorContractError("components must be an array")
    declarations: dict[str, ComponentDeclaration] = {}
    for row in rows:
        if not isinstance(row, Mapping):
            raise RuntimeBehaviorContractError("component runtime row must be an object")
        raw = row.get("declaration")
        if not isinstance(raw, Mapping):
            raise RuntimeBehaviorContractError("component declaration must be an object")
        declaration = ComponentDeclaration.from_dict(raw)
        declarations[declaration.component_id] = declaration
    return declarations


def _declared_capability(
    declaration: ComponentDeclaration,
    *,
    capability_id: str,
    capability_version: str,
) -> CapabilityDeclaration:
    matches = [
        capability
        for capability in declaration.capabilities
        if capability.enabled
        and capability.capability_id == capability_id
        and capability.capability_version == capability_version
    ]
    if len(matches) != 1:
        raise RuntimeBehaviorContractError(
            f"resolved component {declaration.component_id!r} has missing/ambiguous capability "
            f"{capability_id!r}@{capability_version}"
        )
    return matches[0]


def _assert_behavior(
    *,
    route_id: str,
    provider_role: str,
    component: ComponentDeclaration,
    capability_id: str,
    capability_version: str,
    requirement: CapabilityBehaviorRequirement,
) -> None:
    capability = _declared_capability(
        component,
        capability_id=capability_id,
        capability_version=capability_version,
    )
    contract = capability.behavior_contract
    if contract is None:
        raise RuntimeBehaviorContractError(
            f"route {route_id!r} requires behavior metadata but {provider_role} "
            f"{component.component_id!r} uses a legacy/no-behavior capability declaration"
        )
    if not requirement.matches(contract):
        raise RuntimeBehaviorContractError(
            f"route {route_id!r} behavior requirements are not satisfied by {provider_role} "
            f"{component.component_id!r}:{capability_id}"
        )


def validate_runtime_behavior_contract(
    value: Mapping[str, object],
    *,
    qualification_bindings: Iterable[QualificationBinding] = (),
) -> RuntimeConfigurationPlan:
    """Validate the base runtime plan plus optional v2 route behavior requirements.

    Legacy v1 configurations with no ``behavior_requirements`` remain valid.
    When a route requests behavior semantics, both the resolved primary and any
    configured resolved fallback must explicitly satisfy them.
    """

    plan = validate_runtime_configuration(
        value,
        qualification_bindings=qualification_bindings,
    )
    declarations = _component_declarations(value)

    route_rows = value.get("routes", ())
    if not isinstance(route_rows, list):
        raise RuntimeBehaviorContractError("routes must be an array")
    raw_by_id = {
        str(row.get("route_id")): row
        for row in route_rows
        if isinstance(row, Mapping)
    }

    for resolved_route in plan.resolved_routes:
        raw = raw_by_id.get(resolved_route.route_id)
        if not isinstance(raw, Mapping):
            raise RuntimeBehaviorContractError(
                f"resolved route has no configuration row: {resolved_route.route_id}"
            )
        behavior_raw = raw.get("behavior_requirements")
        if behavior_raw is None:
            continue
        if not isinstance(behavior_raw, Mapping):
            raise RuntimeBehaviorContractError(
                f"route behavior_requirements must be an object: {resolved_route.route_id}"
            )
        requirement = CapabilityBehaviorRequirement.from_dict(behavior_raw)
        primary = declarations.get(resolved_route.primary.component_id)
        if primary is None:
            raise RuntimeBehaviorContractError(
                f"resolved primary declaration is missing: {resolved_route.primary.component_id}"
            )
        _assert_behavior(
            route_id=resolved_route.route_id,
            provider_role="primary",
            component=primary,
            capability_id=resolved_route.primary.capability_id,
            capability_version=resolved_route.primary.capability_version,
            requirement=requirement,
        )

        if resolved_route.fallback_component_id:
            fallback = declarations.get(resolved_route.fallback_component_id)
            if fallback is None:
                raise RuntimeBehaviorContractError(
                    f"resolved fallback declaration is missing: {resolved_route.fallback_component_id}"
                )
            _assert_behavior(
                route_id=resolved_route.route_id,
                provider_role="fallback",
                component=fallback,
                capability_id=resolved_route.primary.capability_id,
                capability_version=resolved_route.primary.capability_version,
                requirement=requirement,
            )

    return plan


def load_runtime_behavior_contract(
    path: str | Path,
    *,
    qualification_bindings: Iterable[QualificationBinding] = (),
) -> RuntimeConfigurationPlan:
    """Load a JSON runtime configuration and apply the v1 + v2 behavior gates."""

    # Reuse the base loader for file/JSON diagnostics, then parse once more for
    # the behavior layer. The input is bounded reference configuration and this
    # preserves one semantic contract rather than creating hidden state.
    load_runtime_configuration(path, qualification_bindings=qualification_bindings)
    import json

    config_path = Path(path)
    value = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeBehaviorContractError("runtime configuration must be a JSON object")
    return validate_runtime_behavior_contract(
        value,
        qualification_bindings=qualification_bindings,
    )
