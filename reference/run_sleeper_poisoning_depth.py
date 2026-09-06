#!/usr/bin/env python3
"""Emit exact-head D/F/H/R/P evidence depth for sleeper-poisoning recall re-evaluation."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.sleeper_poisoning_depth import build_sleeper_poisoning_depth_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_sleeper_poisoning_depth_report(args.agent_memory_commit)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0 if report["required_behavioral_cases_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
