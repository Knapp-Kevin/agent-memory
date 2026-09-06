"""PAMA 1.3 compatibility for ADR-032 structural mutation delegation."""

from __future__ import annotations

from collections.abc import Iterable

from ..core import policy, receipts
from .structural_mutation import S0, S1, S2, S3, StructuralImpact, StructuralMutationError


PAMA_SCHEMA_VERSION = "1.3.0"
DOMAIN_SCHEMA_MUTATION = "domain_schema_mutation"


def build_pama_decision_v13(
    proposal: policy.Proposal,
    decision: policy.Decision,
    impact: StructuralImpact,
    *,
    selected_action: str,
    receipt_ref: str,
    selection_mode: str | None = None,
    approval_refs: Iterable[str] = (),
) -> dict:
    """Build a PAMA 1.3 decision bound to exact structural-impact evidence."""
    if proposal.operation != DOMAIN_SCHEMA_MUTATION:
        raise StructuralMutationError("PAMA 1.3 structural builder requires domain_schema_mutation")
    if proposal.proposal_id != impact.proposal.proposal_id:
        raise StructuralMutationError("PAMA proposal and structural impact proposal ids differ")

    structural_class = impact.classification.structural_class
    if structural_class == S0:
        raise StructuralMutationError("S0 rebuild-only work must not be serialized as domain_schema_mutation")

    approvals = tuple(approval_refs)
    allowed = decision.outcome in {policy.ALLOW, policy.ALLOW_WITH_LEDGER}
    if allowed and selected_action != DOMAIN_SCHEMA_MUTATION:
        raise StructuralMutationError("allowed structural mutation must select domain_schema_mutation")
    if not allowed and selected_action == DOMAIN_SCHEMA_MUTATION:
        raise StructuralMutationError("non-allowed PAMA decision cannot select domain_schema_mutation")

    if allowed and structural_class == S1:
        if not impact.classification.autonomous_eligible:
            raise StructuralMutationError("S1 autonomous decision lacks deterministic eligibility")
        if approvals:
            raise StructuralMutationError("autonomous S1 decision must not masquerade as human approval")
        if selection_mode not in (None, "deterministic"):
            raise StructuralMutationError("autonomous S1 selection mode must be deterministic")
        selection_mode = "deterministic"
    elif allowed and structural_class in {S2, S3}:
        if not approvals:
            raise StructuralMutationError("S2/S3 allowed decision requires explicit review references")
        if selection_mode not in {"human", "external"}:
            raise StructuralMutationError("S2/S3 allowed decision selection must be human or external")
    elif not allowed:
        selection_mode = None

    p = impact.proposal
    structural_policy = impact.structural_policy
    basis: dict[str, object] = {
        "evidence_refs": list(proposal.evidence_refs),
        "structural_impact_ref": impact.impact_digest,
        "structural_class": structural_class,
        "structural_classifier_id": structural_policy.classifier_id,
        "structural_classifier_version": structural_policy.classifier_version,
        "structural_state_digest": p.state_digest,
        "structural_dependency_digest": p.dependency_digest,
    }
    if proposal.estimator_refs:
        basis["estimator_refs"] = list(proposal.estimator_refs)
    if proposal.estimator_versions:
        basis["estimator_versions"] = list(proposal.estimator_versions)
    if proposal.confidence is not None:
        basis["confidence"] = proposal.confidence

    policy_record: dict[str, object] = {
        "policy_version": decision.policy_version,
        "structural_policy_id": structural_policy.policy_id,
        "structural_policy_version": structural_policy.policy_version,
    }
    if approvals:
        policy_record["required_review_refs"] = list(approvals)

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
        "basis": basis,
        "policy": policy_record,
        "decision": {
            "outcome": decision.outcome,
            "permitted_actions": list(decision.permitted_actions),
            "prohibited_actions": list(decision.prohibited_actions),
            "selected_action": None if selected_action == receipts.NO_ACTION else selected_action,
            "selection_mode": selection_mode,
            "decision_receipt_ref": receipt_ref,
        },
    }
    if proposal.requested_scope_change:
        document["mutation"]["requested_scope_change"] = proposal.requested_scope_change
    if proposal.tenant_ref:
        document["target"]["tenant_ref"] = proposal.tenant_ref
    if proposal.purpose:
        document["target"]["purpose"] = proposal.purpose

    receipts.validate("pama-decision.schema.json", document)
    return document


def enforce_v13_impact_binding(document: dict, impact: StructuralImpact) -> None:
    """Verify a PAMA 1.3 record still binds the exact classified structural state."""
    receipts.validate("pama-decision.schema.json", document)
    if document.get("schema_version") != PAMA_SCHEMA_VERSION:
        raise StructuralMutationError("structural impact binding requires PAMA 1.3.0")
    if document["proposal_id"] != impact.proposal.proposal_id:
        raise StructuralMutationError("PAMA decision proposal id does not match structural impact")
    basis = document["basis"]
    structural_policy = impact.structural_policy
    expected = {
        "structural_impact_ref": impact.impact_digest,
        "structural_class": impact.classification.structural_class,
        "structural_classifier_id": structural_policy.classifier_id,
        "structural_classifier_version": structural_policy.classifier_version,
        "structural_state_digest": impact.proposal.state_digest,
        "structural_dependency_digest": impact.proposal.dependency_digest,
    }
    for key, value in expected.items():
        if basis.get(key) != value:
            raise StructuralMutationError(f"PAMA 1.3 structural binding mismatch: {key}")
    if document["policy"].get("structural_policy_id") != structural_policy.policy_id:
        raise StructuralMutationError("PAMA 1.3 structural policy id mismatch")
    if document["policy"].get("structural_policy_version") != structural_policy.policy_version:
        raise StructuralMutationError("PAMA 1.3 structural policy version mismatch")
