from __future__ import annotations

from dataclasses import replace
import json
import unittest
from pathlib import Path

import jsonschema

from agentmem_ref.memos_qualification import (
    MEMOS_COMMIT,
    MEMOS_PACKAGE,
    MEMOS_RELEASE,
    MEMOS_VERSION,
    load_component_profile,
    qualify_memos_local_v2017,
)
from agentmem_ref.qualification import QualificationError
from agentmem_ref.resource_provider_substitution import (
    load_component,
    load_qualification_snapshot,
    prove_resource_artifact_substitution,
    qualification_record_from_dict,
    qualification_with_use_posture,
    resource_artifact_substitution_requirement,
)

ROOT = Path(__file__).resolve().parents[2]
MEMOS_PROFILE = ROOT / "reference" / "fixtures" / "component-capabilities" / "memos-local-plugin-v2.0.17.json"
HINDSIGHT_PROFILE = ROOT / "reference" / "fixtures" / "component-capabilities" / "hindsight-v0.9.0.json"
HINDSIGHT_QUALIFICATION = (
    ROOT
    / "reference"
    / "fixtures"
    / "component-qualification"
    / "hindsight-v0.9.0-resource-artifact-qualified-v12.json"
)
PROFILE_SCHEMA = ROOT / "schemas" / "component-capability-profile.schema.json"
QUALIFICATION_SCHEMA = ROOT / "schemas" / "component-capability-qualification.schema.json"


def passing_raw() -> dict:
    return {
        "identity": {
            "repository": "MemTensor/MemOS",
            "package": MEMOS_PACKAGE,
            "release": MEMOS_RELEASE,
            "version": MEMOS_VERSION,
            "commit": MEMOS_COMMIT,
            "source_license": "Apache-2.0",
            "source_license_verified": True,
            "package_license_metadata": "MIT",
            "license_discrepancy_preserved": True,
        },
        "configuration": {
            "adapter": "direct-memory-core",
            "database": "sqlite",
            "hosted_llm_api_key_present": False,
            "hosted_embedding_api_key_present": False,
            "semantic_search_exercised": False,
        },
        "fixture": {
            "trace_id": "agent-memory-resource-trace",
            "session_id": "agent-memory-resource-session",
            "episode_id": "agent-memory-resource-episode",
            "initial_marker": "silveroak317",
            "replacement_marker": "violetstone624",
        },
        "initial": {
            "imported": 1,
            "skipped": 0,
            "trace_count": 1,
            "get_matches_initial": True,
            "candidate_contains_initial": True,
        },
        "same_key_repeat": {
            "imported": 0,
            "skipped": 1,
            "trace_count": 1,
            "get_matches_initial": True,
        },
        "replacement": {
            "updated_same_id": True,
            "trace_count": 1,
            "get_matches_replacement": True,
            "candidate_contains_replacement": True,
            "candidate_contains_initial": False,
        },
        "restart": {
            "restart_succeeded": True,
            "trace_count": 1,
            "get_matches_replacement": True,
            "candidate_contains_replacement": True,
        },
        "durable_repeat_after_restart": {
            "imported": 0,
            "skipped": 1,
            "trace_count": 1,
            "get_matches_replacement": True,
        },
        "deletion": {
            "delete_succeeded": True,
            "get_after_delete_is_null": True,
            "trace_count": 0,
            "candidate_contains_initial": False,
            "candidate_contains_replacement": False,
        },
        "identity_boundary_preserved": True,
        "provider_notes": [],
    }


def memos_qualification_record():
    component = load_component_profile(MEMOS_PROFILE)
    result = qualify_memos_local_v2017(
        raw_evidence=passing_raw(),
        component=component,
        agent_memory_commit="agent-memory-exact-head",
        raw_evidence_ref="raw/memos-v2017.json",
    )
    assert result.qualification is not None
    return component, qualification_record_from_dict(result.qualification)


