"""Real provider substitution proof for qualified resource artifact memory.

This module consumes persisted Capability Qualification v1.2 records. It does
not select providers by implementation resemblance and it never grants recall,
mutation, or action authority. Each provider must independently satisfy the
same explicit capability requirement before substitution evidence is emitted.
"""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Mapping

from .capabilities import (
    CapabilityBehaviorContract,
    CapabilityBehaviorRequirement,
    CapabilityOperationalContract,
    CapabilityOperationalRequirement,
    CapabilityRequirement,
    ComponentDeclaration,
)
from .qualification import (
    AdapterResult,
    QualificationError,
    QualificationRecord,
    QualificationRuntime,
    QualificationSubject,
    QualifiedCapabilityContract,
    prove_provider_substitution,
)

RESOURCE_CAPABILITY_ID = "resource_artifact_memory"
RESOURCE_CAPABILITY_VERSION = "1.0"


def resource_artifact_substitution_requirement() -> CapabilityRequirement:
    """Common boundary independently satisfied by Hindsight and MemOS.

    Atomicity and concurrency are intentionally unconstrained. Neither provider
    has earned stronger fault/concurrency evidence in the bounded fixtures.
    """

    return CapabilityRequirement(
        capability_id=RESOURCE_CAPABILITY_ID,
        capability_version=RESOURCE_CAPABILITY_VERSION,
        minimum_maturity="evidence_proven",
        required_state_postures=("derived",),
        required_scope_postures=("external_scope_bridge",),
        behavior_requirement=CapabilityBehaviorRequirement(
            write=True,
            read=True,
            recall_candidate=True,
            currentness_models=("provider_revalidated",),
            invalidation_models=("provider_revalidation", "explicit_signal"),
            correction_models=("provider_revalidation",),
            deletion_models=("provider_revalidation",),
            residue_models=("scan_required",),
            migration_rebuild_models=("requires_requalification",),
            structural_mutation_requirements=("none",),
        ),
        operational_requirement=CapabilityOperationalRequirement(
            idempotency=("durable_keyed",),
            restart_recovery=("reconstructable", "checkpoint_replay"),
            reconciliation=("deterministic_readback", "authoritative_rebuild"),
        ),
    )


def load_component(path: Path) -> ComponentDeclaration:
    return ComponentDeclaration.from_dict(json.loads(path.read_text(encoding="utf-8")))


def load_qualification_snapshot(path: Path) -> QualificationRecord:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise QualificationError("qualification snapshot must be an object")
    payload = value.get("qualification", value)
    if not isinstance(payload, Mapping):
        raise QualificationError("qualification snapshot does not contain a qualification object")
    record = qualification_record_from_dict(payload)
    source = value.get("source")
    if isinstance(source, Mapping):
        expected = source.get("applicability_digest")
        if expected is not None and expected != record.applicability_digest:
            raise QualificationError("qualification snapshot source applicability digest does not match record")
    return record


def qualification_record_from_dict(value: Mapping[str, object]) -> QualificationRecord:
    """Strictly reconstruct one persisted v1.2 qualification record.

    Recomputing the applicability digest makes persisted qualification evidence
    tamper-evident at the semantic boundary used by provider substitution.
    """

    if value.get("schema_version") != "1.2.0":
        raise QualificationError("real provider substitution requires Capability Qualification v1.2")

    subject_raw = _mapping(value.get("subject"), "subject")
    subject = QualificationSubject(
        component_id=_string(subject_raw, "component_id"),
        component_version=_string(subject_raw, "component_version"),
        implementation_ref=_string(subject_raw, "implementation_ref"),
        capability_id=_string(subject_raw, "capability_id"),
        capability_version=_string(subject_raw, "capability_version"),
        adapter_id=_string(subject_raw, "adapter_id"),
        adapter_version=_string(subject_raw, "adapter_version"),
        qualification_profile_id=_string(subject_raw, "qualification_profile_id"),
        qualification_profile_version=_string(subject_raw, "qualification_profile_version"),
    )

    runtime_raw = _mapping(value.get("runtime"), "runtime")
    runtime = QualificationRuntime(
        configuration_digest=_string(runtime_raw, "configuration_digest"),
        fixture_id=_string(runtime_raw, "fixture_id"),
        fixture_digest=_string(runtime_raw, "fixture_digest"),
        dependency_refs=_strings(runtime_raw.get("dependency_refs")),
        runtime_refs=_strings(runtime_raw.get("runtime_refs")),
    )

    contract_raw = _mapping(value.get("qualified_contract"), "qualified_contract")
    behavior_raw = _mapping(contract_raw.get("behavior_contract"), "qualified_contract.behavior_contract")
    operational_raw = _mapping(contract_raw.get("operational_contract"), "qualified_contract.operational_contract")
    contract = QualifiedCapabilityContract(
        component_profile_version=_string(contract_raw, "component_profile_version"),
        state_posture=_string(contract_raw, "state_posture"),
        scope_posture=_string(contract_raw, "scope_posture"),
        failure_posture=_string(contract_raw, "failure_posture"),
        authority_effect=_string(contract_raw, "authority_effect"),
        behavior_contract=CapabilityBehaviorContract.from_dict(behavior_raw),
        operational_contract=CapabilityOperationalContract.from_dict(operational_raw),
    )

    source_rights = _mapping(value.get("source_rights"), "source_rights")
    evidence = _mapping(value.get("evidence"), "evidence")
    result = _mapping(value.get("result"), "result")
    adapter_results = tuple(
        _adapter_result_from_dict(subject, _mapping(item, "evidence.adapter_results[]"))
        for item in _sequence(evidence.get("adapter_results"), "evidence.adapter_results")
    )
    checks = tuple(
        (
            _string(check, "check_id"),
            _boolean(check, "passed"),
            _string(check, "evidence_ref"),
        )
        for check in (
            _mapping(item, "evidence.checks[]")
            for item in _sequence(evidence.get("checks"), "evidence.checks")
        )
    )

    record = QualificationRecord(
        subject=subject,
        runtime=runtime,
        license_id=_string(source_rights, "license_id"),
        license_ref=_string(source_rights, "license_ref"),
        use_posture=_string(source_rights, "use_posture"),
        operations=_strings(evidence.get("operations")),
        raw_provider_refs=_strings(evidence.get("raw_provider_refs")),
        normalized_refs=_strings(evidence.get("normalized_refs")),
        checks=checks,
        artifact_digests=_strings(evidence.get("artifact_digests")),
        maturity_before=_string(result, "maturity_before"),
        profile_maturity_ceiling=_string(result, "profile_maturity_ceiling"),
        earned_maturity=_string(result, "earned_maturity"),
        adapter_results=adapter_results,
        limitations=_strings(result.get("limitations")),
        qualification_current=_boolean(result, "qualification_current"),
        qualified_contract=contract,
    )
    stored_digest = _string(result, "applicability_digest")
    if record.applicability_digest != stored_digest:
        raise QualificationError("persisted qualification applicability digest does not match reconstructed record")
    if record.authority_effect != "none" or _string(result, "authority_effect") != "none":
        raise QualificationError("persisted provider qualification cannot grant authority")
    return record


