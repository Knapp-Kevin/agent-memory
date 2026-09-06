"""Executable #308 write-to-readable visibility characterization.

The scenarios exercise the provider-neutral contract against the reference
adapter/projection surface where possible, and use deliberately controlled
failure/restart seams where the reference runtime has no background worker.
Timing is observational only. Structural posture is the portable evidence.
"""

from __future__ import annotations

import platform
import sys
from typing import Callable

from . import policy, projections
from .adapter import Clock, GovernedMemoryAdapter
from .projection_governance import ProjectionGovernor
from .substrate import InMemoryTemporalGraph
from .visibility import ABSENCE, VisibilityOperation, VisibilityTracker


TENANT = "tenant:visibility-characterization"
SOURCE = "memory:visibility-characterization"


def _proposal(**overrides) -> policy.Proposal:
    base = dict(
        proposal_id="proposal:visibility-characterization",
        actor_id="agent:visibility-characterization",
        charter_version="charter:visibility-characterization",
        target_reference=SOURCE,
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:visibility-characterization",),
        tenant_ref=TENANT,
        purpose="write_to_readable_visibility_characterization",
    )
    base.update(overrides)
    return policy.Proposal(**base)


def _operation(
    commit: str,
    *,
    memory_version: int,
    operation_type: str,
    required_projection_ids: tuple[str, ...] = (),
    visibility_target: str = "current_value",
) -> VisibilityOperation:
    return VisibilityOperation(
        operation_id=f"op:{operation_type}:{memory_version}",
        memory_id=SOURCE,
        memory_version=memory_version,
        operation_type=operation_type,
        runtime_version="reference-runtime:visibility:1",
        profile_version="visibility-profile:1",
        agent_memory_commit=commit,
        required_projection_ids=required_projection_ids,
        component_versions=("governed-adapter:reference", "projection-governor:reference"),
        capability_versions=("governed-recall:reference", "projection-freshness:reference"),
        receipt_ref="receipt:visibility-characterization",
        correlation_ref="correlation:visibility-characterization",
        visibility_target=visibility_target,
        environment_ref="reference-characterization",
    )


def _finish_current_read(tracker: VisibilityTracker) -> None:
    tracker.governed_recall_current_visible()
    tracker.context_current_visible()
    tracker.stale_current_blocked()


def sync_canonical_only(commit: str) -> dict:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, TENANT, Clock())
    tracker = VisibilityTracker(_operation(commit, memory_version=1, operation_type="promotion"))
    tracker.policy_decided()
    result = adapter.commit_proposal(_proposal(), "visibility current token")
    if not result.committed:
        raise RuntimeError("sync canonical-only characterization did not commit")
    tracker.canonical_committed()
    recall = adapter.governed_recall("visibility current token")
    if recall.admitted != [result.fact_uuid]:
        raise RuntimeError("sync canonical-only value did not become governed-recall visible")
    _finish_current_read(tracker)
    return tracker.evidence()


