"""Receiver-local execution of cross-system correction and deletion obligations.

P7 notices are evidence, not remote commands. This module composes the notice
contract with the existing governed adapter and P4 projection/residue machinery
so a receiver can prove what happened to its own retained copy.

No transport or external project semantics are defined here.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..state import residue
from ..runtime.adapter import CommitResult, GovernedMemoryAdapter
from .deletion_completeness import DeletionCompletenessMeasurement, measure_deletion_completeness
from ..state.projections import CanonicalView, Projection, ProjectionStore, RESIDUAL
from ..state.substrate import TemporalGraphPort
from ..core import policy


@dataclass(frozen=True)
class CorrectionPropagationResult:
    commit: CommitResult
    superseded_fact_uuid: str
    replacement_fact_uuid: str | None


@dataclass(frozen=True)
class DeletionPropagationResult:
    commit: CommitResult
    buckets: dict[str, list[str]]
    independently_observed_residual: tuple[str, ...]
    measurement: DeletionCompletenessMeasurement


def apply_receiver_correction(
    adapter: GovernedMemoryAdapter,
    substrate: TemporalGraphPort,
    *,
    proposal: policy.Proposal,
    superseded_fact_uuid: str,
    corrected_text: str,
    invalid_at: str,
    evidence=None,
) -> CorrectionPropagationResult:
    """Commit a receiver-local correction and supersede, rather than erase, old state."""
    if proposal.operation != "correction":
        raise ValueError("receiver correction propagation requires operation=correction")

    commit = adapter.commit_proposal(proposal, corrected_text, evidence=evidence)
    replacement = commit.fact_uuid if commit.committed else None
    if commit.committed:
        substrate.invalidate_fact(superseded_fact_uuid, invalid_at=invalid_at, expired_at=invalid_at)

    return CorrectionPropagationResult(
        commit=commit,
        superseded_fact_uuid=superseded_fact_uuid,
        replacement_fact_uuid=replacement,
    )


def apply_receiver_deletion(
    adapter: GovernedMemoryAdapter,
    projections: ProjectionStore,
    *,
    proposal: policy.Proposal,
    fact_uuid: str,
    retained_by_policy: set[str] | None = None,
    late_projections: tuple[Projection, ...] = (),
    evidence=None,
) -> DeletionPropagationResult:
    """Execute receiver-local deletion and independently measure retained residue.

    The purge plan is intentionally computed before `late_projections` are
    declared. Tests use that seam to model state created after traversal or
    omitted from the deletion plan. The independent sweep must discover it as
    undeclared residue rather than trusting the deletion receipt's optimism.
    """
    if proposal.operation != "permanent_deletion":
        raise ValueError("receiver deletion propagation requires permanent_deletion")

    plan = residue.plan_purge(projections, proposal.target_reference, retained_by_policy)
    commit = adapter.governed_delete(
        proposal,
        fact_uuid,
        derived_refs=tuple(sorted(plan.declared)),
        evidence=evidence,
    )

    if not commit.committed:
        empty = {
            residue.PURGED: [],
            residue.DECLARED_CONTROLLED: [],
            residue.DECLARED_UNCONTROLLABLE: [],
            residue.UNDECLARED: [],
        }
        measurement = measure_deletion_completeness(empty, ())
        return DeletionPropagationResult(commit, empty, (), measurement)

    # Simulate declarations that arrived after traversal or were omitted from
    # the purge plan. A trustworthy independent sweep must still catch them.
    for projection in late_projections:
        projections.declare(projection)

    purged_projection_ids: set[str] = set()
    residue.apply_purge(projections, plan, purged_projection_ids)

    view = CanonicalView(
        versions={proposal.target_reference: adapter.state_version(proposal.target_reference)},
        tombstoned=adapter.tombstoned_ids(),
        purged=purged_projection_ids,
    )
    buckets = residue.partition(projections, view, plan)
    observed = tuple(
        sorted(
            {
                projection.projection_id
                for projection in projections.all_versions()
                if projection.is_content_bearing and projections.freshness(projection, view) == RESIDUAL
            }
        )
    )
    measurement = measure_deletion_completeness(buckets, observed)
    return DeletionPropagationResult(commit, buckets, observed, measurement)
