#!/usr/bin/env python3
"""Emit exact-head #293 CodeGenome scope/deletion closeout evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.code_graph_qualification import CODEGENOME_COMMIT
from agentmem_ref.codegenome_profile import profile_digest
from agentmem_ref.codegenome_scope_residue import ExternalScopeBinding, build_closeout_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "reference" / "fixtures" / "component-capabilities" / "codegenome.example.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--component-profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--v1-main-downstream", type=Path, required=True)
    parser.add_argument("--v2-main-downstream", type=Path, required=True)
    parser.add_argument("--v1-store-manifest", type=Path, required=True)
    parser.add_argument("--v2-store-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    profile = json.loads(args.component_profile.read_text(encoding="utf-8"))
    binding = ExternalScopeBinding(
        binding_ref="scope-binding:codegenome:qualification-fixture:tenant-a-project-a",
        component_id="codegenome",
        component_version=CODEGENOME_COMMIT,
        component_profile_digest=profile_digest(profile),
        provider_scope_ref="repo://qualification-fixture/codegenome-main",
        agent_memory_scope_ref="tenant://tenant-a/project/project-a",
        tenant_ref="tenant-a",
        project_ref="project-a",
    )
    report = build_closeout_report(
        agent_memory_commit=args.agent_memory_commit,
        component_profile=profile,
        binding=binding,
        v1_main_downstream=args.v1_main_downstream,
        v2_main_downstream=args.v2_main_downstream,
        v1_store_manifest=args.v1_store_manifest,
        v2_store_manifest=args.v2_store_manifest,
    )
    failed = sorted(name for name, passed in report["invariants"].items() if not passed)
    if failed:
        raise SystemExit(f"CodeGenome scope/residue invariants failed: {failed}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "profile": report["profile"],
        "base_qualification": report["base_qualification"],
        "scope_bridge": report["scope_bridge"],
        "deletion_rebuild": report["deletion_rebuild"],
        "invariants": report["invariants"],
        "authority_effect": report["authority_effect"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
