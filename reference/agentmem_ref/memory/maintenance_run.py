"""Public validation entry point for maintenance-run evidence."""

from __future__ import annotations

from typing import Any

from .maintenance_run_bindings import validate_bindings
from .maintenance_run_rules import validate_rules


def validate_run(record: dict[str, Any], pama_decisions: dict[str, dict[str, Any]]) -> None:
    validate_rules(record)
    validate_bindings(record, pama_decisions)


def next_cursor(
    record: dict[str, Any],
    current_cursor: str | int,
    seen_run_ids: set[str],
) -> str | int:
    run_id = record["run_id"]
    if run_id in seen_run_ids:
        raise ValueError("duplicate run identity")
    if record["cursor_before"] != current_cursor:
        raise ValueError("cursor mismatch")
    seen_run_ids.add(run_id)
    if record["transaction_status"] == "committed":
        return record["cursor_after"]
    return current_cursor
