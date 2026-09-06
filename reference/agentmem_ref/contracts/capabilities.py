"""Capability declarations and deterministic component resolution.

This module is the narrow executable surface for ADR-033 and issues #287/#290/#280/#343.
It deliberately does not know about PAMA, recall admission, or memory mutation.
Selecting a component says only which configured implementation may supply a
capability. It never grants authority to use the resulting memory consequence.

``component-capability-v2`` adds machine-readable behavior metadata for the
lifecycle dimensions required by #280. ``component-capability-v3`` preserves
that behavior contract and adds a separate operational contract so substrate
mechanics can constrain provider eligibility without becoming memory semantics
or authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

MATURITY_ORDER = (
    "declared",
    "implemented",
    "runtime_wired",
    "evidence_proven",
    "reference_qualified",
)
_MATURITY_RANK = {name: index for index, name in enumerate(MATURITY_ORDER)}

CURRENTNESS_MODELS = frozenset(
    {
        "not_applicable",
        "canonical_version",
        "basis_versioned",
        "provider_revalidated",
        "external_asserted",
    }
)
INVALIDATION_MODELS = frozenset(
    {
        "not_applicable",
        "version_relation",
        "explicit_signal",
        "provider_revalidation",
    }
)
CORRECTION_MODELS = frozenset(
    {
        "not_applicable",
        "canonical_supersession",
        "invalidate_derived",
        "candidate_only",
        "provider_revalidation",
    }
)
DELETION_MODELS = frozenset(
    {
        "not_applicable",
        "canonical_delete",
        "derived_residue_then_purge",
        "candidate_drop",
        "provider_revalidation",
    }
)
RESIDUE_MODELS = frozenset(
    {
        "not_applicable",
        "none_expected",
        "scan_required",
        "derived_residual",
        "provider_managed",
    }
)
MIGRATION_REBUILD_MODELS = frozenset(
    {
        "not_applicable",
        "rebuild_from_canonical",
        "explicit_migration",
        "requires_requalification",
        "unsupported",
    }
)
STRUCTURAL_MUTATION_REQUIREMENTS = frozenset(
    {
        "none",
        "proposal_only",
        "pama_required",
        "external_authorization_required",
    }
)

WRITE_ATOMICITY_MODELS = frozenset(
    {
        "none",
        "process_local",
        "single_record_atomic",
        "transactional_multi_record",
    }
)
CONCURRENCY_CONTROL_MODELS = frozenset(
    {
        "none",
        "process_local",
        "optimistic_revision",
        "pessimistic_lock",
        "serializable",
    }
)
IDEMPOTENCY_MODELS = frozenset(
    {
        "none",
        "process_local",
        "durable_keyed",
    }
)
RESTART_RECOVERY_MODELS = frozenset(
    {
        "none",
        "process_local_only",
        "reconstructable",
        "checkpoint_replay",
    }
)
RECONCILIATION_MODELS = frozenset(
    {
        "none",
        "process_local_only",
        "deterministic_readback",
        "authoritative_rebuild",
    }
)


class CapabilityResolutionError(ValueError):
    """No configured provider can satisfy the exact requirement."""


class AmbiguousCapabilityError(CapabilityResolutionError):
    """Several providers satisfy a requirement and configuration chooses none."""


@dataclass(frozen=True)
class CapabilityBehaviorContract:
    """Machine-readable lifecycle behavior of one capability.

    This contract is descriptive. For example, ``write=True`` says the
    capability exposes a write surface; it does not authorize a write.
    """

    write: bool
    read: bool
    recall_candidate: bool
    currentness_model: str
    invalidation_model: str
    correction_model: str
    deletion_model: str
    residue_model: str
    migration_rebuild_model: str
    structural_mutation_requirement: str

    def __post_init__(self) -> None:
        checks = (
            ("currentness_model", self.currentness_model, CURRENTNESS_MODELS),
            ("invalidation_model", self.invalidation_model, INVALIDATION_MODELS),
            ("correction_model", self.correction_model, CORRECTION_MODELS),
            ("deletion_model", self.deletion_model, DELETION_MODELS),
            ("residue_model", self.residue_model, RESIDUE_MODELS),
            ("migration_rebuild_model", self.migration_rebuild_model, MIGRATION_REBUILD_MODELS),
            (
                "structural_mutation_requirement",
                self.structural_mutation_requirement,
                STRUCTURAL_MUTATION_REQUIREMENTS,
            ),
        )
        for name, value, allowed in checks:
            if value not in allowed:
                raise ValueError(f"unknown {name}: {value}")

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "CapabilityBehaviorContract":
        operation = value.get("operation_support")
        if not isinstance(operation, Mapping):
            raise ValueError("capability behavior requires operation_support")
        return cls(
            write=bool(operation["write"]),
            read=bool(operation["read"]),
            recall_candidate=bool(operation["recall_candidate"]),
            currentness_model=str(value["currentness_model"]),
            invalidation_model=str(value["invalidation_model"]),
            correction_model=str(value["correction_model"]),
            deletion_model=str(value["deletion_model"]),
            residue_model=str(value["residue_model"]),
            migration_rebuild_model=str(value["migration_rebuild_model"]),
            structural_mutation_requirement=str(value["structural_mutation_requirement"]),
        )

    def to_dict(self) -> dict:
        return {
            "operation_support": {
                "write": self.write,
                "read": self.read,
                "recall_candidate": self.recall_candidate,
            },
            "currentness_model": self.currentness_model,
            "invalidation_model": self.invalidation_model,
            "correction_model": self.correction_model,
            "deletion_model": self.deletion_model,
            "residue_model": self.residue_model,
            "migration_rebuild_model": self.migration_rebuild_model,
            "structural_mutation_requirement": self.structural_mutation_requirement,
        }


@dataclass(frozen=True)
class CapabilityBehaviorRequirement:
    """Optional routing constraints over declared behavior metadata."""

    write: bool | None = None
    read: bool | None = None
    recall_candidate: bool | None = None
    currentness_models: tuple[str, ...] = ()
    invalidation_models: tuple[str, ...] = ()
    correction_models: tuple[str, ...] = ()
    deletion_models: tuple[str, ...] = ()
    residue_models: tuple[str, ...] = ()
    migration_rebuild_models: tuple[str, ...] = ()
    structural_mutation_requirements: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        checks = (
            ("currentness_models", self.currentness_models, CURRENTNESS_MODELS),
            ("invalidation_models", self.invalidation_models, INVALIDATION_MODELS),
            ("correction_models", self.correction_models, CORRECTION_MODELS),
            ("deletion_models", self.deletion_models, DELETION_MODELS),
            ("residue_models", self.residue_models, RESIDUE_MODELS),
            ("migration_rebuild_models", self.migration_rebuild_models, MIGRATION_REBUILD_MODELS),
            (
                "structural_mutation_requirements",
                self.structural_mutation_requirements,
                STRUCTURAL_MUTATION_REQUIREMENTS,
            ),
        )
        for name, values, allowed in checks:
            unknown = sorted(set(values).difference(allowed))
            if unknown:
                raise ValueError(f"unknown {name}: {unknown}")

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "CapabilityBehaviorRequirement":
        operation = value.get("operation_support", {})
        if not isinstance(operation, Mapping):
            raise ValueError("behavior requirement operation_support must be an object")
        return cls(
            write=bool(operation["write"]) if "write" in operation else None,
            read=bool(operation["read"]) if "read" in operation else None,
            recall_candidate=(
                bool(operation["recall_candidate"])
                if "recall_candidate" in operation
                else None
            ),
            currentness_models=tuple(str(item) for item in value.get("currentness_models", ())),
            invalidation_models=tuple(str(item) for item in value.get("invalidation_models", ())),
            correction_models=tuple(str(item) for item in value.get("correction_models", ())),
            deletion_models=tuple(str(item) for item in value.get("deletion_models", ())),
            residue_models=tuple(str(item) for item in value.get("residue_models", ())),
            migration_rebuild_models=tuple(
                str(item) for item in value.get("migration_rebuild_models", ())
            ),
            structural_mutation_requirements=tuple(
                str(item) for item in value.get("structural_mutation_requirements", ())
            ),
        )

    def matches(self, contract: CapabilityBehaviorContract) -> bool:
        operation_checks = (
            (self.write, contract.write),
            (self.read, contract.read),
            (self.recall_candidate, contract.recall_candidate),
        )
        if any(required is not None and required != actual for required, actual in operation_checks):
            return False
        enum_checks = (
            (self.currentness_models, contract.currentness_model),
            (self.invalidation_models, contract.invalidation_model),
            (self.correction_models, contract.correction_model),
            (self.deletion_models, contract.deletion_model),
            (self.residue_models, contract.residue_model),
            (self.migration_rebuild_models, contract.migration_rebuild_model),
            (
                self.structural_mutation_requirements,
                contract.structural_mutation_requirement,
            ),
        )
        return all(not allowed or actual in allowed for allowed, actual in enum_checks)

    def to_dict(self) -> dict:
        operation: dict[str, bool] = {}
        if self.write is not None:
            operation["write"] = self.write
        if self.read is not None:
            operation["read"] = self.read
        if self.recall_candidate is not None:
            operation["recall_candidate"] = self.recall_candidate
        return {
            "operation_support": operation,
            "currentness_models": list(self.currentness_models),
            "invalidation_models": list(self.invalidation_models),
            "correction_models": list(self.correction_models),
            "deletion_models": list(self.deletion_models),
            "residue_models": list(self.residue_models),
            "migration_rebuild_models": list(self.migration_rebuild_models),
            "structural_mutation_requirements": list(self.structural_mutation_requirements),
        }


@dataclass(frozen=True)
class CapabilityOperationalContract:
    """Substrate mechanics that affect provider eligibility, not memory meaning.

    Operational quality cannot grant authority. It only describes whether a
    provider can safely satisfy a caller's explicit execution/recovery posture.
    """

    write_atomicity: str
    concurrency_control: str
    idempotency: str
    restart_recovery: str
    reconciliation: str

    def __post_init__(self) -> None:
        checks = (
            ("write_atomicity", self.write_atomicity, WRITE_ATOMICITY_MODELS),
            ("concurrency_control", self.concurrency_control, CONCURRENCY_CONTROL_MODELS),
            ("idempotency", self.idempotency, IDEMPOTENCY_MODELS),
            ("restart_recovery", self.restart_recovery, RESTART_RECOVERY_MODELS),
            ("reconciliation", self.reconciliation, RECONCILIATION_MODELS),
        )
        for name, value, allowed in checks:
            if value not in allowed:
                raise ValueError(f"unknown {name}: {value}")

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "CapabilityOperationalContract":
        return cls(
            write_atomicity=str(value["write_atomicity"]),
            concurrency_control=str(value["concurrency_control"]),
            idempotency=str(value["idempotency"]),
            restart_recovery=str(value["restart_recovery"]),
            reconciliation=str(value["reconciliation"]),
        )

    def to_dict(self) -> dict:
        return {
            "write_atomicity": self.write_atomicity,
            "concurrency_control": self.concurrency_control,
            "idempotency": self.idempotency,
            "restart_recovery": self.restart_recovery,
            "reconciliation": self.reconciliation,
        }


@dataclass(frozen=True)
class CapabilityOperationalRequirement:
    """Optional routing constraints over substrate operational guarantees."""

    write_atomicity: tuple[str, ...] = ()
    concurrency_control: tuple[str, ...] = ()
    idempotency: tuple[str, ...] = ()
    restart_recovery: tuple[str, ...] = ()
    reconciliation: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        checks = (
            ("write_atomicity", self.write_atomicity, WRITE_ATOMICITY_MODELS),
            ("concurrency_control", self.concurrency_control, CONCURRENCY_CONTROL_MODELS),
            ("idempotency", self.idempotency, IDEMPOTENCY_MODELS),
            ("restart_recovery", self.restart_recovery, RESTART_RECOVERY_MODELS),
            ("reconciliation", self.reconciliation, RECONCILIATION_MODELS),
        )
        for name, values, allowed in checks:
            unknown = sorted(set(values).difference(allowed))
            if unknown:
                raise ValueError(f"unknown operational requirement {name}: {unknown}")

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "CapabilityOperationalRequirement":
        return cls(
            write_atomicity=tuple(str(item) for item in value.get("write_atomicity", ())),
            concurrency_control=tuple(str(item) for item in value.get("concurrency_control", ())),
            idempotency=tuple(str(item) for item in value.get("idempotency", ())),
            restart_recovery=tuple(str(item) for item in value.get("restart_recovery", ())),
            reconciliation=tuple(str(item) for item in value.get("reconciliation", ())),
        )

    def matches(self, contract: CapabilityOperationalContract) -> bool:
        checks = (
            (self.write_atomicity, contract.write_atomicity),
            (self.concurrency_control, contract.concurrency_control),
            (self.idempotency, contract.idempotency),
            (self.restart_recovery, contract.restart_recovery),
            (self.reconciliation, contract.reconciliation),
        )
        return all(not allowed or actual in allowed for allowed, actual in checks)

    def to_dict(self) -> dict:
        return {
            "write_atomicity": list(self.write_atomicity),
            "concurrency_control": list(self.concurrency_control),
            "idempotency": list(self.idempotency),
            "restart_recovery": list(self.restart_recovery),
            "reconciliation": list(self.reconciliation),
        }


@dataclass(frozen=True)
class CapabilityDeclaration:
    capability_id: str
    capability_version: str
    maturity: str
    state_posture: str
    scope_posture: str
    failure_posture: str
    authority_effect: str = "none"
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    enabled: bool = True
    behavior_contract: CapabilityBehaviorContract | None = None
    operational_contract: CapabilityOperationalContract | None = None

    def __post_init__(self) -> None:
        if not self.capability_id or not self.capability_version:
            raise ValueError("capability identity and version are required")
        if self.maturity not in _MATURITY_RANK:
            raise ValueError(f"unknown capability maturity: {self.maturity}")
        if self.authority_effect not in {"none", "proposal_only"}:
            raise ValueError("capability authority_effect must be none or proposal_only")

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "CapabilityDeclaration":
        behavior_raw = value.get("behavior_contract")
        behavior = None
        if behavior_raw is not None:
            if not isinstance(behavior_raw, Mapping):
                raise ValueError("capability behavior_contract must be an object")
            behavior = CapabilityBehaviorContract.from_dict(behavior_raw)

        operational_raw = value.get("operational_contract")
        operational = None
        if operational_raw is not None:
            if not isinstance(operational_raw, Mapping):
                raise ValueError("capability operational_contract must be an object")
            operational = CapabilityOperationalContract.from_dict(operational_raw)

        return cls(
            capability_id=str(value["capability_id"]),
            capability_version=str(value["capability_version"]),
            maturity=str(value["maturity"]),
            state_posture=str(value["state_posture"]),
            scope_posture=str(value["scope_posture"]),
            failure_posture=str(value["failure_posture"]),
            authority_effect=str(value.get("authority_effect", "none")),
            evidence_refs=tuple(str(item) for item in value.get("evidence_refs", ())),
            limitations=tuple(str(item) for item in value.get("limitations", ())),
            enabled=bool(value.get("enabled", True)),
            behavior_contract=behavior,
            operational_contract=operational,
        )

    def to_dict(self) -> dict:
        payload = {
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "maturity": self.maturity,
            "state_posture": self.state_posture,
            "scope_posture": self.scope_posture,
            "failure_posture": self.failure_posture,
            "authority_effect": self.authority_effect,
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
            "enabled": self.enabled,
        }
        if self.behavior_contract is not None:
            payload["behavior_contract"] = self.behavior_contract.to_dict()
        if self.operational_contract is not None:
            payload["operational_contract"] = self.operational_contract.to_dict()
        return payload


@dataclass(frozen=True)
class ComponentDeclaration:
    component_id: str
    component_version: str
    profile_version: str
    failure_posture: str
    capabilities: tuple[CapabilityDeclaration, ...]
    enabled: bool = True
    runtime_ref: str = ""
    provenance_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.component_id or not self.component_version or not self.profile_version:
            raise ValueError("component identity, component version, and profile version are required")
        seen: set[tuple[str, str]] = set()
        for capability in self.capabilities:
            identity = (capability.capability_id, capability.capability_version)
            if identity in seen:
                raise ValueError(f"duplicate capability declaration: {identity}")
            seen.add(identity)

        if self.profile_version in {"component-capability-v2", "component-capability-v3"}:
            missing_behavior = [
                capability.capability_id
                for capability in self.capabilities
                if capability.behavior_contract is None
            ]
            if missing_behavior:
                raise ValueError(
                    f"{self.profile_version} requires behavior_contract for every capability: "
                    f"{missing_behavior}"
                )

        if self.profile_version == "component-capability-v3":
            missing_operational = [
                capability.capability_id
                for capability in self.capabilities
                if capability.operational_contract is None
            ]
            if missing_operational:
                raise ValueError(
                    "component-capability-v3 requires operational_contract for every capability: "
                    f"{missing_operational}"
                )

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "ComponentDeclaration":
        raw_capabilities = value.get("capabilities", ())
        if not isinstance(raw_capabilities, (list, tuple)):
            raise ValueError("component capabilities must be an array")
        return cls(
            component_id=str(value["component_id"]),
            component_version=str(value["component_version"]),
            profile_version=str(value["profile_version"]),
            failure_posture=str(value["failure_posture"]),
            capabilities=tuple(CapabilityDeclaration.from_dict(item) for item in raw_capabilities),
            enabled=bool(value.get("enabled", True)),
            runtime_ref=str(value.get("runtime_ref", "")),
            provenance_refs=tuple(str(item) for item in value.get("provenance_refs", ())),
        )

    def to_dict(self) -> dict:
        return {
            "component_id": self.component_id,
            "component_version": self.component_version,
            "profile_version": self.profile_version,
            "failure_posture": self.failure_posture,
            "enabled": self.enabled,
            "runtime_ref": self.runtime_ref,
            "provenance_refs": list(self.provenance_refs),
            "capabilities": [capability.to_dict() for capability in self.capabilities],
        }


@dataclass(frozen=True)
class CapabilityRequirement:
    capability_id: str
    minimum_maturity: str
    capability_version: str = ""
    required_state_postures: tuple[str, ...] = ()
    required_scope_postures: tuple[str, ...] = ()
    allowed_components: tuple[str, ...] = ()
    preferred_component: str = ""
    behavior_requirement: CapabilityBehaviorRequirement | None = None
    operational_requirement: CapabilityOperationalRequirement | None = None

    def __post_init__(self) -> None:
        if self.minimum_maturity not in _MATURITY_RANK:
            raise ValueError(f"unknown minimum maturity: {self.minimum_maturity}")


@dataclass(frozen=True)
class ResolvedCapability:
    component_id: str
    component_version: str
    profile_version: str
    capability_id: str
    capability_version: str
    maturity: str
    state_posture: str
    scope_posture: str
    failure_posture: str
    authority_effect: str
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    behavior_contract: CapabilityBehaviorContract | None = None
    operational_contract: CapabilityOperationalContract | None = None

    def to_dict(self) -> dict:
        payload = {
            "component_id": self.component_id,
            "component_version": self.component_version,
            "profile_version": self.profile_version,
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "maturity": self.maturity,
            "state_posture": self.state_posture,
            "scope_posture": self.scope_posture,
            "failure_posture": self.failure_posture,
            "authority_effect": self.authority_effect,
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
        }
        if self.behavior_contract is not None:
            payload["behavior_contract"] = self.behavior_contract.to_dict()
        if self.operational_contract is not None:
            payload["operational_contract"] = self.operational_contract.to_dict()
        return payload


@dataclass
class ComponentRegistry:
    """Deterministic registry for independently matured capabilities.

    Registration order is intentionally irrelevant. If several providers remain
    eligible after all explicit constraints, resolution fails unless a preferred
    provider is configured. That is safer than first-match folklore.
    """

    preferences: Mapping[str, str] = field(default_factory=dict)
    _components: dict[str, ComponentDeclaration] = field(default_factory=dict, init=False)

    def register(self, component: ComponentDeclaration) -> None:
        existing = self._components.get(component.component_id)
        if existing is not None and existing.component_version == component.component_version:
            raise ValueError(
                f"component already registered at version {component.component_version}: {component.component_id}"
            )
        self._components[component.component_id] = component

    def register_many(self, components: Iterable[ComponentDeclaration]) -> None:
        for component in components:
            self.register(component)

    def resolve(self, requirement: CapabilityRequirement) -> ResolvedCapability:
        eligible: list[tuple[ComponentDeclaration, CapabilityDeclaration]] = []
        allowed = set(requirement.allowed_components)
        for component in self._components.values():
            if not component.enabled:
                continue
            if allowed and component.component_id not in allowed:
                continue
            for capability in component.capabilities:
                if not capability.enabled or capability.capability_id != requirement.capability_id:
                    continue
                if requirement.capability_version and capability.capability_version != requirement.capability_version:
                    continue
                if not maturity_satisfies(capability.maturity, requirement.minimum_maturity):
                    continue
                if requirement.required_state_postures and capability.state_posture not in requirement.required_state_postures:
                    continue
                if requirement.required_scope_postures and capability.scope_posture not in requirement.required_scope_postures:
                    continue
                if requirement.behavior_requirement is not None:
                    if capability.behavior_contract is None:
                        continue
                    if not requirement.behavior_requirement.matches(capability.behavior_contract):
                        continue
                if requirement.operational_requirement is not None:
                    if capability.operational_contract is None:
                        continue
                    if not requirement.operational_requirement.matches(capability.operational_contract):
                        continue
                eligible.append((component, capability))

        preferred = requirement.preferred_component or self.preferences.get(requirement.capability_id, "")
        if preferred:
            matches = [pair for pair in eligible if pair[0].component_id == preferred]
            if len(matches) != 1:
                raise CapabilityResolutionError(
                    f"preferred provider {preferred!r} is not eligible for {requirement.capability_id!r} "
                    f"at minimum maturity {requirement.minimum_maturity!r}"
                )
            return _resolved(*matches[0])

        if not eligible:
            raise CapabilityResolutionError(
                f"no eligible provider for {requirement.capability_id!r} at minimum maturity "
                f"{requirement.minimum_maturity!r}"
            )
        if len(eligible) > 1:
            providers = sorted(pair[0].component_id for pair in eligible)
            raise AmbiguousCapabilityError(
                f"ambiguous providers for {requirement.capability_id!r}: {providers}; configure explicit preference"
            )
        return _resolved(*eligible[0])

    def resolve_many(self, requirements: Iterable[CapabilityRequirement]) -> tuple[ResolvedCapability, ...]:
        return tuple(self.resolve(requirement) for requirement in requirements)

    def component(self, component_id: str) -> ComponentDeclaration | None:
        return self._components.get(component_id)


def maturity_satisfies(actual: str, minimum: str) -> bool:
    try:
        return _MATURITY_RANK[actual] >= _MATURITY_RANK[minimum]
    except KeyError as exc:
        raise ValueError(f"unknown maturity: {exc.args[0]}") from exc


def _resolved(component: ComponentDeclaration, capability: CapabilityDeclaration) -> ResolvedCapability:
    return ResolvedCapability(
        component_id=component.component_id,
        component_version=component.component_version,
        profile_version=component.profile_version,
        capability_id=capability.capability_id,
        capability_version=capability.capability_version,
        maturity=capability.maturity,
        state_posture=capability.state_posture,
        scope_posture=capability.scope_posture,
        failure_posture=capability.failure_posture,
        authority_effect=capability.authority_effect,
        evidence_refs=capability.evidence_refs,
        limitations=capability.limitations,
        behavior_contract=capability.behavior_contract,
        operational_contract=capability.operational_contract,
    )
