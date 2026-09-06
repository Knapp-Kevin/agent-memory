#!/usr/bin/env python3
"""Emit provider-neutral CodeGenome/Graphify qualification evidence for #300."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.code_graph_qualification import build_qualification_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--fixture-root", type=Path, required=True)
    parser.add_argument("--codegenome-v1-main-downstream", type=Path, required=True)
    parser.add_argument("--codegenome-v1-main-upstream", type=Path, required=True)
    parser.add_argument("--codegenome-v1-decoy-downstream", type=Path, required=True)
    parser.add_argument("--codegenome-v2-main-downstream", type=Path, required=True)
    parser.add_argument("--codegenome-v2-main-upstream", type=Path, required=True)
    parser.add_argument("--codegenome-v2-decoy-downstream", type=Path, required=True)
    parser.add_argument("--codegenome-unavailable-raw", type=Path, required=True)
    parser.add_argument("--codegenome-unavailable-normalized", type=Path, required=True)
    parser.add_argument("--graphify-v1", type=Path, required=True)
    parser.add_argument("--graphify-v2", type=Path, required=True)
    parser.add_argument("--graphify-unavailable-raw", type=Path, required=True)
    parser.add_argument("--graphify-unavailable-normalized", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixture_paths = sorted(args.fixture_root.glob("v*/*.rs"))
    report = build_qualification_report(
        agent_memory_commit=args.agent_memory_commit,
        fixture_paths=fixture_paths,
        codegenome_v1_main_downstream=args.codegenome_v1_main_downstream,
        codegenome_v1_main_upstream=args.codegenome_v1_main_upstream,
        codegenome_v1_decoy_downstream=args.codegenome_v1_decoy_downstream,
        codegenome_v2_main_downstream=args.codegenome_v2_main_downstream,
        codegenome_v2_main_upstream=args.codegenome_v2_main_upstream,
        codegenome_v2_decoy_downstream=args.codegenome_v2_decoy_downstream,
        codegenome_unavailable_raw=args.codegenome_unavailable_raw,
        codegenome_unavailable_normalized=args.codegenome_unavailable_normalized,
        graphify_v1=args.graphify_v1,
        graphify_v2=args.graphify_v2,
        graphify_unavailable_raw=args.graphify_unavailable_raw,
        graphify_unavailable_normalized=args.graphify_unavailable_normalized,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["matched_result"]["both_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
