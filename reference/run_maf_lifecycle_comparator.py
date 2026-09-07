"""Emit pinned Microsoft Agent Framework lifecycle evidence for issue #189."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.maf_lifecycle_comparator import run_comparator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_comparator(args.agent_memory_commit)
    output = Path(args.output)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
