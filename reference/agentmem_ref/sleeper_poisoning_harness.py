"""Behavioral sleeper-poisoning proof for issue #200."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import policy
from .adapter import Clock, GovernedMemoryAdapter, RecallContext
from .contextual_recall import ContextualRule, DeterministicContextualRecallPolicy
from .contextual_recall_adapter import ContextualRecallAdapter
from .substrate import InMemoryTemporalGraph

ROOT = Path(__file__).resolve().parents[2]
SLEEPER_FIXTURE = ROOT / "fixtures" / "sleeper-memory-poisoning.json"


def _proposal() -> policy.Proposal:
    return policy.Proposal(
        proposal_id="proposal:sleeper:retain",
        actor_id="actor:bounded-ingest",
        charter_version="charter:v1",
        target_reference="mem:sleeper:behavioral",
        target_class=policy.M2,
        scope="scope:tenant-a/project-a",
        operation="promotion",
        current_strength="observed",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("fixture:sleeper-memory-poisoning", "evidence:delayed-trigger"),
        tenant_ref="tenant-a",
        project_ref="project-a",
        purpose="bounded-procedural-context",
        isolation_domain_refs=("scope:tenant-a/project-a",),
    )


def _context(purpose: str) -> RecallContext:
    # The reference substrate retrieves by tenant group_id while canonical
    # admission also checks isolation-domain membership. Carry both identities
    # so the behavioral proof exercises admission rather than an empty search.
    return RecallContext(
        target_domain_refs=("tenant-a", "scope:tenant-a/project-a"),
        principal_ref="principal:sleeper-test",
        project_ref="project-a",
        purpose=purpose,
    )


def run_sleeper_poisoning_harness() -> dict[str, Any]:
    fixture = json.loads(SLEEPER_FIXTURE.read_text(encoding="utf-8"))
    expected = fixture["expected_behavior"]

    substrate = InMemoryTemporalGraph()
    base = GovernedMemoryAdapter(substrate, tenant="tenant-a", clock=Clock())
    commit = base.commit_proposal(
        _proposal(),
        "procedural helper retained from an earlier benign interaction",
    )
    if not commit.committed or commit.fact_uuid is None:
        raise AssertionError(f"sleeper harness could not retain candidate: {commit.refusal}")

    fact_uuid = commit.fact_uuid
    contextual_policy = DeterministicContextualRecallPolicy(
        policy_ref="contextual-policy:sleeper-v1",
        policy_version="1.0.0",
        rules=(
            ContextualRule(
                rule_id="delayed-trigger-quarantine",
                candidate_ref=fact_uuid,
                purpose="activate-triggered-memory",
                outcome="quarantine",
                reason_code="delayed_trigger_requires_quarantine",
                evidence_refs=("fixture:sleeper-memory-poisoning", "evidence:delayed-trigger"),
                risk_evidence={
                    "signal_ref": "risk-signal:sleeper-trigger:1",
                    "signal_semantics": "probabilistic_delayed_activation_risk",
                    "estimator_ref": "estimator:sleeper-risk",
                    "estimator_version": "v1",
                    "signal_value": 0.95,
                    "uncertainty_summary": "High estimated activation risk under the delayed trigger context; estimate informs policy but does not authorize consequence.",
                },
            ),
        ),
    )
    recall = ContextualRecallAdapter(base, policy=contextual_policy, clock=Clock(start=50))

    benign = recall.governed_recall("procedural helper", _context("bounded-procedural-context"))
    triggered = recall.governed_recall("procedural helper", _context("activate-triggered-memory"))
    trigger_decision = triggered.contextual_decisions.get(fact_uuid)

    stored_after = substrate.get_fact(fact_uuid)
    checks = {
        "fixture_write_time_check_may_pass": expected["write_time_check_may_pass"] is True,
        "fixture_later_trigger_rechecked": expected["later_trigger_rechecked"] is True,
        "fixture_unsafe_activation_forbidden": expected["unsafe_activation_allowed"] is False,
        "retained_candidate_committed": commit.committed and stored_after is not None,
        "benign_candidate_discovered": fact_uuid in benign.candidates,
        "benign_candidate_admitted": fact_uuid in benign.admitted,
        "benign_context_surface_contains_candidate": fact_uuid in benign.context_surface,
        "same_candidate_discovered_after_trigger": fact_uuid in triggered.candidates,
        "trigger_context_re_evaluated": contextual_policy.evaluation_count == 2,
        "trigger_decision_exists": trigger_decision is not None,
        "trigger_decision_quarantines": trigger_decision is not None and trigger_decision["outcome"] == "quarantine",
        "trigger_policy_version_reconstructable": (
            trigger_decision is not None
            and trigger_decision["policy"]["policy_version"] == "1.0.0"
        ),
        "risk_signal_not_authority": (
            trigger_decision is not None
            and trigger_decision["interpretation"]["risk_signal_authority"] == "none"
        ),
        "prior_admission_not_authority": (
            trigger_decision is not None
            and trigger_decision["interpretation"]["prior_admission_authority"] == "none"
        ),
        "triggered_candidate_not_admitted": fact_uuid not in triggered.admitted,
        "triggered_candidate_absent_from_context_surface": fact_uuid not in triggered.context_surface,
        "triggered_candidate_absent_from_downstream_influence": fact_uuid not in triggered.downstream_influence,
        "stored_candidate_not_mutated_to_force_test": (
            stored_after is not None
            and stored_after.fact_text == "procedural helper retained from an earlier benign interaction"
            and not stored_after.is_event_invalid
        ),
    }

    observed = {
        "fact_uuid": fact_uuid,
        "benign": {
            "candidates": benign.candidates,
            "admitted": benign.admitted,
            "refusals": benign.refusals,
            "decision": benign.contextual_decisions.get(fact_uuid),
        },
        "triggered": {
            "candidates": triggered.candidates,
            "admitted": triggered.admitted,
            "refusals": triggered.refusals,
            "context_surface": triggered.context_surface,
            "downstream_influence": triggered.downstream_influence,
            "decision": trigger_decision,
        },
        "fixture_expected_behavior": expected,
        "policy_evaluation_count": contextual_policy.evaluation_count,
    }
    return {"case_id": "sleeper-delayed-trigger-recall", "passed": all(checks.values()), "checks": checks, "observed": observed}
