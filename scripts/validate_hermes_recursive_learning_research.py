#!/usr/bin/env python3
"""Validate #317 Hermes recursive-learning research records."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs/programs/hermes-research"
RECORD = PROGRAM / "hermes-mutation-surface.json"
README = PROGRAM / "README.md"

HERMES_COMMIT = "165c889e5b4277b56dadd42949a4112c1e6175a6"
EXPECTED_SURFACE_IDS = {
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
}
EXPECTED_STRICT_GAPS = {
    "approved_pending_memory_replay",
    "approved_pending_skill_replay",
    "deterministic_curator_archive",
    "journey_memory_edit_delete",
    "journey_skill_edit_delete",
    "out_of_band_memory_skill_filesystem_write",
}
EXPECTED_RECURSIVE_SCENARIOS = {
    "self_reinforcing_skill_lineage",
    "correction_relearned_by_background_review",
    "stale_human_approval_replay",
    "curator_archive_during_pending_dependency",
    "provider_mirror_failure_after_builtin_commit",
}


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    value = json.loads(RECORD.read_text(encoding="utf-8"))
    readme = README.read_text(encoding="utf-8")

    if value.get("schema_version") != "1.0.0":
        fail("Hermes research record must use schema_version 1.0.0")
    if value.get("research_issue") != "#317":
        fail("Hermes research record must bind #317")
    hermes = value.get("hermes", {})
    if hermes.get("repository") != "NousResearch/hermes-agent":
        fail("Hermes repository identity drifted")
    if hermes.get("commit") != HERMES_COMMIT:
        fail("Hermes research must remain bound to the exact reviewed commit")
    if hermes.get("license") != "MIT":
        fail("Hermes source-rights record must preserve MIT")
    if value.get("research_conclusion") != "generic_durable_state_mutation_middleware_needed_for_strict_mode":
        fail("Hermes research conclusion drifted")
    if value.get("doctrine_disposition") != "no_new_adr":
        fail("#317 must not invent doctrine without a representation-neutral gap")
    if value.get("authority_effect") != "none":
        fail("Hermes research evidence cannot create authority")

    surfaces = value.get("surfaces")
    if not isinstance(surfaces, list):
        fail("Hermes surfaces must be a list")
    surface_ids = [item.get("id") for item in surfaces]
    if len(surface_ids) != len(set(surface_ids)):
        fail("Hermes mutation surfaces contain duplicate ids")
    if set(surface_ids) != EXPECTED_SURFACE_IDS:
        fail(
            "Hermes mutation surface set drifted: "
            f"missing={sorted(EXPECTED_SURFACE_IDS.difference(surface_ids))} "
            f"extra={sorted(set(surface_ids).difference(EXPECTED_SURFACE_IDS))}"
        )
    for item in surfaces:
        if item.get("durable_mutation") not in {True, "provider_dependent"}:
            fail(f"surface lacks durable-mutation classification: {item.get('id')}")
        refs = item.get("source_refs")
        if not isinstance(refs, list) or not refs:
            fail(f"surface lacks source refs: {item.get('id')}")
        if not isinstance(item.get("notes"), str) or not item["notes"].strip():
            fail(f"surface lacks bounded notes: {item.get('id')}")

    postures = value.get("integration_postures", {})
    if set(postures) != {"observe", "govern", "strict"}:
        fail("integration posture set must be observe/govern/strict")
    if postures["observe"].get("supported_today") is not True:
        fail("observe posture should remain available today")
    if postures["govern"].get("supported_today") is not True:
        fail("bounded govern posture should remain available today")
    if postures["strict"].get("supported_today") is not False:
        fail("strict must remain unsupported at the pinned revision")
    strict_gaps = set(postures["strict"].get("blocking_gaps", []))
    if strict_gaps != EXPECTED_STRICT_GAPS:
        fail(f"strict-mode gap set drifted: {sorted(strict_gaps)}")
    for gap in strict_gaps:
        surface = next(item for item in surfaces if item["id"] == gap)
        if surface.get("strict_plugin_only_covered") is not False:
            fail(f"strict blocker unexpectedly claims plugin-only coverage: {gap}")

    primitive = value.get("recommended_interoperability_primitive", {})
    if primitive.get("name") != "generic_durable_state_mutation_middleware":
        fail("recommended Hermes primitive must remain generic durable-state mutation middleware")
    if primitive.get("placement") != "immediately_before_and_after_canonical_durable_state_mutation":
        fail("durable-state middleware must remain persistence-adjacent")
    if set(primitive.get("before_phase", {}).get("decision", [])) != {"allow", "stage", "reject"}:
        fail("before phase must preserve allow/stage/reject decisions")
    if primitive.get("before_phase", {}).get("strict_failure_posture") != "reject_when_required_governor_is_unavailable_or_returns_no_valid_decision":
        fail("strict governor failure posture must remain fail-closed")
    if not primitive.get("after_phase", {}).get("required_fields"):
        fail("after phase must preserve execution receipt fields")

    scenarios = value.get("recursive_evidence_scenarios")
    if not isinstance(scenarios, list):
        fail("recursive evidence scenarios must be a list")
    scenario_ids = {item.get("id") for item in scenarios}
    if scenario_ids != EXPECTED_RECURSIVE_SCENARIOS:
        fail(f"recursive evidence scenario set drifted: {sorted(scenario_ids)}")

    mappings = value.get("capability_mapping")
    if not isinstance(mappings, list) or len(mappings) < 6:
        fail("Hermes capability mapping is incomplete")
    if any(item.get("authority_effect") != "none" for item in mappings):
        fail("Hermes capability mapping cannot create authority")

    if not str(value.get("follow_on_recommendation", "")).startswith("one_bounded_Hermes_integration_issue"):
        fail("#317 follow-on must remain one bounded integration issue")

    required_readme_markers = (
        HERMES_COMMIT,
        "Approved pending memory replay",
        "Deterministic curator archival",
        "Journey edit/delete",
        "generic **durable-state mutation middleware**",
        "provider + pre-tool plugin    -> useful observe/govern, not strict",
        "new Agent Memory doctrine     -> not needed",
    )
    for marker in required_readme_markers:
        if marker not in readme:
            fail(f"Hermes research README missing required conclusion marker: {marker!r}")

    print(
        "hermes-recursive-learning-research: valid "
        f"surfaces={len(surfaces)} strict_gaps={len(strict_gaps)} "
        f"recursive_scenarios={len(scenarios)} doctrine=no_new_adr authority_effect=none"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
