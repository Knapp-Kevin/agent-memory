from __future__ import annotations

import unittest

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext
from agentmem_ref.cognitive_mesh import CognitiveMeshRuntime, MeshObject
from agentmem_ref.evolveai_cognitive_mesh import (
    CAPABILITY_ID,
    SIGNAL_TYPE,
    EvolveAICognitiveMeshError,
    cognitive_signal_from_native_observation,
    experience_from_native_observation,
    parse_native_metabolic_observation,
)
from agentmem_ref.evolveai_profile import COMPONENT_ID, EVOLVEAI_COMMIT, PROPOSAL_ONLY
from agentmem_ref.substrate import InMemoryTemporalGraph

TENANT = "tenant:evolveai-native-mesh"
PROJECT = "project:evolveai-native-mesh"
RAW_REF = "artifact://evolveai-native-observation.json#sha256=fixture"


def raw_observation() -> dict:
    return {
        "schema_version": "1.0.0",
        "provider": "evolveai",
        "provider_version": EVOLVEAI_COMMIT,
        "runtime": {
            "engine": "MockEngine",
            "dimensions": 384,
            "lifecycle_synthesis_threshold": 3,
            "real_embedding_path_exercised": False,
        },
        "observations": {
            "lifecycle_synthesis": True,
            "shadow_candidate_block": True,
        },
        "native_evidence": {
            "detach_traces_processed": 3,
        },
    }


def mesh_object(ref: str = "memory:evolveai-native-synthesis") -> MeshObject:
    return MeshObject(
        object_ref=ref,
        object_type="consolidation_candidate",
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        project_ref=PROJECT,
        purpose="reasoning",
    )


def context() -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:evolveai-native-test",
        project_ref=PROJECT,
        purpose="reasoning",
    )


def runtime() -> CognitiveMeshRuntime:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    return CognitiveMeshRuntime(
        adapter=adapter,
        available_components=(COMPONENT_ID,),
    )


class EvolveAICognitiveMeshTests(unittest.TestCase):
    def test_native_observation_normalizes_without_inventing_confidence(self) -> None:
        observation = parse_native_metabolic_observation(
            raw_observation(), raw_evidence_ref=RAW_REF
        )
        signal = cognitive_signal_from_native_observation(observation)

        self.assertEqual(EVOLVEAI_COMMIT, observation.provider_version)
        self.assertEqual(3, observation.traces_processed)
        self.assertEqual("MockEngine", observation.runtime_engine)
        self.assertFalse(observation.real_embedding_path_exercised)
        self.assertEqual("cognitive_metabolism", signal.module_role)
        self.assertEqual(COMPONENT_ID, signal.source_component)
        self.assertEqual(SIGNAL_TYPE, signal.signal_type)
        self.assertIsNone(signal.confidence)
        self.assertEqual("", signal.provider_verdict)
        self.assertIn(RAW_REF, signal.evidence_refs)
        self.assertIn(CAPABILITY_ID, PROPOSAL_ONLY)

    def test_wrong_provider_or_version_fails_closed(self) -> None:
        wrong_provider = raw_observation()
        wrong_provider["provider"] = "not-evolveai"
        with self.assertRaises(EvolveAICognitiveMeshError):
            parse_native_metabolic_observation(wrong_provider, raw_evidence_ref=RAW_REF)

        wrong_version = raw_observation()
        wrong_version["provider_version"] = "deadbeef"
        with self.assertRaises(EvolveAICognitiveMeshError):
            parse_native_metabolic_observation(wrong_version, raw_evidence_ref=RAW_REF)

    def test_missing_native_synthesis_or_threshold_fails_closed(self) -> None:
        unsynthesized = raw_observation()
        unsynthesized["observations"]["lifecycle_synthesis"] = False
        with self.assertRaises(EvolveAICognitiveMeshError):
            parse_native_metabolic_observation(unsynthesized, raw_evidence_ref=RAW_REF)

        weak_evidence = raw_observation()
        weak_evidence["native_evidence"]["detach_traces_processed"] = 2
        with self.assertRaises(EvolveAICognitiveMeshError):
            parse_native_metabolic_observation(weak_evidence, raw_evidence_ref=RAW_REF)

    def test_native_metabolic_observation_flows_through_pama_and_recall(self) -> None:
        observation = parse_native_metabolic_observation(
            raw_observation(), raw_evidence_ref=RAW_REF
        )
        signal = cognitive_signal_from_native_observation(observation)
        experience = experience_from_native_observation(
            observation,
            experience_ref="episode:evolveai-native-synthesis",
            observed_at="2026-01-01T00:00:00Z",
        )
        mesh = runtime()

        transition = mesh.apply_signal(
            experience=experience,
            cognitive_object=mesh_object(),
            signal=signal,
            actor_id="agent:evolveai-native-test",
            requested_operation="promotion",
            target_class=policy.M2,
            downstream_authority=policy.A1,
            risk_class="low",
        )

        self.assertEqual(policy.ALLOW_WITH_LEDGER, transition.commit.decision.outcome)
        self.assertTrue(transition.commit.committed)
        self.assertEqual(EVOLVEAI_COMMIT, transition.proposal.estimator_versions[0])
        self.assertIsNone(transition.proposal.confidence)
        self.assertIn(RAW_REF, transition.proposal.evidence_refs)

        active = mesh.recall_active(
            "EvolveAI native lifecycle synthesis consolidation candidate",
            context=context(),
        )
        self.assertEqual(["memory:evolveai-native-synthesis"], active.active_object_refs)

    def test_same_native_signal_cannot_self_authorize_crystallization(self) -> None:
        observation = parse_native_metabolic_observation(
            raw_observation(), raw_evidence_ref=RAW_REF
        )
        signal = cognitive_signal_from_native_observation(observation)
        experience = experience_from_native_observation(
            observation,
            experience_ref="episode:evolveai-native-crystallization",
            observed_at="2026-01-01T00:00:00Z",
        )
        mesh = runtime()

        transition = mesh.apply_signal(
            experience=experience,
            cognitive_object=mesh_object(ref="memory:evolveai-native-crystallization"),
            signal=signal,
            actor_id="agent:evolveai-native-test",
            requested_operation="crystallization",
            target_class=policy.M2,
            downstream_authority=policy.A1,
            risk_class="low",
        )

        self.assertEqual(policy.REQUIRE_REVIEW, transition.commit.decision.outcome)
        self.assertFalse(transition.commit.committed)
        self.assertIn("crystallization", transition.commit.decision.prohibited_actions)
        self.assertIsNone(transition.proposal.confidence)


if __name__ == "__main__":
    unittest.main()
