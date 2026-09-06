"""P9 systems/economic characterization for the Agent Memory reference runtime.

The characterization deliberately separates portable structural cost from
machine-local timing. Operation counts, evidence amplification, candidate
counts, and derivation closure sizes are deterministic properties of the
executed reference paths. Latency is observational only and must never become
an authority signal, a governance threshold, or a conformance gate.
"""

from __future__ import annotations

import json
import platform
import statistics
import sys
import time
from dataclasses import asdict, dataclass

from . import policy
from .adapter import Clock, GovernedMemoryAdapter
from .projections import (
    DERIVED_CONTENT,
    DETERMINISTIC,
    REPRODUCIBLE,
    Projection,
    ProjectionStore,
)
from .substrate import Fact, InMemoryTemporalGraph

TENANT = "tenant:p9"


@dataclass(frozen=True)
class TimingSummary:
    samples: int
    minimum_ns: int
    median_ns: int
    maximum_ns: int


def _timed(operation, repeats: int) -> TimingSummary:
    samples: list[int] = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        operation()
        samples.append(time.perf_counter_ns() - started)
    return TimingSummary(
        samples=len(samples),
        minimum_ns=min(samples),
        median_ns=int(statistics.median(samples)),
        maximum_ns=max(samples),
    )


def _proposal(proposal_id: str, target_reference: str) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="agent:p9-characterizer",
        charter_version="charter:p9",
        target_reference=target_reference,
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:p9",),
        estimator_refs=("estimator:p9",),
        estimator_versions=("1",),
        confidence=0.8,
        tenant_ref=TENANT,
        purpose="systems_characterization",
    )


def characterize_write_amplification() -> dict:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    result = adapter.commit_proposal(
        _proposal("proposal:p9-write", "memory:p9-write"),
        "P9 canonical write characterization",
    )
    if not result.committed:
        raise RuntimeError("P9 write characterization path did not commit")

    receipt_bytes = len(json.dumps(result.receipt, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    event_bytes = sum(
        len(json.dumps(event, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        for event in result.events
    )
    return {
        "canonical_mutations": 1,
        "audit_events": len(result.events),
        "decision_receipts": 1,
        "evidence_records_per_canonical_mutation": len(result.events) + 1,
        "serialized_receipt_bytes": receipt_bytes,
        "serialized_event_bytes": event_bytes,
        "serialized_evidence_bytes": receipt_bytes + event_bytes,
    }


def _seed_substrate(size: int) -> tuple[InMemoryTemporalGraph, GovernedMemoryAdapter]:
    """Seed through the governed path (GAP-ARCH-18, LD2).

    Direct `substrate.write_fact` produces facts with no `_fact_scope` entry,
    which recall now refuses as `unknown_scope` per docs/34:139. Seeding through
    `commit_proposal` also makes this characterize recall over *governed* facts,
    which is the production shape. Only `characterize_recall` consumes this
    helper, and it reports counts and timing -- the module's evidence-byte
    figures come from `characterize_write_amplification`, which builds its own
    adapter, so no published number moves.
    """
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    for index in range(size):
        result = adapter.commit_proposal(
            _proposal(f"proposal:p9-seed-{index}", f"memory:p9-seed-{index}"),
            f"systems characterization token-{index}",
        )
        if not result.committed:
            raise RuntimeError("P9 recall seeding did not commit")
    return substrate, adapter


def characterize_recall(size: int, repeats: int) -> dict:
    _, adapter = _seed_substrate(size)
    latest = None

    def run() -> None:
        nonlocal latest
        latest = adapter.governed_recall("systems characterization")

    timing = _timed(run, repeats)
    assert latest is not None
    return {
        "retained_facts": size,
        "candidate_count": len(latest.candidates),
        "admitted_count": len(latest.admitted),
        "timing": asdict(timing),
    }


def _projection_chain(size: int) -> ProjectionStore:
    store = ProjectionStore()
    source = "memory:p9-root"
    for index in range(size):
        projection_id = f"projection:p9:{index}"
        store.declare(
            Projection(
                projection_id=projection_id,
                basis=((source, 1),),
                transform=DETERMINISTIC,
                content_class=DERIVED_CONTENT,
                rebuild=REPRODUCIBLE,
                scope=TENANT,
            )
        )
        source = projection_id
    return store


def characterize_deletion_closure(size: int, repeats: int) -> dict:
    store = _projection_chain(size)
    latest = None

    def run() -> None:
        nonlocal latest
        latest = store.derivation_closure("memory:p9-root")

    timing = _timed(run, repeats)
    assert latest is not None
    return {
        "projection_depth": size,
        "closure_nodes": len(latest),
        "required_projection_purge_operations": len(latest),
        "timing": asdict(timing),
    }


def build_report(agent_memory_commit: str, sizes: tuple[int, ...] = (10, 100, 500), repeats: int = 5) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent_memory_commit must be an exact 40-character commit SHA")
    if not sizes or any(size <= 0 for size in sizes):
        raise ValueError("sizes must contain positive integers")
    if tuple(sorted(set(sizes))) != sizes:
        raise ValueError("sizes must be unique and strictly increasing")
    if repeats < 1:
        raise ValueError("repeats must be positive")

    recall = [characterize_recall(size, repeats) for size in sizes]
    deletion = [characterize_deletion_closure(size, repeats) for size in sizes]

    structural_invariants = {
        "recall_candidate_count_matches_retained_facts": all(
            row["candidate_count"] == row["retained_facts"] for row in recall
        ),
        "deletion_closure_matches_projection_depth": all(
            row["closure_nodes"] == row["projection_depth"] for row in deletion
        ),
        "structural_work_grows_with_workload": all(
            recall[index]["candidate_count"] < recall[index + 1]["candidate_count"]
            and deletion[index]["closure_nodes"] < deletion[index + 1]["closure_nodes"]
            for index in range(len(sizes) - 1)
        ),
    }

    return {
        "profile": "agent-memory-p9-systems-characterization",
        "version": "1.0.0",
        "agent_memory_commit": agent_memory_commit,
        "runner": {
            "python": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "method": {
            "sizes": list(sizes),
            "timing_repeats": repeats,
            "latency_is_observational_only": True,
            "latency_is_not_a_conformance_gate": True,
            "cost_units_are_provider_neutral": True,
        },
        "write_amplification": characterize_write_amplification(),
        "recall_scaling": recall,
        "deletion_propagation_scaling": deletion,
        "structural_invariants": structural_invariants,
        "structural_invariants_passed": all(structural_invariants.values()),
        "claim_boundary": [
            "reference-runtime characterization, not universal production performance",
            "timing values are runner-specific observations",
            "cost and efficiency do not create memory authority",
            "no external provider pricing or hardware cost claim",
        ],
    }
