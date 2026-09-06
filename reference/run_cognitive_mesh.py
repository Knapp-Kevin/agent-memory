#!/usr/bin/env python3
"""Emit deterministic ADR-035 Cognitive Mesh reference evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

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

TENANT = "tenant:cognitive-mesh-evidence"
PROJECT = "project:cognitive-mesh-evidence"


def _runtime(*components: str, recall_policy=None):
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    mesh = CognitiveMeshRuntime(
        adapter=adapter,
        available_components=tuple(components),
        recall_policy=recall_policy,
    )
    return mesh, substrate


def _object(ref: str) -> MeshObject:
    return MeshObject(
        object_ref=ref,
        object_type="semantic_candidate",
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        project_ref=PROJECT,
        purpose="reasoning",
    )


def _experience(ref: str, content: str) -> CognitiveExperience:
    return CognitiveExperience(
        experience_ref=ref,
        content=content,
        source_description="ADR-035 deterministic evidence fixture",
        observed_at="2026-01-01T00:00:00Z",
    )


def _context() -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:cognitive-mesh-evidence",
        project_ref=PROJECT,
        purpose="reasoning",
    )


def run() -> dict:
    mesh, substrate = _runtime("EvolveAI", "CodeGenome", "PredictiveReference")
    happy = mesh.apply_signal(
        experience=_experience("episode:happy", "Prefer explicit evidence before durable promotion"),
        cognitive_object=_object("memory:happy"),
        signal=CognitiveSignal(
            module_role="cognitive_metabolism",
            source_component="EvolveAI",
            signal_type="reinforcement",
            estimator_ref="evolveai:metabolism",
            estimator_version="fixture-v1",
            confidence=0.93,
            evidence_refs=("trace:successful-recall",),
        ),
        actor_id="agent:cognitive-mesh-evidence",
        requested_operation="promotion",
        target_class=policy.M2,
        downstream_authority=policy.A1,
        risk_class="low",
    )
    happy_recall = mesh.recall_active("explicit evidence durable promotion", context=_context())

    confidence_outcomes = []
    for confidence in (0.01, 1.0):
        candidate, _ = _runtime("EvolveAI")
        transition = candidate.apply_signal(
            experience=_experience(f"episode:confidence:{confidence}", "Candidate for crystallization"),
            cognitive_object=_object(f"memory:confidence:{confidence}"),
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
        confidence_outcomes.append(
            {
                "confidence": confidence,
                "pama_outcome": transition.commit.decision.outcome,
                "committed": transition.commit.committed,
            }
        )

    code_mesh, _ = _runtime("CodeGenome")
    code_graph = code_mesh.apply_signal(
        experience=_experience("episode:code", "Function A calls privileged function B"),
        cognitive_object=_object("memory:code"),
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

    predictive_mesh, _ = _runtime("PredictiveReference")
    prediction = predictive_mesh.apply_signal(
        experience=_experience("episode:prediction", "Predicted deployment is safe"),
        cognitive_object=_object("memory:prediction"),
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

    contextual_policy = DeterministicContextualRecallPolicy(
        policy_ref="policy:cognitive-mesh-context",
        policy_version="1.0.0",
        rules=(
            ContextualRule(
                rule_id="fixture-block",
                candidate_ref="memory:context-block",
                outcome="block",
                reason_code="fixture_context_block",
            ),
        ),
    )
    context_mesh, _ = _runtime("EvolveAI", recall_policy=contextual_policy)
    context_transition = context_mesh.apply_signal(
        experience=_experience("episode:context", "Context-sensitive durable memory"),
        cognitive_object=_object("memory:context-block"),
        signal=CognitiveSignal(
            module_role="cognitive_metabolism",
            source_component="EvolveAI",
            signal_type="retention_candidate",
            confidence=0.8,
        ),
        actor_id="agent:cognitive-mesh-evidence",
        requested_operation="promotion",
        target_class=policy.M2,
        downstream_authority=policy.A1,
        risk_class="low",
    )
    context_recall = context_mesh.recall_active("context sensitive durable memory", context=_context())

    replacement_mesh, replacement_substrate = _runtime("EvolveAI")
    replacement_signal = CognitiveSignal(
        module_role="cognitive_metabolism",
        source_component="MetabolismV2",
        signal_type="retention_candidate",
        confidence=0.7,
    )
    missing_component = "not_attempted"
    try:
        replacement_mesh.apply_signal(
            experience=_experience("episode:missing", "Replacement provider memory"),
            cognitive_object=_object("memory:replaceable"),
            signal=replacement_signal,
            actor_id="agent:cognitive-mesh-evidence",
            requested_operation="promotion",
            target_class=policy.M2,
            downstream_authority=policy.A1,
            risk_class="low",
        )
    except CognitiveModuleUnavailable as exc:
        missing_component = str(exc)
    writes_before_replacement = len(replacement_substrate.write_log)
    replacement_mesh.replace_component(old_component="EvolveAI", new_component="MetabolismV2")
    replacement = replacement_mesh.apply_signal(
        experience=_experience("episode:replacement", "Replacement provider memory"),
        cognitive_object=_object("memory:replaceable"),
        signal=replacement_signal,
        actor_id="agent:cognitive-mesh-evidence",
        requested_operation="promotion",
        target_class=policy.M2,
        downstream_authority=policy.A1,
        risk_class="low",
    )

    return {
        "profile": "adr-035-cognitive-mesh-reference-v1",
        "happy_path": {
            "logical_object_ref": happy.object_ref,
            "physical_fact_uuid": happy.commit.fact_uuid,
            "pama_outcome": happy.commit.decision.outcome,
            "committed": happy.commit.committed,
            "experience_retained": ("add_episode", "episode:happy") in substrate.write_log,
            "admitted_fact_uuids": happy_recall.admitted_fact_uuids,
            "active_object_refs": happy_recall.active_object_refs,
            "receipt_id": happy.commit.receipt["receipt_id"],
        },
        "confidence_is_not_authority": confidence_outcomes,
        "reality_graph_is_not_authority": {
            "confidence": code_graph.signal.confidence,
            "pama_outcome": code_graph.commit.decision.outcome,
            "committed": code_graph.commit.committed,
        },
        "provider_verdict_is_not_authority": {
            "provider_verdict": prediction.signal.provider_verdict,
            "confidence": prediction.signal.confidence,
            "requested_downstream_authority": prediction.proposal.downstream_authority,
            "pama_outcome": prediction.commit.decision.outcome,
            "committed": prediction.commit.committed,
        },
        "recall_admission_is_separate": {
            "durable_commit": context_transition.commit.committed,
            "substrate_admitted_fact_uuids": context_recall.admitted_fact_uuids,
            "active_object_refs": context_recall.active_object_refs,
            "refusals": context_recall.refusals,
            "contextual_decision": context_recall.contextual_decisions.get("memory:context-block"),
        },
        "module_replacement": {
            "missing_component_refusal": missing_component,
            "writes_before_replacement": writes_before_replacement,
            "replacement_committed": replacement.commit.committed,
            "logical_object_ref": replacement.object_ref,
            "proposal_target_ref": replacement.proposal.target_reference,
            "physical_fact_uuid": replacement.commit.fact_uuid,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
