#!/usr/bin/env python
"""Emit representation-neutral autonomous-maintenance research evidence for #227."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.autonomous_maintenance_harness import run_autonomous_maintenance_harness


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_autonomous_maintenance_harness()
    report["agent_memory_commit"] = args.agent_memory_commit
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not report["passed"]:
        raise SystemExit("autonomous-maintenance research harness failed")


if __name__ == "__main__":
    main()
