#!/usr/bin/env python3
"""Emit real provider-unavailable evidence for the code-graph qualification."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentmem_ref.code_graph_qualification import codegenome_subject, graphify_subject
from agentmem_ref.component_failure_probe import probe_missing_executable


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=("codegenome", "graphify"), required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--raw-output", type=Path, required=True)
    parser.add_argument("--normalized-output", type=Path, required=True)
    parser.add_argument("--trace-ref", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    subject = codegenome_subject() if args.provider == "codegenome" else graphify_subject()
    probe_missing_executable(
        subject=subject,
        executable=args.executable,
        args=("--version",),
        raw_path=args.raw_output,
        normalized_path=args.normalized_output,
        trace_ref=args.trace_ref,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
