"""Normalize pinned native EvolveAI observations into Cognitive Mesh signals.

This adapter is intentionally narrow. It accepts the exact raw observation
produced by the existing EvolveAI public-facade qualification workload and
translates only the evidenced REM/lifecycle synthesis observation into a typed
CognitiveSignal.

The adapter does not recreate EvolveAI behavior, assign confidence that the
provider did not emit, or grant Agent Memory authority. Native provider output
remains evidence for a proposal-only Cognitive Metabolism signal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .cognitive_mesh import CognitiveExperience, CognitiveSignal
from ..contracts.evolveai_profile import (
    COMPONENT_ID,
    EVOLVEAI_COMMIT,
    SOURCE_REF,
    qualification_evidence_ref,
)


ADAPTER_ID = "evolveai-cognitive-metabolism-mesh-adapter"
ADAPTER_VERSION = "1.0.0"
SIGNAL_TYPE = "rem_synthesis_consolidation_candidate"
CAPABILITY_ID = "rem_synthesis_consolidation"


class EvolveAICognitiveMeshError(ValueError):
    """Native EvolveAI evidence is absent, stale, or outside this adapter contract."""


@dataclass(frozen=True)
class EvolveAINativeMetabolicObservation:
    provider_version: str
    traces_processed: int
    raw_evidence_ref: str
    runtime_engine: str
    real_embedding_path_exercised: bool


def parse_native_metabolic_observation(
    value: Mapping[str, object],
    *,
    raw_evidence_ref: str,
) -> EvolveAINativeMetabolicObservation:
    """Validate the exact provider-native synthesis evidence used by ADR-035."""
    if value.get("provider") != COMPONENT_ID:
        raise EvolveAICognitiveMeshError("native observation provider must be evolveai")
    if value.get("provider_version") != EVOLVEAI_COMMIT:
        raise EvolveAICognitiveMeshError(
            f"native observation must bind EvolveAI commit {EVOLVEAI_COMMIT}"
        )
    if not raw_evidence_ref:
        raise EvolveAICognitiveMeshError("raw_evidence_ref is required")

    observations = value.get("observations")
    if not isinstance(observations, Mapping):
        raise EvolveAICognitiveMeshError("native observation is missing observations")
    if observations.get("lifecycle_synthesis") is not True:
        raise EvolveAICognitiveMeshError(
            "native EvolveAI workload did not prove lifecycle_synthesis"
        )

    native_evidence = value.get("native_evidence")
    if not isinstance(native_evidence, Mapping):
        raise EvolveAICognitiveMeshError("native observation is missing native_evidence")
    traces_processed = native_evidence.get("detach_traces_processed")
    if not isinstance(traces_processed, int) or isinstance(traces_processed, bool):
        raise EvolveAICognitiveMeshError("detach_traces_processed must be an integer")
    if traces_processed < 3:
        raise EvolveAICognitiveMeshError(
            "native synthesis evidence must preserve the configured three-trace threshold"
        )

    runtime = value.get("runtime")
    if not isinstance(runtime, Mapping):
        raise EvolveAICognitiveMeshError("native observation is missing runtime identity")
    engine = runtime.get("engine")
    if not isinstance(engine, str) or not engine:
        raise EvolveAICognitiveMeshError("native runtime engine identity is required")
    real_embedding_path = runtime.get("real_embedding_path_exercised")
    if type(real_embedding_path) is not bool:
        raise EvolveAICognitiveMeshError(
            "real_embedding_path_exercised must remain an explicit boolean"
        )

    return EvolveAINativeMetabolicObservation(
        provider_version=EVOLVEAI_COMMIT,
        traces_processed=traces_processed,
        raw_evidence_ref=raw_evidence_ref,
        runtime_engine=engine,
        real_embedding_path_exercised=real_embedding_path,
    )


def cognitive_signal_from_native_observation(
    observation: EvolveAINativeMetabolicObservation,
) -> CognitiveSignal:
    """Translate provider evidence into a proposal-only Cognitive Metabolism signal."""
    return CognitiveSignal(
        module_role="cognitive_metabolism",
        source_component=COMPONENT_ID,
        signal_type=SIGNAL_TYPE,
        evidence_refs=(
            observation.raw_evidence_ref,
            SOURCE_REF,
            qualification_evidence_ref(CAPABILITY_ID),
        ),
        estimator_ref=f"{SOURCE_REF}#MemoryProcessor.detach",
        estimator_version=observation.provider_version,
        confidence=None,
        provider_verdict="",
    )


def experience_from_native_observation(
    observation: EvolveAINativeMetabolicObservation,
    *,
    experience_ref: str,
    observed_at: str,
) -> CognitiveExperience:
    """Create the Agent Memory evidence object describing the native metabolic event."""
    return CognitiveExperience(
        experience_ref=experience_ref,
        content=(
            "EvolveAI native lifecycle synthesis processed "
            f"{observation.traces_processed} traces and produced a consolidation candidate"
        ),
        source_description=(
            f"{ADAPTER_ID}@{ADAPTER_VERSION}; "
            f"provider={COMPONENT_ID}@{observation.provider_version}; "
            f"runtime={observation.runtime_engine}; "
            f"raw={observation.raw_evidence_ref}"
        ),
        observed_at=observed_at,
    )
