"""The public surface: six of PRD-001 R1's stages as functions of an adapter and an envelope.

Sprint 4a (plan LD4-LD6). Every function first evaluates ADR-030 compatibility
and validates the envelope; a stage runs only on ``current``. ``propose`` and
``approve`` write nothing. ``commit`` and ``forget`` forward the caller's
evidence and attestation to the adapter unchanged and otherwise park there
(DoD 20). No function accepts a verifier: the registry is the adapter's own.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from ..core import policy
from ..runtime.adapter import GovernedMemoryAdapter
from . import contract

__all__ = ["propose", "approve", "commit", "recall", "forget"]


def _gate(envelope: Mapping[str, Any], validator, stage: str):
    """(compat, validated envelope or None, early result or None)."""
    compat = contract.compatibility(envelope)
    if compat != contract.CURRENT:
        return compat, None, contract.result("none", compat)
    try:
        validated = validator(envelope)
    except ValueError as exc:
        return compat, None, contract.result("none", compat, validation_error=str(exc))
    return compat, validated, None


def propose(memory: GovernedMemoryAdapter, envelope: Mapping[str, Any]) -> dict:
    """The proposal stage: evaluate, write nothing."""
    compat, validated, early = _gate(envelope, contract.validate_proposal_envelope, "proposal")
    if early is not None:
        return early
    decision = policy.evaluate(contract.proposal_from_envelope(validated))
    return contract.result("proposal", compat, outcome=decision.outcome,
                           decision=contract.decision_projection(decision))


def approve(memory: GovernedMemoryAdapter, envelope: Mapping[str, Any], *,
            evidence: Sequence = (), attestation: policy.ExternalVerification | None = None) -> dict:
    """The approval stage: ADR-037 4a discharge through the adapter's own registry; write nothing."""
    compat, validated, early = _gate(envelope, contract.validate_proposal_envelope, "approval")
    if early is not None:
        return early
    decision = memory.evaluate_proposal(contract.proposal_from_envelope(validated),
                                        evidence=evidence, attestation=attestation)
    return contract.result("approval", compat, outcome=decision.outcome,
                           decision=contract.decision_projection(decision))


def commit(memory: GovernedMemoryAdapter, envelope: Mapping[str, Any], fact_text: str, *,
           evidence: Sequence = (), attestation: policy.ExternalVerification | None = None) -> dict:
    """The commit stage: the adapter decides again and writes, or parks."""
    compat, validated, early = _gate(envelope, contract.validate_proposal_envelope, "commit")
    if early is not None:
        return early
    outcome = memory.commit_proposal(contract.proposal_from_envelope(validated), fact_text,
                                     evidence=list(evidence) or None, attestation=attestation)
    return contract.result("commit", compat, outcome=outcome.decision.outcome,
                           decision=contract.decision_projection(outcome.decision),
                           receipt=outcome.receipt, committed=outcome.committed,
                           fact_uuid=outcome.fact_uuid, refusal=outcome.refusal)


def recall(memory: GovernedMemoryAdapter, query: str, context_envelope: Mapping[str, Any]) -> dict:
    """Retrieval candidates and recall admission, as the adapter records them."""
    compat, validated, early = _gate(context_envelope, contract.validate_recall_context, "recall")
    if early is not None:
        return early
    admission = memory.governed_recall(query, contract.recall_context_from_envelope(validated))
    return contract.result("recall", compat, candidates=list(admission.candidates),
                           admitted=list(admission.admitted), admissions=dict(admission.decisions))


def forget(memory: GovernedMemoryAdapter, envelope: Mapping[str, Any], *,
           evidence: Sequence = (), attestation: policy.ExternalVerification | None = None) -> dict:
    """Governed deletion of the target's current fact; the adapter's keyword for the attestation is ``external_verification``."""
    compat, validated, early = _gate(envelope, contract.validate_proposal_envelope, "forget")
    if early is not None:
        return early
    proposal = contract.proposal_from_envelope(validated)
    fact_uuid = memory.current_fact_uuid(proposal.target_reference) or ""
    outcome = memory.governed_delete(proposal, fact_uuid,
                                     evidence=list(evidence) or None, external_verification=attestation)
    return contract.result("forget", compat, outcome=outcome.decision.outcome,
                           decision=contract.decision_projection(outcome.decision),
                           receipt=outcome.receipt, committed=outcome.committed,
                           fact_uuid=outcome.fact_uuid, refusal=outcome.refusal)
