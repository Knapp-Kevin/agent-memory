from __future__ import annotations

import unittest

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext
from agentmem_ref.cognitive_mesh import CognitiveMeshRuntime, MeshObject
from agentmem_ref.codegenome_cognitive_mesh import (
    CAPABILITY_ID,
    SIGNAL_TYPE,
    CodeGenomeCognitiveMeshError,
    cognitive_signal_from_native_relation,
    experience_from_native_relation,
    parse_native_relation_observation,
)
from agentmem_ref.codegenome_profile import COMPONENT_ID, QUALIFICATION_EVIDENCE_REF
from agentmem_ref.code_graph_qualification import CODEGENOME_COMMIT
from agentmem_ref.substrate import InMemoryTemporalGraph

TENANT = "tenant:codegenome-native-mesh"
PROJECT = "project:codegenome-native-mesh"
RAW_REF = "artifact://codegenome-native-relation.json#sha256=fixture"
SOURCE_UOR = "1" * 64
TARGET_UOR = "2" * 64
EVIDENCE_UOR = "3" * 64


def raw_observation(*, confidence: float = 0.91) -> dict:
    return {
        "schema_version": "1.0.0",
        "provider": "codegenome",
        "provider_version": CODEGENOME_COMMIT,
        "operation": "code_graph_traversal",
        "query": {
            "file": "main.rs",
            "line": 6,
            "direction": "downstream",
            "max_depth": 2,
            "native_result_confidence": 1.0,
            "path_count": 1,
            "edge_count": 1,
        },
        "target": {"uor": SOURCE_UOR, "kind": "Symbol", "confidence": 1.0},
        "relation": {
            "source_uor": SOURCE_UOR,
            "target_uor": TARGET_UOR,
            "kind": "Calls",
            "confidence": confidence,
            "provenance": {
                "source": "ToolOutput",
                "actor": "rust-extractor",
                "timestamp_ms": 123,
                "justification_uor": None,
            },
            "evidence": [EVIDENCE_UOR],
        },
    }


def mesh_object(ref: str = "reality:code:middle-calls-replacement") -> MeshObject:
    return MeshObject(
        object_ref=ref,
        object_type="code_relation_observation",
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        project_ref=PROJECT,
        purpose="reasoning",
    )


def context() -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:codegenome-native-test",
        project_ref=PROJECT,
        purpose="reasoning",
    )


def runtime() -> CognitiveMeshRuntime:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    return CognitiveMeshRuntime(adapter=adapter, available_components=(COMPONENT_ID,))