def deferred_projection(commit: str) -> dict:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, TENANT, Clock())
    first = adapter.commit_proposal(_proposal(), "deployment Thursday")
    if not first.committed:
        raise RuntimeError("deferred projection baseline did not commit")
    governor = ProjectionGovernor(adapter)
    governor.declare(
        "idx:visibility",
        (SOURCE,),
        projections.DETERMINISTIC,
        projections.REFERENCE_ONLY,
        projections.REPRODUCIBLE,
        TENANT,
    )

    tracker = VisibilityTracker(
        _operation(
            commit,
            memory_version=2,
            operation_type="correction",
            required_projection_ids=("idx:visibility",),
        )
    )
    tracker.policy_decided()
    corrected = adapter.commit_proposal(
        _proposal(
            proposal_id="proposal:visibility-characterization:correction",
            operation="correction",
            current_strength="promoted",
            proposed_strength="promoted",
            approval_refs=("approval:owner",),
            review_satisfied=True,
        ),
        "deployment Friday",
    )
    if not corrected.committed:
        # ADR-037 step 4b-2 (entry #24), operator ruling 2026-09-05.
        #
        # This module parks. Its visibility observations establish whether a
        # *committed* change becomes readable correctly; they do not, before the
        # correction is committed, establish that the correction should be
        # authorised. Using post-consequence visibility evidence as
        # pre-consequence review evidence would be circular.
        #
        # Nor is an adjudication manufactured here to let the scenario proceed:
        # a rule invented to permit exactly the outcome this characterization
        # already expects is the laundering the ruling forbids.
        #
        # So the scenario is **reported blocked** rather than raising. That is
        # itself a true characterization under fail-closed review: an
        # unadjudicated correction never reaches the visibility stage.
        from .pending_verification import PendingVerificationRegistry
        from .resumption import criteria_for

        record = PendingVerificationRegistry().park(
            corrected.proposal if hasattr(corrected, "proposal") else _proposal(
                proposal_id="proposal:visibility-characterization:correction",
                operation="correction",
                current_strength="promoted",
                proposed_strength="promoted",
                approval_refs=("approval:owner",),
                review_satisfied=True,
            ),
            corrected.decision,
        )
        return {
            "scenario": "deferred_projection_visibility",
            "status": "blocked_pending_verification",
            "reason": corrected.refusal or "review_requires_qualified_evidence",
            "unmet_criteria": [c.kind for c in criteria_for(record).unmet],
            "evidence": tracker.evidence(),
        }
    tracker.canonical_committed()
    tracker.projection_refresh_started("idx:visibility")

    if governor.freshness("idx:visibility") != projections.STALE:
        raise RuntimeError("deferred projection was not stale during the lag window")
    old = adapter.governed_recall("Thursday")
    if first.fact_uuid in old.admitted or old.refusals.get(first.fact_uuid) != "superseded_not_current":
        raise RuntimeError("superseded physical fact remained admissible as current")
    current = adapter.governed_recall("Friday")
    if current.admitted != [corrected.fact_uuid]:
        raise RuntimeError("corrected fact was not governed-recall visible")
    _finish_current_read(tracker)
    before_refresh = tracker.evaluate()

    rebuilt = governor.propose_rebuild("idx:visibility")
    if not rebuilt.committed or governor.freshness("idx:visibility") != projections.CURRENT:
        raise RuntimeError("deterministic required projection did not rebuild current")
    tracker.projection_refresh_satisfied("idx:visibility")
    after_refresh = tracker.evaluate()
    return {
        "before_required_refresh": before_refresh,
        "after_required_refresh": after_refresh,
        "evidence": tracker.evidence(),
    }


def required_refresh_failure(commit: str) -> dict:
    tracker = VisibilityTracker(
        _operation(
            commit,
            memory_version=1,
            operation_type="promotion",
            required_projection_ids=("idx:required",),
        )
    )
    tracker.policy_decided()
    tracker.canonical_committed()
    tracker.projection_refresh_started("idx:required")
    tracker.projection_refresh_failed("idx:required", detail="controlled provider failure")
    _finish_current_read(tracker)
    return tracker.evidence()


def restart_during_lag(commit: str) -> dict:
    tracker = VisibilityTracker(
        _operation(
            commit,
            memory_version=1,
            operation_type="promotion",
            required_projection_ids=("idx:restart",),
        )
    )
    tracker.policy_decided()
    tracker.canonical_committed()
    tracker.projection_refresh_started("idx:restart")
    snapshot = tracker.snapshot_for_restart()
    restored = VisibilityTracker.restore_after_restart(snapshot)
    restored.projection_refresh_satisfied("idx:restart")
    _finish_current_read(restored)
    return restored.evidence()


def deletion_residue(commit: str) -> dict:
    tracker = VisibilityTracker(
        _operation(
            commit,
            memory_version=2,
            operation_type="permanent_deletion",
            required_projection_ids=("projection:residue",),
            visibility_target=ABSENCE,
        )
    )
    tracker.policy_decided()
    tracker.canonical_committed()
    tracker.projection_refresh_started("projection:residue")
    _finish_current_read(tracker)
    before_residue = tracker.evaluate()
    tracker.projection_refresh_satisfied("projection:residue")
    after_residue = tracker.evaluate()
    return {
        "before_required_residue": before_residue,
        "after_required_residue": after_residue,
        "evidence": tracker.evidence(),
    }


def _nearest_rank(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, min(len(ordered), int((percentile * len(ordered) + 0.999999999))))
    return ordered[rank - 1]


def _timing_distribution(samples: list[dict], metric_name: str) -> dict:
    values = [
        metric["value_ns"]
        for evidence in samples
        if (metric := evidence["metrics"][metric_name])["reason"] == "observed"
        and metric["value_ns"] is not None
    ]
    return {
        "observed_samples": len(values),
        "p50_ns": _nearest_rank(values, 0.50),
        "p95_ns": _nearest_rank(values, 0.95),
        "p99_ns": _nearest_rank(values, 0.99),
    }


