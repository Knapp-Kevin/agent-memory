"""Constituent PAMA binding checks for maintenance-run evidence."""

from __future__ import annotations

from typing import Any

from ..core import receipts
from .maintenance_run_rules import HOUSEKEEPING


def validate_bindings(
    record: dict[str, Any],
    pama_decisions: dict[str, dict[str, Any]],
) -> None:
    declared_items = record["constituent_decisions"]
    refs = [item["decision_ref"] for item in declared_items]
    if len(refs) != len(set(refs)):
        raise ValueError("constituent decision refs must be unique")

    declared = {item["decision_ref"]: item for item in declared_items}
    planned = set(record["planned_operations"])
    governed = planned - HOUSEKEEPING
    represented = {item["operation"] for item in declared_items}
    missing = governed - represented
    if missing:
        raise ValueError(f"planned governed operations lack PAMA decisions: {sorted(missing)}")

    for item in declared_items:
        if item["operation"] not in planned:
            raise ValueError("constituent operation is absent from planned operation set")

    if set(declared) != set(pama_decisions):
        raise ValueError("resolved PAMA decision set does not match declared refs")

    for decision_ref, item in declared.items():
        document = pama_decisions[decision_ref]
        receipts.validate("pama-decision.schema.json", document)
        if decision_ref != receipts.decision_ref_for(document["proposal_id"]):
            raise ValueError("decision ref does not resolve to supplied PAMA decision")
        if item["operation"] != document["mutation"]["operation"]:
            raise ValueError("constituent operation mismatch")
        if item["outcome"] != document["decision"]["outcome"]:
            raise ValueError("constituent outcome mismatch")

        target = document.get("target", {})
        tenant = target.get("tenant_ref")
        if tenant and tenant != record["scope"]["tenant_ref"]:
            raise ValueError("constituent tenant mismatch")
        purpose = target.get("purpose")
        if purpose and purpose != record["scope"]["purpose"]:
            raise ValueError("constituent purpose mismatch")
