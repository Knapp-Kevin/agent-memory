"""Vendor-neutral policy decision projection and monotonic composition.

Issue #152 keeps three facts separate:

1. Agent Memory/PAMA decides memory-specific mutation authority.
2. An optional external provider may tighten the requested consequence.
3. A composed decision is still not evidence that any enforcement point was
   reached or that the action executed / was prevented.

The projection input identity uses RFC 8785/JCS, an existing reference
validation dependency, so action/state binding is deterministic across runtimes.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Protocol

import rfc8785

from ..core import policy, receipts

PROJECTION_VERSION = "0.1.0"
COMPOSITION_RULE_VERSION = "0.1.0"

ALLOW = "allow"
WARN = "warn"
REQUIRE_APPROVAL = "require_approval"
DENY = "deny"

PROVIDER_NONE = "none"
PROVIDER_ADVISORY = "advisory"
PROVIDER_AUTHORITATIVE = "authoritative"

STATUS_NOT_CONFIGURED = "not_configured"
STATUS_AVAILABLE = "available"
STATUS_UNAVAILABLE = "unavailable"
STATUS_INVALID = "invalid"
STATUS_STALE_IDENTITY = "stale_identity"

EXECUTION_UNKNOWN = "unknown"

_STRICTNESS = {
    ALLOW: 0,
    WARN: 1,
    REQUIRE_APPROVAL: 2,
    DENY: 3,
}

_PAMA_TO_NORMALIZED = {
    policy.ALLOW: ALLOW,
    policy.ALLOW_WITH_LEDGER: ALLOW,
    policy.REQUIRE_REVIEW: REQUIRE_APPROVAL,
    policy.REQUIRE_EXTERNAL_VERIFICATION: REQUIRE_APPROVAL,
    policy.BLOCK: DENY,
    "abstain": REQUIRE_APPROVAL,
    "collect_more_evidence": REQUIRE_APPROVAL,
    "quarantine": DENY,
}

_EXTERNAL_TO_NORMALIZED = {
    "allow": ALLOW,
    "warn": WARN,
    "escalate": REQUIRE_APPROVAL,
    "deny": DENY,
}


class ExternalPolicyProvider(Protocol):
    provider_id: str
    provider_version: str

    def evaluate(self, projection: dict) -> dict | None: ...


@dataclass(frozen=True)
class DeterministicFakeProvider:
    """No-network provider used only to characterize the generic seam."""

    provider_id: str = "fake-policy-provider"
    provider_version: str = "1.0.0"
    decision: str = "allow"
    reason: str = "deterministic conformance fixture"
    available: bool = True
    issued_at: str = "2026-08-12T18:00:00Z"

    def evaluate(self, projection: dict) -> dict | None:
        if not self.available:
            return None
        return build_external_decision(
            provider_id=self.provider_id,
            provider_version=self.provider_version,
            input_identity=projection["input_identity"],
            decision=self.decision,
            reason=self.reason,
            issued_at=self.issued_at,
            evidence={"fixture": True},
        )


def _jcs_sha256(document: dict) -> str:
    canonical = rfc8785.dumps(document)
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _bound_projection_input(proposal: policy.Proposal, decision: policy.Decision) -> dict:
    if not proposal.state_snapshot:
        raise ValueError("external enforcement projection requires a bound state_snapshot")
    return {
        "proposal_id": proposal.proposal_id,
        "memory_id": proposal.target_reference,
        "operation": proposal.operation,
        "actor_id": proposal.actor_id,
        "scope": proposal.scope,
        "tenant_ref": proposal.tenant_ref,
        "purpose": proposal.purpose,
        "isolation_domain_refs": sorted(set(proposal.isolation_domain_refs)),
        "required_isolation_domain_refs": sorted(set(proposal.required_isolation_domain_refs)),
        "state_snapshot": proposal.state_snapshot,
        "risk_class": proposal.risk_class,
        "reversibility": proposal.reversibility,
        "pama_decision_ref": receipts.decision_ref_for(proposal.proposal_id),
        "pama_outcome": decision.outcome,
        "permitted_actions": sorted(set(decision.permitted_actions)),
        "prohibited_actions": sorted(set(decision.prohibited_actions)),
        "policy_version": decision.policy_version,
        "evidence_refs": sorted(set(proposal.evidence_refs)),
    }


def build_projection(
    proposal: policy.Proposal,
    decision: policy.Decision,
    *,
    receipt_ref: str | None = None,
) -> dict:
    """Build the content-minimized action/authority projection.

    ``receipt_ref`` is intentionally not part of ``input_identity``. The same
    action/state authority identity can be projected before or after a local
    receipt object is materialized without changing what the provider evaluated.
    """

    bound = _bound_projection_input(proposal, decision)
    input_identity = _jcs_sha256(bound)
    document = {
        "schema_version": "1.0.0",
        "projection_version": PROJECTION_VERSION,
        "projection_id": f"enforcement-projection:{input_identity}",
        "input_identity": input_identity,
        **bound,
    }
    if receipt_ref:
        document["receipt_ref"] = receipt_ref
    receipts.validate("external-enforcement-decision-projection.schema.json", document)
    return document


def build_external_decision(
    *,
    provider_id: str,
    provider_version: str,
    input_identity: str,
    decision: str,
    reason: str,
    issued_at: str,
    evidence: dict | None = None,
) -> dict:
    document = {
        "schema_version": "1.0.0",
        "provider_id": provider_id,
        "provider_version": provider_version,
        "input_identity": input_identity,
        "decision": decision,
        "reason": reason,
        "issued_at": issued_at,
    }
    if evidence is not None:
        document["evidence"] = evidence
    receipts.validate("external-policy-decision.schema.json", document)
    return document


def external_decision_ref(decision: dict) -> str:
    receipts.validate("external-policy-decision.schema.json", decision)
    return f"external-policy-decision:{_jcs_sha256(decision)}"


def normalize_pama(outcome: str) -> str:
    try:
        return _PAMA_TO_NORMALIZED[outcome]
    except KeyError as exc:
        raise ValueError(f"unsupported PAMA outcome for external composition: {outcome!r}") from exc


def normalize_external(decision: str) -> str:
    try:
        return _EXTERNAL_TO_NORMALIZED[decision]
    except KeyError as exc:
        raise ValueError(f"unsupported external policy decision: {decision!r}") from exc


def strictest(*decisions: str) -> str:
    for decision in decisions:
        if decision not in _STRICTNESS:
            raise ValueError(f"unknown normalized decision {decision!r}")
    return max(decisions, key=lambda value: _STRICTNESS[value])


def compose(
    projection: dict,
    *,
    provider_mode: str,
    external_decision: dict | None = None,
) -> dict:
    """Compose local and external decisions without weakening authority.

    Advisory provider failures preserve the local result while explicitly
    recording that external policy was unavailable/invalid/stale. Authoritative
    provider failures deny. No branch of this function can turn a stricter local
    result into a weaker effective result.
    """

    receipts.validate("external-enforcement-decision-projection.schema.json", projection)
    if provider_mode not in {PROVIDER_NONE, PROVIDER_ADVISORY, PROVIDER_AUTHORITATIVE}:
        raise ValueError(f"invalid provider_mode {provider_mode!r}")
    if provider_mode == PROVIDER_NONE and external_decision is not None:
        raise ValueError("provider_mode 'none' cannot carry an external decision")

    local = normalize_pama(projection["pama_outcome"])
    provider_status = STATUS_NOT_CONFIGURED if provider_mode == PROVIDER_NONE else STATUS_UNAVAILABLE
    external_ref: str | None = None
    external_normalized: str | None = None
    reason = "no external policy provider configured"

    if provider_mode != PROVIDER_NONE and external_decision is not None:
        try:
            receipts.validate("external-policy-decision.schema.json", external_decision)
        except ValueError:
            provider_status = STATUS_INVALID
            reason = "external policy decision failed schema validation"
        else:
            external_ref = external_decision_ref(external_decision)
            if external_decision["input_identity"] != projection["input_identity"]:
                provider_status = STATUS_STALE_IDENTITY
                reason = "external policy decision input identity does not match current projection"
            else:
                provider_status = STATUS_AVAILABLE
                external_normalized = normalize_external(external_decision["decision"])
                reason = external_decision["reason"]

    if provider_status == STATUS_AVAILABLE:
        assert external_normalized is not None
        effective = strictest(local, external_normalized)
    elif provider_mode == PROVIDER_AUTHORITATIVE:
        effective = DENY
    else:
        effective = local

    body = {
        "input_identity": projection["input_identity"],
        "local_decision_ref": projection["pama_decision_ref"],
        "local_normalized_decision": local,
        "provider_mode": provider_mode,
        "external_provider_status": provider_status,
        "effective_decision": effective,
        "composition_rule_version": COMPOSITION_RULE_VERSION,
        "execution_status": EXECUTION_UNKNOWN,
        "reason": reason,
    }
    if external_ref:
        body["external_decision_ref"] = external_ref
    if external_normalized is not None and provider_status == STATUS_AVAILABLE:
        body["external_normalized_decision"] = external_normalized

    composition_identity = _jcs_sha256(body)
    document = {
        "schema_version": "1.0.0",
        "composition_id": f"decision-composition:{composition_identity}",
        **body,
    }
    receipts.validate("decision-composition-receipt.schema.json", document)
    _enforce_monotonicity(document)
    return document


def _enforce_monotonicity(receipt: dict) -> None:
    local = receipt["local_normalized_decision"]
    effective = receipt["effective_decision"]
    if _STRICTNESS[effective] < _STRICTNESS[local]:
        raise ValueError(
            f"composed decision weakened local authority: local={local!r}, effective={effective!r}"
        )
