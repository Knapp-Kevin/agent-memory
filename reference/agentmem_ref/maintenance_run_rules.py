"""Cross-field rules for maintenance-run transaction evidence."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from . import receipts
from .maintenance_run_state import digest_for

COMMIT_ELIGIBLE = {"allow", "allow_with_ledger"}
HOUSEKEEPING = {"index_rebuild", "cache_rebuild", "projection_refresh"}


def validate_rules(record: dict[str, Any]) -> None:
    receipts.validate("maintenance-run-evidence.schema.json", record)
    if record["evidence_digest"] != digest_for(record):
        raise ValueError("digest mismatch")

    start = datetime.fromisoformat(record["started_at"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(record["completed_at"].replace("Z", "+00:00"))
    if end < start:
        raise ValueError("invalid time order")

    status = record["transaction_status"]
    cursor_changed = record["cursor_after"] != record["cursor_before"]

    if status == "committed":
        if record["commit_status"] != "succeeded" or record["validation_status"] != "passed":
            raise ValueError("clean completion requires commit and validation success")
        if record["source_currentness"] != "current":
            raise ValueError("clean completion requires current source evidence")
        if not cursor_changed:
            raise ValueError("clean completion must advance cursor")
        if record.get("rollback_ref") or record.get("quarantine_ref"):
            raise ValueError("clean completion cannot carry recovery refs")
        if any(item["outcome"] not in COMMIT_ELIGIBLE for item in record["constituent_decisions"]):
            raise ValueError("clean completion contains unresolved constituent decision")
        if record["policy_version"] != record["commit_policy_version"] and not record.get("policy_revalidation_ref"):
            raise ValueError("policy version changed without revalidation evidence")
    elif cursor_changed:
        raise ValueError("cursor changed before clean completion")

    if record["commit_status"] == "partial" and status not in {"rolled_back", "quarantined", "failed"}:
        raise ValueError("partial result requires recovery disposition")
    if status == "rolled_back" and not record.get("rollback_ref"):
        raise ValueError("missing rollback reference")
    if status == "quarantined" and not record.get("quarantine_ref"):
        raise ValueError("missing quarantine reference")
    if status == "blocked_stale_source" and record["source_currentness"] == "current":
        raise ValueError("source state does not match disposition")

    planned = set(record["planned_operations"])
    if record["housekeeping_only"]:
        if not planned.issubset(HOUSEKEEPING):
            raise ValueError("housekeeping record includes semantic operation")
        if record["semantic_memory_changed"] or record["constituent_decisions"]:
            raise ValueError("housekeeping record cannot claim semantic change")
