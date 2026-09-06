"""Portable Agent Memory runtime configuration for issue #280.

The configuration is intentionally serialization-neutral. JSON is used by the
reference fixtures because the repository already validates JSON Schema, but a
future CLI, wizard, YAML reader, or TOML reader must map to this same semantic
contract rather than create a second configuration universe.

Configuration is not qualification and never grants authority. The validator
combines declared component capabilities with independently supplied,
previously validated qualification evidence where a route requires it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from importlib import metadata
import json
from pathlib import Path
from typing import Iterable, Mapping

import jsonschema

from .capabilities import (
    AmbiguousCapabilityError,
    CapabilityDeclaration,
    CapabilityRequirement,
    CapabilityResolutionError,
    ComponentDeclaration,
    ComponentRegistry,
    ResolvedCapability,
    maturity_satisfies,
)
from .qualification import QualificationRecord


RUNTIME_CONFIGURATION_SCHEMA_VERSION = "1.0.0"
_DISTRIBUTION_NAME = "agent-memory-reference"
_RUNTIME_SCHEMA_DATA_SUFFIX = "agent_memory_reference/schemas/runtime-configuration.schema.json"
_ALLOWED_SECRET_SCHEMES = ("env://", "secret://", "vault://", "keyring://")
_LITERAL_SECRET_KEYS = frozenset(
    {
        "password",
        "passwd",
        "token",
        "access_token",
        "refresh_token",
        "api_key",
        "apikey",
        "secret",
        "client_secret",
        "private_key",
        "access_key",
        "secret_key",
    }
)


class RuntimeConfigurationError(ValueError):
    """Runtime configuration cannot be interpreted safely."""


@dataclass(frozen=True)
class SourceRights:
    license_id: str
    license_ref: str
    use_posture: str


@dataclass(frozen=True)
class AdapterBinding:
    adapter_id: str
    adapter_version: str
    runtime_ref: str
    secret_refs: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ComponentRuntime:
    declaration: ComponentDeclaration
    adapter: AdapterBinding
    source_rights: SourceRights


@dataclass(frozen=True)
class QualificationRequirement:
    required: bool
    adapter_id: str = ""
    adapter_version: str = ""
    profile_id: str = ""
    profile_version: str = ""
    minimum_earned_maturity: str = ""
    applicability_digest: str = ""


@dataclass(frozen=True)
class RouteConfiguration:
    route_id: str
    capability_id: str
    capability_version: str
    minimum_maturity: str
    allowed_components: tuple[str, ...]
    preferred_component: str
    fallback_components: tuple[str, ...]
    required_state_postures: tuple[str, ...]
    required_scope_postures: tuple[str, ...]
    qualification: QualificationRequirement
    currentness_required: bool
    projection_id: str


@dataclass(frozen=True)
class QualificationBinding:
    """Runtime view derived from a validated #300 QualificationRecord.

    It is supplied independently of configuration so an operator cannot make a
    component qualified by editing the config file.
    """

    component_id: str
    component_version: str
    capability_id: str
    capability_version: str
    adapter_id: str
    adapter_version: str
    qualification_profile_id: str
    qualification_profile_version: str
    applicability_digest: str
    qualification_current: bool
    earned_maturity: str
    source_rights_use_posture: str
    record_ref: str

    @classmethod
    def from_record(cls, record: QualificationRecord, *, record_ref: str) -> "QualificationBinding":
        subject = record.subject
        return cls(
            component_id=subject.component_id,
            component_version=subject.component_version,
            capability_id=subject.capability_id,
            capability_version=subject.capability_version,
            adapter_id=subject.adapter_id,
            adapter_version=subject.adapter_version,
            qualification_profile_id=subject.qualification_profile_id,
            qualification_profile_version=subject.qualification_profile_version,
            applicability_digest=record.applicability_digest,
            qualification_current=record.qualification_current,
            earned_maturity=record.earned_maturity,
            source_rights_use_posture=record.use_posture,
            record_ref=record_ref,
        )


@dataclass(frozen=True)
class ResolvedRoute:
    route_id: str
    primary: ResolvedCapability
    fallback_component_id: str
    qualification_record_ref: str
    fallback_qualification_record_ref: str
    currentness_required: bool
    projection_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "route_id": self.route_id,
            "primary": self.primary.to_dict(),
            "fallback_component_id": self.fallback_component_id or None,
            "qualification_record_ref": self.qualification_record_ref or None,
            "fallback_qualification_record_ref": self.fallback_qualification_record_ref or None,
            "currentness_required": self.currentness_required,
            "projection_id": self.projection_id or None,
            "authority_effect": "none",
        }


@dataclass(frozen=True)
class RuntimeConfigurationPlan:
    schema_version: str
    configuration_digest: str
    entry_mode: str
    runtime_id: str
    runtime_version: str
    profile_id: str
    profile_version: str
    canonical_owner_component_id: str
    canonical_owner_capability_id: str
    durable_governance_profile_id: str
    resolved_routes: tuple[ResolvedRoute, ...]
    required_projection_ids: tuple[str, ...]
    governance_peer_ids: tuple[str, ...]

    @property
    def authority_effect(self) -> str:
        return "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "configuration_digest": self.configuration_digest,
            "entry_mode": self.entry_mode,
            "runtime": {
                "runtime_id": self.runtime_id,
                "runtime_version": self.runtime_version,
                "profile_id": self.profile_id,
                "profile_version": self.profile_version,
            },
            "canonical_owner": {
                "component_id": self.canonical_owner_component_id,
                "capability_id": self.canonical_owner_capability_id,
            },
            "durable_governance_profile_id": self.durable_governance_profile_id,
            "resolved_routes": [route.to_dict() for route in self.resolved_routes],
            "required_projection_ids": list(self.required_projection_ids),
            "governance_peer_ids": list(self.governance_peer_ids),
            "authority_effect": "none",
            "startable": True,
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _configuration_schema_path() -> Path:
    """Locate the canonical runtime schema in source or an installed wheel."""

    source_path = _repo_root() / "schemas" / "runtime-configuration.schema.json"
    if source_path.is_file():
        return source_path

    try:
        distribution_files = metadata.files(_DISTRIBUTION_NAME) or ()
    except metadata.PackageNotFoundError:
        distribution_files = ()

    for entry in distribution_files:
        normalized = str(entry).replace("\\", "/")
        if normalized.endswith(_RUNTIME_SCHEMA_DATA_SUFFIX):
            installed_path = Path(entry.locate())
            if installed_path.is_file():
                return installed_path

    raise RuntimeConfigurationError(
        "runtime configuration schema is unavailable; install the distribution with its packaged schema data"
    )


def _configuration_schema() -> dict:
    return json.loads(_configuration_schema_path().read_text(encoding="utf-8"))


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def configuration_digest(value: Mapping[str, object]) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _reject_literal_secret_keys(value: object, *, path: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            lowered = key.lower()
            if lowered in _LITERAL_SECRET_KEYS or (
                lowered.endswith("_secret") and not lowered.endswith("_secret_ref")
            ):
                dotted = ".".join((*path, key))
                raise RuntimeConfigurationError(
                    f"portable configuration may contain secret references, not literal secret material: {dotted}"
                )
            _reject_literal_secret_keys(child, path=(*path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_literal_secret_keys(child, path=(*path, str(index)))


def _validate_secret_refs(value: Mapping[str, object]) -> None:
    refs: list[str] = []
    for component in value.get("components", ()):  # type: ignore[union-attr]
        if not isinstance(component, Mapping):
            continue
        adapter = component.get("adapter", {})
        if isinstance(adapter, Mapping):
            secret_refs = adapter.get("secret_refs", {})
            if isinstance(secret_refs, Mapping):
                refs.extend(str(item) for item in secret_refs.values())
    for peer in value.get("governance_peers", ()):  # type: ignore[union-attr]
        if not isinstance(peer, Mapping):
            continue
        secret_refs = peer.get("secret_refs", {})
        if isinstance(secret_refs, Mapping):
            refs.extend(str(item) for item in secret_refs.values())
    for ref in refs:
        if not ref.startswith(_ALLOWED_SECRET_SCHEMES):
            raise RuntimeConfigurationError(f"unsupported secret reference scheme: {ref!r}")


def _component_runtime(raw: Mapping[str, object]) -> ComponentRuntime:
    declaration_raw = raw["declaration"]
    adapter_raw = raw["adapter"]
    rights_raw = raw["source_rights"]
    if not isinstance(declaration_raw, Mapping) or not isinstance(adapter_raw, Mapping) or not isinstance(rights_raw, Mapping):
        raise RuntimeConfigurationError("component declaration, adapter, and source_rights must be objects")
    declaration = ComponentDeclaration.from_dict(declaration_raw)
    secret_refs_raw = adapter_raw.get("secret_refs", {})
    secret_refs = tuple(
        sorted((str(key), str(value)) for key, value in secret_refs_raw.items())
    ) if isinstance(secret_refs_raw, Mapping) else ()
    return ComponentRuntime(
        declaration=declaration,
        adapter=AdapterBinding(
            adapter_id=str(adapter_raw["adapter_id"]),
            adapter_version=str(adapter_raw["adapter_version"]),
            runtime_ref=str(adapter_raw["runtime_ref"]),
            secret_refs=secret_refs,
        ),
        source_rights=SourceRights(
            license_id=str(rights_raw["license_id"]),
            license_ref=str(rights_raw["license_ref"]),
            use_posture=str(rights_raw["use_posture"]),
        ),
    )


def _qualification_requirement(raw: Mapping[str, object]) -> QualificationRequirement:
    return QualificationRequirement(
        required=bool(raw.get("required", False)),
        adapter_id=str(raw.get("adapter_id", "")),
        adapter_version=str(raw.get("adapter_version", "")),
        profile_id=str(raw.get("profile_id", "")),
        profile_version=str(raw.get("profile_version", "")),
        minimum_earned_maturity=str(raw.get("minimum_earned_maturity", "")),
        applicability_digest=str(raw.get("applicability_digest", "")),
    )


def _route(raw: Mapping[str, object]) -> RouteConfiguration:
    qualification_raw = raw["qualification"]
    currentness_raw = raw["currentness"]
    if not isinstance(qualification_raw, Mapping) or not isinstance(currentness_raw, Mapping):
        raise RuntimeConfigurationError("route qualification/currentness must be objects")
    return RouteConfiguration(
        route_id=str(raw["route_id"]),
        capability_id=str(raw["capability_id"]),
        capability_version=str(raw["capability_version"]),
        minimum_maturity=str(raw["minimum_maturity"]),
        allowed_components=tuple(str(item) for item in raw["allowed_components"]),
        preferred_component=str(raw.get("preferred_component", "")),
        fallback_components=tuple(str(item) for item in raw.get("fallback_components", ())),
        required_state_postures=tuple(str(item) for item in raw.get("required_state_postures", ())),
        required_scope_postures=tuple(str(item) for item in raw.get("required_scope_postures", ())),
        qualification=_qualification_requirement(qualification_raw),
        currentness_required=bool(currentness_raw.get("required", False)),
        projection_id=str(currentness_raw.get("projection_id", "")),
    )


def _qualification_index(bindings: Iterable[QualificationBinding]) -> dict[tuple[str, str, str, str], list[QualificationBinding]]:
    index: dict[tuple[str, str, str, str], list[QualificationBinding]] = {}
    for binding in bindings:
        key = (
            binding.component_id,
            binding.component_version,
            binding.capability_id,
            binding.capability_version,
        )
        index.setdefault(key, []).append(binding)
    return index


def _binding_for(
    resolved: ResolvedCapability,
    requirement: QualificationRequirement,
    qualification_index: Mapping[tuple[str, str, str, str], list[QualificationBinding]],
) -> QualificationBinding:
    key = (
        resolved.component_id,
        resolved.component_version,
        resolved.capability_id,
        resolved.capability_version,
    )
    candidates = qualification_index.get(key, ())
    matches = [
        item
        for item in candidates
        if item.adapter_id == requirement.adapter_id
        and item.adapter_version == requirement.adapter_version
        and item.qualification_profile_id == requirement.profile_id
        and item.qualification_profile_version == requirement.profile_version
        and item.applicability_digest == requirement.applicability_digest
    ]
    if not matches:
        raise RuntimeConfigurationError(
            f"route qualification is missing/stale for {resolved.component_id}:{resolved.capability_id}"
        )
    if len(matches) > 1:
        raise RuntimeConfigurationError(
            f"ambiguous qualification records for {resolved.component_id}:{resolved.capability_id}"
        )
    binding = matches[0]
    if not binding.qualification_current:
        raise RuntimeConfigurationError(
            f"qualification is non-current for {resolved.component_id}:{resolved.capability_id}"
        )
    if binding.source_rights_use_posture != "runtime_allowed":
        raise RuntimeConfigurationError(
            f"qualification source rights are not runtime_allowed for {resolved.component_id}:{resolved.capability_id}"
        )
    if not maturity_satisfies(binding.earned_maturity, requirement.minimum_earned_maturity):
        raise RuntimeConfigurationError(
            f"qualification maturity shortfall for {resolved.component_id}:{resolved.capability_id}"
        )
    return binding


def _resolve_specific(
    registry: ComponentRegistry,
    route: RouteConfiguration,
    component_id: str,
) -> ResolvedCapability:
    try:
        return registry.resolve(
            CapabilityRequirement(
                capability_id=route.capability_id,
                capability_version=route.capability_version,
                minimum_maturity=route.minimum_maturity,
                required_state_postures=route.required_state_postures,
                required_scope_postures=route.required_scope_postures,
                allowed_components=route.allowed_components,
                preferred_component=component_id,
            )
        )
    except CapabilityResolutionError as exc:
        raise RuntimeConfigurationError(str(exc)) from exc


def _static_fallback_reasons(primary: ResolvedCapability, candidate: ResolvedCapability) -> tuple[str, ...]:
    reasons: list[str] = []
    if candidate.capability_id != primary.capability_id:
        reasons.append("capability_id_mismatch")
    if candidate.capability_version != primary.capability_version:
        reasons.append("capability_version_mismatch")
    if not maturity_satisfies(candidate.maturity, primary.maturity):
        reasons.append("weaker_maturity")
    if candidate.state_posture != primary.state_posture:
        reasons.append("state_posture_mismatch")
    if candidate.scope_posture != primary.scope_posture:
        reasons.append("scope_posture_mismatch")
    if candidate.failure_posture != primary.failure_posture:
        reasons.append("failure_posture_mismatch")
    if candidate.authority_effect != primary.authority_effect:
        reasons.append("authority_effect_mismatch")
    return tuple(reasons)


def _assert_component_runtime_allowed(component: ComponentRuntime) -> None:
    if component.source_rights.use_posture != "runtime_allowed":
        raise RuntimeConfigurationError(
            f"component {component.declaration.component_id!r} is not permitted for runtime use"
        )


def validate_runtime_configuration(
    value: Mapping[str, object],
    *,
    qualification_bindings: Iterable[QualificationBinding] = (),
) -> RuntimeConfigurationPlan:
    """Validate and deterministically resolve one portable runtime configuration."""

    try:
        jsonschema.Draft202012Validator(_configuration_schema()).validate(value)
    except jsonschema.ValidationError as exc:
        path = ".".join(str(part) for part in exc.absolute_path)
        location = f" at {path}" if path else ""
        raise RuntimeConfigurationError(f"runtime configuration schema violation{location}: {exc.message}") from exc

    _reject_literal_secret_keys(value)
    _validate_secret_refs(value)

    component_rows = value["components"]
    route_rows = value["routes"]
    if not isinstance(component_rows, list) or not isinstance(route_rows, list):
        raise RuntimeConfigurationError("components and routes must be arrays")

    components = tuple(_component_runtime(row) for row in component_rows)
    component_ids = [item.declaration.component_id for item in components]
    if len(component_ids) != len(set(component_ids)):
        raise RuntimeConfigurationError("component ids must be unique within one runtime configuration")
    components_by_id = {item.declaration.component_id: item for item in components}

    registry = ComponentRegistry()
    try:
        registry.register_many(item.declaration for item in components)
    except ValueError as exc:
        raise RuntimeConfigurationError(str(exc)) from exc

    canonical_raw = value["canonical_state"]
    if not isinstance(canonical_raw, Mapping):
        raise RuntimeConfigurationError("canonical_state must be an object")
    owner_id = str(canonical_raw["owner_component_id"])
    owner = components_by_id.get(owner_id)
    if owner is None or not owner.declaration.enabled:
        raise RuntimeConfigurationError("canonical-state owner is missing or disabled")
    _assert_component_runtime_allowed(owner)
    owner_capability_id = str(canonical_raw["owner_capability_id"])
    owner_capability_version = str(canonical_raw["owner_capability_version"])
    owner_matches = [
        capability
        for capability in owner.declaration.capabilities
        if capability.enabled
        and capability.capability_id == owner_capability_id
        and capability.capability_version == owner_capability_version
    ]
    if len(owner_matches) != 1:
        raise RuntimeConfigurationError("canonical-state owner capability is missing or ambiguous")
    if owner_matches[0].state_posture != "canonical":
        raise RuntimeConfigurationError("canonical-state owner capability must declare canonical state posture")

    routes = tuple(_route(row) for row in route_rows)
    route_ids = [route.route_id for route in routes]
    if len(route_ids) != len(set(route_ids)):
        raise RuntimeConfigurationError("route ids must be unique")

    qindex = _qualification_index(qualification_bindings)
    resolved_routes: list[ResolvedRoute] = []
    required_projection_ids: list[str] = []

    for route in routes:
        allowed = set(route.allowed_components)
        unknown_allowed = sorted(allowed.difference(components_by_id))
        if unknown_allowed:
            raise RuntimeConfigurationError(
                f"route {route.route_id!r} names unknown allowed components: {unknown_allowed}"
            )
        if route.preferred_component and route.preferred_component not in allowed:
            raise RuntimeConfigurationError(
                f"route {route.route_id!r} preferred component is not in allowed_components"
            )
        if set(route.fallback_components).difference(allowed):
            raise RuntimeConfigurationError(
                f"route {route.route_id!r} fallback_components must be a subset of allowed_components"
            )

        if route.preferred_component:
            primary = _resolve_specific(registry, route, route.preferred_component)
        else:
            try:
                primary = registry.resolve(
                    CapabilityRequirement(
                        capability_id=route.capability_id,
                        capability_version=route.capability_version,
                        minimum_maturity=route.minimum_maturity,
                        required_state_postures=route.required_state_postures,
                        required_scope_postures=route.required_scope_postures,
                        allowed_components=route.allowed_components,
                    )
                )
            except AmbiguousCapabilityError as exc:
                raise RuntimeConfigurationError(str(exc)) from exc
            except CapabilityResolutionError as exc:
                raise RuntimeConfigurationError(str(exc)) from exc

        primary_runtime = components_by_id[primary.component_id]
        _assert_component_runtime_allowed(primary_runtime)
        if (
            primary_runtime.adapter.adapter_id != route.qualification.adapter_id
            or primary_runtime.adapter.adapter_version != route.qualification.adapter_version
        ) and route.qualification.required:
            raise RuntimeConfigurationError(
                f"route {route.route_id!r} qualification adapter does not match configured primary adapter"
            )

        if route.minimum_maturity in {"evidence_proven", "reference_qualified"} and not route.qualification.required:
            raise RuntimeConfigurationError(
                f"route {route.route_id!r} requires evidence maturity but no independent qualification"
            )

        primary_binding: QualificationBinding | None = None
        if route.qualification.required:
            primary_binding = _binding_for(primary, route.qualification, qindex)

        if route.currentness_required:
            if primary.state_posture == "derived" and not route.projection_id:
                raise RuntimeConfigurationError(
                    f"route {route.route_id!r} requires current derived state but has no projection_id"
                )
            if route.projection_id:
                required_projection_ids.append(route.projection_id)

        fallback_component_id = ""
        fallback_record_ref = ""
        compatible_fallbacks: list[tuple[ResolvedCapability, QualificationBinding | None]] = []
        for fallback_id in route.fallback_components:
            if fallback_id == primary.component_id:
                raise RuntimeConfigurationError(
                    f"route {route.route_id!r} cannot list the primary as its own fallback"
                )
            candidate = _resolve_specific(registry, route, fallback_id)
            candidate_runtime = components_by_id[candidate.component_id]
            _assert_component_runtime_allowed(candidate_runtime)
            reasons = _static_fallback_reasons(primary, candidate)
            if reasons:
                raise RuntimeConfigurationError(
                    f"route {route.route_id!r} fallback {fallback_id!r} is weaker/incompatible: {list(reasons)}"
                )
            candidate_binding: QualificationBinding | None = None
            if route.qualification.required:
                if (
                    candidate_runtime.adapter.adapter_id != route.qualification.adapter_id
                    or candidate_runtime.adapter.adapter_version != route.qualification.adapter_version
                ):
                    # Different provider adapters are expected. Qualification
                    # requirements bind profile/version, while each component's
                    # exact adapter is matched by its evidence binding below.
                    candidate_requirement = QualificationRequirement(
                        required=True,
                        adapter_id=candidate_runtime.adapter.adapter_id,
                        adapter_version=candidate_runtime.adapter.adapter_version,
                        profile_id=route.qualification.profile_id,
                        profile_version=route.qualification.profile_version,
                        minimum_earned_maturity=route.qualification.minimum_earned_maturity,
                        applicability_digest="",
                    )
                    # Applicability is provider-specific. Find exactly one
                    # current record for the configured adapter/profile.
                    key = (
                        candidate.component_id,
                        candidate.component_version,
                        candidate.capability_id,
                        candidate.capability_version,
                    )
                    possible = [
                        item
                        for item in qindex.get(key, ())
                        if item.adapter_id == candidate_requirement.adapter_id
                        and item.adapter_version == candidate_requirement.adapter_version
                        and item.qualification_profile_id == candidate_requirement.profile_id
                        and item.qualification_profile_version == candidate_requirement.profile_version
                    ]
                    if len(possible) != 1:
                        raise RuntimeConfigurationError(
                            f"route {route.route_id!r} fallback qualification is missing/ambiguous for {fallback_id!r}"
                        )
                    candidate_binding = possible[0]
                    if not candidate_binding.qualification_current:
                        raise RuntimeConfigurationError(
                            f"route {route.route_id!r} fallback qualification is non-current for {fallback_id!r}"
                        )
                    if candidate_binding.source_rights_use_posture != "runtime_allowed":
                        raise RuntimeConfigurationError(
                            f"route {route.route_id!r} fallback qualification source rights are not runtime_allowed"
                        )
                    if not maturity_satisfies(
                        candidate_binding.earned_maturity,
                        route.qualification.minimum_earned_maturity,
                    ):
                        raise RuntimeConfigurationError(
                            f"route {route.route_id!r} fallback qualification maturity is too weak"
                        )
                else:
                    candidate_binding = _binding_for(candidate, route.qualification, qindex)
            compatible_fallbacks.append((candidate, candidate_binding))

        if len(compatible_fallbacks) > 1:
            raise RuntimeConfigurationError(
                f"route {route.route_id!r} has ambiguous equivalent fallbacks; configure at most one until an explicit composition/order contract exists"
            )
        if compatible_fallbacks:
            fallback, fallback_binding = compatible_fallbacks[0]
            fallback_component_id = fallback.component_id
            fallback_record_ref = fallback_binding.record_ref if fallback_binding else ""

        resolved_routes.append(
            ResolvedRoute(
                route_id=route.route_id,
                primary=primary,
                fallback_component_id=fallback_component_id,
                qualification_record_ref=primary_binding.record_ref if primary_binding else "",
                fallback_qualification_record_ref=fallback_record_ref,
                currentness_required=route.currentness_required,
                projection_id=route.projection_id,
            )
        )

    peer_rows = value.get("governance_peers", ())
    if not isinstance(peer_rows, list):
        raise RuntimeConfigurationError("governance_peers must be an array")
    peer_ids = [str(peer["peer_id"]) for peer in peer_rows if isinstance(peer, Mapping)]
    if len(peer_ids) != len(set(peer_ids)):
        raise RuntimeConfigurationError("governance peer ids must be unique")

    runtime_raw = value["runtime"]
    governance_raw = value["durable_governance"]
    if not isinstance(runtime_raw, Mapping) or not isinstance(governance_raw, Mapping):
        raise RuntimeConfigurationError("runtime and durable_governance must be objects")

    return RuntimeConfigurationPlan(
        schema_version=RUNTIME_CONFIGURATION_SCHEMA_VERSION,
        configuration_digest=configuration_digest(value),
        entry_mode=str(runtime_raw["entry_mode"]),
        runtime_id=str(runtime_raw["runtime_id"]),
        runtime_version=str(runtime_raw["runtime_version"]),
        profile_id=str(runtime_raw["profile_id"]),
        profile_version=str(runtime_raw["profile_version"]),
        canonical_owner_component_id=owner_id,
        canonical_owner_capability_id=owner_capability_id,
        durable_governance_profile_id=str(governance_raw["profile_id"]),
        resolved_routes=tuple(resolved_routes),
        required_projection_ids=tuple(dict.fromkeys(required_projection_ids)),
        governance_peer_ids=tuple(peer_ids),
    )


def load_runtime_configuration(
    path: str | Path,
    *,
    qualification_bindings: Iterable[QualificationBinding] = (),
) -> RuntimeConfigurationPlan:
    """Load a JSON serialization of the portable contract and validate it."""

    config_path = Path(path)
    try:
        value = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeConfigurationError(f"runtime configuration not found: {config_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeConfigurationError(f"runtime configuration is not valid JSON: {config_path}") from exc
    if not isinstance(value, Mapping):
        raise RuntimeConfigurationError("runtime configuration must be a JSON object")
    return validate_runtime_configuration(value, qualification_bindings=qualification_bindings)
