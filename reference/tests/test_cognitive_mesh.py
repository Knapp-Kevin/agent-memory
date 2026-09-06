from __future__ import annotations

import unittest

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext
from agentmem_ref.cognitive_mesh import (
    CognitiveExperience,
    CognitiveMeshRuntime,
    CognitiveModuleUnavailable,
    CognitiveSignal,
    MeshObject,
)
from agentmem_ref.contextual_recall import ContextualRule, DeterministicContextualRecallPolicy
from agentmem_ref.substrate import InMemoryTemporalGraph

TENANT = "tenant:mesh-fixture"
PROJECT = "project:mesh-fixture"


def experience(ref: str = "episode:mesh-1", content: str = "Prefer explicit evidence before durable promotion") -> CognitiveExperience:
    return CognitiveExperience(
        experience_ref=ref,
        content=content,
        source_description="ADR-035 cognitive mesh fixture",
        observed_at="2026-01-01T00:00:00Z",
    )


def mesh_object(ref: str = "memory:mesh-1") -> MeshObject:
    return MeshObject(
        object_ref=ref,
        object_type="semantic_candidate",
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        project_ref=PROJECT,
        purpose="reasoning",
    )


def context() -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:mesh-test",
        project_ref=PROJECT,
        purpose="reasoning",
    )


def runtime(*components: str, recall_policy=None) -> tuple[CognitiveMeshRuntime, InMemoryTemporalGraph]:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    return (
        CognitiveMeshRuntime(
            adapter=adapter,
            available_components=tuple(components),
            recall_policy=recall_policy,
        ),
        substrate,
    )


