"""Reference authority boundary for durable decision overwrite.

This module exercises ADR-025 without turning decision memory into a second
policy engine. Durable decisions are immutable episodes. An overwrite proposal
may be retained as audit evidence without changing current decision state.
Only a proposal whose exact authority grant remains valid is evaluated through
PAMA, and only a permitted PAMA consequence appends supersession evidence.

The central distinctions are:

proposal != approval != committed supersession
historical approval != reusable authority
agent consensus != human confirmation

Stdlib apart from the canonical schema validation reached through ``receipts``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from . import policy, receipts
from .pending_verification import PendingVerificationRegistry

PENDING = "pending"
REJECTED = "rejected"
COMMITTED = "committed"

HUMAN_CONFIRMATION = "human_confirmation"
DELEGATED_POLICY = "delegated_policy"
AGENT_CONSENSUS = "agent_consensus"

#: The remediation the envelope grants a parked proposal (ADR-037 step 4b-2).
ENTER_PENDING_VERIFICATION = "enter_pending_verification"

_RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


@dataclass(frozen=True)
class DurableDecision:
    decision_id: str
    decision_statement: str
    rationale: str
    decision_scope: str
    owner: str
    approval_refs: tuple[str, ...]
    decided_at: str
    status_at_creation: str = "active"
    supersedes: str | None = None
    human_confirmed: bool = False


@dataclass(frozen=True)
class OverwriteProposal:
    proposal_id: str
    proposing_actor: str
    target_decision_id: str
    replacement: DurableDecision
    scope: str
    rationale: str
    evidence_refs: tuple[str, ...]
    conflict_notes: tuple[str, ...]
    state_snapshot: str
    risk_class: str
    target_class: str = policy.M4
    downstream_authority: str = policy.A3
    reversibility: str = "reversible"
    isolation_domain_refs: tuple[str, ...] = ()
    required_isolation_domain_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthorityGrant:
    grant_id: str
    authority_kind: str
    principal_id: str
    proposal_id: str
    target_decision_id: str
    scope: str
    mutation_class: str
    issued_at: str
    expires_at: str
    max_risk_class: str
    authorized_actor_ids: tuple[str, ...]
    revoked: bool = False


@dataclass
class OverwriteResult:
    proposal: OverwriteProposal
    status: str
    reason: str | None = None
    grant: AuthorityGrant | None = None
    decision: policy.Decision | None = None
    pama_decision: dict | None = None
    receipt: dict | None = None
    events: list[dict] = field(default_factory=list)
    supersession_evidence: dict | None = None


class DurableDecisionRegistry:
    """Append-oriented reference registry for ADR-025 evidence.

    Decision objects are never mutated after registration. Current/superseded
    status is derived from the append-only supersession journal. This registry
    demonstrates the authority boundary, not a production decision database.
    """

    def __init__(self, now: Callable[[], str]) -> None:
        self._now = now
        self._decisions: dict[str, DurableDecision] = {}
        self._superseded_by: dict[str, str] = {}
        self._versions: dict[str, int] = {}
        self._proposals: dict[str, OverwriteResult] = {}
        self.supersession_journal: list[dict] = []
        # ADR-037 step 4b-2 (entry #24). Held here, not constructed inline, so a
        # parked record outlives the call that made it -- otherwise parking is a
        # no-op with an event attached, and nothing can ever resume or report on
        # it. This registry is the type Loop 8 generalised the parking lifecycle
        # from, which makes an ephemeral park here particularly incongruous.
        self.pending_verification = PendingVerificationRegistry()
        self.events: list[dict] = []
        self._event_counter = 0
        self._receipt_counter = 0

    def register(self, decision: DurableDecision) -> None:
        self._validate_decision(decision)
        if decision.decision_id in self._decisions:
            raise ValueError(f"decision already exists: {decision.decision_id}")
        if decision.supersedes is not None:
            raise ValueError("initial registration cannot silently supersede another decision")
        self._decisions[decision.decision_id] = decision
        self._versions[decision.decision_id] = 0

    def propose(self, proposal: OverwriteProposal) -> OverwriteResult:
        if proposal.proposal_id in self._proposals:
            raise ValueError(f"overwrite proposal already exists: {proposal.proposal_id}")
        self._validate_proposal_shape(proposal)
        event = self._event(
            "memory.decision_overwrite_proposed",
            proposal,
            self._now(),
            status=PENDING,
        )
        result = OverwriteResult(proposal=proposal, status=PENDING, events=[event])
        self._proposals[proposal.proposal_id] = result
        self.events.append(event)
        return result

    def commit(self, proposal_id: str, grant: AuthorityGrant | None) -> OverwriteResult:
        result = self._proposals.get(proposal_id)
        if result is None:
            raise ValueError(f"unknown overwrite proposal: {proposal_id}")
        if result.status != PENDING:
            return result

        proposal = result.proposal
        now = self._now()
        refusal = self._precommit_refusal(proposal, grant, now)
        if refusal:
            return self._reject(result, grant, now, refusal)

        assert grant is not None
        pama_proposal = policy.Proposal(
            proposal_id=proposal.proposal_id,
            actor_id=proposal.proposing_actor,
            charter_version="decision-overwrite-reference",
            target_reference=proposal.target_decision_id,
            target_class=proposal.target_class,
            scope=proposal.scope,
            operation="decision_overwrite",
            current_strength="canonical",
            proposed_strength="deprecated",
            downstream_authority=proposal.downstream_authority,
            reversibility=proposal.reversibility,
            risk_class=proposal.risk_class,
            evidence_refs=proposal.evidence_refs,
            actor_authority_resolved=True,
            approves_own_authority=grant.principal_id == proposal.proposing_actor,
            approval_refs=(grant.grant_id,),
            review_satisfied=True,
            state_snapshot=proposal.state_snapshot,
            purpose="durable-decision-overwrite",
            isolation_domain_refs=proposal.isolation_domain_refs,
            required_isolation_domain_refs=proposal.required_isolation_domain_refs,
        )
        # GAP-ARCH-04 (LD5): express the authority already validated by
        # _grant_refusal through a channel policy can tell apart from assertion.
        # This is not new authority -- _grant_refusal binds the grant to this
        # proposal and target, derives self-approval from identity, enforces the
        # risk ceiling, and requires HUMAN_CONFIRMATION for high/critical risk,
        # every one of which is stricter than the attestation's own checks.
        attestation = policy.ExternalVerification(
            bound_proposal_id=pama_proposal.proposal_id,
            verifier_principal_id=grant.principal_id,
            authority_kind=grant.authority_kind,
            max_risk_class=grant.max_risk_class,
        )
        decision = policy.evaluate_with_external_verification(pama_proposal, attestation)
        # ADR-037 step 4b-2 (entry #24). `NO_ACTION` is legal only when nothing
        # was permitted (`receipts.enforce_selection`). A parked proposal DOES
        # have a permitted action -- `enter_pending_verification` -- so recording
        # NO_ACTION would raise, and the module would *fail* where the operator's
        # ruling requires it to *park*. Recording the park is the honest
        # selection and satisfies the existing control unchanged.
        if pama_proposal.operation in decision.permitted_actions:
            selected_action = pama_proposal.operation
        elif ENTER_PENDING_VERIFICATION in decision.permitted_actions:
            selected_action = ENTER_PENDING_VERIFICATION
        else:
            selected_action = receipts.NO_ACTION

        before_state = proposal.state_snapshot
        after_state = before_state
        self._receipt_counter += 1
        receipt_id = f"decision-overwrite-receipt:{self._receipt_counter}"

        if decision.outcome == policy.REQUIRE_REVIEW:
            # ADR-037 step 4b-2. The asserted route that used to discharge this
            # at low and medium risk is gone. The AuthorityGrant is NOT offered
            # as evidence: it answers the authority question, not the evidence
            # question, and a valid grant can authorise review of a bad
            # proposal. Collapsing the two would merge two of ADR-037's four
            # axes (operator ruling, 2026-09-05).
            #
            # `enter_pending_verification` is a permitted action for
            # require_review, so parking is the remediation this envelope
            # grants -- not an overreach.
            if pama_proposal.proposal_id not in {
                record.proposal_id for record in self.pending_verification.parked()
            }:
                self.pending_verification.park(pama_proposal, decision)

        if selected_action in (receipts.NO_ACTION, ENTER_PENDING_VERIFICATION):
            receipt = receipts.build_receipt(
                receipt_id=receipt_id,
                proposal=pama_proposal,
                decision=decision,
                selected_action=selected_action,
                selection_mode=(
                    # `none` only when nothing was selected. Parking IS a
                    # selection, and it follows deterministically from the
                    # policy decision -- the schema's own vocabulary for that.
                    "none" if selected_action == receipts.NO_ACTION else "deterministic"
                ),
                timestamp=now,
                before_state=before_state,
                after_state=after_state,
            )
            pama_decision = receipts.build_pama_decision(
                pama_proposal,
                decision,
                selected_action,
                None,
                receipt_id,
            )
            receipts.verify_receipt_decision_pair(receipt, pama_decision)
            result.grant = grant
            result.decision = decision
            result.receipt = receipt
            result.pama_decision = pama_decision
            if selected_action == ENTER_PENDING_VERIFICATION:
                # ADR-037 step 4b-2. A parked proposal is not rejected: it is
                # awaiting qualifying evidence, and `PENDING` is the status this
                # registry already uses for that. Calling it rejected would
                # report a dead end where a remediation path exists, which is
                # the distinction the operator drew between parking and failing.
                result.status = PENDING
                result.reason = "parked_pending_verification"
                result.grant = grant
                return result
            return self._reject(result, grant, now, "pama_not_permitted", receipt_ref=receipt_id)

        new_version = self._versions[proposal.target_decision_id] + 1
        after_state = f"v{new_version}"
        receipt = receipts.build_receipt(
            receipt_id=receipt_id,
            proposal=pama_proposal,
            decision=decision,
            selected_action=selected_action,
            selection_mode="human" if grant.authority_kind == HUMAN_CONFIRMATION else "external",
            timestamp=now,
            before_state=before_state,
            after_state=after_state,
            rollback_ref=f"decision-recovery:{proposal.target_decision_id}:{before_state}",
        )
        pama_decision = receipts.build_pama_decision(
            pama_proposal,
            decision,
            selected_action,
            "human" if grant.authority_kind == HUMAN_CONFIRMATION else "external",
            receipt_id,
        )
        receipts.verify_receipt_decision_pair(receipt, pama_decision)

        replacement = proposal.replacement
        self._decisions[replacement.decision_id] = replacement
        self._versions[proposal.target_decision_id] = new_version
        self._versions[replacement.decision_id] = 0
        self._superseded_by[proposal.target_decision_id] = replacement.decision_id
        evidence = {
            "supersession_id": f"supersession:{proposal.proposal_id}",
            "prior_decision_id": proposal.target_decision_id,
            "replacement_decision_id": replacement.decision_id,
            "proposal_id": proposal.proposal_id,
            "authority_grant_ref": grant.grant_id,
            "authority_kind": grant.authority_kind,
            "receipt_ref": receipt_id,
            "state_before": before_state,
            "state_after": after_state,
            "timestamp": now,
        }
        self.supersession_journal.append(evidence)

        event = self._event(
            "memory.decision_overwrite_committed",
            proposal,
            now,
            status=COMMITTED,
            grant=grant,
            receipt_ref=receipt_id,
            extra_payload={"replacement_decision_id": replacement.decision_id},
        )
        result.status = COMMITTED
        result.reason = None
        result.grant = grant
        result.decision = decision
        result.receipt = receipt
        result.pama_decision = pama_decision
        result.supersession_evidence = evidence
        result.events.append(event)
        self.events.append(event)
        return result

    def decision(self, decision_id: str) -> DurableDecision | None:
        return self._decisions.get(decision_id)

    def decision_status(self, decision_id: str) -> str | None:
        if decision_id not in self._decisions:
            return None
        if decision_id in self._superseded_by:
            return "superseded"
        return self._decisions[decision_id].status_at_creation

    def superseded_by(self, decision_id: str) -> str | None:
        return self._superseded_by.get(decision_id)

    def state_snapshot(self, decision_id: str) -> str:
        if decision_id not in self._decisions:
            raise ValueError(f"unknown decision: {decision_id}")
        return f"v{self._versions[decision_id]}"

    def record_external_state_change(self, decision_id: str) -> str:
        """Advance current state to exercise stale-proposal rejection."""
        if decision_id not in self._decisions:
            raise ValueError(f"unknown decision: {decision_id}")
        self._versions[decision_id] += 1
        return self.state_snapshot(decision_id)

    def _precommit_refusal(
        self,
        proposal: OverwriteProposal,
        grant: AuthorityGrant | None,
        now: str,
    ) -> str | None:
        target = self._decisions.get(proposal.target_decision_id)
        if target is None:
            return "unknown_target_decision"
        if proposal.target_decision_id in self._superseded_by:
            return "target_not_current"
        if proposal.state_snapshot != self.state_snapshot(proposal.target_decision_id):
            return "stale_overwrite_proposal"
        if proposal.replacement.decision_id in self._decisions:
            return "replacement_decision_already_exists"
        if proposal.replacement.supersedes != proposal.target_decision_id:
            return "replacement_supersession_mismatch"
        if proposal.replacement.decision_scope != proposal.scope or target.decision_scope != proposal.scope:
            return "decision_scope_mismatch"
        if grant is None:
            return "authority_required"

        grant_refusal = self._grant_refusal(proposal, target, grant, now)
        if grant_refusal:
            return grant_refusal
        return None

    def _grant_refusal(
        self,
        proposal: OverwriteProposal,
        target: DurableDecision,
        grant: AuthorityGrant,
        now: str,
    ) -> str | None:
        grant_shape = self._grant_shape_refusal(grant, now)
        if grant_shape:
            return grant_shape
        if grant.revoked:
            return "authority_grant_revoked"
        if grant.proposal_id != proposal.proposal_id:
            return "authority_proposal_mismatch"
        if grant.target_decision_id != proposal.target_decision_id:
            return "authority_target_mismatch"
        if grant.scope != proposal.scope:
            return "authority_scope_mismatch"
        if grant.mutation_class != "decision_overwrite":
            return "authority_mutation_mismatch"
        if proposal.proposing_actor not in grant.authorized_actor_ids:
            return "actor_not_delegated"
        if grant.principal_id == proposal.proposing_actor:
            return "self_approval_prohibited"
        if grant.grant_id not in proposal.replacement.approval_refs:
            return "authority_not_recorded_on_replacement"
        if grant.max_risk_class not in _RISK_ORDER:
            return "invalid_authority_risk_ceiling"
        if _RISK_ORDER[proposal.risk_class] > _RISK_ORDER[grant.max_risk_class]:
            return "authority_risk_ceiling_exceeded"

        human_required = target.human_confirmed or proposal.risk_class in ("high", "critical")
        if human_required and grant.authority_kind != HUMAN_CONFIRMATION:
            return "human_confirmation_required"
        if grant.authority_kind not in (HUMAN_CONFIRMATION, DELEGATED_POLICY):
            return "unsupported_authority_kind"
        if grant.authority_kind == DELEGATED_POLICY and proposal.risk_class not in ("low", "medium"):
            return "delegation_not_permitted_for_risk"
        return None

    def _grant_shape_refusal(self, grant: AuthorityGrant, now: str) -> str | None:
        for name in (
            "grant_id",
            "authority_kind",
            "principal_id",
            "proposal_id",
            "target_decision_id",
            "scope",
            "mutation_class",
            "issued_at",
            "expires_at",
            "max_risk_class",
        ):
            if not getattr(grant, name):
                return "invalid_authority_grant"
        if not grant.authorized_actor_ids:
            return "invalid_authority_grant"
        issued = self._parse_time(grant.issued_at)
        expires = self._parse_time(grant.expires_at)
        current = self._parse_time(now)
        if expires <= issued:
            return "invalid_authority_grant"
        if current < issued:
            return "authority_grant_not_yet_valid"
        if current >= expires:
            return "authority_grant_expired"
        return None

    def _reject(
        self,
        result: OverwriteResult,
        grant: AuthorityGrant | None,
        timestamp: str,
        reason: str,
        *,
        receipt_ref: str | None = None,
    ) -> OverwriteResult:
        result.status = REJECTED
        result.reason = reason
        if grant is not None:
            result.grant = grant
        event = self._event(
            "memory.decision_overwrite_rejected",
            result.proposal,
            timestamp,
            status=REJECTED,
            reason=reason,
            grant=grant,
            receipt_ref=receipt_ref,
        )
        result.events.append(event)
        self.events.append(event)
        return result

    @staticmethod
    def _validate_decision(decision: DurableDecision) -> None:
        for name in ("decision_id", "decision_statement", "rationale", "decision_scope", "owner", "decided_at"):
            if not getattr(decision, name):
                raise ValueError(f"decision field {name} must be non-empty")
        if decision.status_at_creation != "active":
            raise ValueError("reference registry accepts only active decision episodes")
        DurableDecisionRegistry._parse_time(decision.decided_at)

    @staticmethod
    def _validate_proposal_shape(proposal: OverwriteProposal) -> None:
        for name in ("proposal_id", "proposing_actor", "target_decision_id", "scope", "rationale", "state_snapshot"):
            if not getattr(proposal, name):
                raise ValueError(f"overwrite proposal field {name} must be non-empty")
        if not proposal.evidence_refs:
            raise ValueError("overwrite proposal requires evidence refs")
        if proposal.risk_class not in _RISK_ORDER:
            raise ValueError(f"invalid overwrite risk class: {proposal.risk_class}")
        DurableDecisionRegistry._validate_decision(proposal.replacement)

    @staticmethod
    def _parse_time(value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"invalid timestamp: {value!r}") from exc
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _event(
        self,
        event_type: str,
        proposal: OverwriteProposal,
        timestamp: str,
        *,
        status: str,
        reason: str | None = None,
        grant: AuthorityGrant | None = None,
        receipt_ref: str | None = None,
        extra_payload: dict | None = None,
    ) -> dict:
        self._event_counter += 1
        payload = {
            "proposal_id": proposal.proposal_id,
            "target_decision_id": proposal.target_decision_id,
            "replacement_decision_id": proposal.replacement.decision_id,
            "scope": proposal.scope,
            "mutation_class": "decision_overwrite",
            "risk_class": proposal.risk_class,
            "state_snapshot": proposal.state_snapshot,
            "status": status,
            "evidence_refs": list(proposal.evidence_refs),
            "conflict_notes": list(proposal.conflict_notes),
        }
        if reason:
            payload["reason"] = reason
        if grant is not None:
            payload["authority_kind"] = grant.authority_kind
            payload["authority_grant_ref"] = grant.grant_id
        if extra_payload:
            payload.update(extra_payload)
        document = {
            "schema_version": "1.0.0",
            "event_id": f"decision-overwrite-event:{self._event_counter}",
            "event_type": event_type,
            "event_version": "1.0.0",
            "timestamp": timestamp,
            "component": "durable-decision-registry",
            "memory_id": proposal.target_decision_id,
            "actor": proposal.proposing_actor,
            "correlation_id": proposal.proposal_id,
            "payload": payload,
        }
        if grant is not None:
            document["authority"] = {"authority_refs": [grant.grant_id]}
        if receipt_ref:
            document["receipt_ref"] = receipt_ref
        receipts.validate("memory-audit-event.schema.json", document)
        return document
