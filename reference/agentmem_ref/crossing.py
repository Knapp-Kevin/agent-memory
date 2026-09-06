"""Governed isolation-domain boundary crossings.

Executable evidence toward proposed ADR-022. The operation that moves or makes
memory influential across a logical boundary is recorded separately from the
PAMA consequence class used to authorize the broadening.

A valid receipt reconstructs a decision made under bound policy/state. It does
not grant permanent permission for future crossings after membership,
delegation, purpose, policy, or revocation state changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import policy, receipts

CROSSING_OPERATIONS = frozenset(
    {
        "share",
        "export",
        "import",
        "copy",
        "promote_scope",
        "summarize_for",
        "derive_for",
        "inherit",
        "publish",
    }
)


@dataclass(frozen=True)
class CrossingRequest:
    operation: str
    source_domain_refs: tuple[str, ...]
    destination_domain_refs: tuple[str, ...]
    actor: str
    principal: str
    purpose: str
    representation_kind: str
    source_refs: tuple[str, ...]
    sensitivity_labels: tuple[str, ...] = ()
    consent_ref: str = ""
    delegation_ref: str = ""
    membership_refs: tuple[str, ...] = ()
    authority_refs: tuple[str, ...] = ()
    policy_refs: tuple[str, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    valid_until: str = ""
    revocation_refs: tuple[str, ...] = ()
    before_scope_refs: tuple[str, ...] = ()
    after_scope_refs: tuple[str, ...] = ()
    privacy_minimized: bool = False
    redaction_ref: str = ""


@dataclass(frozen=True)
class CrossingResult:
    decision: policy.Decision
    receipt: dict
    committed: bool
    refusal: str | None = None


def _outcome_for(decision: policy.Decision) -> tuple[str, bool]:
    if decision.outcome in (policy.ALLOW, policy.ALLOW_WITH_LEDGER):
        return "committed", True
    if decision.outcome == policy.REQUIRE_REVIEW:
        return "review_required", False
    if decision.outcome == policy.REQUIRE_EXTERNAL_VERIFICATION:
        return "verification_required", False
    return "blocked", False


def _evaluate(proposal, evidence, attestation, verifier_registry):
    """Route through the qualified path when evidence is supplied."""
    if evidence:
        from .evidence_qualification import group_by_dependence

        return policy.evaluate_with_qualified_evidence(
            proposal,
            group_by_dependence(
                evidence,
                verifiers=(verifier_registry.as_mapping() if verifier_registry else None),
            ),
            attestation=attestation,
        )
    return policy.evaluate(proposal)


def evaluate_crossing(
    request: CrossingRequest,
    proposal: policy.Proposal,
    *,
    receipt_id: str,
    timestamp: str,
    decision_receipt_ref: str = "",
    ledger_ref: str = "",
    evidence=None,
    attestation: policy.ExternalVerification | None = None,
    verifier_registry=None,
) -> CrossingResult:
    """Evaluate and receipt one requested memory-boundary crossing.

    `request.operation` describes the concrete transfer or influence operation.
    `proposal.operation` must be `scope_expansion` because crossing to a broader
    authority domain is the PAMA consequence under evaluation. This prevents a
    caller from obtaining a weaker envelope by describing an export as a copy
    or summary operation.

    SCOPE ADDITION, disclosed (ADR-037 step 4b-2, entry #24). The flip removed
    the asserted discharge for `require_review`, and this entry point evaluated
    the proposal directly -- leaving every crossing caller refused with no
    reachable remediation. `evidence` defaults to None, so a caller supplying
    none behaves exactly as before and simply parks where it used to discharge
    on assertion. Same reasoning and same shape as the adapter's addition.
    """
    if request.operation not in CROSSING_OPERATIONS:
        raise ValueError(f"unsupported crossing operation: {request.operation}")
    if not request.source_domain_refs or not request.destination_domain_refs:
        raise ValueError("crossing requires explicit source and destination domains")
    if not request.source_refs:
        raise ValueError("crossing requires at least one source memory or derivation ref")
    if proposal.operation != "scope_expansion":
        decision = policy.Decision(
            outcome=policy.BLOCK,
            permitted_actions=(),
            prohibited_actions=(proposal.operation, "scope_expansion"),
            reasons=("boundary crossing must be evaluated as scope_expansion",),
        )
    else:
        decision = _evaluate(proposal, evidence, attestation, verifier_registry)

    outcome, committed = _outcome_for(decision)
    representation = {
        "kind": request.representation_kind,
        "privacy_minimized": request.privacy_minimized,
    }
    if request.redaction_ref:
        representation["redaction_ref"] = request.redaction_ref

    document = {
        "schema_version": "1.0.0",
        "receipt_id": receipt_id,
        "operation": request.operation,
        "source_domain_refs": list(request.source_domain_refs),
        "destination_domain_refs": list(request.destination_domain_refs),
        "actor": request.actor,
        "principal": request.principal,
        "purpose": request.purpose,
        "representation": representation,
        "source_refs": list(request.source_refs),
        "requested_consequence": "scope_expansion",
        "pama_disposition": decision.outcome,
        "policy_version": decision.policy_version,
        "outcome": outcome,
        "timestamp": timestamp,
    }

    optional_lists = (
        ("membership_refs", request.membership_refs),
        ("authority_refs", request.authority_refs),
        ("policy_refs", request.policy_refs),
        ("provenance_refs", request.provenance_refs),
        ("revocation_refs", request.revocation_refs),
        ("before_scope_refs", request.before_scope_refs),
        ("after_scope_refs", request.after_scope_refs),
    )
    for key, values in optional_lists:
        if values:
            document[key] = list(values)
    if request.sensitivity_labels:
        document["sensitivity"] = {"labels": list(request.sensitivity_labels)}
    if request.consent_ref:
        document["consent_ref"] = request.consent_ref
    if request.delegation_ref:
        document["delegation_ref"] = request.delegation_ref
    if request.valid_until:
        document["valid_until"] = request.valid_until
    if decision_receipt_ref:
        document["decision_receipt_ref"] = decision_receipt_ref
    if ledger_ref:
        document["ledger_ref"] = ledger_ref

    receipts.validate("boundary-crossing-receipt.schema.json", document)
    refusal = None if committed else f"crossing not committed: {decision.outcome}"
    return CrossingResult(decision=decision, receipt=document, committed=committed, refusal=refusal)
