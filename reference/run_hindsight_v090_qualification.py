#!/usr/bin/env python3
"""Emit contract-bound Hindsight v0.9.0 qualification evidence for #352."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.hindsight_qualification import (
    load_component_profile,
    qualify_hindsight_v090,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--raw-evidence", type=Path, required=True)
    parser.add_argument("--component-profile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw = json.loads(args.raw_evidence.read_text(encoding="utf-8"))
    component = load_component_profile(args.component_profile)
    result = qualify_hindsight_v090(
        raw_evidence=raw,
        component=component,
        agent_memory_commit=args.agent_memory_commit,
        raw_evidence_ref=str(args.raw_evidence),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result.eligible else 1


if __name__ == "__main__":
    raise SystemExit(main())
