"""Executable evidence for concurrent conflicting durable mutations.

The reference adapter already binds authorization to a proposal's
``state_snapshot``. This module turns that primitive into an explicit runtime
evidence scenario for ADR-020 item 9 and the
``concurrent-conflicting-mutation`` doctrine fixture.

Two actors construct incompatible proposals against the same canonical state.
The first write advances the state. The second proposal keeps its original
snapshot and is therefore stale at commit time. The adapter must refuse it,
leaving exactly one substrate write and enough receipt data to reconstruct the
conflict.

This is optimistic concurrency evidence, not a claim of distributed serializable
transactions or multi-process locking.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import policy
from .adapter import Clock, GovernedMemoryAdapter
from .substrate import InMemoryTemporalGraph

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "concurrent-conflicting-mutation.json"
TARGET = "mem:concurrent-runtime"
TENANT = "tenant-a"


def _proposal(proposal_id: str, actor_id: str, state_snapshot: str, evidence_ref: str) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id=actor_id,
        charter_version="charter-1",
        target_reference=TARGET,
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=(evidence_ref,),
        estimator_refs=("est:concurrency-candidate",),
        estimator_versions=("v1",),
        confidence=0.8,
        state_snapshot=state_snapshot,
        tenant_ref=TENANT,
        purpose="concurrency-evidence",
    )


def run_concurrency_evidence(agent_memory_commit: str) -> dict:
    """Run the two-proposal state-version race and return machine-readable evidence."""
    if len(agent_memory_commit) != 40 or any(ch not in "0123456789abcdef" for ch in agent_memory_commit.lower()):
        raise ValueError("agent_memory_commit must be an exact 40-hex commit")

    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    expected = fixture["expected_behavior"]

    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())

    initial_state = f"v{adapter.state_version(TARGET)}"
    proposal_a = _proposal("prop-concurrent-a", "agent:a", initial_state, "ev:concurrent-a")
    proposal_b = _proposal("prop-concurrent-b", "agent:b", initial_state, "ev:concurrent-b")

    first = adapter.commit_proposal(proposal_a, "candidate A")
    state_after_first = f"v{adapter.state_version(TARGET)}"
    second = adapter.commit_proposal(proposal_b, "candidate B")
    final_state = f"v{adapter.state_version(TARGET)}"

    writes = [entry for entry in substrate.write_log if entry[0] == "write_fact"]
    surviving_facts = list(substrate.all_facts())

    state_revalidated = (
        second.receipt["state_snapshot"] == initial_state
        and second.receipt["before_state"] == state_after_first
        and second.receipt["after_state"] == state_after_first
        and second.refusal == "stale_authorization"
    )
    conflict_recorded = (
        first.committed
        and not second.committed
        and second.refusal == "stale_authorization"
        and second.receipt["selected_action"] == "defer"
    )
    silent_last_writer_wins = len(writes) > 1 or len(surviving_facts) > 1 or final_state != state_after_first

    observed = {
        "silent_last_writer_wins": silent_last_writer_wins,
        "conflict_recorded": conflict_recorded,
        "state_version_revalidated": state_revalidated,
    }
    passed = observed == expected

    return {
        "schema_version": "1.0.0",
        "agent_memory_commit": agent_memory_commit.lower(),
        "fixture_id": fixture["fixture_id"],
        "fixture_version": fixture["fixture_version"],
        "scenario": {
            "target_ref": TARGET,
            "initial_state": initial_state,
            "proposal_a_snapshot": proposal_a.state_snapshot,
            "proposal_b_snapshot": proposal_b.state_snapshot,
        },
        "outcomes": {
            "proposal_a": {
                "proposal_id": proposal_a.proposal_id,
                "committed": first.committed,
                "receipt_ref": first.receipt["receipt_id"],
                "before_state": first.receipt["before_state"],
                "after_state": first.receipt["after_state"],
            },
            "proposal_b": {
                "proposal_id": proposal_b.proposal_id,
                "committed": second.committed,
                "receipt_ref": second.receipt["receipt_id"],
                "requested_state": second.receipt["state_snapshot"],
                "observed_state": second.receipt["before_state"],
                "after_state": second.receipt["after_state"],
                "selected_action": second.receipt["selected_action"],
                "refusal": second.refusal,
            },
            "final_state": final_state,
            "substrate_write_count": len(writes),
            "surviving_fact_count": len(surviving_facts),
        },
        "conflict_record": {
            "winning_proposal_id": proposal_a.proposal_id,
            "rejected_proposal_id": proposal_b.proposal_id,
            "rejected_receipt_ref": second.receipt["receipt_id"],
            "expected_state": proposal_b.state_snapshot,
            "observed_state": second.receipt["before_state"],
            "resolution": second.receipt["selected_action"],
            "reason": second.refusal,
        },
        "expected_behavior": expected,
        "observed_behavior": observed,
        "passed": passed,
        "limitations": [
            "This proves optimistic state-version conflict handling in the reference adapter, not distributed serializability.",
            "The scenario is deterministically interleaved so both proposals originate from the same prior state; it does not claim thread-scheduler coverage.",
            "A stale proposal is deferred and recorded in the evidence report; automatic conflict resolution is not demonstrated.",
        ],
    }
