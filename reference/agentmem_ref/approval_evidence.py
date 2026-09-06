"""Vendor-neutral one-action approval evidence for issue #187.

Approval is evidence about one exact governed action/state identity. It is not a
standing grant, cannot widen a stricter decision, and does not prove execution.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import rfc8785

from . import receipts

APPROVAL_VERSION = "0.1.0"
_OUTCOMES = {"approved", "denied", "revoked"}


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("approval timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def _sha256_ref(value: dict) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def build_approval_evidence(
    composition: dict,
    *,
    principal_ref: str,
    authority_evidence_ref: str,
    scope_ref: str,
    outcome: str,
    mechanism_ref: str,
    issued_at: str,
    expires_at: str | None = None,
    revoked_at: str | None = None,
    revocation_evidence_ref: str | None = None,
    evidence_refs: tuple[str, ...] = (),
) -> dict:
    """Create one-action approval evidence bound to a decision composition."""

    receipts.validate("decision-composition-receipt.schema.json", composition)
    for name, value in (
        ("principal_ref", principal_ref),
        ("authority_evidence_ref", authority_evidence_ref),
        ("scope_ref", scope_ref),
        ("mechanism_ref", mechanism_ref),
        ("issued_at", issued_at),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} must be a non-empty string")
    if outcome not in _OUTCOMES:
        raise ValueError(f"invalid approval outcome {outcome!r}")

    issued = _parse_time(issued_at)
    if expires_at is not None and _parse_time(expires_at) < issued:
        raise ValueError("approval expiry cannot precede issuance")
    if revoked_at is not None and _parse_time(revoked_at) < issued:
        raise ValueError("approval revocation cannot precede issuance")
    if outcome == "revoked" and revoked_at is None:
        raise ValueError("revoked approval requires revoked_at")
    if revoked_at is not None and not revocation_evidence_ref:
        raise ValueError("revoked_at requires revocation_evidence_ref")

    body = {
        "input_identity": composition["input_identity"],
        "composition_id": composition["composition_id"],
        "principal_ref": principal_ref,
        "authority_evidence_ref": authority_evidence_ref,
        "scope_ref": scope_ref,
        "outcome": outcome,
        "mechanism_ref": mechanism_ref,
        "issued_at": issued_at,
        "evidence_refs": list(dict.fromkeys(evidence_refs)),
        "reusable_authority": False,
    }
    if expires_at is not None:
        body["expires_at"] = expires_at
    if revoked_at is not None:
        body["revoked_at"] = revoked_at
        body["revocation_evidence_ref"] = revocation_evidence_ref

    document = {
        "schema_version": "1.0.0",
        "approval_version": APPROVAL_VERSION,
        "approval_id": f"approval:{_sha256_ref(body)}",
        **body,
    }
    receipts.validate("approval-evidence.schema.json", document)
    return document


def verify_approval_evidence(
    approval: dict,
    composition: dict,
    *,
    expected_scope_ref: str,
    observed_at: str,
) -> dict:
    """Verify whether approval currently satisfies ``require_approval``.

    Historical validity is preserved separately from current satisfaction. A
    valid approval presented to an ``allow`` or ``deny`` composition is
    ``not_applicable`` rather than treated as a magic authorization token.
    """

    receipts.validate("approval-evidence.schema.json", approval)
    receipts.validate("decision-composition-receipt.schema.json", composition)
    observed = _parse_time(observed_at)
    reasons: list[str] = []

    if approval["input_identity"] != composition["input_identity"]:
        reasons.append("input_identity_mismatch")
    if approval["composition_id"] != composition["composition_id"]:
        reasons.append("composition_id_mismatch")
    if approval["scope_ref"] != expected_scope_ref:
        reasons.append("scope_ref_mismatch")

    if reasons:
        status = "invalid"
        satisfied = False
    elif composition["effective_decision"] != "require_approval":
        status = "not_applicable"
        satisfied = False
        reasons.append(f"effective_decision:{composition['effective_decision']}")
    elif approval["outcome"] == "denied":
        status = "denied"
        satisfied = False
        reasons.append("approval_denied")
    elif approval["outcome"] == "revoked":
        status = "stale"
        satisfied = False
        reasons.append("approval_revoked")
    elif _parse_time(approval["issued_at"]) > observed:
        status = "invalid"
        satisfied = False
        reasons.append("approval_not_yet_issued")
    elif approval.get("revoked_at") is not None and _parse_time(approval["revoked_at"]) <= observed:
        status = "stale"
        satisfied = False
        reasons.append("approval_revoked")
    elif approval.get("expires_at") is not None and _parse_time(approval["expires_at"]) < observed:
        status = "stale"
        satisfied = False
        reasons.append("approval_expired")
    else:
        status = "current"
        satisfied = approval["outcome"] == "approved"
        if not satisfied:
            reasons.append("approval_not_approved")

    result = {
        "schema_version": "0.1.0",
        "approval_id": approval["approval_id"],
        "input_identity": approval["input_identity"],
        "composition_id": approval["composition_id"],
        "status": status,
        "satisfies_required_approval": satisfied,
        "reasons": list(dict.fromkeys(reasons)),
        "reusable_authority": False,
    }
    receipts.validate("approval-verification-result.schema.json", result)
    return result
