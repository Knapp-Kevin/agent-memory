#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.reusable_grant_harness import run_harness


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    report = run_harness()
    document = {
        "schema_version": "0.1.0",
        "agent_memory_commit": args.agent_memory_commit,
        "program": "reusable-grant-authority-transition",
        **report,
    }
    Path(args.output).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return 1 if document["metrics"]["failed_scenarios"] or document["metrics"]["unsafe_grant_activations"] or document["metrics"]["authority_transition_failures"] or document["metrics"]["policy_derived_attribution_errors"] or document["metrics"]["pama_widening_failures"] or document["metrics"]["recursive_authority_inflation_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
