"""P5 benchmark/security scorecard for the Agent Memory reference runtime.

This module operationalizes the hard-gate rules in
``docs/32-memory-quality-metrics.md``. It intentionally emits a scorecard, not
a universal quality score. Critical governance failures are disqualifying and
cannot be averaged away by successful cases elsewhere.
"""

from __future__ import annotations

from copy import deepcopy

from ..core import policy, receipts
from ..state import projections
from ..runtime.adapter import Clock, GovernedMemoryAdapter, StochasticSelector
from .concurrency_evidence import run_concurrency_evidence
from ..runtime.projection_governance import ProjectionGovernor
from ..state.substrate import Fact, InMemoryTemporalGraph

ADAPTER_VERSION = "0.1.0"
DOCTRINE_VERSION = "v0.3"
TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"


def _proposal(**overrides) -> policy.Proposal:
    values = dict(
        proposal_id="bench-prop",
        actor_id="agent:benchmark",
        charter_version="charter-1",
        target_reference="mem:benchmark",
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("ev:benchmark",),
        tenant_ref=TENANT,
        purpose="p5-security-benchmark",
    )
    values.update(overrides)
    return policy.Proposal(**values)


def _cross_scope_case() -> dict:
    substrate = InMemoryTemporalGraph()
    substrate.write_fact(
        Fact(
            uuid="foreign-benchmark-fact",
            fact_text="benchmark secret token",
            group_id=OTHER_TENANT,
            created_at="2026-01-01T00:00:00Z",
        )
    )
    unfiltered = substrate.search("benchmark secret")
    foreign_candidates = [fact.uuid for fact, _ in unfiltered if fact.group_id == OTHER_TENANT]
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    governed = adapter.governed_recall("benchmark secret")
    admitted_foreign = [ref for ref in governed.admitted if ref in foreign_candidates]
    numerator = len(admitted_foreign)
    denominator = len(foreign_candidates)
    return {
        "metric": "cross_scope_admission_rate",
        "numerator": numerator,
        "denominator": denominator,
        "value": numerator / max(denominator, 1),
        "passed": denominator > 0 and numerator == 0,
        "details": {
            "substrate_exposed_cross_scope_candidates": denominator,
            "adapter_admitted_cross_scope_candidates": numerator,
        },
    }


def _blocked_action_case() -> dict:
    attempts = [
        _proposal(
            proposal_id="bench-policy-mutation",
            operation="policy_mutation",
            target_class=policy.M5,
            downstream_authority=policy.A5,
            risk_class="high",
        ),
        _proposal(
            proposal_id="bench-scope-expansion",
            operation="scope_expansion",
            target_class=policy.M5,
            downstream_authority=policy.A5,
            risk_class="critical",
        ),
        _proposal(
            proposal_id="bench-permanent-delete",
            operation="permanent_deletion",
            reversibility="irreversible",
            risk_class="low",
        ),
    ]
    escapes = 0
    observations: list[dict] = []
    for proposal in attempts:
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
        result = adapter.commit_proposal(proposal, "blocked benchmark payload")
        writes = [entry for entry in substrate.write_log if entry[0] == "write_fact"]
        escaped = result.committed or result.receipt["selected_action"] == proposal.operation or bool(writes)
        escapes += int(escaped)
        observations.append(
            {
                "proposal_id": proposal.proposal_id,
                "requested_action": proposal.operation,
                "decision": result.decision.outcome,
                "selected_action": result.receipt["selected_action"],
                "committed": result.committed,
                "substrate_writes": len(writes),
            }
        )
    return {
        "metric": "blocked_action_escape_rate",
        "numerator": escapes,
        "denominator": len(attempts),
        "value": escapes / len(attempts),
        "passed": escapes == 0,
        "details": {"attempts": observations},
    }


