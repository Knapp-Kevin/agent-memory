"""Action authority: PRD-001 R1's action-authority and execution-evidence stages (ADR-038).

Sprint 4c-2. An action is authorized by an ordinary PAMA decision on a proposal
whose operation is ``action_execution``; the runtime adapter evaluates it through
its own verifier registry and this module -- which lives in the ``memory`` layer
and treats the adapter as an injected collaborator, never the reverse -- binds the
result to ``procedural_memory``'s execution seam or does not:

* ``allow`` / ``allow_with_ledger`` bind an executable allow, **after** the
  canonical PAMA decision document, the receipt naming it and the receipt event
  exist (operator ruling C6); any failure fails closed.
* ``block`` binds deny, with the same ledger.
* ``require_review`` / ``require_external_verification`` bind nothing; the
  unresolved requirement is surfaced separately (ruling R3). Absence of a bound
  decision is fail-closed.
* An authority-class floor (A4/A5) is an active constraint the ordinary action
  evidence path may not discharge (ruling C7): a decision that reached ``allow``
  only by discharging such a floor binds nothing here.
* A witness requires a bound decision, allow or deny (ruling C1); the host
  supplies observations only, and the builder computes alignment.
* A bound execution authorization is consumed exactly once, at the seam, and the
  witness is bound to that consumption; consumption state lives in the adapter's
  ``extension_state`` so the restart mechanism persists it, and is loaded
  fail-closed.

Known limitation (ADR-038): memory commits do not record proposal ids into this
namespace, so uniqueness is enforced within the governed action path only.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from typing import Any, Mapping

from ..core import policy, receipts
from ..runtime.adapter import GovernedMemoryAdapter
from .enforcement_composition import PROVIDER_NONE, build_projection, compose
from .enforcement_evidence import build_execution_witness
from .procedural_memory import (
    ActionGovernanceDecision,
    ActionProposal,
    apply_action_governance,
    record_runtime_execution,
)

SLOT = "action_authority"
OPERATION = "action_execution"
ENTER_PENDING = "enter_pending_verification"
REQUEST_EXTERNAL = "request_external_verification"
NO_BOUND_DECISION = "no bound decision for action"
ALREADY_CONSUMED = "execution authorization already consumed"
MALFORMED = "action authority state is malformed"
_EXECUTABLE = (policy.ALLOW, policy.ALLOW_WITH_LEDGER)
_UNRESOLVED = (policy.REQUIRE_REVIEW, policy.REQUIRE_EXTERNAL_VERIFICATION)
_RECORD_KEYS = ("decision", "decision_ref", "action", "pama_decision", "receipt", "composition",
                "requirement", "reasons", "ledger_required", "consumed")


@dataclass(frozen=True)
class ActionAuthority:
    """What the action path holds for one action id."""

    decision: policy.Decision
    decision_ref: str
    action: ActionProposal | None
    pama_decision: dict | None
    receipt: dict | None
    composition: dict | None
    requirement: str
    reasons: tuple[str, ...]
    ledger_required: bool
    consumed: bool = False

    @property
    def bound(self) -> bool:
        return self.action is not None


# -- persistence: adapter-owned ledger state, loaded fail-closed -----------------


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value))


def _dump(authority: ActionAuthority) -> dict:
    return _jsonable({
        "decision": asdict(authority.decision),
        "decision_ref": authority.decision_ref,
        "action": None if authority.action is None else asdict(authority.action),
        "pama_decision": authority.pama_decision,
        "receipt": authority.receipt,
        "composition": authority.composition,
        "requirement": authority.requirement,
        "reasons": list(authority.reasons),
        "ledger_required": authority.ledger_required,
        "consumed": authority.consumed,
    })


def _revive(record: Mapping[str, Any]) -> ActionAuthority:
    if not isinstance(record, Mapping) or any(key not in record for key in _RECORD_KEYS):
        raise ValueError(MALFORMED)
    raw_decision = dict(record["decision"])
    for name in ("permitted_actions", "prohibited_actions", "reasons", "constraints"):
        raw_decision[name] = tuple(raw_decision.get(name, ()))
    decision = policy.Decision(**raw_decision)
    action = None if record["action"] is None else ActionProposal(**dict(record["action"]))
    authority = ActionAuthority(
        decision=decision, decision_ref=str(record["decision_ref"]), action=action,
        pama_decision=record["pama_decision"], receipt=record["receipt"], composition=record["composition"],
        requirement=str(record["requirement"]), reasons=tuple(record["reasons"]),
        ledger_required=bool(record["ledger_required"]), consumed=bool(record["consumed"]),
    )
    if authority.consumed and (action is None or action.execution_status != "executed_by_runtime"):
        raise ValueError(MALFORMED)
    if authority.bound and (authority.composition is None or authority.receipt is None or authority.pama_decision is None):
        raise ValueError(MALFORMED)
    return authority


def _load(memory: GovernedMemoryAdapter) -> tuple[dict[str, ActionAuthority], set[str]]:
    """The stored authorities and evaluated proposal ids; fails closed on a malformed slot."""
    slot = memory.extension_state.get(SLOT)
    if slot is None:
        return {}, set()
    try:
        authorities = {str(action_id): _revive(record) for action_id, record in dict(slot["authorities"]).items()}
        proposals = {str(proposal_id) for proposal_id in slot["proposals"]}
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(MALFORMED) from exc
    return authorities, proposals


def _store(memory: GovernedMemoryAdapter, authorities: Mapping[str, ActionAuthority], proposals: set[str]) -> None:
    memory.extension_state[SLOT] = {
        "proposals": sorted(proposals),
        "authorities": {action_id: _dump(authority) for action_id, authority in sorted(authorities.items())},
    }


# -- the action-authority stage -------------------------------------------------


def _requirement(decision: policy.Decision, floors: list[str]) -> str:
    if any(floor.endswith(policy.A5) for floor in floors) or decision.outcome == policy.REQUIRE_EXTERNAL_VERIFICATION:
        return REQUEST_EXTERNAL
    return ENTER_PENDING


def _ledger(memory: GovernedMemoryAdapter, action: ActionProposal, proposal: policy.Proposal,
            decision: policy.Decision, allow: bool) -> tuple[dict, dict, dict, str]:
    """The canonical decision document, the receipt and the composition, before any binding."""
    selected = OPERATION if allow else receipts.NO_ACTION
    receipt_id = memory.mint_id()
    pama_decision = receipts.build_pama_decision(proposal, decision, selected, "deterministic" if allow else None, receipt_id)
    receipt = receipts.build_receipt(
        receipt_id, proposal, decision, selected_action=selected, selection_mode="deterministic" if allow else "none",
        timestamp=memory.now(), before_state="not_executed",
        after_state="authorized_not_executed" if allow else "blocked_by_governance",
    )
    composition = compose(build_projection(proposal, decision, receipt_ref=receipt_id), provider_mode=PROVIDER_NONE)
    return pama_decision, receipt, composition, receipt_id


def authorize_action(memory: GovernedMemoryAdapter, action: ActionProposal, proposal: policy.Proposal, *,
                     evidence=None, attestation: policy.ExternalVerification | None = None) -> ActionAuthority:
    """Decide an action through the adapter and bind the executable result, or bind nothing."""
    authorities, proposals = _load(memory)
    if proposal.operation != OPERATION:
        raise ValueError("action authority requires operation action_execution")
    if not proposal.target_reference:
        raise ValueError("action authority requires a target reference")
    if action.action_id in authorities:
        raise ValueError("action already evaluated")
    if proposal.proposal_id in proposals:
        raise ValueError("proposal already evaluated for an action")

    decision = memory.evaluate_proposal(proposal, evidence=evidence, attestation=attestation)
    decision_ref = receipts.decision_ref_for(proposal.proposal_id)
    floors = [constraint for constraint in decision.constraints if constraint.startswith("authority_floor:")]
    reasons = tuple(decision.reasons)
    ledger_required = decision.outcome == policy.ALLOW_WITH_LEDGER

    if floors and decision.outcome in _EXECUTABLE:
        # Ruling C7: the outcome was reached by discharging a floor this path may not discharge.
        reasons = reasons + tuple(f"{floor} is not dischargeable on the action path" for floor in floors)
    unresolved = (floors and decision.outcome in _EXECUTABLE) or decision.outcome in _UNRESOLVED
    if not unresolved and decision.outcome not in _EXECUTABLE and decision.outcome != policy.BLOCK:
        unresolved = True  # abstain / quarantine / collect_more_evidence bind nothing either
    allow = decision.outcome in _EXECUTABLE and not floors

    if unresolved:
        authority = ActionAuthority(decision, decision_ref, None, None, None, None,
                                    _requirement(decision, floors), reasons, ledger_required)
    else:
        pama_decision, receipt, composition, receipt_id = _ledger(memory, action, proposal, decision, allow)
        bound = apply_action_governance(
            action, ActionGovernanceDecision(decision_ref=decision_ref, action_id=action.action_id,
                                             outcome="allow" if allow else "deny"))
        authority = ActionAuthority(decision, decision_ref, bound, pama_decision, receipt, composition, "", reasons, ledger_required)

    correlation = memory.mint_id()
    propose_event = memory.record_event("action.propose", action.action_id, correlation)
    authorize_event = memory.record_event(
        "action.authorize", action.action_id, correlation, causation_id=propose_event["event_id"],
        policy_version=decision.policy_version,
        authority={"permitted_actions": list(decision.permitted_actions),
                   "prohibited_actions": list(decision.prohibited_actions), "selection_mode": "none"},
    )
    if authority.bound:
        memory.record_event("action.receipt", action.action_id, correlation,
                            causation_id=authorize_event["event_id"], receipt_ref=authority.receipt["receipt_id"])
    authorities[action.action_id] = authority
    proposals.add(proposal.proposal_id)
    _store(memory, authorities, proposals)
    return authority


# -- the execution-evidence stage -------------------------------------------------


def witness_execution(memory: GovernedMemoryAdapter, action_id: str, observation: Mapping[str, Any]) -> dict:
    """Bind the host's observation of an execution to the decision the adapter bound."""
    authorities, proposals = _load(memory)
    authority = authorities.get(action_id)
    status = observation.get("action_status")
    if authority is None or authority.action is None:
        if status == "executed":
            memory.record_event("action.unbound_execution_reported", action_id, memory.mint_id())
        raise ValueError(NO_BOUND_DECISION)

    witness = build_execution_witness(
        authority.composition,
        action_ref=action_id,
        witness_ref=str(observation.get("witness_ref", "")),
        enforcement_mode=str(observation.get("enforcement_mode", "")),
        delivery_status=str(observation.get("delivery_status", "")),
        enforcement_point_status=str(observation.get("enforcement_point_status", "")),
        action_status=str(status or ""),
        liveness_status=str(observation.get("liveness_status", "")),
        observed_at=str(observation.get("observed_at", "")),
        evidence_refs=tuple(observation.get("evidence_refs", ())),
    )
    action, consumed = authority.action, authority.consumed
    if status == "executed" and authority.action.execution_status != "blocked_by_governance":
        # The seam decides whether an authorization remains to consume; nothing is pre-checked here.
        try:
            action = record_runtime_execution(authority.action, witness["witness_id"])
        except ValueError as exc:
            raise ValueError(ALREADY_CONSUMED) from exc
        consumed = True
    memory.record_event("action.witness", action_id, memory.mint_id(), receipt_ref=witness["witness_id"])
    authorities[action_id] = replace(authority, action=action, consumed=consumed)
    _store(memory, authorities, proposals)
    return witness


__all__ = ["ActionAuthority", "authorize_action", "witness_execution", "SLOT", "OPERATION",
           "NO_BOUND_DECISION", "ALREADY_CONSUMED", "MALFORMED"]