def build_visibility_report(agent_memory_commit: str, repeats: int = 5) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent_memory_commit must be an exact 40-character commit SHA")
    if repeats < 1:
        raise ValueError("repeats must be positive")

    sync_samples = [sync_canonical_only(agent_memory_commit) for _ in range(repeats)]
    deferred_samples = [deferred_projection(agent_memory_commit) for _ in range(repeats)]
    failure = required_refresh_failure(agent_memory_commit)
    restart = restart_during_lag(agent_memory_commit)
    deletion = deletion_residue(agent_memory_commit)

    deferred_evidence = [sample["evidence"] for sample in deferred_samples]
    deferred_parked = [
        sample for sample in deferred_samples
        if sample.get("status") == "blocked_pending_verification"
    ]
    structural_invariants = {
        "sync_canonical_only_quiescent": all(
            sample["disposition"]["quiescent"] for sample in sync_samples
        ),
        # ADR-037 step 4b-2 (entry #24). A deferred-projection sample that
        # parked never reaches the refresh window, so these invariants are
        # evaluated over the samples that got there. The parked ones are
        # reported separately below rather than silently dropped or counted as
        # satisfied -- an unadjudicated correction not reaching the visibility
        # stage is a true observation under fail-closed review, not a gap.
        "deferred_projection_blocks_before_refresh": all(
            not sample["before_required_refresh"]["quiescent"]
            for sample in deferred_samples
            if "before_required_refresh" in sample
        ),
        "deferred_projection_quiescent_after_refresh": all(
            sample["after_required_refresh"]["quiescent"]
            for sample in deferred_samples
            if "after_required_refresh" in sample
        ),
        "deferred_projection_parked_samples_reported": all(
            sample.get("status") == "blocked_pending_verification"
            and sample.get("unmet_criteria")
            for sample in deferred_samples
            if "before_required_refresh" not in sample
        ),
        "required_failure_settled_not_quiescent": (
            failure["disposition"]["settled"]
            and not failure["disposition"]["quiescent"]
            and failure["disposition"]["posture"] == "degraded"
        ),
        "restart_preserves_obligation_without_cross_clock_latency": (
            restart["disposition"]["quiescent"]
            and restart["metrics"]["request_to_quiescence"]["reason"]
            == "cross_restart_monotonic_segments"
        ),
        "deletion_waits_for_required_residue": (
            not deletion["before_required_residue"]["quiescent"]
            and deletion["after_required_residue"]["quiescent"]
        ),
    }

    return {
        "profile": "agent-memory-write-readable-visibility",
        "version": "1.0.0",
        "agent_memory_commit": agent_memory_commit,
        "runner": {
            "python": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "method": {
            "repeats": repeats,
            "latency_is_observational_only": True,
            "latency_is_not_a_conformance_gate": True,
            "latency_is_not_authority": True,
            "restart_timing_is_segmented": True,
        },
        "scenarios": {
            "sync_canonical_only": sync_samples[0],
            "deferred_projection": deferred_samples[0],
            "required_refresh_failure": failure,
            "restart_during_lag": restart,
            "deletion_residue": deletion,
        },
        "timing_distributions": {
            "sync_request_to_canonical_durable": _timing_distribution(
                sync_samples, "request_to_canonical_durable"
            ),
            "sync_request_to_quiescence": _timing_distribution(
                sync_samples, "request_to_quiescence"
            ),
            "deferred_canonical_to_required_projections_current": _timing_distribution(
                deferred_evidence, "canonical_to_required_projections_current"
            ),
            "deferred_request_to_quiescence": _timing_distribution(
                deferred_evidence, "request_to_quiescence"
            ),
        },
        "structural_invariants": structural_invariants,
        "structural_invariants_passed": all(structural_invariants.values()),
        "claim_boundary": [
            "reference-runtime evidence, not universal provider performance",
            "observed latency is environment-specific and non-authoritative",
            "settled means all required obligations reached explicit terminal state",
            "quiescent additionally requires every correctness-required obligation satisfied",
            "cross-restart monotonic duration is unavailable rather than fabricated",
            "provider-native completion markers do not establish Agent Memory quiescence by themselves",
        ],
    }
