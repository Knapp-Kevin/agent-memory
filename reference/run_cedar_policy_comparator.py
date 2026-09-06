#!/usr/bin/env python
"""Run the pinned Cedar external-policy composition comparator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.cedar_policy_comparator import run_comparator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--cedar-binary", default="cedar")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_comparator(args.agent_memory_commit, cedar_binary=args.cedar_binary)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
