"""Parked verification state: ADR-037 implementation, step 1 of 4.

A proposal that policy refuses is not, today, recorded anywhere. The refusal
returns and the attempt evaporates. ADR-037 holds that fail-closed cannot mean
a dead end under full automation -- a refusal must leave behind a record that
names what was refused, why, and which route out remains open.

This module builds that record and nothing else.

What it deliberately does NOT do, because ADR-037 fixes the order:

  step 2  evidence qualification and dependence lineage -- not here
  step 3  governed resumption -- **landed**, see ``resume`` and ``resumption``
  step 4  fail-closed ``require_review`` -- ``policy._apply_review`` is untouched

``resume`` was deliberately absent until step 3 (entry #20) -- not stubbed, not
raising ``NotImplementedError``, because a stub is an invitation and its absence
was a statement. Step 2's qualification machinery had to exist first, or a
proposal could leave the parked state without the means to decide whether it
should. It now exists and still grants nothing: a parked proposal carries no
authority, and resumption returns a re-evaluation rather than a permission
(ADR-037 section 5).

Parking is for refusals **with a route**. The envelope has three states, and
only the middle band parks::

    allow / allow_with_ledger    nothing was refused                   refuse
    require_review               enter_pending_verification permitted  park
    require_external_verificat.  request_external_verification granted park
    block                        enter_pending_verification PROHIBITED refuse

The two ends are refused for different reasons. Parking a permitted proposal
would manufacture a governance record for an event that did not occur. Parking
a blocked one would contradict the envelope being recorded -- ``_envelope``
names ``enter_pending_verification`` in the *prohibited* set for ``block`` --
and would create a record that can never leave the parked state, since no
evidence discharges an absorbing block.

The record retains the whole ``Proposal``, not a summary of it. Step 3 must
re-evaluate policy from scratch, ``policy.evaluate`` takes a ``Proposal``, and
the floors and modifiers read fields no identity summary preserves. Retaining
the proposal is also what carries ``state_snapshot`` forward, so resumption can
apply the staleness guard -- the specific risk parking introduces, since
parking is by definition a delay.

Parked records have no eviction path in this cycle. Retention belongs to #363.

Stdlib apart from the canonical schema validation reached through ``receipts``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from . import policy, receipts

#: Outcomes that park. Both are refusals that granted a route out.
PARKABLE = (policy.REQUIRE_REVIEW, policy.REQUIRE_EXTERNAL_VERIFICATION)

#: Refused because nothing was refused -- there is no remediation to record.
_PERMITTED_OUTCOMES = (policy.ALLOW, policy.ALLOW_WITH_LEDGER)

EVENT_TYPE = "memory.pending_verification"
COMPONENT = "pending-verification-registry"


@dataclass(frozen=True)
class ParkedProposal:
    """A refusal preserved with its decision, its route, and its identity.

    Frozen, and it exposes no method. It is evidence of a refusal, not a
    handle for undoing one. ``decision`` is the refusal verbatim; nothing
    here restates or narrows it.
    """

    proposal: policy.Proposal
    decision: policy.Decision
    correlation_id: str
    parked_at: str
    policy_version: str

    @property
    def proposal_id(self) -> str:
        return self.proposal.proposal_id

    @property
    def permitted_actions(self) -> tuple[str, ...]:
        """The route out, taken from the decision rather than restated.

        The route differs by outcome -- ``enter_pending_verification`` for
        ``require_review``, ``request_external_verification`` for
        ``require_external_verification``. Deriving it from the decision is
        what keeps this from becoming another caller-asserted input.
        """
        return self.decision.permitted_actions


class PendingVerificationRegistry:
    """Records refusals that have somewhere to go. Discharges nothing.

    ``park``, ``get`` and ``parked`` return no permission and mutate no
    decision. ``resume`` (step 3, entry #20) re-evaluates and returns a fresh
    ``Decision``; it too grants nothing and leaves the parked record unchanged.
    """

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._parked: dict[str, ParkedProposal] = {}
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._event_counter = 0
        self.events: list[dict] = []

    def park(
        self,
        proposal: policy.Proposal,
        decision: policy.Decision,
        *,
        correlation_id: str | None = None,
    ) -> ParkedProposal:
        """Record a refusal that granted a route out.

        Raises on a permitted outcome, on ``block``, and on a duplicate
        ``proposal_id``. Emits exactly one schema-valid audit event.
        """
        outcome = decision.outcome
        if outcome in _PERMITTED_OUTCOMES:
            raise ValueError(
                f"refusing to park proposal {proposal.proposal_id!r}: outcome is "
                f"{outcome!r}, which permitted the operation. Parking a permitted "
                "proposal would manufacture a governance record for a refusal "
                "that did not happen."
            )
        if outcome == policy.BLOCK:
            raise ValueError(
                f"refusing to park proposal {proposal.proposal_id!r}: outcome is "
                "'block', whose envelope names 'enter_pending_verification' in the "
                "prohibited set. Parking it would contradict the recorded envelope "
                "and create a record that can never be resumed, because no evidence "
                "discharges a block."
            )
        if outcome not in PARKABLE:
            raise ValueError(
                f"refusing to park proposal {proposal.proposal_id!r}: unrecognised "
                f"outcome {outcome!r} is not one of {PARKABLE}."
            )
        if proposal.proposal_id in self._parked:
            raise ValueError(
                f"proposal already parked: {proposal.proposal_id!r}. Parking is "
                "append-oriented; overwriting would erase the evidence of the "
                "first refusal."
            )

        parked_at = self._now().isoformat().replace("+00:00", "Z")
        record = ParkedProposal(
            proposal=proposal,
            decision=decision,
            correlation_id=correlation_id or proposal.proposal_id,
            parked_at=parked_at,
            policy_version=decision.policy_version,
        )
        self._parked[proposal.proposal_id] = record
        self._emit(record)
        return record

    def resume(self, proposal_id: str, **kwargs):
        """Re-evaluate a parked proposal. ADR-037 step 3 (ledger entry #20).

        Absent until step 3, deliberately: step 2's qualification machinery had
        to exist before anything could leave the parked state, or a proposal
        could resume without the means to decide whether it should.

        This returns a ``ResumptionResult`` carrying a freshly computed
        ``Decision``. It grants nothing, commits nothing, and does not mark the
        record discharged -- the parked record is unchanged by resumption,
        successful or not. Only ``evidence`` among the keyword arguments is the
        actor's contribution; the attestation, verifier registry, current state
        version and current policy version are the evaluator's.

        Imported here rather than at module scope so the two modules do not
        import each other in a cycle.
        """
        from .resumption import resume_parked

        record = self._parked.get(proposal_id)
        if record is None:
            from .resumption import NOT_PARKED, CriteriaReport, ResumptionResult

            return ResumptionResult(
                proposal_id=proposal_id,
                resumed=False,
                decision=None,
                refusal=NOT_PARKED,
                report=CriteriaReport(proposal_id, "", ()),
            )
        return resume_parked(record, **kwargs)

    def get(self, proposal_id: str) -> ParkedProposal | None:
        """The parked record, or None. Reading does not discharge."""
        return self._parked.get(proposal_id)

    def parked(self) -> tuple[ParkedProposal, ...]:
        """Every parked record, in park order."""
        return tuple(self._parked.values())

    def _emit(self, record: ParkedProposal) -> None:
        self._event_counter += 1
        # Fields the audit-event schema models get their modeled home. Burying
        # correlation_id in payload validates and is still wrong: it is then
        # invisible to any consumer joining on the modeled field, which is the
        # entire reason the record carries it.
        document = {
            "schema_version": "1.0.0",
            "event_id": f"pending-verification-event:{self._event_counter}",
            "event_type": EVENT_TYPE,
            "event_version": "1.0.0",
            "timestamp": record.parked_at,
            "component": COMPONENT,
            "memory_id": record.proposal.target_reference,
            "actor": record.proposal.actor_id,
            "correlation_id": record.correlation_id,
            "policy_version": record.policy_version,
            "state_snapshot": record.proposal.state_snapshot,
            "payload": {
                "proposal_id": record.proposal_id,
                "outcome": record.decision.outcome,
                "reasons": list(record.decision.reasons),
                "permitted_actions": list(record.decision.permitted_actions),
                "prohibited_actions": list(record.decision.prohibited_actions),
                "operation": record.proposal.operation,
                "risk_class": record.proposal.risk_class,
                "parked_at": record.parked_at,
            },
        }
        receipts.validate("memory-audit-event.schema.json", document)
        self.events.append(document)
