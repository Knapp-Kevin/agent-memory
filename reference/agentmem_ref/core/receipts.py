"""Construction and validation of governance evidence.

Emits three artifacts, each conforming to a schema already canonical in this
repository rather than to a shape invented here:

- a PAMA decision record   (`schemas/pama-decision.schema.json`)
- a decision receipt       (`schemas/decision-receipt.schema.json`)
- audit events             (`schemas/memory-audit-event.schema.json`)

The substrate under evaluation persists none of this, which is precisely why
the adapter must.

`jsonschema` is required here, matching the validator dependency policy in
CONTRIBUTING: fixture and link validation stay standard-library, schema
validation may use it.
"""

from __future__ import annotations

import json
from functools import lru_cache
from importlib import resources
from pathlib import Path

import jsonschema

from . import policy
from .._paths import REPO_ROOT, PACKAGE_NAME

_SOURCE_SCHEMAS = REPO_ROOT / "schemas"


def _packaged_schemas() -> Path:
    return Path(str(resources.files(PACKAGE_NAME) / "_schemas"))


def schema_dir() -> Path:
    """Canonical schemas: source tree when present, packaged copy when installed."""
    if _SOURCE_SCHEMAS.is_dir():
        return _SOURCE_SCHEMAS
    packaged = _packaged_schemas()
    if packaged.is_dir():
        return packaged
    raise FileNotFoundError(
        "canonical schemas are unavailable; install the distribution with its packaged schema data"
    )

#: Sentinel recorded when governance permitted no action at all.
NO_ACTION = "none"

_DEFERRED_OUTCOMES = {
    "require_review",
    "require_external_verification",
    "abstain",
    "quarantine",
    "collect_more_evidence",
}


@lru_cache(maxsize=None)
def _validator(schema_name: str) -> jsonschema.Draft202012Validator:
    schema = json.loads((schema_dir() / schema_name).read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def validate(schema_name: str, document: dict) -> None:
    """Raise if the document does not satisfy its canonical schema."""
    errors = sorted(_validator(schema_name).iter_errors(document), key=lambda e: list(e.path))
    if errors:
        location = ".".join(str(part) for part in errors[0].path) or "<root>"
        raise ValueError(f"{schema_name} at {location}: {errors[0].message}")


def decision_ref_for(proposal_id: str) -> str:
    """Stable logical reference for the PAMA decision produced for a proposal.

    The PAMA decision already carries ``proposal_id`` as its stable identity
    anchor. This names that artifact without introducing a second, cyclic
    content identity merely to link it back from the receipt.
    """
    if not proposal_id:
        raise ValueError("decision reference requires a proposal id")
    return f"pama-decision:{proposal_id}"


def enforce_selection(permitted: tuple[str, ...], selected: str) -> None:
    """Selected action must come from the permitted set.

    JSON Schema cannot portably express this membership across sibling
    properties, so the receipt schema delegates it to consumers. This is that
    enforcement. `NO_ACTION` is legal only when nothing was permitted.
    """
    if selected == NO_ACTION:
        if permitted:
            raise ValueError("no action recorded although governance permitted actions")
        return
    if selected not in permitted:
        raise ValueError(f"selected action {selected!r} is not in the permitted set {list(permitted)}")


def enforce_decision_consistency(
    outcome: str,
    requested_action: str,
    permitted: tuple[str, ...],
    prohibited: tuple[str, ...],
) -> None:
    """Reject authority outcomes that contradict their action envelope.

    This intentionally enforces only invariants that are stable across the
    current decision vocabulary. It does not invent one universal policy table.
    """
    overlap = set(permitted) & set(prohibited)
    if overlap:
        raise ValueError(f"actions cannot be both permitted and prohibited: {sorted(overlap)}")

    if outcome in ("allow", "allow_with_ledger"):
        if requested_action not in permitted:
            raise ValueError(f"{outcome} must permit the requested action {requested_action!r}")
        if requested_action in prohibited:
            raise ValueError(f"{outcome} cannot prohibit the requested action {requested_action!r}")
        return

    if outcome == "block":
        if permitted:
            raise ValueError("block outcome cannot expose permitted actions")
        if requested_action not in prohibited:
            raise ValueError("block outcome must prohibit the requested action")
        return

    if outcome in _DEFERRED_OUTCOMES:
        if requested_action in permitted:
            raise ValueError(f"{outcome} cannot directly permit the requested action")
        if requested_action not in prohibited:
            raise ValueError(f"{outcome} must keep the requested action prohibited pending resolution")
        return

    raise ValueError(f"unknown decision outcome {outcome!r}")


def build_pama_decision(
    proposal: policy.Proposal,
    decision: policy.Decision,
    selected_action: str,
    selection_mode: str | None,
    receipt_ref: str,
) -> dict:
    # PAMA decision 1.1.0 adds the closed-enum `decision_overwrite` operation.
    # Existing operations remain 1.0.0 so older decision artifacts and closed
    # consumers do not acquire a new semantic contract retroactively.
    schema_version = "1.1.0" if proposal.operation == "decision_overwrite" else "1.0.0"
    document = {
        "schema_version": schema_version,
        "proposal_id": proposal.proposal_id,
        "proposing_actor": {"id": proposal.actor_id, "charter_version": proposal.charter_version},
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
            "selected_action": None if selected_action == NO_ACTION else selected_action,
            "selection_mode": selection_mode,
            "decision_receipt_ref": receipt_ref,
        },
    }
    if proposal.tenant_ref:
        document["target"]["tenant_ref"] = proposal.tenant_ref
    if proposal.purpose:
        document["target"]["purpose"] = proposal.purpose
    _attach_estimates(document["basis"], proposal)
    validate("pama-decision.schema.json", document)
    return document


