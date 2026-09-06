from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema

from agentmem_ref.capabilities import (
    CapabilityBehaviorContract,
    CapabilityBehaviorRequirement,
    CapabilityDeclaration,
    CapabilityOperationalContract,
    CapabilityOperationalRequirement,
    CapabilityRequirement,
    ComponentDeclaration,
)
from agentmem_ref.qualification import (
    AdapterResult,
    QualificationError,
    QualificationRuntime,
    QualificationSubject,
    QualifiedCapabilityContract,
    StaleQualificationError,
    applicability_digest,
    prove_provider_substitution,
    qualification_from_adapter_results,
)

ROOT = Path(__file__).resolve().parents[2]
CAPABILITY_ID = "epistemic_belief_memory"
CAPABILITY_VERSION = "1.0"


def behavior(*, correction_model: str = "invalidate_derived") -> CapabilityBehaviorContract:
    return CapabilityBehaviorContract(
        write=True,
        read=True,
        recall_candidate=True,
        currentness_model="basis_versioned",
        invalidation_model="version_relation",
        correction_model=correction_model,
        deletion_model="derived_residue_then_purge",
        residue_model="scan_required",
        migration_rebuild_model="requires_requalification",
        structural_mutation_requirement="none",
    )


def durable_a() -> CapabilityOperationalContract:
    return CapabilityOperationalContract(
        write_atomicity="single_record_atomic",
        concurrency_control="optimistic_revision",
        idempotency="durable_keyed",
        restart_recovery="reconstructable",
        reconciliation="deterministic_readback",
    )


def durable_b() -> CapabilityOperationalContract:
    return CapabilityOperationalContract(
        write_atomicity="transactional_multi_record",
        concurrency_control="serializable",
        idempotency="durable_keyed",
        restart_recovery="checkpoint_replay",
        reconciliation="authoritative_rebuild",
    )


def process_local() -> CapabilityOperationalContract:
    return CapabilityOperationalContract(
        write_atomicity="process_local",
        concurrency_control="process_local",
        idempotency="process_local",
        restart_recovery="process_local_only",
        reconciliation="process_local_only",
    )


def component(
    component_id: str,
    operational: CapabilityOperationalContract,
    *,
    capability_behavior: CapabilityBehaviorContract | None = None,
    authority_effect: str = "none",
    version: str = "1.0.0",
) -> ComponentDeclaration:
    return ComponentDeclaration(
        component_id=component_id,
        component_version=version,
        profile_version="component-capability-v3",
        failure_posture="fail_closed",
        runtime_ref=f"synthetic://{component_id}",
        capabilities=(
            CapabilityDeclaration(
                capability_id=CAPABILITY_ID,
                capability_version=CAPABILITY_VERSION,
                maturity="evidence_proven",
                state_posture="derived",
                scope_posture="enforces_agent_memory_scope",
                failure_posture="fail_closed",
                authority_effect=authority_effect,
                behavior_contract=capability_behavior or behavior(),
                operational_contract=operational,
            ),
        ),
    )


def subject(value: ComponentDeclaration) -> QualificationSubject:
    return QualificationSubject(
        component_id=value.component_id,
        component_version=value.component_version,
        implementation_ref=f"synthetic:{value.component_id}@{value.component_version}",
        capability_id=CAPABILITY_ID,
        capability_version=CAPABILITY_VERSION,
        adapter_id="synthetic-epistemic-adapter",
        adapter_version="1.0.0",
        qualification_profile_id="epistemic-portability-v1",
        qualification_profile_version="1.0.0",
    )


def runtime(value: ComponentDeclaration) -> QualificationRuntime:
    marker = value.component_id.encode("utf-8").hex()[:8].ljust(8, "0")
    return QualificationRuntime(
        configuration_digest="sha256:" + (marker * 8)[:64],
        fixture_id="epistemic-portability-v1",
        fixture_digest="sha256:" + "b" * 64,
        dependency_refs=("python:stdlib",),
        runtime_refs=("synthetic-reference",),
    )