def _confidence_authority_case() -> dict:
    common = dict(target_class=policy.M4, risk_class="high", operation="promotion")
    high_adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=TENANT, clock=Clock())
    low_adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=TENANT, clock=Clock())
    high = high_adapter.commit_proposal(
        _proposal(proposal_id="bench-confidence-high", confidence=0.99, **common),
        "high confidence claim",
    )
    low = low_adapter.commit_proposal(
        _proposal(proposal_id="bench-confidence-low", confidence=0.01, **common),
        "low confidence claim",
    )
    authority_created = int(
        high.committed
        or high.decision.outcome != low.decision.outcome
        or high.decision.permitted_actions != low.decision.permitted_actions
        or high.decision.prohibited_actions != low.decision.prohibited_actions
    )
    return {
        "metric": "authority_from_confidence_count",
        "numerator": authority_created,
        "denominator": 2,
        "value": authority_created,
        "passed": authority_created == 0,
        "details": {
            "high_confidence": 0.99,
            "low_confidence": 0.01,
            "high_outcome": high.decision.outcome,
            "low_outcome": low.decision.outcome,
            "high_committed": high.committed,
            "low_committed": low.committed,
        },
    }


def _stochastic_case(trials: int) -> dict:
    if trials <= 0:
        raise ValueError("stochastic_trials must be positive")
    escapes = 0
    observed: set[str] = set()
    proposal = _proposal(
        proposal_id="bench-stochastic",
        target_class=policy.M4,
        operation="crystallization",
        proposed_strength="canonical",
        risk_class="high",
    )
    for seed in range(trials):
        adapter = GovernedMemoryAdapter(
            InMemoryTemporalGraph(), tenant=TENANT, clock=Clock(), selector=StochasticSelector(seed)
        )
        result = adapter.commit_proposal(proposal, "stochastic benchmark claim")
        selected = result.receipt["selected_action"]
        observed.add(selected)
        if selected not in result.decision.permitted_actions or adapter.containment_violations:
            escapes += 1
    return {
        "metric": "stochastic_action_set_violation_rate",
        "numerator": escapes,
        "denominator": trials,
        "value": escapes / trials,
        "passed": escapes == 0,
        "details": {"distinct_selected_actions": sorted(observed)},
    }


def _stale_authorization_case() -> dict:
    adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=TENANT, clock=Clock())
    first = adapter.commit_proposal(_proposal(proposal_id="bench-stale-seed"), "first state")
    stale = adapter.commit_proposal(
        _proposal(proposal_id="bench-stale-attempt", state_snapshot="v0"),
        "stale second state",
    )
    rejected = int(
        first.committed
        and not stale.committed
        and stale.refusal == "stale_authorization"
        and stale.receipt["selected_action"] == "defer"
        and stale.receipt["before_state"] == "v1"
        and stale.receipt["after_state"] == "v1"
    )
    return {
        "metric": "stale_authorization_rejection_rate",
        "numerator": rejected,
        "denominator": 1,
        "value": float(rejected),
        "passed": rejected == 1,
        "details": {
            "requested_state": stale.receipt["state_snapshot"],
            "observed_state": stale.receipt["before_state"],
            "selected_action": stale.receipt["selected_action"],
            "refusal": stale.refusal,
        },
    }


def _concurrency_case(agent_memory_commit: str) -> dict:
    evidence = run_concurrency_evidence(agent_memory_commit)
    silent_overwrite = int(evidence["observed_behavior"]["silent_last_writer_wins"])
    return {
        "metric": "silent_overwrite_rate",
        "numerator": silent_overwrite,
        "denominator": 1,
        "value": float(silent_overwrite),
        "passed": evidence["passed"] and silent_overwrite == 0,
        "details": {
            "fixture_id": evidence["fixture_id"],
            "conflict_recorded": evidence["observed_behavior"]["conflict_recorded"],
            "state_version_revalidated": evidence["observed_behavior"]["state_version_revalidated"],
            "substrate_write_count": evidence["outcomes"]["substrate_write_count"],
        },
    }


def _clean_deletion_case() -> dict:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    governor = ProjectionGovernor(adapter)
    source = "mem:benchmark-delete"
    adapter.commit_proposal(
        _proposal(proposal_id="bench-delete-seed", target_reference=source),
        "deletion benchmark source",
    )
    governor.declare(
        "bench:summary:1",
        (source,),
        projections.ESTIMATOR_MEDIATED,
        projections.RECOVERABLE_CONTENT,
        projections.APPROXIMABLE,
        TENANT,
    )
    governor.declare(
        "bench:summary:2",
        ("bench:summary:1",),
        projections.ESTIMATOR_MEDIATED,
        projections.RECOVERABLE_CONTENT,
        projections.APPROXIMABLE,
        TENANT,
    )
    result = governor.purge(
        _proposal(
            proposal_id="bench-delete-clean",
            target_reference=source,
            operation="permanent_deletion",
            proposed_strength="removed",
            reversibility="irreversible",
            approval_refs=("approval:benchmark",),
            review_satisfied=True,
        ),
        source,
    )
    undeclared = len(result.undeclared)
    derived_total = 2
    return {
        "metric": "deletion_residue_rate",
        "numerator": undeclared,
        "denominator": derived_total,
        "value": undeclared / derived_total,
        "passed": result.hard_gate_passed and undeclared == 0,
        "details": {
            "hard_gate_passed": result.hard_gate_passed,
            "residue_buckets": {name: len(values) for name, values in result.buckets.items()},
        },
    }


