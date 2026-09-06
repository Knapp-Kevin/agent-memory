"""Conservative mutation classification for pinned Hermes memory/skill tools."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from . import INTERCEPTABLE_TOOLS

_READ_ONLY_ACTIONS = frozenset(
    {
        "show",
        "read",
        "list",
        "get",
        "status",
        "inspect",
        "pending",
    }
)


def operation_name(tool_name: str, args: Optional[Mapping[str, Any]]) -> str:
    safe = args if isinstance(args, Mapping) else {}
    if tool_name == "memory":
        return str(safe.get("action") or "unknown").strip().lower()
    if tool_name == "skill_manage":
        return str(safe.get("action") or safe.get("mode") or "unknown").strip().lower()
    return "not_applicable"


def is_potential_durable_mutation(
    tool_name: str,
    args: Optional[Mapping[str, Any]],
) -> bool:
    if tool_name not in INTERCEPTABLE_TOOLS:
        return False
    operation = operation_name(tool_name, args)
    # At the exact researched profile, known read-only operations are allowed
    # through untouched. Unknown/new actions are treated conservatively as
    # potential mutations until a new Hermes profile is qualified.
    return operation not in _READ_ONLY_ACTIONS
