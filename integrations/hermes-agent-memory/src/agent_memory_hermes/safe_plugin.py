"""Fail-closed Hermes hook wrapper.

Hermes deliberately isolates plugin callback exceptions. A required governance
integration therefore cannot rely on an exception to stop a durable tool call.
This wrapper converts integration/configuration failure into an explicit native
Hermes block for the two durable model-tool surfaces this profile governs.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from . import INTERCEPTABLE_TOOLS
from .plugin import runtime_for_current_home


def _pre_tool_hook(
    tool_name: str = "",
    args: Optional[Mapping[str, Any]] = None,
    **kwargs: Any,
):
    if tool_name not in INTERCEPTABLE_TOOLS:
        return None
    try:
        return runtime_for_current_home().on_pre_tool_call(tool_name=tool_name, args=args, **kwargs)
    except Exception as exc:
        return {
            "action": "block",
            "message": (
                "Agent Memory Hermes integration failed before durable-state admission; "
                f"refusing {tool_name} mutation rather than allowing through plugin failure. "
                f"error={type(exc).__name__}"
            ),
        }


def _post_tool_hook(
    tool_name: str = "",
    args: Optional[Mapping[str, Any]] = None,
    **kwargs: Any,
) -> None:
    if tool_name not in INTERCEPTABLE_TOOLS:
        return
    try:
        runtime_for_current_home().on_post_tool_call(tool_name=tool_name, args=args, **kwargs)
    except Exception:
        # Post-execution evidence failure cannot retroactively change the
        # execution result. Hermes' own hook isolation will also log plugin
        # errors; the next doctor/coverage run reports integration readiness.
        return


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _pre_tool_hook)
    ctx.register_hook("post_tool_call", _post_tool_hook)
