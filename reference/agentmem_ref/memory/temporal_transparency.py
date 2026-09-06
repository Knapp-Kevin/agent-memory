"""Provider-neutral transparency receipt normalization for #265.

Verified inclusion or consistency evidence can strengthen historical integrity,
but it does not by itself establish complete history, global non-equivocation,
Agent Memory currentness, or PAMA authority.
"""

from __future__ import annotations

from typing import Any, Mapping

from ..core import receipts

AUTHORITY_EFFECT = "none"
PROFILE_ID = "agent-memory/temporal-transparency-receipt"
_VERIFICATION_VALUES = {"verified", "invalid", "unknown"}
_CLAIM_VALUES = {"inclusion", "consistency"}


def _required(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _digest(value: Any, field: str) -> str:
    value = _required(value, field)
    if not value.startswith("sha256:") or len(value) != 71:
        raise ValueError(f"{field} must be sha256:<64hex>")
    try:
        int(value[7:], 16)
    except ValueError as exc:
        raise ValueError(f"{field} must be sha256:<64hex>") from exc
    if value[7:] != value[7:].lower():
        raise ValueError(f"{field} must use lowercase hex")
    return value


def build_transparency_receipt_evidence(
    *,
    subject_reference_profile: str,
    subject_ref: str,
    claim_kind: str,
    vds_profile: str,
    verification_status: str,
    receipt_ref: str,
    verifier_profile: str,
    verifier_version: str,
    verifier_source_ref: str,
    evidence_refs: list[str] | tuple[str, ...],
    tree_size: int | None = None,
    prior_tree_size: int | None = None,
    root_ref: str | None = None,
    prior_root_ref: str | None = None,
) -> dict[str, Any]:
    """Normalize already-verified transparency evidence into an Agent Memory boundary."""
    if claim_kind not in _CLAIM_VALUES:
        raise ValueError(f"unsupported claim_kind: {claim_kind}")
    if verification_status not in _VERIFICATION_VALUES:
        raise ValueError(f"unsupported verification_status: {verification_status}")
    subject_reference_profile = _required(subject_reference_profile, "subject_reference_profile")
    subject_ref = _digest(subject_ref, "subject_ref")
    vds_profile = _required(vds_profile, "vds_profile")
    receipt_ref = _required(receipt_ref, "receipt_ref")
    verifier_profile = _required(verifier_profile, "verifier_profile")
    verifier_version = _required(verifier_version, "verifier_version")
    verifier_source_ref = _required(verifier_source_ref, "verifier_source_ref")

    refs = list(dict.fromkeys(evidence_refs))
    if not all(isinstance(item, str) and item for item in refs):
        raise ValueError("evidence_refs must contain non-empty strings")
    if verification_status == "verified" and not refs:
        raise ValueError("verified transparency evidence requires evidence_refs")

    if tree_size is not None and (isinstance(tree_size, bool) or not isinstance(tree_size, int) or tree_size < 1):
        raise ValueError("tree_size must be a positive integer")
    if prior_tree_size is not None and (
        isinstance(prior_tree_size, bool) or not isinstance(prior_tree_size, int) or prior_tree_size < 1
    ):
        raise ValueError("prior_tree_size must be a positive integer")
    if root_ref is not None:
        root_ref = _digest(root_ref, "root_ref")
    if prior_root_ref is not None:
        prior_root_ref = _digest(prior_root_ref, "prior_root_ref")

    if claim_kind == "inclusion":
        if tree_size is None or root_ref is None:
            raise ValueError("inclusion evidence requires tree_size and root_ref")
        if prior_tree_size is not None or prior_root_ref is not None:
            raise ValueError("inclusion evidence must not carry prior tree state")
    else:
        if None in (tree_size, prior_tree_size, root_ref, prior_root_ref):
            raise ValueError("consistency evidence requires prior and current tree state")
        if prior_tree_size >= tree_size:
            raise ValueError("consistency evidence requires prior_tree_size < tree_size")

    evidence = {
        "schema_version": "1.0.0",
        "profile_id": PROFILE_ID,
        "subject_reference_profile": subject_reference_profile,
        "subject_ref": subject_ref,
        "claim_kind": claim_kind,
        "vds_profile": vds_profile,
        "verification_status": verification_status,
        "receipt_ref": receipt_ref,
        "tree_size": tree_size,
        "prior_tree_size": prior_tree_size,
        "root_ref": root_ref,
        "prior_root_ref": prior_root_ref,
        "verifier": {
            "profile": verifier_profile,
            "version": verifier_version,
            "source_ref": verifier_source_ref,
        },
        "evidence_refs": refs,
        "interpretation": {
            "authority_effect": AUTHORITY_EFFECT,
            "event_occurrence_time_proven": False,
            "currentness": "not_established",
            "complete_history_proven": False,
            "global_non_equivocation_proven": False,
        },
    }
    receipts.validate("temporal-transparency-receipt.schema.json", evidence)
    return evidence


def verify_transparency_binding(
    evidence: Mapping[str, Any],
    *,
    expected_subject_reference_profile: str,
    expected_subject_ref: str,
) -> dict[str, Any]:
    """Verify exact subject binding while keeping the receipt's claim bounded."""
    material = dict(evidence)
    receipts.validate("temporal-transparency-receipt.schema.json", material)
    expected_subject_reference_profile = _required(
        expected_subject_reference_profile, "expected_subject_reference_profile"
    )
    expected_subject_ref = _digest(expected_subject_ref, "expected_subject_ref")

    bound = (
        material["verification_status"] == "verified"
        and material["subject_reference_profile"] == expected_subject_reference_profile
        and material["subject_ref"] == expected_subject_ref
    )
    return {
        "bound": bound,
        "verification_status": material["verification_status"],
        "claim_kind": material["claim_kind"],
        "append_only_transition_verified": bound and material["claim_kind"] == "consistency",
        "inclusion_verified": bound and material["claim_kind"] == "inclusion",
        "complete_history_proven": False,
        "global_non_equivocation_proven": False,
        "event_occurrence_time_proven": False,
        "currentness": "not_established",
        "authority_effect": AUTHORITY_EFFECT,
    }
