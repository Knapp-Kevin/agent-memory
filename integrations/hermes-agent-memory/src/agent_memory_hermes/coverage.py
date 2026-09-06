"""Coverage and doctor semantics for the pinned Hermes integration profile."""

from __future__ import annotations

from typing import Any

from . import (
    HERMES_COMMIT,
    HERMES_REPOSITORY,
    INTEGRATION_PROFILE,
    INTEGRATION_VERSION,
    MUTATION_SURFACES,
    STRICT_BLOCKERS,
)
from .config import IntegrationConfig


_INTERCEPTABLE = {
    "foreground_builtin_memory_tool",
    "foreground_skill_manage",
    "background_review_memory",
    "background_review_skill_manage",
    "curator_llm_consolidation",
}
_OBSERVED_PROVIDER = {"external_memory_provider_mirror"}


def _surface_status(surface: str, mode: str) -> str:
    if surface in _INTERCEPTABLE:
        return "intercepted" if mode in {"govern", "strict"} else "observed"
    if surface in _OBSERVED_PROVIDER:
        return "observed"
    return "uncovered"


def _recursive_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "self_reinforcing_skill_lineage",
            "status": "governor_evaluable_when_lineage_available",
            "requirement": "causally related experience/skill/output lineage must not be counted as independent corroboration",
            "integration_support": "candidate schema preserves lineage_refs when upstream/caller provides them and always preserves Hermes tool/session scope",
        },
        {
            "scenario_id": "correction_relearned_by_background_review",
            "status": "governor_evaluable_when_supersession_evidence_available",
            "requirement": "a corrected/rejected value remains non-current unless new independent evidence satisfies readmission policy",
            "integration_support": "candidate schema preserves provenance_refs and blocks when the external governor rejects the reproposal",
        },
        {
            "scenario_id": "stale_human_approval_replay",
            "status": "uncovered_requires_future_durable_state_hook",
            "requirement": "approval replay must revalidate reviewed before-state digest, candidate digest, and scope immediately before commit",
            "blocking_surface": "approved_pending_memory_replay",
        },
        {
            "scenario_id": "curator_archive_during_pending_dependency",
            "status": "uncovered_requires_future_durable_state_hook",
            "requirement": "skill retirement/archive must check live dependencies and residue obligations before durable transition",
            "blocking_surface": "deterministic_curator_archive",
        },
        {
            "scenario_id": "provider_mirror_failure_after_builtin_commit",
            "status": "modeled",
            "requirement": "built-in commit remains committed while failed external projection is unsettled/non-quiescent; no rollback may be claimed",
            "integration_support": "MemoryProvider records canonical_builtin_state=committed, external_projection=failed, settled=false, quiescent=false",
        },
    ]


def build_coverage_report(
    config: IntegrationConfig,
    *,
    observed_hermes_revision: str,
) -> dict[str, Any]:
    current = observed_hermes_revision == config.expected_hermes_revision == HERMES_COMMIT
    surfaces = []
    for surface in MUTATION_SURFACES:
        notes: list[str] = []
        if surface in {"background_review_memory", "background_review_skill_manage"}:
            notes.append(
                "mechanically routed through the same model tool hook, but the pinned pre_tool_call metadata does not expose Hermes _memory_write_origin"
            )
        if surface == "external_memory_provider_mirror":
            notes.append("post-commit observation only; provider callback is not built-in admission authority")
        if surface in STRICT_BLOCKERS:
            notes.append("does not traverse the normal tool executor at the pinned Hermes profile")
        surfaces.append(
            {
                "surface_id": surface,
                "status": _surface_status(surface, config.mode),
                "origin_precision": (
                    "mechanical_path_only"
                    if surface in {"background_review_memory", "background_review_skill_manage"}
                    else "surface_specific"
                ),
                "notes": notes,
            }
        )

    reasons: list[str] = []
    if config.mode == "strict":
        reasons.append("strict mode is unsupported at the pinned Hermes profile")
    if config.require_exact_profile and not current:
        reasons.append(
            "exact Hermes profile is not current: "
            f"observed={observed_hermes_revision} expected={config.expected_hermes_revision}"
        )
    if config.mode == "govern" and config.governor_required and not config.governor_command:
        reasons.append("govern mode requires a configured governor_command")

    ready = not reasons
    return {
        "schema_version": "1.0.0",
        "hermes": {
            "repository": HERMES_REPOSITORY,
            "observed_revision": observed_hermes_revision,
            "expected_revision": config.expected_hermes_revision,
            "research_pin": HERMES_COMMIT,
            "profile_current": current,
        },
        "integration": {
            "profile": INTEGRATION_PROFILE,
            "version": INTEGRATION_VERSION,
            "mode": config.mode,
            "ready": ready,
            "governor_required": config.governor_required,
            "governor_configured": bool(config.governor_command),
            "record_payloads": config.record_payloads,
        },
        "surfaces": surfaces,
        "strict": {
            "supported": False,
            "blocking_surfaces": list(STRICT_BLOCKERS),
            "reason": "six consequential durable mutation families remain outside plugin/provider interception",
        },
        "recursive_evidence_scenarios": _recursive_scenarios(),
        "limitations": [
            "external MemoryProvider observation is post-commit and incomplete for background/approval/curator/Journey/direct-file mutation paths",
            "pre_tool_call cannot distinguish foreground from background_review origin at the pinned profile without additional Hermes metadata",
            "Agent Memory stage cannot be represented as a native staged durable mutation through the generic pre_tool_call hook",
            "full causal lineage and supersession state are not exposed by Hermes pre_tool_call metadata; govern mode preserves such refs when supplied and must not invent them",
        ],
        "reasons_not_ready": reasons,
        "authority_effect": "none",
    }
