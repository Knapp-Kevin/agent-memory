"""Governed reference implementation of epistemic belief memory.

This module implements the first bounded ``epistemic_belief_memory`` runtime
surface introduced by Capability Contract v3. It intentionally does not decide
truth. Claims, beliefs, and hypotheses remain epistemic state with explicit
confidence, directional evidence, and append-only revision lineage.

The module composes existing Agent Memory primitives:

epistemic revision
  -> Cognitive Mesh signal
  -> PAMA authority envelope
  -> governed commit/refusal
  -> governed recall

Retraction uses the existing governed pruning consequence so historical content
remains attributable while no replacement claim becomes current recall state.

The reference implementation is process-local. Its v3 capability profile says
so explicitly; restart/reconciliation portability is future work.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core import policy
from ..runtime.adapter import CommitResult, GovernedMemoryAdapter, RecallContext
from .cognitive_mesh import (
    ActiveCognition,
    CognitiveExperience,
    CognitiveMeshRuntime,
    CognitiveSignal,
    MeshObject,
)
from ..core.contextual_recall import DeterministicContextualRecallPolicy

EPISTEMIC_COMPONENT_ID = "agent-memory-epistemic-reference"
CAPABILITY_ID = "epistemic_belief_memory"

EPISTEMIC_KINDS = frozenset({"claim", "belief", "hypothesis"})
EPISTEMIC_STATUSES = frozenset({"active", "disputed", "retracted"})


class EpistemicRevisionError(ValueError):
    """Base error for an invalid epistemic revision."""


class StaleEpistemicRevision(EpistemicRevisionError):
    """A revision did not extend the current append-only lineage."""


class RetractedBeliefError(EpistemicRevisionError):
    """A retracted belief requires an explicit future readmission path."""


@dataclass(frozen=True)
class EpistemicScope:
    """Governed scope carried by every revision of one belief."""

    scope: str
    isolation_domain_refs: tuple[str, ...] = ()
    required_isolation_domain_refs: tuple[str, ...] = ()
    project_ref: str = ""
    task_ref: str = ""
    purpose: str = "reasoning"

    def __post_init__(self) -> None:
        if not self.scope:
            raise EpistemicRevisionError("epistemic scope is required")
        required = set(self.required_isolation_domain_refs)
        bound = set(self.isolation_domain_refs)
        if required and not required.issubset(bound):
            raise EpistemicRevisionError(
                "required isolation domains must be present in isolation_domain_refs"
            )


@dataclass(frozen=True)
class BeliefRevision:
    """One immutable epistemic revision.

    ``epistemic_kind`` describes the retained epistemic object, not truth.
    ``epistemic_status`` is the status of this revision when it becomes current.
    Historical current/superseded posture is computed from append-only lineage.
    """

    belief_ref: str
    revision_ref: str
    epistemic_kind: str
    claim_text: str
    confidence: float | None
    scope: EpistemicScope
    source_component: str
    observed_at: str
    supporting_evidence_refs: tuple[str, ...] = ()
    contradicting_evidence_refs: tuple[str, ...] = ()
    revision_reason: str = ""
    prior_revision_ref: str = ""
    epistemic_status: str = "active"
    estimator_ref: str = ""
    estimator_version: str = ""

    def __post_init__(self) -> None:
        if not self.belief_ref or not self.revision_ref:
            raise EpistemicRevisionError("belief_ref and revision_ref are required")
        if self.epistemic_kind not in EPISTEMIC_KINDS:
            raise EpistemicRevisionError(
                f"unsupported epistemic_kind: {self.epistemic_kind}"
            )
        if self.epistemic_status not in EPISTEMIC_STATUSES:
            raise EpistemicRevisionError(
                f"unsupported epistemic_status: {self.epistemic_status}"
            )
        if not self.source_component or not self.observed_at:
            raise EpistemicRevisionError(
                "source_component and observed_at are required"
            )
        if self.epistemic_status == "retracted":
            if self.claim_text:
                raise EpistemicRevisionError(
                    "retracted revision must not carry replacement claim_text"
                )
        elif not self.claim_text:
            raise EpistemicRevisionError(
                "active/disputed epistemic revision requires claim_text"
            )
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise EpistemicRevisionError("confidence must be between 0 and 1")
        if self.prior_revision_ref and not self.revision_reason:
            raise EpistemicRevisionError(
                "non-initial revision requires revision_reason"
            )
        for name, refs in (
            ("supporting_evidence_refs", self.supporting_evidence_refs),
            ("contradicting_evidence_refs", self.contradicting_evidence_refs),
        ):
            if len(set(refs)) != len(refs):
                raise EpistemicRevisionError(f"{name} must not contain duplicates")

    @property
    def evidence_refs(self) -> tuple[str, ...]:
        """Directional evidence flattened only for the generic PAMA evidence list."""
        return tuple(
            dict.fromkeys(
                self.supporting_evidence_refs + self.contradicting_evidence_refs
            )
        )


@dataclass(frozen=True)
class EpistemicRevisionResult:
    """Governed consequence of one attempted epistemic revision."""

    revision: BeliefRevision
    commit: CommitResult
    fact_uuid: str | None
    lineage_state: str


@dataclass
class EpistemicBeliefMemory:
    """Process-local reference runtime for governed epistemic belief state."""

    adapter: GovernedMemoryAdapter
    available_components: tuple[str, ...]
    recall_policy: DeterministicContextualRecallPolicy | None = None
    _mesh: CognitiveMeshRuntime = field(init=False, repr=False)
    _history: dict[str, list[BeliefRevision]] = field(
        default_factory=dict, init=False, repr=False
    )
    _fact_by_revision: dict[str, str] = field(
        default_factory=dict, init=False, repr=False
    )

    def __post_init__(self) -> None:
        self._mesh = CognitiveMeshRuntime(
            adapter=self.adapter,
            available_components=self.available_components,
            recall_policy=self.recall_policy,
        )

    def apply_revision(
        self,
        revision: BeliefRevision,
        *,
        actor_id: str,
        target_class: str = policy.M2,
        downstream_authority: str = policy.A1,
        risk_class: str = "low",
        review_satisfied: bool = False,
        approval_refs: tuple[str, ...] = (),
        evidence=None,
        attestation=None,
    ) -> EpistemicRevisionResult:
        """Retain or revise a belief through Cognitive Mesh and PAMA.

        ADR-037 step 4b-2, DoD 20: forwards the qualified-evidence channel.

        A refused proposal is returned to the caller but is never appended to
        current/history state. Confidence is carried as estimator evidence only.
        """
        if revision.epistemic_status == "retracted":
            return self.retract(
                revision,
                actor_id=actor_id,
                target_class=target_class,
                downstream_authority=downstream_authority,
                risk_class=risk_class,
                review_satisfied=review_satisfied,
                approval_refs=approval_refs,
                evidence=evidence,
                attestation=attestation,
            )

        current = self.current(revision.belief_ref)
        self._ensure_new_revision_ref(revision)
        self._validate_lineage(revision, current)
        if current is not None and current.epistemic_status == "retracted":
            raise RetractedBeliefError(
                "retracted belief requires an explicit readmission path"
            )

        operation = "promotion" if current is None else "correction"
        experience = CognitiveExperience(
            experience_ref=revision.revision_ref,
            content=revision.claim_text,
            source_description=(
                f"epistemic {revision.epistemic_kind} revision "
                f"from {revision.source_component}"
            ),
            observed_at=revision.observed_at,
        )
        cognitive_object = MeshObject(
            object_ref=revision.belief_ref,
            object_type=CAPABILITY_ID,
            scope=revision.scope.scope,
            evidence_refs=revision.evidence_refs,
            isolation_domain_refs=revision.scope.isolation_domain_refs,
            required_isolation_domain_refs=(
                revision.scope.required_isolation_domain_refs
            ),
            project_ref=revision.scope.project_ref,
            task_ref=revision.scope.task_ref,
            purpose=revision.scope.purpose,
        )
        signal = CognitiveSignal(
            module_role="epistemic_memory",
            source_component=revision.source_component,
            signal_type="epistemic_revision",
            evidence_refs=revision.evidence_refs,
            estimator_ref=revision.estimator_ref,
            estimator_version=revision.estimator_version,
            confidence=revision.confidence,
        )
        transition = self._mesh.apply_signal(
            experience=experience,
            cognitive_object=cognitive_object,
            signal=signal,
            actor_id=actor_id,
            requested_operation=operation,
            target_class=target_class,
            downstream_authority=downstream_authority,
            risk_class=risk_class,
            current_strength=(
                "observed"
                if current is None
                else (
                    "tentative"
                    if current.epistemic_status == "disputed"
                    else "promoted"
                )
            ),
            proposed_strength=(
                "tentative"
                if revision.epistemic_status == "disputed"
                else "promoted"
            ),
            charter_version="epistemic-belief-memory-ref-v1",
            proposal_id=f"proposal:{revision.revision_ref}",
            review_satisfied=review_satisfied,
            approval_refs=approval_refs,
            evidence=evidence,
            attestation=attestation,
        )

        if transition.commit.committed:
            self._history.setdefault(revision.belief_ref, []).append(revision)
            if transition.commit.fact_uuid is None:
                raise RuntimeError("committed epistemic revision requires fact_uuid")
            self._fact_by_revision[revision.revision_ref] = (
                transition.commit.fact_uuid
            )

        return EpistemicRevisionResult(
            revision=revision,
            commit=transition.commit,
            fact_uuid=transition.commit.fact_uuid,
            lineage_state=(
                self.revision_state(revision.belief_ref, revision.revision_ref)
                if transition.commit.committed
                else "refused"
            ),
        )

    def retract(
        self,
        revision: BeliefRevision,
        *,
        actor_id: str,
        target_class: str = policy.M2,
        downstream_authority: str = policy.A1,
        risk_class: str = "low",
        review_satisfied: bool = False,
        approval_refs: tuple[str, ...] = (),
        evidence=None,
        attestation=None,
    ) -> EpistemicRevisionResult:
        """Append a retraction while pruning the current claim from active recall."""
        if revision.epistemic_status != "retracted":
            raise EpistemicRevisionError(
                "retract() requires epistemic_status='retracted'"
            )
        current = self.current(revision.belief_ref)
        self._ensure_new_revision_ref(revision)
        if current is None:
            raise EpistemicRevisionError("cannot retract an unknown belief")
        self._validate_lineage(revision, current)
        if current.epistemic_status == "retracted":
            raise RetractedBeliefError("belief is already retracted")

        current_fact_uuid = self.adapter.current_fact_uuid(revision.belief_ref)
        if current_fact_uuid is None:
            raise EpistemicRevisionError(
                "current belief has no governed recall fact to retract"
            )

        evidence_refs = tuple(
            dict.fromkeys(
                revision.evidence_refs
                + (revision.prior_revision_ref,)
            )
        )
        proposal = policy.Proposal(
            proposal_id=f"proposal:{revision.revision_ref}",
            actor_id=actor_id,
            charter_version="epistemic-belief-memory-ref-v1",
            target_reference=revision.belief_ref,
            target_class=target_class,
            scope=revision.scope.scope,
            operation="pruning",
            current_strength=(
                "tentative"
                if current.epistemic_status == "disputed"
                else "promoted"
            ),
            proposed_strength="archived",
            downstream_authority=downstream_authority,
            reversibility="reversible",
            risk_class=risk_class,
            evidence_refs=evidence_refs,
            estimator_refs=(
                (revision.estimator_ref,) if revision.estimator_ref else ()
            ),
            estimator_versions=(
                (revision.estimator_version,)
                if revision.estimator_version
                else ()
            ),
            confidence=revision.confidence,
            review_satisfied=review_satisfied,
            approval_refs=approval_refs,
            purpose=revision.scope.purpose,
            isolation_domain_refs=revision.scope.isolation_domain_refs,
            required_isolation_domain_refs=(
                revision.scope.required_isolation_domain_refs
            ),
            project_ref=revision.scope.project_ref,
            task_ref=revision.scope.task_ref,
        )
        commit = self.adapter.governed_delete(
            proposal,
            current_fact_uuid,
        )
        if commit.committed:
            self._history.setdefault(revision.belief_ref, []).append(revision)

        return EpistemicRevisionResult(
            revision=revision,
            commit=commit,
            fact_uuid=current_fact_uuid if commit.committed else None,
            lineage_state=(
                self.revision_state(revision.belief_ref, revision.revision_ref)
                if commit.committed
                else "refused"
            ),
        )

    def current(self, belief_ref: str) -> BeliefRevision | None:
        history = self._history.get(belief_ref, ())
        return history[-1] if history else None

    def current_claim(self, belief_ref: str) -> str | None:
        current = self.current(belief_ref)
        if current is None or current.epistemic_status == "retracted":
            return None
        return current.claim_text

    def history(self, belief_ref: str) -> tuple[BeliefRevision, ...]:
        return tuple(self._history.get(belief_ref, ()))

    def revision_state(self, belief_ref: str, revision_ref: str) -> str:
        history = self._history.get(belief_ref, ())
        matches = [item for item in history if item.revision_ref == revision_ref]
        if not matches:
            raise KeyError(revision_ref)
        current = history[-1]
        if current.revision_ref != revision_ref:
            return "superseded"
        if current.epistemic_status == "disputed":
            return "disputed"
        if current.epistemic_status == "retracted":
            return "retracted"
        return "current"

    def fact_uuid(self, revision_ref: str) -> str | None:
        return self._fact_by_revision.get(revision_ref)

    def recall_active(
        self,
        query: str,
        *,
        context: RecallContext,
    ) -> ActiveCognition:
        result = self._mesh.recall_active(query, context=context)
        for object_ref in tuple(result.active_object_refs):
            current = self.current(object_ref)
            if current is None or current.epistemic_status != "disputed":
                continue
            result.active_object_refs.remove(object_ref)
            fact_uuid = self._fact_by_revision.get(current.revision_ref)
            if fact_uuid:
                result.refusals[fact_uuid] = "epistemic_disputed"
        return result

    def replace_component(self, *, old_component: str, new_component: str) -> None:
        self._mesh.replace_component(
            old_component=old_component,
            new_component=new_component,
        )

    def _ensure_new_revision_ref(self, revision: BeliefRevision) -> None:
        if any(
            item.revision_ref == revision.revision_ref
            for item in self._history.get(revision.belief_ref, ())
        ):
            raise EpistemicRevisionError(
                f"revision_ref already exists for belief: {revision.revision_ref}"
            )

    @staticmethod
    def _validate_lineage(
        revision: BeliefRevision,
        current: BeliefRevision | None,
    ) -> None:
        if current is None:
            if revision.prior_revision_ref:
                raise StaleEpistemicRevision(
                    "initial belief revision must not declare prior_revision_ref"
                )
            return
        if revision.prior_revision_ref != current.revision_ref:
            raise StaleEpistemicRevision(
                "revision must extend the current revision_ref"
            )
        if revision.scope != current.scope:
            raise EpistemicRevisionError(
                "belief revision cannot silently change governed scope"
            )
