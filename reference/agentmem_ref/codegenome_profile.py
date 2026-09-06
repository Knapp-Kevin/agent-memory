"""Evidence-bounded CodeGenome multi-capability profile validation for #293.

The profile is deliberately broader than the executable qualification surface.
Each capability carries its own maturity ceiling. A stronger repository version,
a useful model score, or success in another capability cannot promote it.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from .capabilities import ComponentDeclaration, MATURITY_ORDER
from .code_graph_qualification import CODEGENOME_COMMIT, PROFILE_ID, PROFILE_VERSION


COMPONENT_ID = "codegenome"
COMPONENT_PROFILE_VERSION = "component-capability-v2"
QUALIFICATION_EVIDENCE_REF = (
    f"qualification:codegenome:{PROFILE_ID}@{PROFILE_VERSION}"
)
SOURCE_REF = f"repo://MythologIQ-Labs-LLC/CodeGenome@{CODEGENOME_COMMIT}"

CAPABILITY_CEILINGS: dict[str, str] = {
    "content_addressed_code_identity": "implemented",
    "multi_overlay_graph_state": "implemented",
    "code_graph_traversal": "evidence_proven",
    "graph_candidate_retrieval": "implemented",
    "graph_augmented_context_assembly": "declared",
    "structural_program_analysis": "implemented",
    "impact_propagation": "implemented",
    "embedding_persistence": "implemented",
    "vector_similarity": "implemented",
    "vector_candidate_retrieval": "implemented",
    "confidence_evidence_fusion": "implemented",
    "freshness_currentness": "implemented",
    "provenance_observer_separation": "implemented",
    "multi_language_extraction": "implemented",
    "mcp_agent_exposure": "implemented",
    "experiment_evaluation": "implemented",
    "lsp_overlay": "declared",
    "deletion_rebuild": "implemented",
}

REQUIRED_DISABLED = frozenset(
    {
        "graph_augmented_context_assembly",
        "lsp_overlay",
        "deletion_rebuild",
    }
)
PROPOSAL_ONLY = frozenset({"impact_propagation", "experiment_evaluation"})


class CodeGenomeProfileError(ValueError):
    """The CodeGenome declaration exceeds the evidence available at its pin."""


def _rank(maturity: str) -> int:
    try:
        return MATURITY_ORDER.index(maturity)
    except ValueError as exc:
        raise CodeGenomeProfileError(f"unknown capability maturity {maturity!r}") from exc


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
        raise CodeGenomeProfileError("CodeGenome profile component_id must be 'codegenome'")
    if component.component_version != CODEGENOME_COMMIT:
        raise CodeGenomeProfileError(
            f"CodeGenome profile must bind exact tested commit {CODEGENOME_COMMIT}"
        )
    if component.profile_version != COMPONENT_PROFILE_VERSION:
        raise CodeGenomeProfileError("CodeGenome profile must use component-capability-v2")
    if component.runtime_ref != SOURCE_REF.removeprefix("repo://"):
        raise CodeGenomeProfileError("CodeGenome runtime_ref must bind the exact source revision")
    if component.failure_posture != "explicit_unavailable":
        raise CodeGenomeProfileError("CodeGenome provider failure must remain explicitly unavailable")
    if SOURCE_REF not in component.provenance_refs:
        raise CodeGenomeProfileError("CodeGenome profile must preserve its exact source provenance ref")

    capabilities = _capability_map(component)
    if set(capabilities) != set(CAPABILITY_CEILINGS):
        missing = sorted(set(CAPABILITY_CEILINGS).difference(capabilities))
        extra = sorted(set(capabilities).difference(CAPABILITY_CEILINGS))
        raise CodeGenomeProfileError(
            f"CodeGenome capability inventory changed without profile review; missing={missing}, extra={extra}"
        )

    for capability_id, ceiling in CAPABILITY_CEILINGS.items():
        capability = capabilities[capability_id]
        if _rank(capability.maturity) > _rank(ceiling):
            raise CodeGenomeProfileError(
                f"{capability_id} maturity {capability.maturity} exceeds evidence ceiling {ceiling}"
            )
        if capability.scope_posture != "external_scope_bridge":
            raise CodeGenomeProfileError(
                f"{capability_id} must use explicit external_scope_bridge"
            )
        if capability.state_posture == "canonical":
            raise CodeGenomeProfileError(
                f"{capability_id} cannot become canonical Agent Memory state"
            )
        if capability.behavior_contract is None:
            raise CodeGenomeProfileError(f"{capability_id} is missing v2 behavior metadata")
        if not capability.evidence_refs:
            raise CodeGenomeProfileError(f"{capability_id} requires bounded evidence refs")
        if capability_id in REQUIRED_DISABLED and capability.enabled:
            raise CodeGenomeProfileError(
                f"{capability_id} must remain disabled until dedicated qualification exists"
            )
        if capability_id not in REQUIRED_DISABLED and not capability.enabled:
            raise CodeGenomeProfileError(
                f"{capability_id} unexpectedly disabled; change requires explicit profile review"
            )
        expected_authority = "proposal_only" if capability_id in PROPOSAL_ONLY else "none"
        if capability.authority_effect != expected_authority:
            raise CodeGenomeProfileError(
                f"{capability_id} authority_effect must remain {expected_authority}"
            )
        if capability.maturity == "reference_qualified":
            raise CodeGenomeProfileError(
                f"{capability_id} has no reference-qualified evidence at this profile revision"
            )

    traversal = capabilities["code_graph_traversal"]
    if traversal.maturity != "evidence_proven":
        raise CodeGenomeProfileError("code_graph_traversal must preserve its earned evidence_proven maturity")
    if QUALIFICATION_EVIDENCE_REF not in traversal.evidence_refs:
        raise CodeGenomeProfileError(
            "code_graph_traversal must bind the exact code-graph qualification profile"
        )

    vector = capabilities["vector_candidate_retrieval"]
    if vector.maturity != "implemented":
        raise CodeGenomeProfileError(
            "vector_candidate_retrieval remains implemented until a supported product runtime path is qualified"
        )
    graph_rag = capabilities["graph_augmented_context_assembly"]
    if graph_rag.maturity != "declared" or graph_rag.enabled:
        raise CodeGenomeProfileError(
            "graph_augmented_context_assembly remains declared and disabled until end-to-end qualification"
        )
    lsp = capabilities["lsp_overlay"]
    if lsp.maturity != "declared" or lsp.enabled:
        raise CodeGenomeProfileError("LSP overlay remains a disabled declared stub")
    deletion = capabilities["deletion_rebuild"]
    if deletion.enabled:
        raise CodeGenomeProfileError(
            "deletion_rebuild remains disabled until residue/rebuild qualification exists"
        )

    return component


def build_profile_report(value: Mapping[str, object], *, agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40 or any(ch not in "0123456789abcdef" for ch in agent_memory_commit):
        raise CodeGenomeProfileError("agent_memory_commit must be 40 lowercase hex characters")
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
    proposal_surfaces = sorted(
        capability.capability_id
        for capability in component.capabilities
        if capability.authority_effect == "proposal_only"
    )

    invariants = {
        "exact_codegenome_pin": component.component_version == CODEGENOME_COMMIT,
        "profile_v2_behavior_complete": all(
            capability.behavior_contract is not None for capability in component.capabilities
        ),
        "code_graph_traversal_evidence_proven": capabilities["code_graph_traversal"].maturity
        == "evidence_proven",
        "qualification_profile_bound": QUALIFICATION_EVIDENCE_REF
        in capabilities["code_graph_traversal"].evidence_refs,
        "vector_runtime_not_overstated": capabilities["vector_candidate_retrieval"].maturity
        == "implemented",
        "graph_rag_not_overstated": capabilities["graph_augmented_context_assembly"].maturity
        == "declared"
        and not capabilities["graph_augmented_context_assembly"].enabled,
        "lsp_stub_not_promoted": capabilities["lsp_overlay"].maturity == "declared"
        and not capabilities["lsp_overlay"].enabled,
        "deletion_residue_not_overstated": not capabilities["deletion_rebuild"].enabled,
        "scope_bridge_explicit": all(
            capability.scope_posture == "external_scope_bridge"
            for capability in component.capabilities
        ),
        "no_canonical_state_claims": all(
            capability.state_posture != "canonical" for capability in component.capabilities
        ),
        "no_reference_qualified_claims": all(
            capability.maturity != "reference_qualified" for capability in component.capabilities
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
            "license_id": "MIT",
            "license_ref": f"MythologIQ-Labs-LLC/CodeGenome/LICENSE@{CODEGENOME_COMMIT}",
            "use_posture": "runtime_allowed",
        },
        "qualification_binding": {
            "capability_id": "code_graph_traversal",
            "qualification_profile_id": PROFILE_ID,
            "qualification_profile_version": PROFILE_VERSION,
            "evidence_ref": QUALIFICATION_EVIDENCE_REF,
        },
        "maturity_counts": maturity_counts,
        "proposal_only_surfaces": proposal_surfaces,
        "capabilities": [capability.to_dict() for capability in component.capabilities],
        "invariants": invariants,
        "authority_effect": "none",
    }
