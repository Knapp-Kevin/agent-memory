#!/usr/bin/env python3
"""Emit the security evidence-depth report and poisoning behavioral evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.security_evidence_depth import build_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument(
        "--benchmark-security",
        help="Optional same-head P5 benchmark-security JSON used only as independently generated R evidence.",
    )
    parser.add_argument("--output")
    args = parser.parse_args()

    benchmark = None
    if args.benchmark_security:
        benchmark = json.loads(Path(args.benchmark_security).read_text(encoding="utf-8"))

    report = build_report(args.agent_memory_commit, benchmark_security=benchmark)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    if not report["required_behavioral_cases_passed"]:
        failed = [claim["claim_id"] for claim in report["claims"] if not claim["behavioral_passed"]]
        print(f"security poisoning behavioral gate failed: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
