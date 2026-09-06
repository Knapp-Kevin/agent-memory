"""Bounded ADR-035 Cognitive Mesh reference path.

This module does not attempt to implement cognition. It composes existing Agent
Memory primitives to prove the architectural seam introduced by ADR-035:

experience / observation
  -> stable logical cognitive identity + evidence
  -> typed provider signal
  -> PAMA-governed candidate transition
  -> durable commit or refusal
  -> governed recall
  -> active cognition

The provider signal is deliberately non-authoritative. Reinforcement, graph
confidence, prediction confidence, and provider-native verdicts remain typed
inputs/evidence. They never select a PAMA outcome or bypass recall admission.

The Cognitive Mesh contract here is intentionally small. Object types and
module roles are open strings rather than a universal ontology. The reference
proves shared identity and handoff semantics, not a final cognitive taxonomy.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core import policy
from ..runtime.adapter import CommitResult, GovernedMemoryAdapter, RecallContext
from ..core.contextual_recall import ADMITTING_OUTCOMES, DeterministicContextualRecallPolicy
from ..state.substrate import Episode


class CognitiveModuleUnavailable(RuntimeError):
    """Raised when a requested provider is not present in the configured mesh."""


@dataclass(frozen=True)
class CognitiveExperience:
    """Source experience/observation retained as evidence before promotion."""

    experience_ref: str
    content: str
    source_description: str
    observed_at: str

    def __post_init__(self) -> None:
        if not self.experience_ref or not self.content or not self.observed_at:
            raise ValueError("experience_ref, content, and observed_at are required")


@dataclass(frozen=True)
class MeshObject:
    """Representation-neutral logical cognitive identity.

    `object_type` is intentionally not an enum. ADR-035 must not accidentally
    turn this bounded reference slice into a universal ontology.
    """

    object_ref: str
    object_type: str
    scope: str
    evidence_refs: tuple[str, ...] = ()
    isolation_domain_refs: tuple[str, ...] = ()
    required_isolation_domain_refs: tuple[str, ...] = ()
    project_ref: str = ""
    task_ref: str = ""
    purpose: str = ""

    def __post_init__(self) -> None:
        if not self.object_ref or not self.object_type or not self.scope:
            raise ValueError("object_ref, object_type, and scope are required")


@dataclass(frozen=True)
class CognitiveSignal:
    """Typed, non-authoritative output from a cognitive/reality provider."""

    module_role: str
    source_component: str
    signal_type: str
    evidence_refs: tuple[str, ...] = ()
    estimator_ref: str = ""
    estimator_version: str = ""
    confidence: float | None = None
    provider_verdict: str = ""

    def __post_init__(self) -> None:
        if not self.module_role or not self.source_component or not self.signal_type:
            raise ValueError("module_role, source_component, and signal_type are required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class CognitiveTransition:
    """One cognitive proposal plus the governed consequence it actually earned."""

    object_ref: str
    object_type: str
    experience_ref: str
    signal: CognitiveSignal
    proposal: policy.Proposal
    commit: CommitResult


@dataclass
class ActiveCognition:
    """Governed recall result after substrate and contextual admission."""

    candidate_fact_uuids: list[str] = field(default_factory=list)
    admitted_fact_uuids: list[str] = field(default_factory=list)
    active_object_refs: list[str] = field(default_factory=list)
    refusals: dict[str, str] = field(default_factory=dict)
    contextual_decisions: dict[str, dict] = field(default_factory=dict)


class CognitiveMeshRuntime:
    """Minimal composition layer over existing Agent Memory runtime primitives."""

    def __init__(
        self,
        *,
        adapter: GovernedMemoryAdapter,
        available_components: tuple[str, ...],
        recall_policy: DeterministicContextualRecallPolicy | None = None,
    ) -> None:
        self._adapter = adapter
        self._available_components = set(available_components)
        self._recall_policy = recall_policy or DeterministicContextualRecallPolicy(
            policy_ref="policy:cognitive-mesh-recall",
            policy_version="1.0.0",
        )
        self._object_by_fact: dict[str, str] = {}

    def apply_signal(
        self,
        *,
        experience: CognitiveExperience,
        cognitive_object: MeshObject,
        signal: CognitiveSignal,
        actor_id: str,
        requested_operation: str,
        target_class: str,
        downstream_authority: str,
        risk_class: str,
        reversibility: str = "reversible",
        current_strength: str = "observed",
        proposed_strength: str = "promoted",
        charter_version: str = "cognitive-mesh-ref-v1",
        proposal_id: str | None = None,
        review_satisfied: bool = False,
        approval_refs: tuple[str, ...] = (),
        evidence=None,
        attestation=None,
    ) -> CognitiveTransition:
        """Turn a provider signal into a proposal, never directly into authority.

        ADR-037 step 4b-2, DoD 20: forwards the qualified-evidence channel. A
        provider signal still creates no authority of its own -- that was true
        before and evidence does not change it. PAMA still decides.
        """
        self._require_component(signal.source_component)
        evidence_refs = tuple(
            dict.fromkeys(
                (experience.experience_ref,)
                + cognitive_object.evidence_refs
                + signal.evidence_refs
            )
        )
        estimator_refs = (signal.estimator_ref,) if signal.estimator_ref else ()
        estimator_versions = (signal.estimator_version,) if signal.estimator_version else ()
        proposal = policy.Proposal(
            proposal_id=proposal_id or f"proposal:{cognitive_object.object_ref}:{signal.signal_type}",
            actor_id=actor_id,
            charter_version=charter_version,
            target_reference=cognitive_object.object_ref,
            target_class=target_class,
            scope=cognitive_object.scope,
            operation=requested_operation,
            current_strength=current_strength,
            proposed_strength=proposed_strength,
            downstream_authority=downstream_authority,
            reversibility=reversibility,
            risk_class=risk_class,
            evidence_refs=evidence_refs,
            estimator_refs=estimator_refs,
            estimator_versions=estimator_versions,
            confidence=signal.confidence,
            review_satisfied=review_satisfied,
            approval_refs=approval_refs,
            purpose=cognitive_object.purpose,
            isolation_domain_refs=cognitive_object.isolation_domain_refs,
            required_isolation_domain_refs=cognitive_object.required_isolation_domain_refs,
            project_ref=cognitive_object.project_ref,
            task_ref=cognitive_object.task_ref,
        )
        episode = Episode(
            uuid=experience.experience_ref,
            content=experience.content,
            source_description=experience.source_description,
            valid_at=experience.observed_at,
            group_id=cognitive_object.scope,
        )
        commit = self._adapter.commit_proposal(
            proposal, experience.content, episode=episode,
            evidence=evidence, attestation=attestation,
        )
        if commit.committed and commit.fact_uuid:
            self._object_by_fact[commit.fact_uuid] = cognitive_object.object_ref
        return CognitiveTransition(
            object_ref=cognitive_object.object_ref,
            object_type=cognitive_object.object_type,
            experience_ref=experience.experience_ref,
            signal=signal,
            proposal=proposal,
            commit=commit,
        )

    def recall_active(
        self,
        query: str,
        *,
        context: RecallContext,
    ) -> ActiveCognition:
        """Retrieve through the adapter, then apply current contextual admission."""
        substrate_admission = self._adapter.governed_recall(query, context=context)
        result = ActiveCognition(
            candidate_fact_uuids=list(substrate_admission.candidates),
            admitted_fact_uuids=list(substrate_admission.admitted),
            refusals=dict(substrate_admission.refusals),
        )
        for fact_uuid in substrate_admission.admitted:
            object_ref = self._object_by_fact.get(fact_uuid, fact_uuid)
            decision = self._recall_policy.evaluate(
                object_ref,
                context,
                evaluated_at="2026-01-01T00:10:00Z",
            )
            result.contextual_decisions[object_ref] = decision
            if decision["outcome"] in ADMITTING_OUTCOMES:
                result.active_object_refs.append(object_ref)
            else:
                result.refusals[fact_uuid] = f"contextual_{decision['outcome']}"
        return result

    def replace_component(self, *, old_component: str, new_component: str) -> None:
        """Replace an implementation registration without rewriting mesh identity."""
        if not new_component:
            raise ValueError("new_component is required")
        self._available_components.discard(old_component)
        self._available_components.add(new_component)

    def _require_component(self, source_component: str) -> None:
        if source_component not in self._available_components:
            raise CognitiveModuleUnavailable(
                f"cognitive component unavailable: {source_component}"
            )