def record(value: ComponentDeclaration, *, use_posture: str = "runtime_allowed"):
    qsubject = subject(value)
    qruntime = runtime(value)
    adapter = AdapterResult(
        subject=qsubject,
        operation="retain_and_revise_belief",
        runtime_identity=f"runtime:{value.component_id}",
        input_refs=("fixture:belief:001",),
        raw_provider_refs=(f"artifact:{value.component_id}:raw",),
        normalized_refs=(f"artifact:{value.component_id}:normalized",),
        currentness="current",
        failure_result="none",
        trace_ref=f"trace:{value.component_id}",
    )
    return qualification_from_adapter_results(
        subject=qsubject,
        runtime=qruntime,
        license_id="Apache-2.0",
        license_ref=f"synthetic:{value.component_id}:LICENSE",
        use_posture=use_posture,
        results=(adapter,),
        checks=(
            ("belief-kind-preserved", True, f"artifact:{value.component_id}:normalized"),
            ("confidence-non-authoritative", True, f"artifact:{value.component_id}:normalized"),
            ("operational-posture-observed", True, f"artifact:{value.component_id}:raw"),
        ),
        artifact_digests=("sha256:" + "c" * 64,),
        maturity_before="runtime_wired",
        profile_maturity_ceiling="evidence_proven",
        earned_maturity="evidence_proven",
        qualified_contract=QualifiedCapabilityContract.from_component(
            value,
            capability_id=CAPABILITY_ID,
            capability_version=CAPABILITY_VERSION,
        ),
    )


def durable_requirement() -> CapabilityRequirement:
    return CapabilityRequirement(
        capability_id=CAPABILITY_ID,
        capability_version=CAPABILITY_VERSION,
        minimum_maturity="evidence_proven",
        required_state_postures=("derived",),
        required_scope_postures=("enforces_agent_memory_scope",),
        behavior_requirement=CapabilityBehaviorRequirement(
            write=True,
            read=True,
            recall_candidate=True,
            currentness_models=("basis_versioned",),
            correction_models=("invalidate_derived",),
        ),
        operational_requirement=CapabilityOperationalRequirement(
            write_atomicity=("single_record_atomic", "transactional_multi_record"),
            concurrency_control=("optimistic_revision", "serializable"),
            idempotency=("durable_keyed",),
            restart_recovery=("reconstructable", "checkpoint_replay"),
            reconciliation=("deterministic_readback", "authoritative_rebuild"),
        ),
    )


