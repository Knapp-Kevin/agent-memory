"""Governed reference implementation of predictive and counterfactual memory.

This module implements the first bounded ``predictive_counterfactual_memory``
runtime surface introduced by Capability Contract v3. Forecasts, simulations,
and counterfactual trajectories remain explicitly predictive state. Later
observations are retained as evidence for a separate comparison artifact; they
do not rewrite the prediction into observed history.

The module composes existing Agent Memory primitives:

prediction revision
  -> Cognitive Mesh signal
  -> PAMA authority envelope
  -> governed commit/refusal
  -> predictive recall

observed outcome evidence
  -> separate comparison artifact
  -> Cognitive Mesh signal
  -> PAMA authority envelope
  -> governed commit/refusal

The reference implementation is process-local. Its v3 capability profile says
so explicitly; restart/reconciliation portability and actual simulation/model
execution are future work.
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

PREDICTIVE_COMPONENT_ID = "agent-memory-predictive-reference"
CAPABILITY_ID = "predictive_counterfactual_memory"

PREDICTION_KINDS = frozenset({"forecast", "simulation", "counterfactual"})
COMPARISON_DISPOSITIONS = frozenset(
    {"matched", "contradicted", "partial", "unresolved"}
)


class PredictiveRevisionError(ValueError):
    """Base error for invalid predictive state or comparison."""


class StalePredictionRevision(PredictiveRevisionError):
    """A prediction revision did not extend the current append-only lineage."""


@dataclass(frozen=True)
class PredictiveScope:
    """Governed scope carried by every revision of one prediction."""

    scope: str
    isolation_domain_refs: tuple[str, ...] = ()
    required_isolation_domain_refs: tuple[str, ...] = ()
    project_ref: str = ""
    task_ref: str = ""
    purpose: str = "planning"

    def __post_init__(self) -> None:
        if not self.scope:
            raise PredictiveRevisionError("predictive scope is required")
        required = set(self.required_isolation_domain_refs)
        bound = set(self.isolation_domain_refs)
        if required and not required.issubset(bound):
            raise PredictiveRevisionError(
                "required isolation domains must be present in isolation_domain_refs"
            )


@dataclass(frozen=True)
class PredictionRevision:
    """One immutable forecast/simulation/counterfactual revision.

    ``prediction_kind`` remains predictive metadata for the lifetime of the
    revision. Outcome comparison never mutates it into an observation.
    """

    prediction_ref: str
    revision_ref: str
    prediction_kind: str
    expected_outcome: str
    confidence: float | None
    scope: PredictiveScope
    source_component: str
    created_at: str
    target_window: str
    basis_evidence_refs: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    prior_revision_ref: str = ""
    revision_reason: str = ""
    estimator_ref: str = ""
    estimator_version: str = ""

    def __post_init__(self) -> None:
        if not self.prediction_ref or not self.revision_ref:
            raise PredictiveRevisionError(
                "prediction_ref and revision_ref are required"
            )
        if self.prediction_kind not in PREDICTION_KINDS:
            raise PredictiveRevisionError(
                f"unsupported prediction_kind: {self.prediction_kind}"
            )
        if not self.expected_outcome:
            raise PredictiveRevisionError("expected_outcome is required")
        if not self.source_component or not self.created_at or not self.target_window:
            raise PredictiveRevisionError(
                "source_component, created_at, and target_window are required"
            )
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise PredictiveRevisionError("confidence must be between 0 and 1")
        if self.prior_revision_ref and not self.revision_reason:
            raise PredictiveRevisionError(
                "non-initial prediction revision requires revision_reason"
            )
        if len(set(self.basis_evidence_refs)) != len(self.basis_evidence_refs):
            raise PredictiveRevisionError(
                "basis_evidence_refs must not contain duplicates"
            )
        if len(set(self.assumptions)) != len(self.assumptions):
            raise PredictiveRevisionError("assumptions must not contain duplicates")


@dataclass(frozen=True)
class PredictionOutcomeComparison:
    """Separate derived comparison between prediction and observed evidence.

    The comparison is not the observation itself and does not change the
    prediction's kind. ``disposition`` is descriptive and never authority.
    """

    comparison_ref: str
    prediction_ref: str
    prediction_revision_ref: str
    observed_outcome_summary: str
    observed_evidence_refs: tuple[str, ...]
    observed_at: str
    disposition: str
    source_component: str
    comparison_evidence_refs: tuple[str, ...] = ()
    confidence: float | None = None
    estimator_ref: str = ""
    estimator_version: str = ""

    def __post_init__(self) -> None:
        if not self.comparison_ref or not self.prediction_ref:
            raise PredictiveRevisionError(
                "comparison_ref and prediction_ref are required"
            )
        if not self.prediction_revision_ref:
            raise PredictiveRevisionError(
                "prediction_revision_ref is required"
            )
        if not self.observed_outcome_summary or not self.observed_at:
            raise PredictiveRevisionError(
                "observed_outcome_summary and observed_at are required"
            )
        if not self.observed_evidence_refs:
            raise PredictiveRevisionError(
                "observed_evidence_refs are required for outcome comparison"
            )
        if self.disposition not in COMPARISON_DISPOSITIONS:
            raise PredictiveRevisionError(
                f"unsupported comparison disposition: {self.disposition}"
            )
        if not self.source_component:
            raise PredictiveRevisionError(
                "comparison source_component is required"
            )
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise PredictiveRevisionError("confidence must be between 0 and 1")
        for name, refs in (
            ("observed_evidence_refs", self.observed_evidence_refs),
            ("comparison_evidence_refs", self.comparison_evidence_refs),
        ):
            if len(set(refs)) != len(refs):
                raise PredictiveRevisionError(f"{name} must not contain duplicates")

    @property
    def evidence_refs(self) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                self.observed_evidence_refs + self.comparison_evidence_refs
            )
        )


@dataclass(frozen=True)
class PredictionRevisionResult:
    """Governed consequence of one attempted prediction revision."""

    revision: PredictionRevision
    commit: CommitResult
    fact_uuid: str | None
    lineage_state: str


@dataclass(frozen=True)
class PredictionComparisonResult:
    """Governed consequence of retaining one outcome comparison."""

    comparison: PredictionOutcomeComparison
    commit: CommitResult
    fact_uuid: str | None


@dataclass
class PredictiveCounterfactualMemory:
    """Process-local reference runtime for governed predictive state."""

    adapter: GovernedMemoryAdapter
    available_components: tuple[str, ...]
    recall_policy: DeterministicContextualRecallPolicy | None = None
    _mesh: CognitiveMeshRuntime = field(init=False, repr=False)
    _history: dict[str, list[PredictionRevision]] = field(
        default_factory=dict, init=False, repr=False
    )
    _fact_by_revision: dict[str, str] = field(
        default_factory=dict, init=False, repr=False
    )
    _comparisons: dict[str, PredictionOutcomeComparison] = field(
        default_factory=dict, init=False, repr=False
    )
    _comparison_refs_by_prediction: dict[str, list[str]] = field(
        default_factory=dict, init=False, repr=False
    )
    _fact_by_comparison: dict[str, str] = field(
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
        revision: PredictionRevision,
        *,
        actor_id: str,
        target_class: str = policy.M2,
        downstream_authority: str = policy.A1,
        risk_class: str = "low",
        review_satisfied: bool = False,
        evidence=None,
        attestation=None,
        approval_refs: tuple[str, ...] = (),
    ) -> PredictionRevisionResult:
        """Retain/revise predictive state through Cognitive Mesh and PAMA."""
        current = self.current(revision.prediction_ref)
        self._ensure_new_revision_ref(revision)
        self._validate_lineage(revision, current)

        operation = "promotion" if current is None else "correction"
        experience = CognitiveExperience(
            experience_ref=revision.revision_ref,
            content=self._prediction_fact_text(revision),
            source_description=(
                f"predictive {revision.prediction_kind} revision "
                f"from {revision.source_component}"
            ),
            observed_at=revision.created_at,
        )
        cognitive_object = MeshObject(
            object_ref=revision.prediction_ref,
            object_type=CAPABILITY_ID,
            scope=revision.scope.scope,
            evidence_refs=revision.basis_evidence_refs,
            isolation_domain_refs=revision.scope.isolation_domain_refs,
            required_isolation_domain_refs=(
                revision.scope.required_isolation_domain_refs
            ),
            project_ref=revision.scope.project_ref,
            task_ref=revision.scope.task_ref,
            purpose=revision.scope.purpose,
        )
        signal = CognitiveSignal(
            module_role="predictive_world_model",
            source_component=revision.source_component,
            signal_type=f"{revision.prediction_kind}_revision",
            evidence_refs=revision.basis_evidence_refs,
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
            current_strength="observed" if current is None else "tentative",
            proposed_strength="tentative",
            charter_version="predictive-counterfactual-memory-ref-v1",
            proposal_id=f"proposal:{revision.revision_ref}",
            review_satisfied=review_satisfied,
            approval_refs=approval_refs,
            evidence=evidence,
            attestation=attestation,
        )

        if transition.commit.committed:
            self._history.setdefault(revision.prediction_ref, []).append(revision)
            if transition.commit.fact_uuid is None:
                raise RuntimeError("committed prediction revision requires fact_uuid")
            self._fact_by_revision[revision.revision_ref] = (
                transition.commit.fact_uuid
            )

        return PredictionRevisionResult(
            revision=revision,
            commit=transition.commit,
            fact_uuid=transition.commit.fact_uuid,
            lineage_state=(
                self.revision_state(
                    revision.prediction_ref,
                    revision.revision_ref,
                )
                if transition.commit.committed
                else "refused"
            ),
        )

    def record_outcome_comparison(
        self,
        comparison: PredictionOutcomeComparison,
        *,
        actor_id: str,
        scope: PredictiveScope | None = None,
        target_class: str = policy.M2,
        downstream_authority: str = policy.A1,
        risk_class: str = "low",
        review_satisfied: bool = False,
        evidence=None,
        attestation=None,
        approval_refs: tuple[str, ...] = (),
    ) -> PredictionComparisonResult:
        """Retain a derived comparison without rewriting prediction history."""
        if comparison.comparison_ref in self._comparisons:
            raise PredictiveRevisionError(
                f"comparison_ref already exists: {comparison.comparison_ref}"
            )
        prediction_revision = self._revision(
            comparison.prediction_ref,
            comparison.prediction_revision_ref,
        )
        effective_scope = scope or prediction_revision.scope
        if effective_scope != prediction_revision.scope:
            raise PredictiveRevisionError(
                "outcome comparison cannot silently change governed prediction scope"
            )

        content = self._comparison_fact_text(
            prediction_revision,
            comparison,
        )
        experience = CognitiveExperience(
            experience_ref=comparison.comparison_ref,
            content=content,
            source_description=(
                "prediction/outcome comparison; observed evidence remains "
                "separate from predictive state"
            ),
            observed_at=comparison.observed_at,
        )
        cognitive_object = MeshObject(
            object_ref=comparison.comparison_ref,
            object_type="prediction_outcome_comparison",
            scope=effective_scope.scope,
            evidence_refs=tuple(
                dict.fromkeys(
                    (comparison.prediction_revision_ref,)
                    + comparison.evidence_refs
                )
            ),
            isolation_domain_refs=effective_scope.isolation_domain_refs,
            required_isolation_domain_refs=(
                effective_scope.required_isolation_domain_refs
            ),
            project_ref=effective_scope.project_ref,
            task_ref=effective_scope.task_ref,
            purpose=effective_scope.purpose,
        )
        signal = CognitiveSignal(
            module_role="predictive_world_model",
            source_component=comparison.source_component,
            signal_type="prediction_outcome_comparison",
            evidence_refs=tuple(
                dict.fromkeys(
                    (comparison.prediction_revision_ref,)
                    + comparison.evidence_refs
                )
            ),
            estimator_ref=comparison.estimator_ref,
            estimator_version=comparison.estimator_version,
            confidence=comparison.confidence,
            provider_verdict=comparison.disposition,
        )
        transition = self._mesh.apply_signal(
            experience=experience,
            cognitive_object=cognitive_object,
            signal=signal,
            actor_id=actor_id,
            requested_operation="promotion",
            target_class=target_class,
            downstream_authority=downstream_authority,
            risk_class=risk_class,
            current_strength="observed",
            proposed_strength="tentative",
            charter_version="predictive-counterfactual-memory-ref-v1",
            proposal_id=f"proposal:{comparison.comparison_ref}",
            review_satisfied=review_satisfied,
            approval_refs=approval_refs,
            evidence=evidence,
            attestation=attestation,
        )

        if transition.commit.committed:
            self._comparisons[comparison.comparison_ref] = comparison
            self._comparison_refs_by_prediction.setdefault(
                comparison.prediction_ref,
                [],
            ).append(comparison.comparison_ref)
            if transition.commit.fact_uuid is None:
                raise RuntimeError("committed comparison requires fact_uuid")
            self._fact_by_comparison[comparison.comparison_ref] = (
                transition.commit.fact_uuid
            )

        return PredictionComparisonResult(
            comparison=comparison,
            commit=transition.commit,
            fact_uuid=transition.commit.fact_uuid,
        )

    def current(self, prediction_ref: str) -> PredictionRevision | None:
        history = self._history.get(prediction_ref, ())
        return history[-1] if history else None

    def history(self, prediction_ref: str) -> tuple[PredictionRevision, ...]:
        return tuple(self._history.get(prediction_ref, ()))

    def revision_state(self, prediction_ref: str, revision_ref: str) -> str:
        history = self._history.get(prediction_ref, ())
        matches = [item for item in history if item.revision_ref == revision_ref]
        if not matches:
            raise KeyError(revision_ref)
        return "current" if history[-1].revision_ref == revision_ref else "superseded"

    def comparison(self, comparison_ref: str) -> PredictionOutcomeComparison | None:
        return self._comparisons.get(comparison_ref)

    def comparisons_for(
        self,
        prediction_ref: str,
    ) -> tuple[PredictionOutcomeComparison, ...]:
        return tuple(
            self._comparisons[ref]
            for ref in self._comparison_refs_by_prediction.get(prediction_ref, ())
        )

    def fact_uuid(self, revision_ref: str) -> str | None:
        return self._fact_by_revision.get(revision_ref)

    def comparison_fact_uuid(self, comparison_ref: str) -> str | None:
        return self._fact_by_comparison.get(comparison_ref)

    def recall_active(
        self,
        query: str,
        *,
        context: RecallContext,
    ) -> ActiveCognition:
        return self._mesh.recall_active(query, context=context)

    def replace_component(self, *, old_component: str, new_component: str) -> None:
        self._mesh.replace_component(
            old_component=old_component,
            new_component=new_component,
        )

    def _ensure_new_revision_ref(self, revision: PredictionRevision) -> None:
        if any(
            item.revision_ref == revision.revision_ref
            for item in self._history.get(revision.prediction_ref, ())
        ):
            raise PredictiveRevisionError(
                f"revision_ref already exists for prediction: {revision.revision_ref}"
            )

    @staticmethod
    def _validate_lineage(
        revision: PredictionRevision,
        current: PredictionRevision | None,
    ) -> None:
        if current is None:
            if revision.prior_revision_ref:
                raise StalePredictionRevision(
                    "initial prediction revision must not declare prior_revision_ref"
                )
            return
        if revision.prior_revision_ref != current.revision_ref:
            raise StalePredictionRevision(
                "prediction revision must extend the current revision_ref"
            )
        if revision.scope != current.scope:
            raise PredictiveRevisionError(
                "prediction revision cannot silently change governed scope"
            )
        if revision.prediction_kind != current.prediction_kind:
            raise PredictiveRevisionError(
                "prediction revision cannot silently change prediction_kind"
            )

    def _revision(
        self,
        prediction_ref: str,
        revision_ref: str,
    ) -> PredictionRevision:
        for revision in self._history.get(prediction_ref, ()):
            if revision.revision_ref == revision_ref:
                return revision
        raise PredictiveRevisionError(
            f"unknown prediction revision: {prediction_ref}/{revision_ref}"
        )

    @staticmethod
    def _prediction_fact_text(revision: PredictionRevision) -> str:
        return (
            f"PREDICTIVE[{revision.prediction_kind}] target={revision.target_window}: "
            f"{revision.expected_outcome}"
        )

    @staticmethod
    def _comparison_fact_text(
        revision: PredictionRevision,
        comparison: PredictionOutcomeComparison,
    ) -> str:
        return (
            f"PREDICTION_COMPARISON[{comparison.disposition}] "
            f"prediction_kind={revision.prediction_kind}; "
            f"predicted={revision.expected_outcome}; "
            f"observed_summary={comparison.observed_outcome_summary}"
        )