class CognitiveMeshTests(unittest.TestCase):
    def test_evolveai_metabolic_signal_commits_only_through_pama_then_recall(self) -> None:
        mesh, substrate = runtime("EvolveAI")
        signal = CognitiveSignal(
            module_role="cognitive_metabolism",
            source_component="EvolveAI",
            signal_type="reinforcement",
            estimator_ref="evolveai:metabolism",
            estimator_version="fixture-v1",
            confidence=0.93,
            evidence_refs=("trace:successful-recall",),
        )

        transition = mesh.apply_signal(
            experience=experience(),
            cognitive_object=mesh_object(),
            signal=signal,
            actor_id="agent:mesh-test",
            requested_operation="promotion",
            target_class=policy.M2,
            downstream_authority=policy.A1,
            risk_class="low",
        )

        self.assertEqual(policy.ALLOW_WITH_LEDGER, transition.commit.decision.outcome)
        self.assertTrue(transition.commit.committed)
        self.assertIsNotNone(transition.commit.fact_uuid)
        self.assertEqual(transition.object_ref, transition.proposal.target_reference)
        self.assertEqual(0.93, transition.proposal.confidence)
        self.assertIn(("add_episode", "episode:mesh-1"), substrate.write_log)

        active = mesh.recall_active("explicit evidence durable promotion", context=context())
        self.assertIn(transition.commit.fact_uuid, active.candidate_fact_uuids)
        self.assertIn(transition.commit.fact_uuid, active.admitted_fact_uuids)
        self.assertEqual(["memory:mesh-1"], active.active_object_refs)

    def test_reinforcement_confidence_cannot_self_authorize_crystallization(self) -> None:
        outcomes = []
        for confidence in (0.01, 1.0):
            mesh, _ = runtime("EvolveAI")
            transition = mesh.apply_signal(
                experience=experience(ref=f"episode:confidence:{confidence}"),
                cognitive_object=mesh_object(ref=f"memory:confidence:{confidence}"),
                signal=CognitiveSignal(
                    module_role="cognitive_metabolism",
                    source_component="EvolveAI",
                    signal_type="crystallization_candidate",
                    estimator_ref="evolveai:crystallizer",
                    estimator_version="fixture-v1",
                    confidence=confidence,
                ),
                actor_id="agent:optimizer",
                requested_operation="crystallization",
                target_class=policy.M2,
                downstream_authority=policy.A1,
                risk_class="low",
            )
            outcomes.append(transition.commit.decision.outcome)
            self.assertFalse(transition.commit.committed)
            self.assertIn("crystallization", transition.commit.decision.prohibited_actions)

        self.assertEqual([policy.REQUIRE_REVIEW, policy.REQUIRE_REVIEW], outcomes)

    def test_codegenome_graph_confidence_cannot_grant_durable_authority(self) -> None:
        mesh, _ = runtime("CodeGenome")
        transition = mesh.apply_signal(
            experience=experience(ref="episode:codegraph", content="Function A calls privileged function B"),
            cognitive_object=mesh_object(ref="memory:codegraph"),
            signal=CognitiveSignal(
                module_role="reality_graph",
                source_component="CodeGenome",
                signal_type="graph_relation_confidence",
                estimator_ref="codegenome:fused-edge",
                estimator_version="fixture-v1",
                confidence=1.0,
            ),
            actor_id="agent:code",
            requested_operation="crystallization",
            target_class=policy.M2,
            downstream_authority=policy.A1,
            risk_class="low",
        )

        self.assertEqual(policy.REQUIRE_REVIEW, transition.commit.decision.outcome)
        self.assertFalse(transition.commit.committed)
        self.assertEqual(("codegenome:fused-edge",), transition.proposal.estimator_refs)

    def test_provider_pass_verdict_cannot_grant_external_action_authority(self) -> None:
        mesh, _ = runtime("PredictiveReference")
        transition = mesh.apply_signal(
            experience=experience(ref="episode:prediction", content="Predicted deployment is safe"),
            cognitive_object=mesh_object(ref="memory:prediction"),
            signal=CognitiveSignal(
                module_role="predictive_world_model",
                source_component="PredictiveReference",
                signal_type="prediction_confidence",
                estimator_ref="predictor:deployment",
                estimator_version="fixture-v1",
                confidence=1.0,
                provider_verdict="PASS",
            ),
            actor_id="agent:predictor",
            requested_operation="promotion",
            target_class=policy.M2,
            downstream_authority=policy.A4,
            risk_class="low",
        )

        self.assertEqual("PASS", transition.signal.provider_verdict)
        self.assertEqual(policy.REQUIRE_REVIEW, transition.commit.decision.outcome)
        self.assertFalse(transition.commit.committed)
        self.assertIn("promotion", transition.commit.decision.prohibited_actions)

    def test_contextual_recall_can_block_already_durable_memory(self) -> None:
        recall_policy = DeterministicContextualRecallPolicy(
            policy_ref="policy:mesh-context",
            policy_version="1.0.0",
            rules=(
                ContextualRule(
                    rule_id="block-sensitive-context",
                    candidate_ref="memory:context-block",
                    outcome="block",
                    reason_code="fixture_context_block",
                ),
            ),
        )
        mesh, _ = runtime("EvolveAI", recall_policy=recall_policy)
        transition = mesh.apply_signal(
            experience=experience(ref="episode:context-block", content="Context-sensitive durable memory"),
            cognitive_object=mesh_object(ref="memory:context-block"),
            signal=CognitiveSignal(
                module_role="cognitive_metabolism",
                source_component="EvolveAI",
                signal_type="retention_candidate",
                confidence=0.8,
            ),
            actor_id="agent:mesh-test",
            requested_operation="promotion",
            target_class=policy.M2,
            downstream_authority=policy.A1,
            risk_class="low",
        )
        self.assertTrue(transition.commit.committed)

        active = mesh.recall_active("context sensitive durable memory", context=context())
        self.assertIn(transition.commit.fact_uuid, active.admitted_fact_uuids)
        self.assertEqual([], active.active_object_refs)
        self.assertEqual(
            "contextual_block",
            active.refusals[transition.commit.fact_uuid],
        )
        self.assertEqual(
            "current_recall_only",
            active.contextual_decisions["memory:context-block"]["interpretation"]["authority_effect"],
        )

    def test_missing_component_fails_explicitly_and_replacement_preserves_logical_identity(self) -> None:
        mesh, substrate = runtime("EvolveAI")
        replacement_signal = CognitiveSignal(
            module_role="cognitive_metabolism",
            source_component="MetabolismV2",
            signal_type="retention_candidate",
            confidence=0.7,
        )
        obj = mesh_object(ref="memory:replaceable")

        with self.assertRaises(CognitiveModuleUnavailable):
            mesh.apply_signal(
                experience=experience(ref="episode:unavailable"),
                cognitive_object=obj,
                signal=replacement_signal,
                actor_id="agent:mesh-test",
                requested_operation="promotion",
                target_class=policy.M2,
                downstream_authority=policy.A1,
                risk_class="low",
            )
        self.assertEqual([], substrate.write_log)

        mesh.replace_component(old_component="EvolveAI", new_component="MetabolismV2")
        transition = mesh.apply_signal(
            experience=experience(ref="episode:replacement"),
            cognitive_object=obj,
            signal=replacement_signal,
            actor_id="agent:mesh-test",
            requested_operation="promotion",
            target_class=policy.M2,
            downstream_authority=policy.A1,
            risk_class="low",
        )

        self.assertTrue(transition.commit.committed)
        self.assertEqual("memory:replaceable", transition.object_ref)
        self.assertEqual("memory:replaceable", transition.proposal.target_reference)


if __name__ == "__main__":
    unittest.main()
