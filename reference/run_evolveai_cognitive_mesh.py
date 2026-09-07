#!/usr/bin/env python3
"""Carry pinned native EvolveAI metabolism evidence through the Cognitive Mesh."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext
from agentmem_ref.cognitive_mesh import CognitiveMeshRuntime, MeshObject
from agentmem_ref.evolveai_cognitive_mesh import (
    ADAPTER_ID,
    ADAPTER_VERSION,
    CAPABILITY_ID,
    cognitive_signal_from_native_observation,
    experience_from_native_observation,
    parse_native_metabolic_observation,
)
from agentmem_ref.evolveai_profile import COMPONENT_ID, EVOLVEAI_COMMIT, PROPOSAL_ONLY
from agentmem_ref.substrate import InMemoryTemporalGraph

TENANT = "tenant:evolveai-native-mesh-evidence"
PROJECT = "project:evolveai-native-mesh-evidence"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mesh_runtime() -> CognitiveMeshRuntime:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    return CognitiveMeshRuntime(adapter=adapter, available_components=(COMPONENT_ID,))


def mesh_object(ref: str) -> MeshObject:
    return MeshObject(
        object_ref=ref,
        object_type="consolidation_candidate",
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        project_ref=PROJECT,
        purpose="reasoning",
    )


def recall_context() -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:evolveai-native-mesh-evidence",
        project_ref=PROJECT,
        purpose="reasoning",
    )


def run(raw_path: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw_digest = sha256_file(raw_path)
    raw_ref = f"artifact://evolveai-native-observation.json#sha256={raw_digest}"
    observation = parse_native_metabolic_observation(raw, raw_evidence_ref=raw_ref)
    signal = cognitive_signal_from_native_observation(observation)
    experience = experience_from_native_observation(
        observation,
        experience_ref="episode:evolveai-native-rem-synthesis",
        observed_at="2026-01-01T00:00:00Z",
    )

    positive_mesh = mesh_runtime()
    positive = positive_mesh.apply_signal(
        experience=experience,
        cognitive_object=mesh_object("memory:evolveai-native-rem-synthesis"),
        signal=signal,
        actor_id="agent:evolveai-native-mesh-evidence",
        requested_operation="promotion",
        target_class=policy.M2,
        downstream_authority=policy.A1,
        risk_class="low",
    )
    active = positive_mesh.recall_active(
        "EvolveAI native lifecycle synthesis consolidation candidate",
        context=recall_context(),
    )

    authority_mesh = mesh_runtime()
    authority_challenge = authority_mesh.apply_signal(
        experience=experience_from_native_observation(
            observation,
            experience_ref="episode:evolveai-native-authority-challenge",
            observed_at="2026-01-01T00:00:00Z",
        ),
        cognitive_object=mesh_object("memory:evolveai-native-authority-challenge"),
        signal=signal,
        actor_id="agent:evolveai-native-mesh-evidence",
        requested_operation="crystallization",
        target_class=policy.M2,
        downstream_authority=policy.A1,
        risk_class="low",
    )

    return {
        "profile": "adr-035-evolveai-native-cognitive-mesh-v1",
        "provider": {
            "component_id": COMPONENT_ID,
            "component_version": observation.provider_version,
            "expected_component_version": EVOLVEAI_COMMIT,
            "runtime_engine": observation.runtime_engine,
            "real_embedding_path_exercised": observation.real_embedding_path_exercised,
            "native_traces_processed": observation.traces_processed,
            "raw_evidence_ref": raw_ref,
        },
        "adapter": {
            "adapter_id": ADAPTER_ID,
            "adapter_version": ADAPTER_VERSION,
            "capability_id": CAPABILITY_ID,
            "authority_effect": "proposal_only" if CAPABILITY_ID in PROPOSAL_ONLY else "unexpected",
        },
        "normalized_signal": {
            "module_role": signal.module_role,
            "source_component": signal.source_component,
            "signal_type": signal.signal_type,
            "estimator_ref": signal.estimator_ref,
            "estimator_version": signal.estimator_version,
            "confidence": signal.confidence,
            "provider_verdict": signal.provider_verdict,
            "evidence_refs": list(signal.evidence_refs),
        },
        "governed_positive_path": {
            "logical_object_ref": positive.object_ref,
            "provider_fact_uuid": positive.commit.fact_uuid,
            "pama_outcome": positive.commit.decision.outcome,
            "committed": positive.commit.committed,
            "receipt_id": positive.commit.receipt["receipt_id"],
            "active_object_refs": active.active_object_refs,
            "admitted_fact_uuids": active.admitted_fact_uuids,
        },
        "authority_containment": {
            "requested_operation": authority_challenge.proposal.operation,
            "pama_outcome": authority_challenge.commit.decision.outcome,
            "committed": authority_challenge.commit.committed,
            "prohibited_actions": list(authority_challenge.commit.decision.prohibited_actions),
            "confidence_was_invented": signal.confidence is not None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run(args.raw)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