class CodeGenomeCognitiveMeshTests(unittest.TestCase):
    def test_native_relation_preserves_provider_evidence_and_confidence(self) -> None:
        observation = parse_native_relation_observation(raw_observation(), raw_evidence_ref=RAW_REF)
        signal = cognitive_signal_from_native_relation(observation)

        self.assertEqual(CODEGENOME_COMMIT, observation.provider_version)
        self.assertEqual("Calls", observation.relation)
        self.assertEqual(0.91, observation.confidence)
        self.assertEqual((EVIDENCE_UOR,), observation.evidence_uors)
        self.assertEqual("reality_graph", signal.module_role)
        self.assertEqual(COMPONENT_ID, signal.source_component)
        self.assertEqual(SIGNAL_TYPE, signal.signal_type)
        self.assertEqual(0.91, signal.confidence)
        self.assertEqual("", signal.provider_verdict)
        self.assertIn(RAW_REF, signal.evidence_refs)
        self.assertIn(f"uor:{SOURCE_UOR}", signal.evidence_refs)
        self.assertIn(f"uor:{TARGET_UOR}", signal.evidence_refs)
        self.assertIn(f"uor:{EVIDENCE_UOR}", signal.evidence_refs)
        self.assertIn(QUALIFICATION_EVIDENCE_REF, signal.evidence_refs)
        self.assertEqual("code_graph_traversal", CAPABILITY_ID)

    def test_wrong_provider_version_or_operation_fails_closed(self) -> None:
        wrong_provider = raw_observation()
        wrong_provider["provider"] = "not-codegenome"
        with self.assertRaises(CodeGenomeCognitiveMeshError):
            parse_native_relation_observation(wrong_provider, raw_evidence_ref=RAW_REF)

        wrong_version = raw_observation()
        wrong_version["provider_version"] = "deadbeef"
        with self.assertRaises(CodeGenomeCognitiveMeshError):
            parse_native_relation_observation(wrong_version, raw_evidence_ref=RAW_REF)

        wrong_operation = raw_observation()
        wrong_operation["operation"] = "impact_propagation"
        with self.assertRaises(CodeGenomeCognitiveMeshError):
            parse_native_relation_observation(wrong_operation, raw_evidence_ref=RAW_REF)

    def test_invalid_uor_or_confidence_fails_closed(self) -> None:
        bad_uor = raw_observation()
        bad_uor["relation"]["source_uor"] = "not-a-uor"
        with self.assertRaises(CodeGenomeCognitiveMeshError):
            parse_native_relation_observation(bad_uor, raw_evidence_ref=RAW_REF)

        bad_confidence = raw_observation(confidence=1.1)
        with self.assertRaises(CodeGenomeCognitiveMeshError):
            parse_native_relation_observation(bad_confidence, raw_evidence_ref=RAW_REF)

    def test_native_relation_flows_through_pama_and_recall_without_identity_laundering(self) -> None:
        observation = parse_native_relation_observation(raw_observation(), raw_evidence_ref=RAW_REF)
        signal = cognitive_signal_from_native_relation(observation)
        experience = experience_from_native_relation(
            observation,
            experience_ref="episode:codegenome-native-relation",
            observed_at="2026-01-01T00:00:00Z",
        )
        mesh = runtime()
        logical_ref = "reality:code:middle-calls-replacement"

        transition = mesh.apply_signal(
            experience=experience,
            cognitive_object=mesh_object(logical_ref),
            signal=signal,
            actor_id="agent:codegenome-native-test",
            requested_operation="promotion",
            target_class=policy.M2,
            downstream_authority=policy.A1,
            risk_class="low",
        )

        self.assertTrue(transition.commit.committed)
        self.assertEqual(policy.ALLOW_WITH_LEDGER, transition.commit.decision.outcome)
        self.assertEqual(logical_ref, transition.object_ref)
        self.assertNotEqual(f"uor:{SOURCE_UOR}", transition.object_ref)
        self.assertEqual(0.91, transition.proposal.confidence)
        self.assertEqual(CODEGENOME_COMMIT, transition.proposal.estimator_versions[0])

        active = mesh.recall_active("CodeGenome observed code relation Calls", context=context())
        self.assertEqual([logical_ref], active.active_object_refs)

    def test_perfect_native_graph_confidence_cannot_self_authorize_crystallization(self) -> None:
        observation = parse_native_relation_observation(
            raw_observation(confidence=1.0), raw_evidence_ref=RAW_REF
        )
        signal = cognitive_signal_from_native_relation(observation)
        mesh = runtime()
        transition = mesh.apply_signal(
            experience=experience_from_native_relation(
                observation,
                experience_ref="episode:codegenome-native-authority-challenge",
                observed_at="2026-01-01T00:00:00Z",
            ),
            cognitive_object=mesh_object("reality:code:authority-challenge"),
            signal=signal,
            actor_id="agent:codegenome-native-test",
            requested_operation="crystallization",
            target_class=policy.M2,
            downstream_authority=policy.A1,
            risk_class="low",
        )

        self.assertEqual(1.0, transition.proposal.confidence)
        self.assertEqual(policy.REQUIRE_REVIEW, transition.commit.decision.outcome)
        self.assertFalse(transition.commit.committed)


if __name__ == "__main__":
    unittest.main()