def _attach_estimates(basis: dict, proposal: policy.Proposal) -> None:
    if proposal.estimator_refs:
        basis["estimator_refs"] = list(proposal.estimator_refs)
    if proposal.estimator_versions:
        basis["estimator_versions"] = list(proposal.estimator_versions)
    if proposal.confidence is not None:
        basis["confidence"] = proposal.confidence


def build_receipt(
    receipt_id: str,
    proposal: policy.Proposal,
    decision: policy.Decision,
    selected_action: str,
    selection_mode: str,
    timestamp: str,
    before_state: str,
    after_state: str,
    rollback_ref: str | None = None,
) -> dict:
    enforce_decision_consistency(
        decision.outcome,
        proposal.operation,
        decision.permitted_actions,
        decision.prohibited_actions,
    )
    enforce_selection(decision.permitted_actions, selected_action)
    document = {
        "schema_version": "1.1.0",
        "receipt_id": receipt_id,
        "decision_ref": decision_ref_for(proposal.proposal_id),
        "decision_outcome": decision.outcome,
        "memory_id": proposal.target_reference,
        "actor": proposal.actor_id,
        "requested_action": proposal.operation,
        "state_snapshot": proposal.state_snapshot,
        "policy_version": decision.policy_version,
        "permitted_actions": list(decision.permitted_actions),
        "prohibited_actions": list(decision.prohibited_actions),
        "selected_action": selected_action,
        "selection_mode": selection_mode,
        "before_state": before_state,
        "after_state": after_state,
        "evidence_refs": list(proposal.evidence_refs),
        "timestamp": timestamp,
    }
    if proposal.estimator_refs:
        document["estimate_refs"] = list(proposal.estimator_refs)
    if proposal.estimator_versions:
        document["estimator_versions"] = {
            ref: version
            for ref, version in zip(proposal.estimator_refs, proposal.estimator_versions)
        }
    if rollback_ref:
        document["rollback_or_recovery_ref"] = rollback_ref
    validate("decision-receipt.schema.json", document)
    return document


def verify_receipt_decision_pair(receipt: dict, pama_decision: dict) -> None:
    """Verify that a receipt and PAMA decision describe the same authority event."""
    validate("decision-receipt.schema.json", receipt)
    validate("pama-decision.schema.json", pama_decision)

    expected_ref = decision_ref_for(pama_decision["proposal_id"])
    if receipt.get("decision_ref") != expected_ref:
        raise ValueError(
            f"receipt decision_ref {receipt.get('decision_ref')!r} does not match {expected_ref!r}"
        )

    decision = pama_decision["decision"]
    comparisons = {
        "decision_outcome": decision["outcome"],
        "permitted_actions": decision["permitted_actions"],
        "prohibited_actions": decision["prohibited_actions"],
        "policy_version": pama_decision["policy"]["policy_version"],
    }
    for receipt_field, decision_value in comparisons.items():
        if receipt.get(receipt_field) != decision_value:
            raise ValueError(
                f"receipt {receipt_field} does not match referenced decision: "
                f"receipt={receipt.get(receipt_field)!r} decision={decision_value!r}"
            )

    receipt_selected = receipt["selected_action"]
    decision_selected = decision.get("selected_action")
    normalized_decision_selected = NO_ACTION if decision_selected is None else decision_selected
    if receipt_selected != normalized_decision_selected:
        raise ValueError(
            "receipt selected_action does not match referenced decision: "
            f"receipt={receipt_selected!r} decision={normalized_decision_selected!r}"
        )

    if decision.get("decision_receipt_ref") != receipt["receipt_id"]:
        raise ValueError("referenced decision does not point back to this receipt")

    enforce_decision_consistency(
        receipt["decision_outcome"],
        receipt["requested_action"],
        tuple(receipt["permitted_actions"]),
        tuple(receipt.get("prohibited_actions") or ()),
    )
    enforce_selection(tuple(receipt["permitted_actions"]), receipt_selected)


def build_audit_event(
    event_id: str,
    event_type: str,
    timestamp: str,
    component: str,
    memory_id: str,
    correlation_id: str,
    causation_id: str | None = None,
    policy_version: str | None = None,
    authority: dict | None = None,
    receipt_ref: str | None = None,
) -> dict:
    document = {
        "schema_version": "1.0.0",
        "event_id": event_id,
        "event_type": event_type,
        "event_version": "1.0.0",
        "timestamp": timestamp,
        "component": component,
        "memory_id": memory_id,
        "correlation_id": correlation_id,
    }
    for key, value in (
        ("causation_id", causation_id),
        ("policy_version", policy_version),
        ("authority", authority),
        ("receipt_ref", receipt_ref),
    ):
        if value is not None:
            document[key] = value
    validate("memory-audit-event.schema.json", document)
    return document
