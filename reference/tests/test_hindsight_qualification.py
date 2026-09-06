from __future__ import annotations

import json
import unittest
from pathlib import Path

import jsonschema

from agentmem_ref.hindsight_qualification import (
    CAPABILITY_ID,
    HINDSIGHT_COMMIT,
    HINDSIGHT_RELEASE,
    HINDSIGHT_VERSION,
    load_component_profile,
    qualify_hindsight_v090,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "reference" / "fixtures" / "component-capabilities" / "hindsight-v0.9.0.json"
PROFILE_SCHEMA = ROOT / "schemas" / "component-capability-profile.schema.json"
QUALIFICATION_SCHEMA = ROOT / "schemas" / "component-capability-qualification.schema.json"


def passing_raw() -> dict:
    return {
        "identity": {
            "repository": "vectorize-io/hindsight",
            "release": HINDSIGHT_RELEASE,
            "version": HINDSIGHT_VERSION,
            "commit": HINDSIGHT_COMMIT,
            "license": "MIT",
            "license_verified": True,
        },
        "configuration": {
            "llm_provider": "none",
            "retain_extraction_mode": "chunks",
            "external_llm_api_key_present": False,
            "database": "pg0",
        },
        "fixture": {
            "bank_id": "agent-memory-hindsight-v090",
            "document_id": "agent-memory-stable-document",
            "initial_marker": "alphacedar731",
            "replacement_marker": "omegamaple842",
        },
        "identity_boundary_preserved": True,
        "initial": {
            "document_count": 1,
            "document_text_matches": True,
            "recall_contains_initial": True,
        },
        "same_key_repeat": {
            "document_count": 1,
            "document_text_matches": True,
        },
        "replacement": {
            "document_count": 1,
            "document_text_matches_replacement": True,
            "recall_contains_replacement": True,
            "recall_contains_initial": False,
        },
        "restart": {
            "daemon_restart_succeeded": True,
            "document_count": 1,
            "document_text_matches_replacement": True,
            "recall_contains_replacement": True,
        },
        "durable_repeat_after_restart": {
            "document_count": 1,
            "document_text_matches_replacement": True,
        },
        "deletion": {
            "delete_succeeded": True,
            "get_after_delete_failed": True,
            "document_count": 0,
            "recall_contains_initial": False,
            "recall_contains_replacement": False,
        },
        "commands": [],
        "provider_notes": [],
    }


class HindsightQualificationTests(unittest.TestCase):
    def test_component_profile_is_schema_valid_and_bounded(self) -> None:
        value = json.loads(PROFILE.read_text(encoding="utf-8"))
        schema = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(value)

        component = load_component_profile(PROFILE)
        self.assertEqual("component-capability-v3", component.profile_version)
        self.assertEqual(1, len(component.capabilities))
        capability = component.capabilities[0]
        self.assertEqual(CAPABILITY_ID, capability.capability_id)
        self.assertEqual("evidence_proven", capability.maturity)
        self.assertEqual("external_scope_bridge", capability.scope_posture)
        self.assertEqual("none", capability.authority_effect)
        self.assertEqual("none", capability.operational_contract.write_atomicity)
        self.assertEqual("none", capability.operational_contract.concurrency_control)
        self.assertEqual("durable_keyed", capability.operational_contract.idempotency)
        self.assertEqual("reconstructable", capability.operational_contract.restart_recovery)
        self.assertEqual("deterministic_readback", capability.operational_contract.reconciliation)

    def test_passing_raw_evidence_emits_v12_contract_bound_qualification(self) -> None:
        component = load_component_profile(PROFILE)
        result = qualify_hindsight_v090(
            raw_evidence=passing_raw(),
            component=component,
            agent_memory_commit="agent-memory-exact-head",
            raw_evidence_ref="raw/hindsight-v090.json",
        )

        self.assertTrue(result.eligible)
        self.assertEqual("none", result.authority_effect)
        self.assertIsNotNone(result.qualification)
        qualification = result.qualification
        self.assertEqual("1.2.0", qualification["schema_version"])
        self.assertEqual("evidence_proven", qualification["result"]["earned_maturity"])
        self.assertEqual("none", qualification["result"]["authority_effect"])
        self.assertEqual("runtime_allowed", qualification["source_rights"]["use_posture"])
        self.assertEqual(
            "reconstructable",
            qualification["qualified_contract"]["operational_contract"]["restart_recovery"],
        )

        schema = json.loads(QUALIFICATION_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(qualification)

    def test_replacement_recall_residue_refuses_candidate_contract(self) -> None:
        raw = passing_raw()
        raw["replacement"]["recall_contains_initial"] = True
        result = qualify_hindsight_v090(
            raw_evidence=raw,
            component=load_component_profile(PROFILE),
            agent_memory_commit="head",
            raw_evidence_ref="raw.json",
        )

        self.assertFalse(result.eligible)
        self.assertIsNone(result.qualification)
        failed = {item.check_id for item in result.observations if not item.passed}
        self.assertIn("stable-key-replacement-currentness", failed)

    def test_restart_failure_refuses_reconstructable_claim(self) -> None:
        raw = passing_raw()
        raw["restart"]["daemon_restart_succeeded"] = False
        result = qualify_hindsight_v090(
            raw_evidence=raw,
            component=load_component_profile(PROFILE),
            agent_memory_commit="head",
            raw_evidence_ref="raw.json",
        )

        self.assertFalse(result.eligible)
        self.assertIsNone(result.qualification)
        failed = {item.check_id for item in result.observations if not item.passed}
        self.assertIn("restart-reconstruction", failed)

    def test_delete_residue_refuses_provider_deletion_contract(self) -> None:
        raw = passing_raw()
        raw["deletion"]["recall_contains_replacement"] = True
        result = qualify_hindsight_v090(
            raw_evidence=raw,
            component=load_component_profile(PROFILE),
            agent_memory_commit="head",
            raw_evidence_ref="raw.json",
        )

        self.assertFalse(result.eligible)
        self.assertIsNone(result.qualification)
        failed = {item.check_id for item in result.observations if not item.passed}
        self.assertIn("delete-readback-and-recall-residue", failed)

    def test_wrong_release_or_source_cannot_be_qualified(self) -> None:
        raw = passing_raw()
        raw["identity"]["commit"] = "0" * 40
        result = qualify_hindsight_v090(
            raw_evidence=raw,
            component=load_component_profile(PROFILE),
            agent_memory_commit="head",
            raw_evidence_ref="raw.json",
        )
        self.assertFalse(result.eligible)
        failed = {item.check_id for item in result.observations if not item.passed}
        self.assertIn("exact-provider-identity", failed)

    def test_llm_key_or_non_chunk_mode_cannot_satisfy_bounded_fixture(self) -> None:
        for mutation in (
            ("external_llm_api_key_present", True),
            ("retain_extraction_mode", "concise"),
            ("llm_provider", "openai"),
        ):
            raw = passing_raw()
            raw["configuration"][mutation[0]] = mutation[1]
            result = qualify_hindsight_v090(
                raw_evidence=raw,
                component=load_component_profile(PROFILE),
                agent_memory_commit="head",
                raw_evidence_ref="raw.json",
            )
            self.assertFalse(result.eligible)
            failed = {item.check_id for item in result.observations if not item.passed}
            self.assertIn("llm-free-chunk-path", failed)

    def test_profile_does_not_promote_richer_hindsight_capabilities(self) -> None:
        component = load_component_profile(PROFILE)
        declared = {capability.capability_id for capability in component.capabilities}
        self.assertEqual({"resource_artifact_memory"}, declared)
        for forbidden in (
            "semantic_fact_memory",
            "epistemic_belief_memory",
            "predictive_counterfactual_memory",
            "graph_state",
            "causal_model_memory",
            "policy_memory",
        ):
            self.assertNotIn(forbidden, declared)

    def test_provider_native_identity_never_creates_authority(self) -> None:
        raw = passing_raw()
        raw["identity_boundary_preserved"] = False
        result = qualify_hindsight_v090(
            raw_evidence=raw,
            component=load_component_profile(PROFILE),
            agent_memory_commit="head",
            raw_evidence_ref="raw.json",
        )
        self.assertFalse(result.eligible)
        self.assertEqual("none", result.authority_effect)
        failed = {item.check_id for item in result.observations if not item.passed}
        self.assertIn("provider-identity-is-not-agent-memory-identity", failed)


if __name__ == "__main__":
    unittest.main()