class MemOSQualificationTests(unittest.TestCase):
    def test_component_profile_is_schema_valid_and_bounded(self) -> None:
        value = json.loads(MEMOS_PROFILE.read_text(encoding="utf-8"))
        schema = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(value)

        component = load_component_profile(MEMOS_PROFILE)
        self.assertEqual("component-capability-v3", component.profile_version)
        self.assertEqual(1, len(component.capabilities))
        capability = component.capabilities[0]
        self.assertEqual("resource_artifact_memory", capability.capability_id)
        self.assertEqual("evidence_proven", capability.maturity)
        self.assertEqual("derived", capability.state_posture)
        self.assertEqual("external_scope_bridge", capability.scope_posture)
        self.assertEqual("none", capability.authority_effect)
        self.assertEqual("none", capability.operational_contract.write_atomicity)
        self.assertEqual("none", capability.operational_contract.concurrency_control)
        self.assertEqual("durable_keyed", capability.operational_contract.idempotency)
        self.assertEqual("reconstructable", capability.operational_contract.restart_recovery)
        self.assertEqual("deterministic_readback", capability.operational_contract.reconciliation)

    def test_passing_raw_evidence_emits_v12_contract_bound_qualification(self) -> None:
        component = load_component_profile(MEMOS_PROFILE)
        result = qualify_memos_local_v2017(
            raw_evidence=passing_raw(),
            component=component,
            agent_memory_commit="agent-memory-exact-head",
            raw_evidence_ref="raw/memos-v2017.json",
        )
        self.assertTrue(result.eligible)
        self.assertEqual("none", result.authority_effect)
        self.assertIsNotNone(result.qualification)
        qualification = result.qualification
        self.assertEqual("1.2.0", qualification["schema_version"])
        self.assertEqual("Apache-2.0", qualification["source_rights"]["license_id"])
        self.assertEqual("runtime_allowed", qualification["source_rights"]["use_posture"])
        self.assertEqual("evidence_proven", qualification["result"]["earned_maturity"])
        self.assertEqual("none", qualification["result"]["authority_effect"])
        self.assertTrue(any("MIT" in item for item in qualification["result"]["limitations"]))
        schema = json.loads(QUALIFICATION_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(qualification)

    def test_license_discrepancy_must_be_preserved(self) -> None:
        raw = passing_raw()
        raw["identity"]["license_discrepancy_preserved"] = False
        result = qualify_memos_local_v2017(
            raw_evidence=raw,
            component=load_component_profile(MEMOS_PROFILE),
            agent_memory_commit="head",
            raw_evidence_ref="raw.json",
        )
        self.assertFalse(result.eligible)
        self.assertIsNone(result.qualification)
        failed = {item.check_id for item in result.observations if not item.passed}
        self.assertIn("source-rights-discrepancy-preserved", failed)

    def test_stable_key_collision_must_skip_not_duplicate(self) -> None:
        raw = passing_raw()
        raw["same_key_repeat"].update(imported=1, skipped=0, trace_count=2)
        result = qualify_memos_local_v2017(
            raw_evidence=raw,
            component=load_component_profile(MEMOS_PROFILE),
            agent_memory_commit="head",
            raw_evidence_ref="raw.json",
        )
        self.assertFalse(result.eligible)
        failed = {item.check_id for item in result.observations if not item.passed}
        self.assertIn("stable-key-repeat-idempotency", failed)

    def test_same_id_update_must_remove_old_candidate_text(self) -> None:
        raw = passing_raw()
        raw["replacement"]["candidate_contains_initial"] = True
        result = qualify_memos_local_v2017(
            raw_evidence=raw,
            component=load_component_profile(MEMOS_PROFILE),
            agent_memory_commit="head",
            raw_evidence_ref="raw.json",
        )
        self.assertFalse(result.eligible)
        failed = {item.check_id for item in result.observations if not item.passed}
        self.assertIn("stable-key-update-currentness", failed)

    def test_restart_and_post_restart_collision_are_required(self) -> None:
        for section, key, value, expected in (
            ("restart", "restart_succeeded", False, "restart-reconstruction"),
            ("durable_repeat_after_restart", "imported", 1, "durable-key-after-restart"),
        ):
            raw = passing_raw()
            raw[section][key] = value
            result = qualify_memos_local_v2017(
                raw_evidence=raw,
                component=load_component_profile(MEMOS_PROFILE),
                agent_memory_commit="head",
                raw_evidence_ref="raw.json",
            )
            self.assertFalse(result.eligible)
            failed = {item.check_id for item in result.observations if not item.passed}
            self.assertIn(expected, failed)

    def test_delete_residue_refuses_candidate_contract(self) -> None:
        raw = passing_raw()
        raw["deletion"]["candidate_contains_replacement"] = True
        result = qualify_memos_local_v2017(
            raw_evidence=raw,
            component=load_component_profile(MEMOS_PROFILE),
            agent_memory_commit="head",
            raw_evidence_ref="raw.json",
        )
        self.assertFalse(result.eligible)
        failed = {item.check_id for item in result.observations if not item.passed}
        self.assertIn("delete-readback-and-candidate-residue", failed)

    def test_profile_does_not_promote_learned_memos_surfaces(self) -> None:
        component = load_component_profile(MEMOS_PROFILE)
        self.assertEqual({"resource_artifact_memory"}, {item.capability_id for item in component.capabilities})
        for forbidden in (
            "semantic_fact_memory",
            "epistemic_belief_memory",
            "predictive_counterfactual_memory",
            "procedural_memory",
            "graph_state",
            "policy_memory",
        ):
            self.assertNotIn(forbidden, {item.capability_id for item in component.capabilities})

    def test_persisted_hindsight_snapshot_reconstructs_exact_applicability(self) -> None:
        record = load_qualification_snapshot(HINDSIGHT_QUALIFICATION)
        self.assertEqual(
            "sha256:a1776c55d7984706f75f429a605e13cd56e14cd02bfa334697e8509982bd7f5e",
            record.applicability_digest,
        )
        record.assert_current_declaration(load_component(HINDSIGHT_PROFILE))

    def test_real_provider_contracts_satisfy_same_requirement_without_internal_equality(self) -> None:
        hindsight_component = load_component(HINDSIGHT_PROFILE)
        hindsight_qualification = load_qualification_snapshot(HINDSIGHT_QUALIFICATION)
        memos_component, memos_qualification = memos_qualification_record()

        result = prove_resource_artifact_substitution(
            primary_component=hindsight_component,
            primary_qualification=hindsight_qualification,
            replacement_component=memos_component,
            replacement_qualification=memos_qualification,
        )
        self.assertEqual("none", result["authority_effect"])
        self.assertEqual("hindsight-v0.9.0", result["substitution"]["primary_component"])
        self.assertEqual("memos-local-plugin-v2.0.17", result["substitution"]["replacement_component"])
        self.assertNotEqual(
            hindsight_component.capabilities[0].behavior_contract.invalidation_model,
            memos_component.capabilities[0].behavior_contract.invalidation_model,
        )
        requirement = resource_artifact_substitution_requirement()
        self.assertEqual(("durable_keyed",), requirement.operational_requirement.idempotency)

    def test_weaker_durable_contract_is_not_substitutable(self) -> None:
        hindsight_component = load_component(HINDSIGHT_PROFILE)
        hindsight_qualification = load_qualification_snapshot(HINDSIGHT_QUALIFICATION)
        memos_component, memos_qualification = memos_qualification_record()
        capability = memos_component.capabilities[0]
        weaker_operational = replace(capability.operational_contract, idempotency="process_local")
        weaker_capability = replace(capability, operational_contract=weaker_operational)
        weaker_component = replace(memos_component, capabilities=(weaker_capability,))
        weaker_contract = replace(
            memos_qualification.qualified_contract,
            operational_contract=weaker_operational,
        )
        weaker_qualification = replace(memos_qualification, qualified_contract=weaker_contract)

        with self.assertRaisesRegex(QualificationError, "operational contract"):
            prove_resource_artifact_substitution(
                primary_component=hindsight_component,
                primary_qualification=hindsight_qualification,
                replacement_component=weaker_component,
                replacement_qualification=weaker_qualification,
            )

    def test_process_local_restart_or_reconciliation_is_not_substitutable(self) -> None:
        for field_name in ("restart_recovery", "reconciliation"):
            hindsight_component = load_component(HINDSIGHT_PROFILE)
            hindsight_qualification = load_qualification_snapshot(HINDSIGHT_QUALIFICATION)
            memos_component, memos_qualification = memos_qualification_record()
            capability = memos_component.capabilities[0]
            replacement_value = "process_local_only"
            weaker_operational = replace(capability.operational_contract, **{field_name: replacement_value})
            weaker_component = replace(
                memos_component,
                capabilities=(replace(capability, operational_contract=weaker_operational),),
            )
            weaker_qualification = replace(
                memos_qualification,
                qualified_contract=replace(
                    memos_qualification.qualified_contract,
                    operational_contract=weaker_operational,
                ),
            )
            with self.assertRaisesRegex(QualificationError, "operational contract"):
                prove_resource_artifact_substitution(
                    primary_component=hindsight_component,
                    primary_qualification=hindsight_qualification,
                    replacement_component=weaker_component,
                    replacement_qualification=weaker_qualification,
                )

    def test_comparator_only_source_rights_cannot_enter_runtime_substitution(self) -> None:
        hindsight_component = load_component(HINDSIGHT_PROFILE)
        hindsight_qualification = load_qualification_snapshot(HINDSIGHT_QUALIFICATION)
        memos_component, memos_qualification = memos_qualification_record()
        with self.assertRaisesRegex(QualificationError, "runtime-allowed"):
            prove_resource_artifact_substitution(
                primary_component=hindsight_component,
                primary_qualification=hindsight_qualification,
                replacement_component=memos_component,
                replacement_qualification=qualification_with_use_posture(memos_qualification, "comparator_only"),
            )

    def test_authority_posture_change_cannot_hide_inside_substitution(self) -> None:
        hindsight_component = load_component(HINDSIGHT_PROFILE)
        hindsight_qualification = load_qualification_snapshot(HINDSIGHT_QUALIFICATION)
        memos_component, memos_qualification = memos_qualification_record()
        capability = memos_component.capabilities[0]
        authority_component = replace(memos_component, capabilities=(replace(capability, authority_effect="proposal_only"),))
        with self.assertRaises(QualificationError):
            prove_resource_artifact_substitution(
                primary_component=hindsight_component,
                primary_qualification=hindsight_qualification,
                replacement_component=authority_component,
                replacement_qualification=memos_qualification,
            )

    def test_legacy_v11_record_cannot_be_deserialized_for_real_substitution(self) -> None:
        snapshot = json.loads(HINDSIGHT_QUALIFICATION.read_text(encoding="utf-8"))["qualification"]
        snapshot["schema_version"] = "1.1.0"
        snapshot.pop("qualified_contract")
        with self.assertRaisesRegex(QualificationError, "v1.2"):
            qualification_record_from_dict(snapshot)

    def test_tampered_snapshot_digest_is_rejected(self) -> None:
        snapshot = json.loads(HINDSIGHT_QUALIFICATION.read_text(encoding="utf-8"))["qualification"]
        snapshot["runtime"]["fixture_id"] = "tampered-fixture"
        with self.assertRaisesRegex(QualificationError, "applicability digest"):
            qualification_record_from_dict(snapshot)


if __name__ == "__main__":
    unittest.main()
