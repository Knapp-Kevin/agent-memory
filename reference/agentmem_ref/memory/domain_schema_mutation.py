"""Versioned PAMA support for governed application/domain ontology changes.

This module is intentionally narrow. It adds one known consequential operation
without introducing a canonical domain ontology or giving discovery estimators
any durable authority.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from ..core import policy, receipts

DOMAIN_SCHEMA_MUTATION = "domain_schema_mutation"
PAMA_SCHEMA_VERSION = "1.2.0"

_OUTCOME_ORDER = {
    policy.ALLOW: 0,
    policy.ALLOW_WITH_LEDGER: 1,
    policy.REQUIRE_REVIEW: 2,
    policy.REQUIRE_EXTERNAL_VERIFICATION: 3,
    policy.BLOCK: 4,
}


def required_outcome_for_risk(risk_class: str) -> str:
    """Return the minimum PAMA posture for domain-schema mutation."""
    if risk_class in ("low", "medium"):
        return policy.REQUIRE_REVIEW
    if risk_class in ("high", "critical"):
        return policy.REQUIRE_EXTERNAL_VERIFICATION
    raise ValueError(f"unsupported risk class {risk_class!r}")


def _envelope(outcome: str, operation: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if outcome == policy.REQUIRE_REVIEW:
        return ("enter_pending_verification", "collect_more_evidence", "defer"), (operation,)
    if outcome == policy.REQUIRE_EXTERNAL_VERIFICATION:
        return ("request_external_verification", "collect_more_evidence", "defer"), (operation,)
    if outcome == policy.BLOCK:
        return (), (operation, "enter_pending_verification", "request_external_verification")
    if outcome in (policy.ALLOW, policy.ALLOW_WITH_LEDGER):
        return (operation, "collect_more_evidence", "defer"), ()
    raise ValueError(f"unsupported outcome {outcome!r}")


def _strictest_decision(
    current: policy.Decision,
    minimum_outcome: str,
    operation: str,
    reason: str,
) -> policy.Decision:
    if _OUTCOME_ORDER[current.outcome] >= _OUTCOME_ORDER[minimum_outcome]:
        return current
    permitted, prohibited = _envelope(minimum_outcome, operation)
    return policy.Decision(
        outcome=minimum_outcome,
        permitted_actions=permitted,
        prohibited_actions=prohibited,
        reasons=current.reasons + (reason,),
        policy_version=current.policy_version,
    )


def _scope_expansion_floor(proposal: policy.Proposal) -> policy.Decision:
    scope_proposal = replace(proposal, operation="scope_expansion", review_satisfied=False)
    return policy.evaluate(scope_proposal)


def _discharge_review(decision: policy.Decision, proposal: policy.Proposal) -> policy.Decision:
    if decision.outcome not in (policy.REQUIRE_REVIEW, policy.REQUIRE_EXTERNAL_VERIFICATION):
        return decision
    if not proposal.review_satisfied:
        return decision
    if not proposal.approval_refs or proposal.approves_own_authority:
        return policy.Decision(
            outcome=decision.outcome,
            permitted_actions=decision.permitted_actions,
            prohibited_actions=decision.prohibited_actions,
            reasons=decision.reasons + ("review claimed without an external approval record",),
            policy_version=decision.policy_version,
        )
    permitted, prohibited = _envelope(policy.ALLOW_WITH_LEDGER, proposal.operation)
    return policy.Decision(
        outcome=policy.ALLOW_WITH_LEDGER,
        permitted_actions=permitted,
        prohibited_actions=prohibited,
        reasons=decision.reasons + (f"review discharged by {list(proposal.approval_refs)}",),
        policy_version=decision.policy_version,
    )


def evaluate(
    proposal: policy.Proposal,
    *,
    requested_scope_change: str = "",
) -> policy.Decision:
    """Evaluate a domain-schema mutation while preserving stricter PAMA floors.

    The generic evaluator first runs with review discharge disabled, preserving
    actor, target-class, downstream-authority, isolation, reversibility, and
    evidence constraints. The explicit operation and any scope-expansion floor
    are then applied. Only after those floors exist may a valid external review
    discharge the resulting review/verification requirement.
    """
    if proposal.operation != DOMAIN_SCHEMA_MUTATION:
        raise ValueError("domain-schema evaluator requires domain_schema_mutation")

    undecided_review = replace(proposal, review_satisfied=False)
    decision = policy.evaluate(undecided_review)
    decision = _strictest_decision(
        decision,
        required_outcome_for_risk(proposal.risk_class),
        proposal.operation,
        "domain-schema mutation minimum",
    )

    if requested_scope_change:
        scope_decision = _scope_expansion_floor(undecided_review)
        decision = _strictest_decision(
            decision,
            scope_decision.outcome,
            proposal.operation,
            "scope-expansion floor preserved",
        )

    return _discharge_review(decision, proposal)


def build_pama_decision(
    proposal: policy.Proposal,
    decision: policy.Decision,
    *,
    selected_action: str,
    selection_mode: str | None,
    receipt_ref: str,
    requested_scope_change: str = "",
) -> dict:
    """Build and validate a canonical PAMA 1.2.0 decision artifact."""
    if proposal.operation != DOMAIN_SCHEMA_MUTATION:
        raise ValueError("1.2.0 builder requires domain_schema_mutation")

    document = {
        "schema_version": PAMA_SCHEMA_VERSION,
        "proposal_id": proposal.proposal_id,
        "proposing_actor": {
            "id": proposal.actor_id,
            "charter_version": proposal.charter_version,
        },
        "target": {
            "reference": proposal.target_reference,
            "class": proposal.target_class,
            "scope": proposal.scope,
        },
        "mutation": {
            "operation": proposal.operation,
            "current_strength": proposal.current_strength,
            "proposed_strength": proposal.proposed_strength,
            "downstream_authority": proposal.downstream_authority,
            "reversibility": proposal.reversibility,
            "risk_class": proposal.risk_class,
        },
        "basis": {"evidence_refs": list(proposal.evidence_refs)},
        "policy": {"policy_version": decision.policy_version},
        "decision": {
            "outcome": decision.outcome,
            "permitted_actions": list(decision.permitted_actions),
            "prohibited_actions": list(decision.prohibited_actions),
            "selected_action": None if selected_action == receipts.NO_ACTION else selected_action,
            "selection_mode": selection_mode,
            "decision_receipt_ref": receipt_ref,
        },
    }
    if requested_scope_change:
        document["mutation"]["requested_scope_change"] = requested_scope_change
    if proposal.tenant_ref:
        document["target"]["tenant_ref"] = proposal.tenant_ref
    if proposal.purpose:
        document["target"]["purpose"] = proposal.purpose
    if proposal.estimator_refs:
        document["basis"]["estimator_refs"] = list(proposal.estimator_refs)
    if proposal.estimator_versions:
        document["basis"]["estimator_versions"] = list(proposal.estimator_versions)
    if proposal.confidence is not None:
        document["basis"]["confidence"] = proposal.confidence

    receipts.validate("pama-decision.schema.json", document)
    return document


def enforce_consumer_compatibility(
    pama_decision: dict,
    *,
    supported_schema_versions: Iterable[str],
    supported_operations: Iterable[str] | None = None,
) -> None:
    """Fail explicitly when a consequential consumer cannot interpret the record."""
    receipts.validate("pama-decision.schema.json", pama_decision)
    version = pama_decision.get("schema_version")
    if version not in set(supported_schema_versions):
        raise ValueError(f"unsupported PAMA schema version {version!r}")

    if supported_operations is not None:
        operation = pama_decision["mutation"]["operation"]
        if operation not in set(supported_operations):
            raise ValueError(f"unsupported PAMA operation {operation!r}")
