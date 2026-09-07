#!/usr/bin/env python3
"""Emit exact-head executable evidence for issue #276."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.logical_state_algebra_pressure import run_logical_state_algebra_pressure


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", default="logical-state-algebra-pressure-evidence.json")
    args = parser.parse_args()

    report = run_logical_state_algebra_pressure(args.agent_memory_commit)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