def prove_resource_artifact_substitution(
    *,
    primary_component: ComponentDeclaration,
    primary_qualification: QualificationRecord,
    replacement_component: ComponentDeclaration,
    replacement_qualification: QualificationRecord,
) -> dict[str, object]:
    requirement = resource_artifact_substitution_requirement()
    evidence = prove_provider_substitution(
        primary_component=primary_component,
        primary_qualification=primary_qualification,
        replacement_component=replacement_component,
        replacement_qualification=replacement_qualification,
        requirement=requirement,
    )
    return {
        "requirement": {
            "capability_id": requirement.capability_id,
            "capability_version": requirement.capability_version,
            "minimum_maturity": requirement.minimum_maturity,
            "required_state_postures": list(requirement.required_state_postures),
            "required_scope_postures": list(requirement.required_scope_postures),
            "behavior_requirement": requirement.behavior_requirement.to_dict()
            if requirement.behavior_requirement
            else None,
            "operational_requirement": requirement.operational_requirement.to_dict()
            if requirement.operational_requirement
            else None,
        },
        "substitution": evidence.to_dict(),
        "authority_effect": "none",
    }


def qualification_with_use_posture(record: QualificationRecord, use_posture: str) -> QualificationRecord:
    """Test helper for adversarial source-rights substitution proofs."""
    return replace(record, use_posture=use_posture)


def _adapter_result_from_dict(subject: QualificationSubject, value: Mapping[str, object]) -> AdapterResult:
    if _string(value, "authority_effect") != "none":
        raise QualificationError("persisted adapter result cannot grant authority")
    return AdapterResult(
        subject=subject,
        operation=_string(value, "operation"),
        runtime_identity=_string(value, "runtime_identity"),
        input_refs=_strings(value.get("input_refs")),
        raw_provider_refs=_strings(value.get("raw_provider_refs")),
        normalized_refs=_strings(value.get("normalized_refs")),
        currentness=_string(value, "currentness"),
        failure_result=_string(value, "failure_result"),
        trace_ref=_string(value, "trace_ref"),
    )


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise QualificationError(f"{name} must be an object")
    return value


def _sequence(value: object, name: str) -> tuple[object, ...]:
    if not isinstance(value, (list, tuple)):
        raise QualificationError(f"{name} must be an array")
    return tuple(value)


def _strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    items = _sequence(value, "string array")
    if any(not isinstance(item, str) or not item for item in items):
        raise QualificationError("string array values must be non-empty strings")
    return tuple(items)  # type: ignore[return-value]


def _string(value: Mapping[str, object], key: str) -> str:
    raw = value.get(key)
    if not isinstance(raw, str) or not raw:
        raise QualificationError(f"{key} must be a non-empty string")
    return raw


def _boolean(value: Mapping[str, object], key: str) -> bool:
    raw = value.get(key)
    if not isinstance(raw, bool):
        raise QualificationError(f"{key} must be boolean")
    return raw
