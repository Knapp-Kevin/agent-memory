#!/usr/bin/env python3
"""Execute the pinned Mem0 P6 comparator and emit machine-readable evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Mem0 reads this during import. Keep comparator execution network-silent.
os.environ["MEM0_TELEMETRY"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.mem0_comparator import run_mem0_comparator  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = run_mem0_comparator(args.agent_memory_commit)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    if not report["execution_success"]:
        failed = [name for name, case in report["scenarios"].items() if not case["passed"]]
        print(f"Mem0 comparator scenario failure: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
