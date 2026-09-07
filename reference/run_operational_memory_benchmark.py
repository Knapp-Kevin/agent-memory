#!/usr/bin/env python
"""Run the matched local operational-memory benchmark for issue #230."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.operational_memory_benchmark import run_operational_memory_benchmark


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_operational_memory_benchmark()
    report["agent_memory_commit"] = args.agent_memory_commit

    reps = {item["representation"]: item for item in report["representations"]}
    required = {
        "explicit_extracted",
        "retrieval_nearest_exemplar",
        "compact_learned_predictive",
        "hybrid_explicit_plus_learned",
    }
    if set(reps) != required:
        raise SystemExit(f"unexpected benchmark representations: {sorted(reps)}")
    for name, result in reps.items():
        for phase in ("current_only", "stale_contaminated", "recovered_current_only"):
            if result[phase]["all"]["count"] <= 0:
                raise SystemExit(f"{name}:{phase} produced no scored rows")
            if not 0.0 <= result[phase]["all"]["intercept_success_rate"] <= 1.0:
                raise SystemExit(f"{name}:{phase} invalid success rate")
    if report["interpretation"]["capability_metrics_are_not_authority"] is not True:
        raise SystemExit("benchmark lost authority separation")

    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
