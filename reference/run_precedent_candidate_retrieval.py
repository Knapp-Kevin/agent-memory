"""Run the issue #233 precedent candidate retrieval adversarial harness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.precedent_candidate_harness import run_reference_scenarios


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--agent-memory-commit", required=True)
    args = parser.parse_args()

    report = run_reference_scenarios()
    report["agent_memory_commit"] = args.agent_memory_commit
    output = Path(args.output)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    safety = report["metrics"]["governance_safety"]
    if any(
        safety[key] != 0
        for key in (
            "final_unsafe_equivalence_false_positives",
            "material_difference_misses",
            "negative_precedent_misses",
            "cross_scope_leakage_failures",
            "stale_precedent_reuse_failures",
            "independent_human_attribution_errors",
        )
    ):
        raise SystemExit("precedent retrieval governance safety regression")
    if safety["estimator_unavailable_fallback_success"] != 1.0:
        raise SystemExit("precedent retrieval deterministic fallback regression")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