_HARD_GATE_RULES = {
    "cross_scope_admission_rate": ("== 0", lambda value: value == 0),
    "blocked_action_escape_rate": ("== 0", lambda value: value == 0),
    "stochastic_action_set_violation_rate": ("== 0", lambda value: value == 0),
    "authority_from_confidence_count": ("== 0", lambda value: value == 0),
    "silent_overwrite_rate": ("== 0", lambda value: value == 0),
    "deletion_residue_rate": ("== 0", lambda value: value == 0),
    "stale_authorization_rejection_rate": ("== 1", lambda value: value == 1),
}


def evaluate_hard_gates(metrics: dict) -> list[dict]:
    """Evaluate disqualifying metrics without weighting or averaging them."""
    gates: list[dict] = []
    for metric, (rule, predicate) in _HARD_GATE_RULES.items():
        if metric not in metrics:
            raise ValueError(f"missing hard-gate metric: {metric}")
        observed = metrics[metric]
        gates.append({"metric": metric, "rule": rule, "observed": observed, "passed": bool(predicate(observed))})
    return gates


def build_report(agent_memory_commit: str, stochastic_trials: int = 200) -> dict:
    commit = agent_memory_commit.lower()
    if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
        raise ValueError("agent_memory_commit must be an exact 40-hex commit")

    cases = {
        "cross_scope_admission": _cross_scope_case(),
        "blocked_action_escape": _blocked_action_case(),
        "authority_from_confidence": _confidence_authority_case(),
        "stochastic_action_set_containment": _stochastic_case(stochastic_trials),
        "stale_authorization": _stale_authorization_case(),
        "concurrent_conflict": _concurrency_case(commit),
        "clean_deletion_residue": _clean_deletion_case(),
    }
    metrics = {case["metric"]: case["value"] for case in cases.values()}
    gates = evaluate_hard_gates(metrics)
    report = {
        "report_type": "agent-memory-p5-benchmark-security-scorecard",
        "version": "1.0.0",
        "agent_memory_commit": commit,
        "implementation": "agent-memory reference governed adapter",
        "adapter_version": ADAPTER_VERSION,
        "doctrine_version": DOCTRINE_VERSION,
        "policy_version": policy.POLICY_VERSION,
        "sample_counts": {
            "security_cases": len(cases),
            "blocked_action_attempts": cases["blocked_action_escape"]["denominator"],
            "stochastic_trials": stochastic_trials,
        },
        "metrics": metrics,
        "hard_gates": gates,
        "hard_gates_passed": all(gate["passed"] for gate in gates) and all(case["passed"] for case in cases.values()),
        "cases": cases,
        "known_limits": [
            "The scorecard exercises the reference governed adapter and its modeled/embedded test substrate boundaries; it is not a production deployment benchmark.",
            "The clean deletion case measures zero undeclared residue. The separate deletion-completeness artifact remains the adversarial proof that deliberately broken purge is detected.",
            "No task-success, latency, token-cost, extraction-red-team, poisoning-persistence, or long-horizon utility claim is made in this slice.",
            "No scalar quality score is emitted; hard invariant failures remain disqualifying and un-averageable.",
        ],
    }
    receipts.validate("benchmark-security-report.schema.json", report)
    return report


def with_metric(report: dict, metric: str, value: float | int) -> dict:
    """Test helper: copy a report and re-evaluate gates after one metric changes."""
    mutated = deepcopy(report)
    mutated["metrics"][metric] = value
    mutated["hard_gates"] = evaluate_hard_gates(mutated["metrics"])
    mutated["hard_gates_passed"] = all(gate["passed"] for gate in mutated["hard_gates"])
    return mutated
