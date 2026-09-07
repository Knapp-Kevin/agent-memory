#!/usr/bin/env python
"""Emit exact-head derivation currentness evidence depth."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.derivation_currentness_depth import build_derivation_currentness_depth_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = build_derivation_currentness_depth_report(args.agent_memory_commit)
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