class QualificationV12Tests(unittest.TestCase):
    def schema(self) -> dict:
        return json.loads(
            (ROOT / "schemas" / "component-capability-qualification.schema.json").read_text(
                encoding="utf-8"
            )
        )

    def test_legacy_v11_record_remains_schema_valid(self) -> None:
        value = component("external-a", durable_a())
        qsubject = subject(value)
        adapter = AdapterResult(
            subject=qsubject,
            operation="query",
            runtime_identity="legacy-runtime",
            input_refs=("fixture",),
            raw_provider_refs=("raw",),
            normalized_refs=("normalized",),
            currentness="current",
            failure_result="none",
            trace_ref="trace",
        )
        legacy = qualification_from_adapter_results(
            subject=qsubject,
            runtime=runtime(value),
            license_id="Apache-2.0",
            license_ref="legacy-license",
            use_posture="runtime_allowed",
            results=(adapter,),
            checks=(("legacy-positive", True, "normalized"),),
            artifact_digests=("sha256:" + "d" * 64,),
            maturity_before="runtime_wired",
            profile_maturity_ceiling="evidence_proven",
            earned_maturity="evidence_proven",
        ).to_dict()

        self.assertEqual("1.1.0", legacy["schema_version"])
        jsonschema.Draft202012Validator(self.schema()).validate(legacy)
        self.assertNotIn("qualified_contract", legacy)

    def test_v12_record_requires_and_serializes_qualified_contract(self) -> None:
        value = component("external-a", durable_a())
        payload = record(value).to_dict()

        self.assertEqual("1.2.0", payload["schema_version"])
        self.assertEqual(
            "component-capability-v3",
            payload["qualified_contract"]["component_profile_version"],
        )
        self.assertEqual(
            "reconstructable",
            payload["qualified_contract"]["operational_contract"]["restart_recovery"],
        )
        jsonschema.Draft202012Validator(self.schema()).validate(payload)

        broken = dict(payload)
        broken.pop("qualified_contract")
        with self.assertRaises(jsonschema.ValidationError):
            jsonschema.Draft202012Validator(self.schema()).validate(broken)

    def test_behavior_or_operational_drift_changes_applicability(self) -> None:
        original = component("external-a", durable_a())
        qrecord = record(original)
        original_digest = qrecord.applicability_digest

        changed_behavior = component(
            "external-a",
            durable_a(),
            capability_behavior=behavior(correction_model="provider_revalidation"),
        )
        changed_behavior_contract = QualifiedCapabilityContract.from_component(
            changed_behavior,
            capability_id=CAPABILITY_ID,
            capability_version=CAPABILITY_VERSION,
        )
        self.assertNotEqual(
            original_digest,
            applicability_digest(subject(original), runtime(original), changed_behavior_contract),
        )

        changed_operational = component("external-a", durable_b())
        with self.assertRaises(StaleQualificationError):
            qrecord.assert_current_declaration(changed_operational)

    def test_legacy_record_cannot_be_used_as_v3_contract_qualification(self) -> None:
        value = component("external-a", durable_a())
        qsubject = subject(value)
        adapter = AdapterResult(
            subject=qsubject,
            operation="query",
            runtime_identity="legacy-runtime",
            input_refs=("fixture",),
            raw_provider_refs=("raw",),
            normalized_refs=("normalized",),
            currentness="current",
            failure_result="none",
            trace_ref="trace",
        )
        legacy = qualification_from_adapter_results(
            subject=qsubject,
            runtime=runtime(value),
            license_id="Apache-2.0",
            license_ref="legacy-license",
            use_posture="runtime_allowed",
            results=(adapter,),
            checks=(("legacy-positive", True, "normalized"),),
            artifact_digests=("sha256:" + "e" * 64,),
            maturity_before="runtime_wired",
            profile_maturity_ceiling="evidence_proven",
            earned_maturity="evidence_proven",
        )
        contract = QualifiedCapabilityContract.from_component(
            value,
            capability_id=CAPABILITY_ID,
            capability_version=CAPABILITY_VERSION,
        )
        with self.assertRaises(StaleQualificationError):
            legacy.assert_applicable(qsubject, runtime(value), contract)

    def test_differently_implemented_durable_providers_are_substitutable(self) -> None:
        first = component("external-durable-a", durable_a())
        second = component("external-durable-b", durable_b())

        evidence = prove_provider_substitution(
            primary_component=first,
            primary_qualification=record(first),
            replacement_component=second,
            replacement_qualification=record(second),
            requirement=durable_requirement(),
        )

        self.assertEqual("external-durable-a", evidence.primary_component)
        self.assertEqual("external-durable-b", evidence.replacement_component)
        self.assertEqual("none", evidence.provider_authority_effect)
        self.assertEqual("none", evidence.authority_effect)
        self.assertNotEqual(
            first.capabilities[0].operational_contract,
            second.capabilities[0].operational_contract,
        )

    def test_process_local_provider_fails_durable_requirement(self) -> None:
        durable = component("external-durable-a", durable_a())
        local = component("external-local", process_local())

        with self.assertRaisesRegex(QualificationError, "operational contract"):
            prove_provider_substitution(
                primary_component=durable,
                primary_qualification=record(durable),
                replacement_component=local,
                replacement_qualification=record(local),
                requirement=durable_requirement(),
            )

    def test_runtime_substitution_requires_runtime_allowed_source_rights(self) -> None:
        first = component("external-durable-a", durable_a())
        second = component("external-durable-b", durable_b())

        with self.assertRaisesRegex(QualificationError, "runtime-allowed"):
            prove_provider_substitution(
                primary_component=first,
                primary_qualification=record(first),
                replacement_component=second,
                replacement_qualification=record(second, use_posture="comparator_only"),
                requirement=durable_requirement(),
            )

    def test_authority_posture_cannot_change_during_substitution(self) -> None:
        first = component("external-durable-a", durable_a(), authority_effect="none")
        second = component("external-durable-b", durable_b(), authority_effect="proposal_only")

        with self.assertRaisesRegex(QualificationError, "authority posture"):
            prove_provider_substitution(
                primary_component=first,
                primary_qualification=record(first),
                replacement_component=second,
                replacement_qualification=record(second),
                requirement=durable_requirement(),
            )

    def test_substitution_evidence_is_non_authoritative(self) -> None:
        first = component("external-durable-a", durable_a())
        second = component("external-durable-b", durable_b())
        evidence = prove_provider_substitution(
            primary_component=first,
            primary_qualification=record(first),
            replacement_component=second,
            replacement_qualification=record(second),
            requirement=durable_requirement(),
        ).to_dict()

        self.assertEqual("none", evidence["authority_effect"])
        self.assertTrue(evidence["requirement_digest"].startswith("sha256:"))
        self.assertNotEqual(
            evidence["primary_qualification_digest"],
            evidence["replacement_qualification_digest"],
        )


if __name__ == "__main__":
    unittest.main()
