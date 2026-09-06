"""Normalize pinned native CodeGenome graph observations into Cognitive Mesh signals.

This adapter consumes one provider-native, evidence-bearing relation discovered by
the already-qualified code_graph_traversal surface and translates it into a
non-authoritative Reality Plane signal.

Provider UOR identity, confidence, provenance, and evidence remain provider
claims/evidence. They do not become Agent Memory logical identity or authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .cognitive_mesh import CognitiveExperience, CognitiveSignal
from .codegenome_profile import COMPONENT_ID, QUALIFICATION_EVIDENCE_REF, SOURCE_REF
from .code_graph_qualification import CODEGENOME_COMMIT

ADAPTER_ID = "codegenome-code-reality-mesh-adapter"
ADAPTER_VERSION = "1.0.0"
CAPABILITY_ID = "code_graph_traversal"
SIGNAL_TYPE = "code_relation_observation"


class CodeGenomeCognitiveMeshError(ValueError):
    """Native CodeGenome evidence is absent, stale, or outside this adapter contract."""


@dataclass(frozen=True)
class CodeGenomeNativeRelationObservation:
    provider_version: str
    source_uor: str
    target_uor: str
    relation: str
    confidence: float
    provenance_source: str
    provenance_actor: str
    provenance_timestamp_ms: int
    evidence_uors: tuple[str, ...]
    raw_evidence_ref: str


def _nonempty_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise CodeGenomeCognitiveMeshError(f"{field} must be a non-empty string")
    return value


def _uor(value: object, field: str) -> str:
    text = _nonempty_string(value, field)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise CodeGenomeCognitiveMeshError(
            f"{field} must be a 64-character lowercase UOR hex value"
        )
    return text


def _evidence_uors(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise CodeGenomeCognitiveMeshError("relation.evidence must be a sequence")
    return tuple(_uor(item, "relation.evidence[]") for item in value)


def parse_native_relation_observation(
    value: Mapping[str, object],
    *,
    raw_evidence_ref: str,
) -> CodeGenomeNativeRelationObservation:
    """Validate one relation emitted by the pinned provider-native traversal driver."""
    if value.get("provider") != COMPONENT_ID:
        raise CodeGenomeCognitiveMeshError("native observation provider must be codegenome")
    if value.get("provider_version") != CODEGENOME_COMMIT:
        raise CodeGenomeCognitiveMeshError(
            f"native observation must bind CodeGenome commit {CODEGENOME_COMMIT}"
        )
    if value.get("operation") != "code_graph_traversal":
        raise CodeGenomeCognitiveMeshError(
            "native observation must come from code_graph_traversal"
        )
    if not raw_evidence_ref:
        raise CodeGenomeCognitiveMeshError("raw_evidence_ref is required")

    relation = value.get("relation")
    if not isinstance(relation, Mapping):
        raise CodeGenomeCognitiveMeshError("native observation is missing relation")
    confidence = relation.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise CodeGenomeCognitiveMeshError("relation.confidence must be numeric")
    confidence = float(confidence)
    if not 0.0 <= confidence <= 1.0:
        raise CodeGenomeCognitiveMeshError("relation.confidence must be between 0 and 1")

    provenance = relation.get("provenance")
    if not isinstance(provenance, Mapping):
        raise CodeGenomeCognitiveMeshError("native relation is missing provenance")
    timestamp = provenance.get("timestamp_ms")
    if isinstance(timestamp, bool) or not isinstance(timestamp, int) or timestamp < 0:
        raise CodeGenomeCognitiveMeshError(
            "relation provenance timestamp_ms must be a non-negative integer"
        )

    return CodeGenomeNativeRelationObservation(
        provider_version=CODEGENOME_COMMIT,
        source_uor=_uor(relation.get("source_uor"), "relation.source_uor"),
        target_uor=_uor(relation.get("target_uor"), "relation.target_uor"),
        relation=_nonempty_string(relation.get("kind"), "relation.kind"),
        confidence=confidence,
        provenance_source=_nonempty_string(
            provenance.get("source"), "relation.provenance.source"
        ),
        provenance_actor=_nonempty_string(
            provenance.get("actor"), "relation.provenance.actor"
        ),
        provenance_timestamp_ms=timestamp,
        evidence_uors=_evidence_uors(relation.get("evidence", [])),
        raw_evidence_ref=raw_evidence_ref,
    )


def cognitive_signal_from_native_relation(
    observation: CodeGenomeNativeRelationObservation,
) -> CognitiveSignal:
    """Translate provider-native graph evidence into a non-authoritative Reality signal."""
    provider_evidence = tuple(f"uor:{value}" for value in observation.evidence_uors)
    return CognitiveSignal(
        module_role="reality_graph",
        source_component=COMPONENT_ID,
        signal_type=SIGNAL_TYPE,
        evidence_refs=(
            observation.raw_evidence_ref,
            SOURCE_REF,
            QUALIFICATION_EVIDENCE_REF,
            f"uor:{observation.source_uor}",
            f"uor:{observation.target_uor}",
            *provider_evidence,
        ),
        estimator_ref=f"{SOURCE_REF}#graph::traversal::execute",
        estimator_version=observation.provider_version,
        confidence=observation.confidence,
        provider_verdict="",
    )


def experience_from_native_relation(
    observation: CodeGenomeNativeRelationObservation,
    *,
    experience_ref: str,
    observed_at: str,
) -> CognitiveExperience:
    """Create the Agent Memory evidence object describing the native relation observation."""
    return CognitiveExperience(
        experience_ref=experience_ref,
        content=(
            "CodeGenome observed code relation "
            f"{observation.source_uor} {observation.relation} {observation.target_uor} "
            f"with provider confidence {observation.confidence:.6f}"
        ),
        source_description=(
            f"{ADAPTER_ID}@{ADAPTER_VERSION}; "
            f"provider={COMPONENT_ID}@{observation.provider_version}; "
            f"provenance={observation.provenance_source}:{observation.provenance_actor}; "
            f"raw={observation.raw_evidence_ref}"
        ),
        observed_at=observed_at,
    )
