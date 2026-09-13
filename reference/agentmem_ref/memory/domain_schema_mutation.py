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


def required_outcome_for_risk(risk_class: str) -> str:
    """Return the PAMA 1.2 base posture for domain-schema mutation."""
    if risk_class in ("low", "medium"):
        return policy.REQUIRE_REVIEW
    if risk_class in ("high", "critical"):
        return policy.REQUIRE_EXTERNAL_VERIFICATION
    raise ValueError(f"unsupported risk class {risk_class!r}")


def evaluate(
    proposal: policy.Proposal,
    *,
    requested_scope_change: str = "",
    evidence=None,
    attestation: policy.ExternalVerification | None = None,
    verifier_registry=None,
) -> policy.Decision:
    """Evaluate PAMA 1.2 domain-schema mutation through shared authority logic.

    The 1.2 profile owns the operation's base risk cell. Shared PAMA owns every
    authority floor, modifier, and discharge mechanism. This matters because
    ADR-037 removed caller-asserted ``review_satisfied`` / ``approval_refs`` as
    an authority path after this profile originally shipped.

    Qualified evidence is grouped through an evaluator-held ``VerifierRegistry``
    when one is supplied. A bound attestation can discharge only an existing
    ``require_external_verification`` outcome. With neither, review remains
    fail-closed and the shared evaluator names the remediation route.
    """
    if proposal.operation != DOMAIN_SCHEMA_MUTATION:
        raise ValueError("domain-schema evaluator requires domain_schema_mutation")

    if requested_scope_change and proposal.requested_scope_change:
        if requested_scope_change != proposal.requested_scope_change:
            raise ValueError("requested_scope_change disagrees with proposal")
    scope_change = requested_scope_change or proposal.requested_scope_change
    evaluated = (
        replace(proposal, requested_scope_change=scope_change)
        if scope_change != proposal.requested_scope_change
        else proposal
    )
    base = required_outcome_for_risk(evaluated.risk_class)

    if evidence:
        from ..core.evidence_qualification import group_by_dependence

        return policy.evaluate_with_qualified_evidence(
            evaluated,
            group_by_dependence(
                evidence,
                verifiers=(verifier_registry.as_mapping() if verifier_registry else None),
            ),
            base_outcome=base,
            attestation=attestation,
        )
    if attestation is not None:
        return policy.evaluate_with_external_verification(
            evaluated,
            attestation,
            base_outcome=base,
        )
    return policy.evaluate_with_base_outcome(
        evaluated,
        base_outcome=base,
    )


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
    scope_change = requested_scope_change or proposal.requested_scope_change
    if scope_change:
        document["mutation"]["requested_scope_change"] = scope_change
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
