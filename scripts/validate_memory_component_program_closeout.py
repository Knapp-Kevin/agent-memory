#!/usr/bin/env python3
"""Validate the #274 memory component/capability program closeout."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = ROOT / "docs/programs/memory-modules"
CLOSEOUT = PROGRAM / "program-closeout.json"
EVOLVE_PROFILE = ROOT / "reference/fixtures/component-capabilities/evolveai.example.json"
CODEGENOME_PROFILE = ROOT / "reference/fixtures/component-capabilities/codegenome.example.json"
PROGRAM_README = PROGRAM / "README.md"
WIKI = ROOT / "wiki-src/Mutable-Memory-Fabric.md"

EXPECTED_EVOLVE = "21161ce7b88dbffeb7ed59757b4d02d24a9c2acd"
EXPECTED_CODEGENOME = "43a6b7147ec78ec5c616723fa1dd30f342174860"
EXPECTED_EVOLVE_REFERENCE_QUALIFIED = {
    "audited_deletion",
    "content_addressed_exact_retrieval",
    "l3_provenance_audit",
    "persistent_snapshot_restart",
}
EXPECTED_CODEGENOME_EVIDENCE_PROVEN = {"code_graph_traversal"}
EXPECTED_ACCEPTANCE_COUNT = 17


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise SystemExit(message)


def capability_map(profile: dict) -> dict[str, dict]:
    return {item["capability_id"]: item for item in profile["capabilities"]}


def main() -> int:
    closeout = load(CLOSEOUT)
    evolve = load(EVOLVE_PROFILE)
    codegenome = load(CODEGENOME_PROFILE)
    program_readme = PROGRAM_README.read_text(encoding="utf-8")
    wiki = WIKI.read_text(encoding="utf-8")

    if closeout.get("schema_version") != "1.0.0":
        fail("program-closeout.json must use schema_version 1.0.0")
    if closeout.get("program_issue") != "#274":
        fail("program-closeout.json must bind #274")
    if closeout.get("status") != "ready_to_close_after_exact_head_validation":
        fail("program-closeout.json must preserve the pre-merge closeout status")
    if closeout.get("doctrine_disposition") != "no_new_adr":
        fail("#274 closeout must not invent a new ADR")
    if closeout.get("authority_effect") != "none":
        fail("#274 closeout evidence cannot create authority")

    acceptance = closeout.get("acceptance_criteria")
    if not isinstance(acceptance, list) or len(acceptance) != EXPECTED_ACCEPTANCE_COUNT:
        fail(f"expected {EXPECTED_ACCEPTANCE_COUNT} #274 acceptance rows")
    names = [item.get("criterion") for item in acceptance]
    if len(names) != len(set(names)):
        fail("#274 acceptance criteria contain duplicates")
    for item in acceptance:
        if item.get("satisfied") is not True:
            fail(f"unsatisfied #274 acceptance criterion: {item.get('criterion')}")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            fail(f"acceptance criterion lacks evidence: {item.get('criterion')}")

    first_party = closeout.get("first_party_qualification_boundaries", {})
    evolve_closeout = first_party.get("evolveai", {})
    codegenome_closeout = first_party.get("codegenome", {})

    if evolve.get("component_id") != "evolveai" or evolve.get("component_version") != EXPECTED_EVOLVE:
        fail("EvolveAI component profile is not bound to the repaired exact revision")
    if evolve.get("profile_version") != "component-capability-v2":
        fail("EvolveAI must use component-capability-v2")
    evolve_caps = capability_map(evolve)
    evolve_reference = {
        capability_id
        for capability_id, item in evolve_caps.items()
        if item.get("maturity") == "reference_qualified"
    }
    if len(evolve_caps) != 15:
        fail("EvolveAI closeout expects exactly 15 capability rows")
    if evolve_reference != EXPECTED_EVOLVE_REFERENCE_QUALIFIED:
        fail(f"unexpected EvolveAI reference-qualified set: {sorted(evolve_reference)}")
    if evolve_closeout.get("provider_revision") != EXPECTED_EVOLVE:
        fail("closeout EvolveAI revision does not match component profile")
    if set(evolve_closeout.get("reference_qualified_capabilities", [])) != evolve_reference:
        fail("closeout EvolveAI reference-qualified set does not match profile")
    if evolve_closeout.get("authority_effect") != "none":
        fail("EvolveAI closeout boundary cannot create authority")

    if codegenome.get("component_id") != "codegenome" or codegenome.get("component_version") != EXPECTED_CODEGENOME:
        fail("CodeGenome component profile is not bound to the exact qualified revision")
    if codegenome.get("profile_version") != "component-capability-v2":
        fail("CodeGenome must use component-capability-v2")
    codegenome_caps = capability_map(codegenome)
    if len(codegenome_caps) != 18:
        fail("CodeGenome closeout expects exactly 18 capability rows")
    codegenome_reference = {
        capability_id
        for capability_id, item in codegenome_caps.items()
        if item.get("maturity") == "reference_qualified"
    }
    codegenome_proven = {
        capability_id
        for capability_id, item in codegenome_caps.items()
        if item.get("maturity") == "evidence_proven"
    }
    if codegenome_reference:
        fail(f"CodeGenome must not gain reference qualification at this boundary: {sorted(codegenome_reference)}")
    if codegenome_proven != EXPECTED_CODEGENOME_EVIDENCE_PROVEN:
        fail(f"unexpected CodeGenome evidence-proven set: {sorted(codegenome_proven)}")
    if codegenome_closeout.get("provider_revision") != EXPECTED_CODEGENOME:
        fail("closeout CodeGenome revision does not match component profile")
    if set(codegenome_closeout.get("evidence_proven_capabilities", [])) != codegenome_proven:
        fail("closeout CodeGenome evidence-proven set does not match profile")
    if codegenome_closeout.get("reference_qualified_capabilities") != []:
        fail("closeout must preserve empty CodeGenome reference-qualified set")
    if codegenome_closeout.get("authority_effect") != "none":
        fail("CodeGenome closeout boundary cannot create authority")

    stale_living_markers = (
        "#280 — broader component/capability runtime contract and routing fabric, open",
        "#292 — EvolveAI capability qualification, open",
        "#293 — broader CodeGenome capability qualification, open",
        "Open EvolveAI #19",
        "Current planning pin:\n\n`7cd42412ceed2ab638249a1517b2a6dac46f1312`",
    )
    for marker in stale_living_markers:
        if marker in program_readme or marker in wiki:
            fail(f"living component documentation still contains stale marker: {marker!r}")

    required_readme_markers = (
        "program implementation complete",
        EXPECTED_EVOLVE,
        EXPECTED_CODEGENOME,
        "4 reference_qualified",
        "No CodeGenome capability is currently `reference_qualified`",
        "program-closeout.json",
    )
    for marker in required_readme_markers:
        if marker not in program_readme:
            fail(f"component program README missing current marker: {marker!r}")

    required_wiki_markers = (
        EXPECTED_EVOLVE,
        EXPECTED_CODEGENOME,
        "EvolveAI PR #21",
        "No CodeGenome capability is currently `reference_qualified`",
        "#292 — EvolveAI qualification",
        "#293 — CodeGenome qualification",
    )
    for marker in required_wiki_markers:
        if marker not in wiki:
            fail(f"Mutable Memory Fabric Wiki missing current marker: {marker!r}")

    public_paths = (
        ROOT / "README.md",
        ROOT / "docs/42-governed-mutable-memory-fabric.md",
        PROGRAM_README,
        WIKI,
        ROOT / "assets/diagrams/agent-memory-flow.png",
        ROOT / "assets/diagrams/agent-memory-flow-light.png",
        PROGRAM / "evolveai-multicapability-profile.md",
        PROGRAM / "codegenome-multicapability-profile.md",
    )
    missing_paths = [str(path.relative_to(ROOT)) for path in public_paths if not path.exists()]
    if missing_paths:
        fail(f"#274 public closeout paths missing: {missing_paths}")

    historical = closeout.get("historical_snapshot_posture", {})
    if historical.get("first_party_capability_inventory_rewritten") is not False:
        fail("historical first-party inventory must remain an explicit unrevised snapshot")

    print(
        "memory-component-program-closeout: valid "
        f"acceptance={len(acceptance)} evolve_caps={len(evolve_caps)} "
        f"evolve_reference={len(evolve_reference)} codegenome_caps={len(codegenome_caps)} "
        f"codegenome_evidence_proven={len(codegenome_proven)} authority_effect=none"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
