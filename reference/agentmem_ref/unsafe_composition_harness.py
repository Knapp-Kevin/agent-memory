"""Fixture-linked unsafe multi-memory composition evidence for issue #206.

This module does not redefine composition policy. It exercises the existing
set-level gate from #132 against the named security fixture and makes the final
assembled-context/downstream surfaces explicit for evidence accounting.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import policy
from .adapter import Clock, GovernedMemoryAdapter, RecallContext
from .composition import CompositionCandidate, CompositionConstraint, evaluate_composition
from .substrate import InMemoryTemporalGraph

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "unsafe-multi-memory-composition.json"
TENANT = "tenant-a"
DOMAIN_RED = "domain:composition-red"
DOMAIN_BLUE = "domain:composition-blue"
DOMAIN_GREEN = "domain:composition-green"
QUERY = "rotation evidence shared composition token"


def _proposal(reference: str, domain: str) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=f"composition-evidence:{reference}",
        actor_id="agent:composition-evidence",
        charter_version="charter:composition-evidence-v1",
        target_reference=reference,
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=(f"evidence:{reference}",),
        tenant_ref=TENANT,
        purpose="unsafe-composition-evidence",
        isolation_domain_refs=(domain,),
    )


def _setup() -> tuple[GovernedMemoryAdapter, str, str]:
    adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=TENANT, clock=Clock())
    red = adapter.commit_proposal(_proposal("mem:composition-red", DOMAIN_RED), QUERY)
    blue = adapter.commit_proposal(_proposal("mem:composition-blue", DOMAIN_BLUE), QUERY)
    if not red.committed or not blue.committed or red.fact_uuid is None or blue.fact_uuid is None:
        raise AssertionError("unsafe-composition harness setup could not commit both bounded memories")
    return adapter, red.fact_uuid, blue.fact_uuid


def _surface(result) -> tuple[list[str], list[str]]:
    """Return bounded context/downstream identity surfaces for the composition.

    The reference proof does not model a downstream agent. It records only
    whether the composition gate made the requested memory set eligible for
    assembly/influence. A rejected set therefore has no output surface.
    """
    if not result.allowed:
        return [], []
    assembled = list(result.memory_refs)
    return assembled, list(assembled)


def run_unsafe_composition_harness() -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected = fixture["expected_behavior"]
    adapter, red_uuid, blue_uuid = _setup()

    recall = adapter.governed_recall(
        QUERY,
        RecallContext(
            target_domain_refs=(DOMAIN_RED, DOMAIN_BLUE),
            principal_ref="principal:composition-evidence",
            purpose="unsafe-composition-evidence",
        ),
    )
    candidates = (
        CompositionCandidate(red_uuid, (DOMAIN_RED,)),
        CompositionCandidate(blue_uuid, (DOMAIN_BLUE,)),
    )
    fixture_constraint = CompositionConstraint(
        constraint_ref="fixture:memory-a-plus-memory-b",
        prohibited_domain_set=(DOMAIN_RED, DOMAIN_BLUE),
        reason="fixture-defined combined context is unsafe",
    )

    blocked = evaluate_composition(
        candidates,
        admitted_memory_refs=tuple(recall.admitted),
        constraints=(fixture_constraint,),
    )
    assembled_context, downstream_influence = _surface(blocked)

    no_constraint = evaluate_composition(
        candidates,
        admitted_memory_refs=tuple(recall.admitted),
        constraints=(),
    )
    unrelated_constraint = evaluate_composition(
        candidates,
        admitted_memory_refs=tuple(recall.admitted),
        constraints=(
            CompositionConstraint(
                constraint_ref="policy:red-green-only",
                prohibited_domain_set=(DOMAIN_RED, DOMAIN_GREEN),
                reason="unrelated domain combination",
            ),
        ),
    )
    reversed_candidates = tuple(reversed(candidates))
    reversed_constraint = CompositionConstraint(
        constraint_ref="fixture:memory-a-plus-memory-b",
        prohibited_domain_set=(DOMAIN_BLUE, DOMAIN_RED),
        reason="same set, reversed declaration order",
    )
    reversed_result = evaluate_composition(
        reversed_candidates,
        admitted_memory_refs=tuple(reversed(recall.admitted)),
        constraints=(reversed_constraint,),
    )
    duplicate_result = evaluate_composition(
        (candidates[0], candidates[0]),
        admitted_memory_refs=tuple(recall.admitted),
        constraints=(),
    )
    unresolved_result = evaluate_composition(
        (
            candidates[0],
            CompositionCandidate(blue_uuid, ()),
        ),
        admitted_memory_refs=tuple(recall.admitted),
        constraints=(),
    )
    unadmitted_result = evaluate_composition(
        candidates,
        admitted_memory_refs=(red_uuid,),
        constraints=(),
    )

    # Prove a candidate denied by ordinary recall cannot be rescued by a set-level
    # composition that would otherwise carry no explicit prohibition.
    adapter.mark_disputed(blue_uuid)
    denied_recall = adapter.governed_recall(
        QUERY,
        RecallContext(
            target_domain_refs=(DOMAIN_RED, DOMAIN_BLUE),
            principal_ref="principal:composition-evidence",
            purpose="unsafe-composition-evidence",
        ),
    )
    denied_candidate_result = evaluate_composition(
        candidates,
        admitted_memory_refs=tuple(denied_recall.admitted),
        constraints=(),
    )

    checks = {
        "fixture_individual_candidates_may_pass": expected["individual_candidates_may_pass"] is True,
        "fixture_combined_context_not_admitted": expected["combined_context_admitted"] is False,
        "fixture_composition_governance_runs": expected["composition_governance_runs"] is True,
        "both_candidates_discovered": red_uuid in recall.candidates and blue_uuid in recall.candidates,
        "both_candidates_individually_admitted": red_uuid in recall.admitted and blue_uuid in recall.admitted,
        "unsafe_combination_rejected": not blocked.allowed,
        "composition_reason_reconstructable": blocked.reason == "cross_domain_composition_prohibited",
        "violated_constraint_reconstructable": blocked.violated_constraint_refs == ("fixture:memory-a-plus-memory-b",),
        "domain_provenance_reconstructable": set(blocked.domain_refs) == {DOMAIN_RED, DOMAIN_BLUE},
        "blocked_composition_has_no_assembled_context": assembled_context == [],
        "blocked_composition_has_no_downstream_influence": downstream_influence == [],
        "no_constraint_does_not_invent_block": no_constraint.allowed,
        "unrelated_constraint_does_not_invent_block": unrelated_constraint.allowed,
        "candidate_order_cannot_bypass_gate": not reversed_result.allowed,
        "constraint_domain_order_is_semantically_set_like": reversed_result.reason == "cross_domain_composition_prohibited",
        "duplicate_refs_fail_closed": not duplicate_result.allowed and duplicate_result.reason == "duplicate_memory_reference",
        "unresolved_domain_fails_closed": (
            not unresolved_result.allowed and unresolved_result.reason == "composition_candidate_scope_unresolved"
        ),
        "unadmitted_candidate_fails_closed": (
            not unadmitted_result.allowed and unadmitted_result.reason == "composition_candidate_not_admitted"
        ),
        "ordinary_recall_denial_survives_composition": (
            blue_uuid not in denied_recall.admitted
            and denied_recall.refusals.get(blue_uuid) == "disputed"
            and not denied_candidate_result.allowed
            and denied_candidate_result.reason == "composition_candidate_not_admitted"
        ),
    }

    return {
        "case_id": "unsafe-multi-memory-composition",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "candidate_refs": [red_uuid, blue_uuid],
            "individual_admitted_refs": list(recall.admitted),
            "blocked": {
                "reason": blocked.reason,
                "domain_refs": list(blocked.domain_refs),
                "violated_constraint_refs": list(blocked.violated_constraint_refs),
                "assembled_context": assembled_context,
                "downstream_influence": downstream_influence,
            },
            "no_constraint_allowed": no_constraint.allowed,
            "unrelated_constraint_allowed": unrelated_constraint.allowed,
            "reversed_order_allowed": reversed_result.allowed,
            "denied_recall_refusals": denied_recall.refusals,
        },
    }
