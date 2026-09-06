"""Governed operations over derived state.

Composes the projection sidecar with the authority gate so that the four
consequential derived-state operations are governed rather than incidental:

- **declare** a projection, recording its basis at build time;
- **correct** a canonical unit, which makes dependents stale by relation and
  supersedes content-bearing projections without erasing what a prior decision
  relied on;
- **purge** a canonical unit across the transitive closure of its basis,
  producing a residue partition and an independent sweep; and
- **rebuild** a projection, which is a governed mutation whenever an estimator
  would produce the new content.

That last one is the design spike's least obvious finding. If detecting
staleness could trigger recomputation on its own, an estimator would gain the
ability to write content into memory whenever it can cause a version bump.
Invalidation would become a write channel, which is authority laundering with
a maintenance job in front of it.

Stdlib only apart from schema validation reached through `receipts`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core import policy, receipts
from ..state import residue
from ..state.projections import (
    CanonicalView,
    Projection,
    ProjectionStore,
    RESIDUAL,
    STALE,
)


@dataclass
class CorrectionResult:
    memory_id: str
    new_version: int
    now_stale: list[str] = field(default_factory=list)
    superseded: list[str] = field(default_factory=list)


@dataclass
class PurgeResult:
    decision: policy.Decision
    receipt: dict
    committed: bool = False
    buckets: dict = field(default_factory=dict)
    undeclared: list[str] = field(default_factory=list)
    refusal: str | None = None

    @property
    def hard_gate_passed(self) -> bool:
        """Undeclared residue is disqualifying and un-averageable."""
        return not self.undeclared


@dataclass
class RebuildResult:
    decision: policy.Decision | None
    committed: bool = False
    refusal: str | None = None
    categorical: bool = False


def _evaluate(proposal, evidence, verifier_registry):
    """Route through the qualified path when evidence is supplied.

    ADR-037 step 4b-2, DoD 20: both governed entry points below reach a
    mutation, so both forward the channel rather than burying it.
    """
    if evidence:
        from ..core.evidence_qualification import group_by_dependence

        return policy.evaluate_with_qualified_evidence(
            proposal,
            group_by_dependence(
                evidence,
                verifiers=(verifier_registry.as_mapping() if verifier_registry else None),
            ),
        )
    return policy.evaluate(proposal)


class ProjectionGovernor:
    """Governs derived state on top of a `GovernedMemoryAdapter`."""

    def __init__(self, adapter, store: ProjectionStore | None = None) -> None:
        self._adapter = adapter
        self.store = store or ProjectionStore()
        self._purged: set[str] = set()

    # -- state ----------------------------------------------------------

    def view(self) -> CanonicalView:
        versions = {
            memory_id: self._adapter.state_version(memory_id)
            for memory_id in self._known_sources()
        }
        return CanonicalView(versions, self._adapter.tombstoned_ids(), set(self._purged))

    def _known_sources(self) -> set[str]:
        sources: set[str] = set()
        for projection in self.store.all_versions():
            sources.update(projection.basis_map)
        return sources

    def freshness(self, projection_id: str) -> str | None:
        projection = self.store.get(projection_id)
        if projection is None:
            return None
        return self.store.freshness(projection, self.view())

    # -- declaration -----------------------------------------------------

    def declare(
        self,
        projection_id: str,
        basis_ids: tuple[str, ...],
        transform: str,
        content_class: str,
        rebuild: str,
        scope: str,
        reachable: bool = True,
        note: str = "",
    ) -> Projection:
        """Record a projection with the versions it actually read."""
        basis = tuple((source, self._version_of(source)) for source in basis_ids)
        return self.store.declare(
            Projection(
                projection_id=projection_id,
                basis=basis,
                transform=transform,
                content_class=content_class,
                rebuild=rebuild,
                scope=scope,
                reachable=reachable,
                note=note,
            )
        )

    def _version_of(self, source: str) -> int:
        projection = self.store.get(source)
        if projection is not None:
            return projection.version
        return self._adapter.state_version(source)

    # -- correction ------------------------------------------------------

    def correct(self, memory_id: str) -> CorrectionResult:
        """Advance canonical version; dependents become stale by relation.

        Content-bearing projections are superseded rather than overwritten, so
        a decision that relied on the earlier content stays reconstructable.
        """
        new_version = self._adapter.record_correction(memory_id)
        result = CorrectionResult(memory_id=memory_id, new_version=new_version)
        view = self.view()
        for projection in self.store.dependents_of(memory_id):
            if self.store.freshness(projection, view) != STALE:
                continue
            result.now_stale.append(projection.projection_id)
            if projection.is_content_bearing:
                rebased = tuple(
                    (source, new_version if source == memory_id else read)
                    for source, read in projection.basis
                )
                self.store.supersede(projection.projection_id, rebased)
                result.superseded.append(projection.projection_id)
        return result

    # -- purge -----------------------------------------------------------

    def purge(
        self,
        proposal: policy.Proposal,
        memory_id: str,
        retained_by_policy: set[str] | None = None,
        evidence=None,
        verifier_registry=None,
    ) -> PurgeResult:
        """Purge a canonical unit and the transitive closure of its derivations.

        ADR-037 step 4b-2, DoD 20: forwards the qualified-evidence channel.
        """
        decision = _evaluate(proposal, evidence, verifier_registry)
        permitted = proposal.operation in decision.permitted_actions
        if not permitted:
            deferral = self._deferral(decision)
            receipt = self._receipt(
                proposal, decision, deferral,
                "deterministic" if deferral != receipts.NO_ACTION else "none",
            )
            return PurgeResult(
                decision=decision,
                receipt=receipt,
                committed=False,
                refusal="purge not authorized",
            )

        plan = residue.plan_purge(self.store, memory_id, retained_by_policy)
        residue.apply_purge(self.store, plan, self._purged)
        self._purged.add(memory_id)

        buckets = residue.partition(self.store, self.view(), plan)
        receipt = self._receipt(proposal, decision, proposal.operation, "deterministic")
        self._adapter.events.append(
            receipts.build_audit_event(
                event_id=f"{receipt['receipt_id']}-residue",
                event_type="memory.delete",
                timestamp=receipt["timestamp"],
                component="projection-governor",
                memory_id=memory_id,
                correlation_id=receipt["receipt_id"],
                policy_version=decision.policy_version,
                receipt_ref=receipt["receipt_id"],
            )
        )
        return PurgeResult(
            decision=decision,
            receipt=receipt,
            committed=True,
            buckets=buckets,
            undeclared=buckets[residue.UNDECLARED],
        )

    def sweep(self, declared: set[str] | None = None) -> list[str]:
        """Independent residue sweep, not a report from the purge."""
        return residue.independent_sweep(self.store, self.view(), declared or set())

    # -- rebuild ---------------------------------------------------------

    def propose_rebuild(
        self,
        projection_id: str,
        proposal: policy.Proposal | None = None,
        evidence=None,
        verifier_registry=None,
    ) -> RebuildResult:
        """Rebuild is a governed mutation unless it is deterministic and reproducible.

        ADR-037 step 4b-2, DoD 20: forwards the qualified-evidence channel.
        """
        projection = self.store.get(projection_id)
        if projection is None:
            return RebuildResult(decision=None, refusal="unknown projection")

        if not projection.requires_authority_to_rebuild:
            self._rebase(projection)
            return RebuildResult(decision=None, committed=True, categorical=True)

        if proposal is None:
            return RebuildResult(
                decision=None,
                refusal="estimator-mediated rebuild requires an authority decision",
            )

        decision = _evaluate(proposal, evidence, verifier_registry)
        if proposal.operation not in decision.permitted_actions:
            return RebuildResult(decision=decision, refusal="rebuild not authorized")
        self._rebase(projection)
        return RebuildResult(decision=decision, committed=True)

    def _rebase(self, projection: Projection) -> None:
        rebased = tuple((source, self._version_of(source)) for source, _ in projection.basis)
        self.store.supersede(projection.projection_id, rebased)

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _deferral(decision: policy.Decision) -> str:
        """A refusal still selects from the envelope when one exists."""
        if not decision.permitted_actions:
            return receipts.NO_ACTION
        if "defer" in decision.permitted_actions:
            return "defer"
        return decision.permitted_actions[0]

    def _receipt(self, proposal, decision, selected: str, mode: str) -> dict:
        version = f"v{self._adapter.state_version(proposal.target_reference)}"
        return receipts.build_receipt(
            receipt_id=f"purge-{proposal.proposal_id}",
            proposal=proposal,
            decision=decision,
            selected_action=selected,
            selection_mode=mode,
            timestamp="2026-01-01T00:00:00Z",
            before_state=version,
            after_state=version,
        )
