"""Version-bound component capability qualification helpers.

Qualification records describe behavior proven by an exact implementation and
adapter profile. They never grant memory mutation, structural, recall-admission,
or action authority.

Qualification v1.2 extends the #300 evidence contract with Capability Contract
v3 behavior/operational bindings. Historical v1.1 records remain valid evidence,
but cannot silently stand in for v3 operational qualification.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

from .capabilities import (
    MATURITY_ORDER,
    CapabilityBehaviorContract,
    CapabilityOperationalContract,
    CapabilityRequirement,
    ComponentDeclaration,
    maturity_satisfies,
)

LEGACY_QUALIFICATION_SCHEMA_VERSION = "1.1.0"
QUALIFICATION_SCHEMA_VERSION = "1.2.0"


class QualificationError(ValueError):
    """Qualification evidence is invalid or not applicable."""


class StaleQualificationError(QualificationError):
    """A qualification record does not apply to the requested exact subject."""


@dataclass(frozen=True)
class QualificationSubject:
    component_id: str
    component_version: str
    implementation_ref: str
    capability_id: str
    capability_version: str
    adapter_id: str
    adapter_version: str
    qualification_profile_id: str
    qualification_profile_version: str

    def __post_init__(self) -> None:
        for name, value in self.to_dict().items():
            if not value:
                raise ValueError(f"{name} is required")

    def to_dict(self) -> dict[str, str]:
        return {
            "component_id": self.component_id,
            "component_version": self.component_version,
            "implementation_ref": self.implementation_ref,
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "adapter_id": self.adapter_id,
            "adapter_version": self.adapter_version,
            "qualification_profile_id": self.qualification_profile_id,
            "qualification_profile_version": self.qualification_profile_version,
        }


@dataclass(frozen=True)
class QualificationRuntime:
    configuration_digest: str
    fixture_id: str
    fixture_digest: str
    dependency_refs: tuple[str, ...] = ()
    runtime_refs: tuple[str, ...] = ()

    def applicability_dict(self) -> dict[str, object]:
        return {
            "configuration_digest": self.configuration_digest,
            "fixture_id": self.fixture_id,
            "fixture_digest": self.fixture_digest,
            "dependency_refs": list(self.dependency_refs),
            "runtime_refs": list(self.runtime_refs),
        }


@dataclass(frozen=True)
class QualifiedCapabilityContract:
    """Exact v2/v3 capability posture proven by a qualification run.

    The contract is part of qualification applicability. Changing behavior or
    substrate operational guarantees therefore requires explicit compatibility
    evidence or requalification even when component/runtime strings stay fixed.
    """

    component_profile_version: str
    state_posture: str
    scope_posture: str
    failure_posture: str
    authority_effect: str
    behavior_contract: CapabilityBehaviorContract
    operational_contract: CapabilityOperationalContract | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("component_profile_version", self.component_profile_version),
            ("state_posture", self.state_posture),
            ("scope_posture", self.scope_posture),
            ("failure_posture", self.failure_posture),
        ):
            if not value:
                raise QualificationError(f"qualified capability {name} is required")
        if self.authority_effect not in {"none", "proposal_only"}:
            raise QualificationError("qualified capability authority_effect must be none or proposal_only")
        if self.component_profile_version == "component-capability-v3" and self.operational_contract is None:
            raise QualificationError("component-capability-v3 qualification requires operational_contract")

    @classmethod
    def from_component(
        cls,
        component: ComponentDeclaration,
        *,
        capability_id: str,
        capability_version: str,
    ) -> "QualifiedCapabilityContract":
        matches = [
            capability
            for capability in component.capabilities
            if capability.capability_id == capability_id
            and capability.capability_version == capability_version
        ]
        if len(matches) != 1:
            raise QualificationError(
                f"component {component.component_id!r} does not expose exactly one "
                f"{capability_id!r}@{capability_version!r} capability"
            )
        capability = matches[0]
        if capability.behavior_contract is None:
            raise QualificationError("qualified capability requires behavior_contract")
        return cls(
            component_profile_version=component.profile_version,
            state_posture=capability.state_posture,
            scope_posture=capability.scope_posture,
            failure_posture=capability.failure_posture,
            authority_effect=capability.authority_effect,
            behavior_contract=capability.behavior_contract,
            operational_contract=capability.operational_contract,
        )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "component_profile_version": self.component_profile_version,
            "state_posture": self.state_posture,
            "scope_posture": self.scope_posture,
            "failure_posture": self.failure_posture,
            "authority_effect": self.authority_effect,
            "behavior_contract": self.behavior_contract.to_dict(),
        }
        if self.operational_contract is not None:
            payload["operational_contract"] = self.operational_contract.to_dict()
        return payload


@dataclass(frozen=True)
class AdapterResult:
    """Provider-neutral envelope preserving native and normalized evidence refs."""

    subject: QualificationSubject
    operation: str
    runtime_identity: str
    input_refs: tuple[str, ...]
    raw_provider_refs: tuple[str, ...]
    normalized_refs: tuple[str, ...]
    currentness: str
    failure_result: str
    trace_ref: str

    def __post_init__(self) -> None:
        if not self.operation or not self.runtime_identity or not self.trace_ref:
            raise ValueError("operation, runtime identity, and trace reference are required")
        if not self.currentness:
            raise ValueError("adapter currentness posture is required")
        if not self.failure_result:
            raise ValueError("adapter failure result is required")
        if not self.raw_provider_refs:
            raise ValueError("raw provider evidence must be preserved")
        if not self.normalized_refs:
            raise ValueError("normalized evidence reference is required")

    @property
    def authority_effect(self) -> str:
        return "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "operation": self.operation,
            "runtime_identity": self.runtime_identity,
            "input_refs": list(self.input_refs),
            "raw_provider_refs": list(self.raw_provider_refs),
            "normalized_refs": list(self.normalized_refs),
            "currentness": self.currentness,
            "failure_result": self.failure_result,
            "trace_ref": self.trace_ref,
            "authority_effect": "none",
        }


@dataclass(frozen=True)
class QualificationRecord:
    subject: QualificationSubject
    runtime: QualificationRuntime
    license_id: str
    license_ref: str
    use_posture: str
    operations: tuple[str, ...]
    raw_provider_refs: tuple[str, ...]
    normalized_refs: tuple[str, ...]
    checks: tuple[tuple[str, bool, str], ...]
    artifact_digests: tuple[str, ...]
    maturity_before: str
    profile_maturity_ceiling: str
    earned_maturity: str
    adapter_results: tuple[AdapterResult, ...] = ()
    limitations: tuple[str, ...] = ()
    qualification_current: bool = True
    qualified_contract: QualifiedCapabilityContract | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("maturity_before", self.maturity_before),
            ("profile_maturity_ceiling", self.profile_maturity_ceiling),
            ("earned_maturity", self.earned_maturity),
        ):
            if value not in MATURITY_ORDER:
                raise ValueError(f"unknown {name}: {value}")
        if not maturity_satisfies(self.profile_maturity_ceiling, self.earned_maturity):
            raise QualificationError("earned maturity exceeds the qualification profile ceiling")
        if not self.license_id or not self.license_ref:
            raise QualificationError("source-rights license identity and exact reference are required")
        if self.use_posture not in {"runtime_allowed", "comparator_only", "disallowed"}:
            raise ValueError("unknown source-rights use posture")
        if self.use_posture == "disallowed" and self.qualification_current:
            raise QualificationError("disallowed source cannot produce a current qualification")
        if not self.operations:
            raise QualificationError("qualification must exercise at least one operation")
        if not self.raw_provider_refs or not self.normalized_refs or not self.artifact_digests:
            raise QualificationError("qualification must preserve raw, normalized, and digest evidence")
        for result in self.adapter_results:
            if result.subject != self.subject:
                raise QualificationError("stored adapter result subject does not match qualification subject")
            if result.authority_effect != "none":
                raise QualificationError("stored adapter result cannot grant authority")
        if self.earned_maturity == "reference_qualified":
            if self.profile_maturity_ceiling != "reference_qualified":
                raise QualificationError("reference_qualified requires an explicit reference-qualified profile ceiling")
            if self.use_posture != "runtime_allowed":
                raise QualificationError("reference_qualified requires runtime-allowed source rights")
            if not self.checks or not all(passed for _, passed, _ in self.checks):
                raise QualificationError("reference_qualified requires every required profile check to pass")
            if not self.adapter_results:
                raise QualificationError("reference_qualified requires reconstructable adapter-result evidence")

    @property
    def schema_version(self) -> str:
        return QUALIFICATION_SCHEMA_VERSION if self.qualified_contract is not None else LEGACY_QUALIFICATION_SCHEMA_VERSION

    @property
    def applicability_digest(self) -> str:
        return applicability_digest(self.subject, self.runtime, self.qualified_contract)

    @property
    def authority_effect(self) -> str:
        return "none"

    @property
    def failure_results(self) -> tuple[str, ...]:
        """Failure outcomes preserved by the exact qualification run."""
        return tuple(result.failure_result for result in self.adapter_results)

    def assert_applicable(
        self,
        subject: QualificationSubject,
        runtime: QualificationRuntime,
        qualified_contract: QualifiedCapabilityContract | None = None,
    ) -> None:
        if (self.qualified_contract is None) != (qualified_contract is None):
            raise StaleQualificationError(
                "qualification contract generation changed; v1.1 evidence cannot substitute for v1.2 contract-bound qualification"
            )
        expected = applicability_digest(subject, runtime, qualified_contract)
        if expected != self.applicability_digest:
            raise StaleQualificationError(
                "qualification applicability changed; explicit compatibility evidence or requalification is required"
            )
        if not self.qualification_current:
            raise StaleQualificationError("qualification is explicitly non-current")

    def assert_current_declaration(self, component: ComponentDeclaration) -> None:
        """Require the current declaration to match the exact contract that was qualified."""
        if self.qualified_contract is None:
            raise StaleQualificationError(
                "legacy qualification has no contract binding; v3 runtime use requires requalification"
            )
        if component.component_id != self.subject.component_id:
            raise StaleQualificationError("qualification component identity changed")
        if component.component_version != self.subject.component_version:
            raise StaleQualificationError("qualification component version changed")
        current_contract = QualifiedCapabilityContract.from_component(
            component,
            capability_id=self.subject.capability_id,
            capability_version=self.subject.capability_version,
        )
        self.assert_applicable(self.subject, self.runtime, current_contract)
        capability = _find_subject_capability(component, self.subject)
        if not maturity_satisfies(capability.maturity, self.earned_maturity):
            raise StaleQualificationError(
                "current capability declaration is below the maturity earned by this qualification"
            )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "subject": self.subject.to_dict(),
            "runtime": self.runtime.applicability_dict(),
            "source_rights": {
                "license_id": self.license_id,
                "license_ref": self.license_ref,
                "use_posture": self.use_posture,
            },
            "evidence": {
                "operations": list(self.operations),
                "raw_provider_refs": list(self.raw_provider_refs),
                "normalized_refs": list(self.normalized_refs),
                "adapter_results": [result.to_dict() for result in self.adapter_results],
                "checks": [
                    {"check_id": check_id, "passed": passed, "evidence_ref": evidence_ref}
                    for check_id, passed, evidence_ref in self.checks
                ],
                "artifact_digests": list(self.artifact_digests),
            },
            "result": {
                "maturity_before": self.maturity_before,
                "profile_maturity_ceiling": self.profile_maturity_ceiling,
                "earned_maturity": self.earned_maturity,
                "applicability_digest": self.applicability_digest,
                "qualification_current": self.qualification_current,
                "authority_effect": "none",
                "limitations": list(self.limitations),
            },
        }
        if self.qualified_contract is not None:
            payload["qualified_contract"] = self.qualified_contract.to_dict()
        return payload


def applicability_digest(
    subject: QualificationSubject,
    runtime: QualificationRuntime,
    qualified_contract: QualifiedCapabilityContract | None = None,
) -> str:
    """Hash the exact qualification applicability boundary using deterministic JSON."""

    payload: dict[str, object] = {
        "subject": subject.to_dict(),
        "runtime": runtime.applicability_dict(),
    }
    if qualified_contract is not None:
        payload["qualified_contract"] = qualified_contract.to_dict()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


def qualification_from_adapter_results(
    *,
    subject: QualificationSubject,
    runtime: QualificationRuntime,
    license_id: str,
    license_ref: str,
    use_posture: str,
    results: Sequence[AdapterResult],
    checks: Sequence[tuple[str, bool, str]],
    artifact_digests: Sequence[str],
    maturity_before: str,
    profile_maturity_ceiling: str,
    earned_maturity: str,
    limitations: Sequence[str] = (),
    qualified_contract: QualifiedCapabilityContract | None = None,
) -> QualificationRecord:
    if not results:
        raise QualificationError("at least one adapter result is required")
    for result in results:
        if result.subject != subject:
            raise QualificationError("adapter result subject does not match qualification subject")
        if result.authority_effect != "none":
            raise QualificationError("adapter result cannot grant authority")
    return QualificationRecord(
        subject=subject,
        runtime=runtime,
        license_id=license_id,
        license_ref=license_ref,
        use_posture=use_posture,
        operations=tuple(dict.fromkeys(result.operation for result in results)),
        raw_provider_refs=tuple(ref for result in results for ref in result.raw_provider_refs),
        normalized_refs=tuple(ref for result in results for ref in result.normalized_refs),
        checks=tuple(checks),
        artifact_digests=tuple(dict.fromkeys(artifact_digests)),
        maturity_before=maturity_before,
        profile_maturity_ceiling=profile_maturity_ceiling,
        earned_maturity=earned_maturity,
        adapter_results=tuple(results),
        limitations=tuple(limitations),
        qualified_contract=qualified_contract,
    )


@dataclass(frozen=True)
class SubstitutionEvidence:
    """Evidence that two qualified providers satisfy one requested capability boundary."""

    primary_component: str
    replacement_component: str
    capability_id: str
    capability_version: str
    requirement_digest: str
    primary_qualification_digest: str
    replacement_qualification_digest: str
    provider_authority_effect: str

    @property
    def authority_effect(self) -> str:
        return "none"

    def to_dict(self) -> dict[str, str]:
        return {
            "primary_component": self.primary_component,
            "replacement_component": self.replacement_component,
            "capability_id": self.capability_id,
            "capability_version": self.capability_version,
            "requirement_digest": self.requirement_digest,
            "primary_qualification_digest": self.primary_qualification_digest,
            "replacement_qualification_digest": self.replacement_qualification_digest,
            "provider_authority_effect": self.provider_authority_effect,
            "authority_effect": "none",
        }


def prove_provider_substitution(
    *,
    primary_component: ComponentDeclaration,
    primary_qualification: QualificationRecord,
    replacement_component: ComponentDeclaration,
    replacement_qualification: QualificationRecord,
    requirement: CapabilityRequirement,
) -> SubstitutionEvidence:
    """Prove qualified runtime substitution without requiring provider internals to match."""
    if primary_component.component_id == replacement_component.component_id:
        raise QualificationError("provider substitution requires distinct component identities")

    primary_capability = _qualified_capability_for_requirement(
        primary_component, primary_qualification, requirement
    )
    replacement_capability = _qualified_capability_for_requirement(
        replacement_component, replacement_qualification, requirement
    )
    if primary_capability.authority_effect != replacement_capability.authority_effect:
        raise QualificationError(
            "provider substitution cannot silently change capability authority posture"
        )

    capability_version = requirement.capability_version or primary_capability.capability_version
    if replacement_capability.capability_version != capability_version:
        raise QualificationError("provider substitution capability versions differ")

    return SubstitutionEvidence(
        primary_component=primary_component.component_id,
        replacement_component=replacement_component.component_id,
        capability_id=requirement.capability_id,
        capability_version=capability_version,
        requirement_digest=_requirement_digest(requirement),
        primary_qualification_digest=primary_qualification.applicability_digest,
        replacement_qualification_digest=replacement_qualification.applicability_digest,
        provider_authority_effect=primary_capability.authority_effect,
    )


def _qualified_capability_for_requirement(
    component: ComponentDeclaration,
    qualification: QualificationRecord,
    requirement: CapabilityRequirement,
):
    qualification.assert_current_declaration(component)
    if qualification.use_posture != "runtime_allowed":
        raise QualificationError("runtime provider substitution requires runtime-allowed source rights")
    if qualification.subject.capability_id != requirement.capability_id:
        raise QualificationError("qualification capability does not match substitution requirement")
    if requirement.capability_version and qualification.subject.capability_version != requirement.capability_version:
        raise QualificationError("qualification capability version does not match substitution requirement")
    if not maturity_satisfies(qualification.earned_maturity, requirement.minimum_maturity):
        raise QualificationError("qualification maturity is below substitution requirement")

    capability = _find_subject_capability(component, qualification.subject)
    if not component.enabled or not capability.enabled:
        raise QualificationError("qualified provider is disabled")
    if requirement.allowed_components and component.component_id not in requirement.allowed_components:
        raise QualificationError("qualified provider is outside allowed component set")
    if requirement.preferred_component and component.component_id != requirement.preferred_component:
        raise QualificationError("qualified provider does not match explicit preferred component")
    if requirement.required_state_postures and capability.state_posture not in requirement.required_state_postures:
        raise QualificationError("qualified provider state posture does not satisfy requirement")
    if requirement.required_scope_postures and capability.scope_posture not in requirement.required_scope_postures:
        raise QualificationError("qualified provider scope posture does not satisfy requirement")
    if requirement.behavior_requirement is not None:
        if capability.behavior_contract is None or not requirement.behavior_requirement.matches(capability.behavior_contract):
            raise QualificationError("qualified provider behavior contract does not satisfy requirement")
    if requirement.operational_requirement is not None:
        if capability.operational_contract is None or not requirement.operational_requirement.matches(capability.operational_contract):
            raise QualificationError("qualified provider operational contract does not satisfy requirement")
    return capability


def _find_subject_capability(component: ComponentDeclaration, subject: QualificationSubject):
    matches = [
        capability
        for capability in component.capabilities
        if capability.capability_id == subject.capability_id
        and capability.capability_version == subject.capability_version
    ]
    if len(matches) != 1:
        raise StaleQualificationError(
            "current component declaration no longer exposes the qualified capability identity"
        )
    return matches[0]


def _requirement_digest(requirement: CapabilityRequirement) -> str:
    payload: dict[str, object] = {
        "capability_id": requirement.capability_id,
        "capability_version": requirement.capability_version,
        "minimum_maturity": requirement.minimum_maturity,
        "required_state_postures": list(requirement.required_state_postures),
        "required_scope_postures": list(requirement.required_scope_postures),
        "allowed_components": list(requirement.allowed_components),
        "preferred_component": requirement.preferred_component,
        "behavior_requirement": (
            requirement.behavior_requirement.to_dict()
            if requirement.behavior_requirement is not None
            else None
        ),
        "operational_requirement": (
            requirement.operational_requirement.to_dict()
            if requirement.operational_requirement is not None
            else None
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()
