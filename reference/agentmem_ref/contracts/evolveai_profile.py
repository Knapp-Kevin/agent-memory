"""Evidence-bounded EvolveAI multi-capability profile validation for #292."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from .capabilities import ComponentDeclaration, MATURITY_ORDER

EVOLVEAI_COMMIT = "21161ce7b88dbffeb7ed59757b4d02d24a9c2acd"
COMPONENT_ID = "evolveai"
COMPONENT_PROFILE_VERSION = "component-capability-v2"
ADAPTER_ID = "evolveai-public-facade-adapter"
ADAPTER_VERSION = "1.0.0"
QUALIFICATION_PROFILE_ID = "evolveai-public-facade-behavior"
QUALIFICATION_PROFILE_VERSION = "1.0.0"
SOURCE_REF = f"repo://MythologIQ-Labs-LLC/EvolveAI@{EVOLVEAI_COMMIT}"
IMPLEMENTATION_REF = SOURCE_REF.removeprefix("repo://")

EXPECTED_MATURITY: dict[str, str] = {
    "transient_cache_storage": "implemented",
    "vector_representation": "evidence_proven",
    "vector_candidate_retrieval": "evidence_proven",
    "temporal_graph": "evidence_proven",
    "graph_traversal": "evidence_proven",
    "graph_augmented_context_assembly": "declared",
    "content_addressed_exact_retrieval": "reference_qualified",
    "tier_routing": "evidence_proven",
    "lifecycle_decay": "runtime_wired",
    "lifecycle_orchestration": "evidence_proven",
    "rem_synthesis_consolidation": "evidence_proven",
    "negative_failure_memory": "evidence_proven",
    "persistent_snapshot_restart": "reference_qualified",
    "audited_deletion": "reference_qualified",
    "l3_provenance_audit": "reference_qualified",
}

REQUIRED_DISABLED = frozenset({"graph_augmented_context_assembly"})
PROPOSAL_ONLY = frozenset(
    {
        "tier_routing",
        "lifecycle_decay",
        "lifecycle_orchestration",
        "rem_synthesis_consolidation",
        "negative_failure_memory",
    }
)
REFERENCE_QUALIFIED = frozenset(
    {
        "content_addressed_exact_retrieval",
        "persistent_snapshot_restart",
        "audited_deletion",
        "l3_provenance_audit",
    }
)
QUALIFIED_CAPABILITIES = frozenset(
    capability_id
    for capability_id, maturity in EXPECTED_MATURITY.items()
    if maturity not in {"declared", "implemented"}
)


class EvolveAIProfileError(ValueError):
    """The EvolveAI declaration exceeds or drifts from its evidence boundary."""


def qualification_evidence_ref(capability_id: str) -> str:
    return (
        f"qualification:evolveai:{capability_id}@"
        f"{QUALIFICATION_PROFILE_ID}/{QUALIFICATION_PROFILE_VERSION}"
    )


def _rank(maturity: str) -> int:
    try:
        return MATURITY_ORDER.index(maturity)
    except ValueError as exc:
        raise EvolveAIProfileError(f"unknown capability maturity {maturity!r}") from exc


def _capability_map(component: ComponentDeclaration) -> dict[str, object]:
    return {capability.capability_id: capability for capability in component.capabilities}


def profile_digest(value: Mapping[str, object]) -> str:
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(rendered).hexdigest()


def load_profile(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    validate_profile(value)
    return value


def validate_profile(value: Mapping[str, object]) -> ComponentDeclaration:
    component = ComponentDeclaration.from_dict(value)
    if component.component_id != COMPONENT_ID:
        raise EvolveAIProfileError("EvolveAI profile component_id must be 'evolveai'")
    if component.component_version != EVOLVEAI_COMMIT:
        raise EvolveAIProfileError(f"EvolveAI profile must bind repaired commit {EVOLVEAI_COMMIT}")
    if component.profile_version != COMPONENT_PROFILE_VERSION:
        raise EvolveAIProfileError("EvolveAI profile must use component-capability-v2")
    if component.runtime_ref != IMPLEMENTATION_REF:
        raise EvolveAIProfileError("EvolveAI runtime_ref must bind the exact source revision")
    if component.failure_posture != "explicit_unavailable":
        raise EvolveAIProfileError("EvolveAI provider failure must remain explicitly unavailable")
    if SOURCE_REF not in component.provenance_refs:
        raise EvolveAIProfileError("EvolveAI profile must preserve exact source provenance")
    if "issue://MythologIQ-Labs-LLC/EvolveAI/19" not in component.provenance_refs:
        raise EvolveAIProfileError("repaired deletion profile must preserve EvolveAI #19 provenance")

    capabilities = _capability_map(component)
    if set(capabilities) != set(EXPECTED_MATURITY):
        missing = sorted(set(EXPECTED_MATURITY).difference(capabilities))
        extra = sorted(set(capabilities).difference(EXPECTED_MATURITY))
        raise EvolveAIProfileError(
            f"EvolveAI capability inventory changed without review; missing={missing}, extra={extra}"
        )

    for capability_id, expected_maturity in EXPECTED_MATURITY.items():
        capability = capabilities[capability_id]
        if capability.maturity != expected_maturity:
            raise EvolveAIProfileError(
                f"{capability_id} maturity must remain {expected_maturity} at this profile revision"
            )
        if capability.scope_posture != "external_scope_bridge":
            raise EvolveAIProfileError(f"{capability_id} must use external_scope_bridge")
        if capability.state_posture == "canonical":
            raise EvolveAIProfileError(f"{capability_id} cannot become canonical Agent Memory state")
        if capability.behavior_contract is None:
            raise EvolveAIProfileError(f"{capability_id} is missing v2 behavior metadata")
        if not capability.evidence_refs:
            raise EvolveAIProfileError(f"{capability_id} requires bounded evidence refs")
        expected_authority = "proposal_only" if capability_id in PROPOSAL_ONLY else "none"
        if capability.authority_effect != expected_authority:
            raise EvolveAIProfileError(
                f"{capability_id} authority_effect must remain {expected_authority}"
            )
        if capability_id in REQUIRED_DISABLED and capability.enabled:
            raise EvolveAIProfileError(f"{capability_id} must remain disabled")
        if capability_id not in REQUIRED_DISABLED and not capability.enabled:
            raise EvolveAIProfileError(f"{capability_id} unexpectedly disabled")
        if capability_id in QUALIFIED_CAPABILITIES:
            evidence_ref = qualification_evidence_ref(capability_id)
            if evidence_ref not in capability.evidence_refs:
                raise EvolveAIProfileError(
                    f"{capability_id} must bind exact qualification evidence {evidence_ref}"
                )
        if _rank(capability.maturity) >= _rank("runtime_wired") and capability_id not in QUALIFIED_CAPABILITIES:
            raise EvolveAIProfileError(
                f"{capability_id} cannot advance beyond source-level maturity without #298 evidence"
            )

    if {cid for cid, cap in capabilities.items() if cap.maturity == "reference_qualified"} != set(
        REFERENCE_QUALIFIED
    ):
        raise EvolveAIProfileError("reference-qualified EvolveAI capability set changed without review")

    graph_rag = capabilities["graph_augmented_context_assembly"]
    if graph_rag.maturity != "declared" or graph_rag.enabled:
        raise EvolveAIProfileError("GraphRAG must remain declared and disabled")

    vector = capabilities["vector_candidate_retrieval"]
    if not any("mock" in item.lower() for item in vector.limitations):
        raise EvolveAIProfileError("vector qualification must disclose the mock-engine boundary")

    shadow = capabilities["negative_failure_memory"]
    if shadow.authority_effect != "proposal_only" or not any(
        "authority" in item.lower() for item in shadow.limitations
    ):
        raise EvolveAIProfileError("Shadow Genome must remain proposal-only evidence")

    deletion = capabilities["audited_deletion"]
    if not any("transitive" in item.lower() for item in deletion.limitations):
        raise EvolveAIProfileError("audited deletion must refuse transitive-forgetting overclaim")
    if not any("EvolveAI#19" in item for item in deletion.evidence_refs):
        raise EvolveAIProfileError("audited deletion must bind the repaired EvolveAI #19 evidence")

    return component


def build_scope_binding(*, agent_memory_scope: str, provider_scope: str, profile_sha256: str) -> dict:
    if not agent_memory_scope or not provider_scope:
        raise EvolveAIProfileError("both Agent Memory and provider scopes are required")
    if not profile_sha256.startswith("sha256:"):
        raise EvolveAIProfileError("profile digest must be sha256-bound")
    return {
        "agent_memory_scope": agent_memory_scope,
        "provider_scope": provider_scope,
        "component_version": EVOLVEAI_COMMIT,
        "component_profile_digest": profile_sha256,
        "authority_effect": "none",
    }


def assert_scope_binding(
    binding: Mapping[str, object],
    *,
    requested_scope: str,
    profile_sha256: str,
    component_version: str = EVOLVEAI_COMMIT,
) -> None:
    if binding.get("agent_memory_scope") != requested_scope:
        raise EvolveAIProfileError("EvolveAI scope binding does not match requested Agent Memory scope")
    if binding.get("component_version") != component_version:
        raise EvolveAIProfileError("EvolveAI scope binding is stale for this component version")
    if binding.get("component_profile_digest") != profile_sha256:
        raise EvolveAIProfileError("EvolveAI scope binding is stale for this profile digest")
    if binding.get("authority_effect") != "none":
        raise EvolveAIProfileError("scope binding cannot create authority")


def build_profile_report(value: Mapping[str, object], *, agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40 or any(ch not in "0123456789abcdef" for ch in agent_memory_commit):
        raise EvolveAIProfileError("agent_memory_commit must be 40 lowercase hex characters")
    component = validate_profile(value)
    capabilities = _capability_map(component)
    maturity_counts = {name: 0 for name in MATURITY_ORDER}
    for capability in component.capabilities:
        maturity_counts[capability.maturity] += 1

    direct_authority = [
        capability.capability_id
        for capability in component.capabilities
        if capability.authority_effect not in {"none", "proposal_only"}
    ]
    invariants = {
        "exact_repaired_evolveai_pin": component.component_version == EVOLVEAI_COMMIT,
        "profile_v2_behavior_complete": all(
            capability.behavior_contract is not None for capability in component.capabilities
        ),
        "external_scope_bridge_explicit": all(
            capability.scope_posture == "external_scope_bridge" for capability in component.capabilities
        ),
        "graphrag_not_overstated": not capabilities["graph_augmented_context_assembly"].enabled,
        "mock_vector_boundary_explicit": any(
            "mock" in item.lower() for item in capabilities["vector_candidate_retrieval"].limitations
        ),
        "shadow_has_no_agent_memory_authority": capabilities["negative_failure_memory"].authority_effect
        == "proposal_only",
        "audited_delete_not_transitive_forgetting": any(
            "transitive" in item.lower() for item in capabilities["audited_deletion"].limitations
        ),
        "reference_qualified_set_bounded": {
            cid for cid, cap in capabilities.items() if cap.maturity == "reference_qualified"
        }
        == set(REFERENCE_QUALIFIED),
        "no_canonical_state_claims": all(
            capability.state_posture != "canonical" for capability in component.capabilities
        ),
        "no_direct_authority": not direct_authority,
    }
    return {
        "schema_version": "1.0.0",
        "agent_memory_commit": agent_memory_commit,
        "component": {
            "component_id": component.component_id,
            "component_version": component.component_version,
            "runtime_ref": component.runtime_ref,
            "profile_version": component.profile_version,
            "profile_digest": profile_digest(value),
        },
        "source_rights": {
            "license_id": "Apache-2.0",
            "license_ref": f"MythologIQ-Labs-LLC/EvolveAI/LICENSE@{EVOLVEAI_COMMIT}",
            "use_posture": "runtime_allowed",
        },
        "maturity_counts": maturity_counts,
        "reference_qualified_capabilities": sorted(REFERENCE_QUALIFIED),
        "proposal_only_surfaces": sorted(PROPOSAL_ONLY),
        "capabilities": [capability.to_dict() for capability in component.capabilities],
        "invariants": invariants,
        "authority_effect": "none",
    }
