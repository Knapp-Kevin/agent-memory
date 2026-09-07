"""The public contract: versioned envelopes, ADR-030 compatibility, and the conversions behind them.

Sprint 4a (plan ``docs/plan-sprint4a-public-api-contract.md``, LD1 and LD3). A
consumer expresses a proposal or a recall context as a schema-backed envelope
carrying ``contract_version``; the surface converts it to the internal
dataclasses and projects decisions back out. The evaluator-side fields of
``Proposal`` -- ``review_satisfied``, ``approval_refs``,
``approves_own_authority``, ``actor_authority_resolved`` -- are not part of the
contract and are rejected at validation, so no envelope can assert a review.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping

from ..core import policy, receipts
from ..runtime.adapter import RecallContext

CONTRACT_VERSION = "1.0.0"

PROPOSAL_SCHEMA = "api-proposal-envelope.schema.json"
RECALL_CONTEXT_SCHEMA = "api-recall-context.schema.json"
RESULT_SCHEMA = "api-result-envelope.schema.json"

CURRENT = "current"
MIGRATION_REQUIRED = "migration_required"
INCOMPATIBLE = "incompatible"
UNKNOWN = "unknown"

#: The Proposal fields a consumer may set. Everything else on Proposal is evaluator-side.
PUBLIC_PROPOSAL_FIELDS = (
    "proposal_id", "actor_id", "charter_version", "target_reference", "target_class", "scope",
    "operation", "current_strength", "proposed_strength", "downstream_authority", "reversibility",
    "risk_class", "evidence_refs", "estimator_refs", "estimator_versions", "confidence",
    "requested_scope_change", "state_snapshot", "tenant_ref", "purpose", "isolation_domain_refs",
    "required_isolation_domain_refs", "project_ref", "task_ref",
)
_TUPLE_FIELDS = (
    "evidence_refs", "estimator_refs", "estimator_versions", "isolation_domain_refs",
    "required_isolation_domain_refs",
)


def compatibility(envelope: Mapping[str, Any]) -> str:
    """ADR-030's four states for the envelope's ``contract_version`` against ``CONTRACT_VERSION``."""
    raw = envelope.get("contract_version") if isinstance(envelope, Mapping) else None
    try:
        major, minor, _patch = (int(part) for part in str(raw).split("."))
    except (ValueError, AttributeError, TypeError):
        return UNKNOWN
    ours = tuple(int(part) for part in CONTRACT_VERSION.split("."))
    if major != ours[0]:
        return INCOMPATIBLE
    if (major, minor) < ours[:2]:
        return MIGRATION_REQUIRED
    return CURRENT


def validate_proposal_envelope(envelope: Mapping[str, Any]) -> dict:
    receipts.validate(PROPOSAL_SCHEMA, dict(envelope))
    return dict(envelope)


def validate_recall_context(envelope: Mapping[str, Any]) -> dict:
    receipts.validate(RECALL_CONTEXT_SCHEMA, dict(envelope))
    return dict(envelope)


def proposal_from_envelope(envelope: Mapping[str, Any]) -> policy.Proposal:
    """The internal Proposal; evaluator-side fields keep their defaults."""
    fields = {name: envelope[name] for name in PUBLIC_PROPOSAL_FIELDS if name in envelope}
    for name in _TUPLE_FIELDS:
        if name in fields:
            fields[name] = tuple(fields[name])
    return policy.Proposal(**fields)


def recall_context_from_envelope(envelope: Mapping[str, Any]) -> RecallContext:
    return RecallContext(
        target_domain_refs=tuple(envelope["target_domain_refs"]),
        principal_ref=envelope.get("principal_ref", ""),
        project_ref=envelope.get("project_ref", ""),
        task_ref=envelope.get("task_ref", ""),
        purpose=envelope.get("purpose", ""),
    )


def decision_projection(decision: policy.Decision) -> dict:
    return {
        "outcome": decision.outcome,
        "permitted_actions": list(decision.permitted_actions),
        "prohibited_actions": list(decision.prohibited_actions),
        "reasons": list(decision.reasons),
        "policy_version": decision.policy_version,
        "discharge_authority": decision.discharge_authority,
        "review_discharge": decision.review_discharge,
    }


def result(stage: str, compat: str, **fields: Any) -> dict:
    """A result envelope, validated against its schema before it is returned."""
    document = {"contract_version": CONTRACT_VERSION, "compatibility": compat, "stage": stage}
    document.update({key: value for key, value in fields.items() if value is not None})
    receipts.validate(RESULT_SCHEMA, document)
    return document


__all__ = [
    "CONTRACT_VERSION", "CURRENT", "MIGRATION_REQUIRED", "INCOMPATIBLE", "UNKNOWN",
    "PUBLIC_PROPOSAL_FIELDS", "compatibility", "validate_proposal_envelope",
    "validate_recall_context", "proposal_from_envelope", "recall_context_from_envelope",
    "decision_projection", "result",
]
