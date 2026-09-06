"""Optional semantic re-admission profile over the governed reference adapter.

The core adapter keeps deterministic exact-value protection. This profile adds
an estimator-mediated *review signal* for paraphrase/semantic-equivalence cases
without making semantic matching a canonical identity primitive.

A semantic match may stop the proposal before PAMA and route it to
reconciliation. It cannot emit allow/block, cannot satisfy review, and cannot
turn a rejected value into authority. An externally approved correction may
proceed through the ordinary PAMA path; a semantic non-match likewise creates
no permission and leaves PAMA fully authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import policy, receipts
from .adapter import CommitResult, GovernedMemoryAdapter
from .readmission import (
    REQUIRE_RECONCILIATION,
    SemanticReadmissionRouting,
    SemanticSimilaritySignal,
    route_semantic_similarity,
)


@dataclass
class SemanticCommitResult:
    committed: bool
    refusal: str | None = None
    routing: SemanticReadmissionRouting | None = None
    downstream: CommitResult | None = None
    events: list[dict] = field(default_factory=list)


class SemanticReadmissionAdapter(GovernedMemoryAdapter):
    """Governed adapter profile that treats semantic equivalence as review evidence."""

    def active_rejection_records(self, memory_id: str) -> tuple[dict, ...]:
        return self._rejected_values.active_records(memory_id)

    def commit_with_semantic_signal(
        self,
        proposal: policy.Proposal,
        fact_text: str,
        semantic_signal: SemanticSimilaritySignal | None = None,
        episode=None,
        *,
        evidence=None,
        attestation=None,
    ) -> SemanticCommitResult:
        """ADR-037 step 4b-2, DoD 20: this subclass reaches a governed mutation,
        so it forwards the qualified-evidence channel rather than burying it.

        A semantic signal still creates no permission of its own -- it never
        did, and evidence does not change that. PAMA still decides."""
        if semantic_signal is None:
            downstream = super().commit_proposal(
                proposal, fact_text, episode,
                evidence=evidence, attestation=attestation,
            )
            return SemanticCommitResult(
                committed=downstream.committed,
                refusal=downstream.refusal,
                downstream=downstream,
                events=list(downstream.events),
            )

        signal_valid = self._semantic_signal_is_bound(proposal, semantic_signal)
        routing = route_semantic_similarity(semantic_signal)
        signal_event = self._semantic_event(
            proposal,
            semantic_signal,
            routing,
            event_type="memory.semantic_readmission_signal",
            valid_active_rejection=signal_valid,
        )
        self.events.append(signal_event)

        if not signal_valid:
            refusal_event = self._semantic_event(
                proposal,
                semantic_signal,
                routing,
                event_type="memory.semantic_readmission_signal_rejected",
                valid_active_rejection=False,
                refusal="semantic_reconciliation_signal_invalid",
            )
            self.events.append(refusal_event)
            return SemanticCommitResult(
                committed=False,
                refusal="semantic_reconciliation_signal_invalid",
                routing=routing,
                events=[signal_event, refusal_event],
            )

        if routing.review_required and not self._approved_reversal(proposal):
            review_event = self._semantic_event(
                proposal,
                semantic_signal,
                routing,
                event_type="memory.semantic_readmission_review_required",
                valid_active_rejection=True,
                refusal="semantic_reconciliation_required",
            )
            self.events.append(review_event)
            return SemanticCommitResult(
                committed=False,
                refusal="semantic_reconciliation_required",
                routing=routing,
                events=[signal_event, review_event],
            )

        # A non-match creates no permission. A matched signal whose review has
        # already been satisfied by an external approved correction likewise
        # creates no authority of its own. In both cases PAMA still decides.
        downstream = super().commit_proposal(
            proposal, fact_text, episode, evidence=evidence, attestation=attestation
        )
        events = [signal_event] + list(downstream.events)
        return SemanticCommitResult(
            committed=downstream.committed,
            refusal=downstream.refusal,
            routing=routing,
            downstream=downstream,
            events=events,
        )

    def governed_delete(
        self,
        proposal: policy.Proposal,
        fact_uuid: str,
        derived_refs: tuple[str, ...] = (),
        external_verification=None,
        evidence=None,
    ) -> CommitResult:
        """ADR-037 step 4b-2, DoD 20: forwards the deletion channels."""
        result = super().governed_delete(
            proposal, fact_uuid, derived_refs, external_verification, evidence
        )
        if result.committed and proposal.operation == "permanent_deletion":
            purged = self._rejected_values.purge_memory(proposal.target_reference)
            event = self._purge_event(proposal, result.receipt["receipt_id"], purged)
            result.events.append(event)
            self.events.append(event)
        return result

    def _supersede_current(self, proposal: policy.Proposal) -> None:
        """Preserve correction authority in rejection metadata for this profile."""
        current_uuid = self._current_fact_by_memory.get(proposal.target_reference)
        if not current_uuid:
            return
        current = self._substrate.get_fact(current_uuid)
        if current is None or current.is_event_invalid:
            return

        rejected_at = self._clock.now()
        self._rejected_values.reject(
            memory_id=proposal.target_reference,
            value=current.fact_text,
            superseded_fact_uuid=current.uuid,
            correction_proposal_id=proposal.proposal_id,
            evidence_refs=tuple(proposal.evidence_refs),
            authority_refs=tuple(proposal.approval_refs),
            scope=proposal.scope,
            rejected_at=rejected_at,
        )
        self._substrate.invalidate_fact(
            current.uuid,
            invalid_at=rejected_at,
            expired_at=self._clock.now(),
        )

    def _semantic_signal_is_bound(
        self,
        proposal: policy.Proposal,
        signal: SemanticSimilaritySignal,
    ) -> bool:
        if signal.memory_id != proposal.target_reference:
            return False
        return self._rejected_values.find_active_by_ref(
            proposal.target_reference,
            signal.rejection_ref,
        ) is not None

    @staticmethod
    def _approved_reversal(proposal: policy.Proposal) -> bool:
        return (
            proposal.operation == "correction"
            and proposal.review_satisfied
            and bool(proposal.approval_refs)
            and not proposal.approves_own_authority
        )

    def _semantic_event(
        self,
        proposal: policy.Proposal,
        signal: SemanticSimilaritySignal,
        routing: SemanticReadmissionRouting,
        *,
        event_type: str,
        valid_active_rejection: bool,
        refusal: str | None = None,
    ) -> dict:
        signal_payload = {
            "signal_type": "semantic_rejected_value_similarity",
            "signal_semantics": "candidate_match_for_reconciliation_not_authority",
            "signal_value": signal.candidate_match,
            "estimator_id": signal.estimator_id,
            "estimator_version": signal.estimator_version,
        }
        if signal.confidence is not None:
            signal_payload["uncertainty"] = {"reported_confidence": signal.confidence}
        payload = {
            "proposal_id": proposal.proposal_id,
            "rejection_ref": signal.rejection_ref,
            "evidence_refs": list(signal.evidence_refs),
            "routing_consequence": routing.consequence,
            "review_required": routing.review_required,
            "valid_active_rejection": valid_active_rejection,
            "proposal_review_satisfied": proposal.review_satisfied,
            "proposal_approval_refs": list(proposal.approval_refs),
        }
        if refusal:
            payload["refusal"] = refusal
        document = {
            "schema_version": "1.0.0",
            "event_id": self._ids.next(),
            "event_type": event_type,
            "event_version": "1.0.0",
            "timestamp": self._clock.now(),
            "memory_id": proposal.target_reference,
            "actor": proposal.actor_id,
            "component": "semantic-readmission-adapter",
            "correlation_id": proposal.proposal_id,
            "signal": signal_payload,
            "payload": payload,
        }
        receipts.validate("memory-audit-event.schema.json", document)
        return document

    def _purge_event(self, proposal: policy.Proposal, receipt_ref: str, purged_records: int) -> dict:
        document = {
            "schema_version": "1.0.0",
            "event_id": self._ids.next(),
            "event_type": "memory.rejection_history_purged",
            "event_version": "1.0.0",
            "timestamp": self._clock.now(),
            "memory_id": proposal.target_reference,
            "actor": proposal.actor_id,
            "component": "semantic-readmission-adapter",
            "correlation_id": proposal.proposal_id,
            "receipt_ref": receipt_ref,
            "payload": {
                "purged_rejection_records": purged_records,
                "reason": "permanent_deletion",
            },
        }
        receipts.validate("memory-audit-event.schema.json", document)
        return document
