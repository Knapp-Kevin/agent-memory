#!/usr/bin/env python3
"""Carry pinned native CodeGenome Reality Graph evidence through the Cognitive Mesh."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext
from agentmem_ref.cognitive_mesh import CognitiveMeshRuntime, MeshObject
from agentmem_ref.codegenome_cognitive_mesh import (
    ADAPTER_ID,
    ADAPTER_VERSION,
    CAPABILITY_ID,
    cognitive_signal_from_native_relation,
    experience_from_native_relation,
    parse_native_relation_observation,
)
from agentmem_ref.codegenome_profile import COMPONENT_ID, QUALIFICATION_EVIDENCE_REF
from agentmem_ref.code_graph_qualification import CODEGENOME_COMMIT
from agentmem_ref.substrate import InMemoryTemporalGraph

TENANT = "tenant:codegenome-native-mesh-evidence"
PROJECT = "project:codegenome-native-mesh-evidence"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mesh_runtime() -> CognitiveMeshRuntime:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    return CognitiveMeshRuntime(adapter=adapter, available_components=(COMPONENT_ID,))


def mesh_object(ref: str) -> MeshObject:
    return MeshObject(
        object_ref=ref,
        object_type="code_relation_observation",
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        project_ref=PROJECT,
        purpose="reasoning",
    )


def recall_context() -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:codegenome-native-mesh-evidence",
        project_ref=PROJECT,
        purpose="reasoning",
    )


def run(raw_path: Path) -> dict:
    raw = json.loads(raw_path.read_text(encoding="utf-8"))
    raw_digest = sha256_file(raw_path)
    raw_ref = f"artifact://codegenome-native-relation.json#sha256={raw_digest}"
    observation = parse_native_relation_observation(raw, raw_evidence_ref=raw_ref)
    signal = cognitive_signal_from_native_relation(observation)
    experience = experience_from_native_relation(
        observation,
        experience_ref="episode:codegenome-native-relation",
        observed_at="2026-01-01T00:00:00Z",
    )

    logical_ref = "reality:code:native-call-relation"
    positive_mesh = mesh_runtime()
    positive = positive_mesh.apply_signal(
        experience=experience,
        cognitive_object=mesh_object(logical_ref),
        signal=signal,
        actor_id="agent:codegenome-native-mesh-evidence",
        requested_operation="promotion",
        target_class=policy.M2,
        downstream_authority=policy.A1,
        risk_class="low",
    )
    active = positive_mesh.recall_active(
        "CodeGenome observed code relation",
        context=recall_context(),
    )

    authority_mesh = mesh_runtime()
    authority = authority_mesh.apply_signal(
        experience=experience_from_native_relation(
            observation,
            experience_ref="episode:codegenome-native-authority-challenge",
            observed_at="2026-01-01T00:00:00Z",
        ),
        cognitive_object=mesh_object("reality:code:native-authority-challenge"),
        signal=signal,
        actor_id="agent:codegenome-native-mesh-evidence",
        requested_operation="crystallization",
        target_class=policy.M2,
        downstream_authority=policy.A1,
        risk_class="low",
    )

    return {
        "profile": "adr-035-codegenome-native-reality-mesh-v1",
        "provider": {
            "component_id": COMPONENT_ID,
            "component_version": observation.provider_version,
            "expected_component_version": CODEGENOME_COMMIT,
            "source_uor": observation.source_uor,
            "target_uor": observation.target_uor,
            "relation": observation.relation,
            "confidence": observation.confidence,
            "provenance_source": observation.provenance_source,
            "provenance_actor": observation.provenance_actor,
            "provenance_timestamp_ms": observation.provenance_timestamp_ms,
            "evidence_uors": list(observation.evidence_uors),
            "raw_evidence_ref": raw_ref,
        },
        "adapter": {
            "adapter_id": ADAPTER_ID,
            "adapter_version": ADAPTER_VERSION,
            "capability_id": CAPABILITY_ID,
            "qualification_evidence_ref": QUALIFICATION_EVIDENCE_REF,
            "authority_effect": "none",
            "maturity_change": "none",
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
            "provider_source_uor": observation.source_uor,
            "provider_target_uor": observation.target_uor,
            "provider_fact_uuid": positive.commit.fact_uuid,
            "pama_outcome": positive.commit.decision.outcome,
            "committed": positive.commit.committed,
            "receipt_id": positive.commit.receipt["receipt_id"],
            "active_object_refs": active.active_object_refs,
            "identity_independent": positive.object_ref not in {
                f"uor:{observation.source_uor}",
                f"uor:{observation.target_uor}",
            },
        },
        "authority_containment": {
            "provider_confidence": signal.confidence,
            "requested_operation": authority.proposal.operation,
            "pama_outcome": authority.commit.decision.outcome,
            "committed": authority.commit.committed,
            "provider_verdict": signal.provider_verdict,
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
