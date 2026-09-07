"""Agent Memory integration for Hermes Agent."""

from __future__ import annotations

INTEGRATION_VERSION = "0.1.0"
INTEGRATION_PROFILE = "agent-memory-hermes/1.0.0"
HERMES_REPOSITORY = "NousResearch/hermes-agent"
HERMES_COMMIT = "165c889e5b4277b56dadd42949a4112c1e6175a6"

INTERCEPTABLE_TOOLS = frozenset({"memory", "skill_manage"})

STRICT_BLOCKERS = (
    "approved_pending_memory_replay",
    "approved_pending_skill_replay",
    "deterministic_curator_archive",
    "journey_memory_edit_delete",
    "journey_skill_edit_delete",
    "out_of_band_memory_skill_filesystem_write",
)

MUTATION_SURFACES = (
    "foreground_builtin_memory_tool",
    "foreground_skill_manage",
    "background_review_memory",
    "background_review_skill_manage",
    "approved_pending_memory_replay",
    "approved_pending_skill_replay",
    "deterministic_curator_archive",
    "curator_llm_consolidation",
    "journey_memory_edit_delete",
    "journey_skill_edit_delete",
    "external_memory_provider_mirror",
    "out_of_band_memory_skill_filesystem_write",
)

__all__ = [
    "HERMES_COMMIT",
    "HERMES_REPOSITORY",
    "INTEGRATION_PROFILE",
    "INTEGRATION_VERSION",
    "INTERCEPTABLE_TOOLS",
    "MUTATION_SURFACES",
    "STRICT_BLOCKERS",
]
