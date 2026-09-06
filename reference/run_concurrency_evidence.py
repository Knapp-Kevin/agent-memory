#!/usr/bin/env python3
"""Emit exact-commit machine-readable concurrency evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.concurrency_evidence import run_concurrency_evidence  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", default="concurrency-evidence.json")
    args = parser.parse_args()

    report = run_concurrency_evidence(args.agent_memory_commit)
    output = Path(args.output)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
