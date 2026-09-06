#!/usr/bin/env python3
"""Emit exact-head CodeGenome multi-capability profile evidence for #293."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import jsonschema

from agentmem_ref.codegenome_profile import build_profile_report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROFILE = ROOT / "reference" / "fixtures" / "component-capabilities" / "codegenome.example.json"
PROFILE_SCHEMA = ROOT / "schemas" / "component-capability-profile.schema.json"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--profile", type=Path, default=DEFAULT_PROFILE)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    value = json.loads(args.profile.read_text(encoding="utf-8"))
    schema = json.loads(PROFILE_SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(value)

    report = build_profile_report(value, agent_memory_commit=args.agent_memory_commit)
    failed = sorted(name for name, passed in report["invariants"].items() if not passed)
    if failed:
        raise SystemExit(f"CodeGenome profile invariants failed: {failed}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "component": report["component"],
        "maturity_counts": report["maturity_counts"],
        "invariants": report["invariants"],
        "authority_effect": report["authority_effect"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
