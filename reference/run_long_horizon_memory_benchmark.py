#!/usr/bin/env python
"""Emit the local V2 long-horizon benchmark evidence artifact."""

import argparse
import json
from pathlib import Path

from agentmem_ref.long_horizon_benchmark import run_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = run_benchmark()
    report["agent_memory_commit"] = args.agent_memory_commit
    if len(report["representations"]) != 4:
        raise SystemExit("local V2 benchmark did not produce four representation families")

    explicit = next(row for row in report["representations"] if row["representation"] == "explicit_extracted")
    for stage in range(3):
        if explicit["current_only"][f"stage_{stage}"]["mean_plan_error_px"] > 0.05:
            raise SystemExit("explicit baseline temporal alignment regression")

    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
