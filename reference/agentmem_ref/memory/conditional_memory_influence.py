"""Vendor-neutral admission evidence for model-internal conditional memory."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from ..core import receipts

UNAVAILABLE_REF = "urn:agent-memory:evidence:unavailable"

NONCLAIMS = (
    "address_is_not_identity",
    "prefetch_is_not_admission",
    "external_deletion_is_not_internal_forgetting",
    "influence_is_not_mutation_authority",
    "collision_is_not_equivalence",
    "configured_gate_is_not_enforcement_proof",
)


def opaque_address_digest(address: Any) -> str:
    """Hash an address description without retaining token IDs or raw lookup values."""
    raw = json.dumps(address, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def map_currentness(applicability_status: str | None, source_state: str | None = None) -> str:
    """Map generic derivation/source posture into the profile's bounded vocabulary."""
    if applicability_status == "current" and source_state in (None, "current"):
        return "current"
    if source_state == "revoked":
        return "revoked"
    if source_state == "deleted":
        return "deleted_residue"
    if applicability_status in {"revalidation_required", "stale", "non_current"}:
        return "stale"
    return "unknown"


def decide_gate(
    *,
    table_partition: str | None,
    requested_partition: str | None,
    currentness: str | None,
    suppression: str | None,
    table_version_supported: bool | None = True,
) -> tuple[str, tuple[str, ...]]:
    """Return the narrowest explicit gate result for one influence attempt."""
    if table_version_supported is not True:
        return "block_unknown", ("table format/version is unsupported or unavailable",)
    if not table_partition or not requested_partition:
        return "block_unknown", ("partition evidence unavailable",)
    if table_partition != requested_partition:
        return "block_scope", ("requested partition does not match active table partition",)
    if currentness in (None, "unknown"):
        return "block_unknown", ("table currentness unavailable",)
    if currentness != "current":
        return "block_stale", (f"table currentness is {currentness}",)
    if suppression in (None, "unknown"):
        return "block_unknown", ("suppression posture unavailable",)
    if suppression == "suppressed":
        return "block_suppressed", ("active suppression overlay applies",)
    if suppression != "clear":
        return "block_unknown", ("unsupported suppression posture",)
    return "allow", ("table current, partition matched, suppression clear",)


def _evidence_safe_table(table: dict[str, Any]) -> dict[str, Any]:
    safe = dict(table)
    for field in ("partition_ref", "currentness_ref", "suppression_overlay_ref"):
        if not safe.get(field):
            safe[field] = UNAVAILABLE_REF
    return safe


def _evidence_safe_request(request: dict[str, Any]) -> dict[str, Any]:
    safe = dict(request)
    if not safe.get("partition_ref"):
        safe["partition_ref"] = UNAVAILABLE_REF
    return safe


def normalize_influence(
    *,
    influence_id: str,
    lookup_ref: str,
    address: Any,
    table: dict[str, Any],
    request: dict[str, Any],
    currentness: str | None,
    suppression: str | None,
    enforcement_posture: str,
    correlation_ref: str,
    observed_at: str,
    collision_ref: str | None = None,
    table_version_supported: bool | None = True,
) -> dict[str, Any]:
    """Build privacy-minimized evidence for a conditional-memory influence gate."""
    result, reasons = decide_gate(
        table_partition=table.get("partition_ref"),
        requested_partition=request.get("partition_ref"),
        currentness=currentness,
        suppression=suppression,
        table_version_supported=table_version_supported,
    )
    document: dict[str, Any] = {
        "schema_version": "1.0.0",
        "profile_version": "0.1.0",
        "influence_id": influence_id,
        "lookup_ref": lookup_ref,
        "opaque_address_digest": opaque_address_digest(address),
        "table": _evidence_safe_table(table),
        "request": _evidence_safe_request(request),
        "currentness": currentness or "unknown",
        "suppression": suppression or "unknown",
        "gate": {
            "result": result,
            "reasons": list(reasons),
            "influence_eligible": result == "allow",
        },
        "enforcement_posture": enforcement_posture,
        "correlation_ref": correlation_ref,
        "observed_at": observed_at,
        "nonclaims": list(NONCLAIMS),
    }
    if collision_ref:
        document["collision_ref"] = collision_ref
    receipts.validate("conditional-memory-influence.schema.json", document)
    return document


def validate_table_replacement(old_record: dict[str, Any], new_record: dict[str, Any]) -> None:
    """Prove replacement identity without mutating historical influence evidence."""
    receipts.validate("conditional-memory-influence.schema.json", old_record)
    receipts.validate("conditional-memory-influence.schema.json", new_record)
    old_table = old_record["table"]
    new_table = new_record["table"]
    if old_table["table_id"] == new_table["table_id"]:
        raise ValueError("replacement table must have distinct table identity")
    if old_table["table_digest"] == new_table["table_digest"]:
        raise ValueError("replacement table must have distinct artifact digest")
    if new_record["gate"]["result"] == "allow" and new_record["currentness"] != "current":
        raise ValueError("replacement cannot be influence-eligible without current evidence")
