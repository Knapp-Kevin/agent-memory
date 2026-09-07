#!/usr/bin/env python
"""Run the pinned OPA external-policy composition comparator."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.opa_policy_comparator import run_comparator


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--opa-binary", default="opa")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_comparator(args.agent_memory_commit, opa_binary=args.opa_binary)
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
