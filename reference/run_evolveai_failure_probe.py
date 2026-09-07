#!/usr/bin/env python3
"""Emit real unavailable-adapter evidence for the EvolveAI qualification lane."""

from __future__ import annotations

import argparse
from pathlib import Path

from agentmem_ref.component_failure_probe import probe_missing_executable
from agentmem_ref.evolveai_profile import (
    ADAPTER_ID,
    ADAPTER_VERSION,
    EVOLVEAI_COMMIT,
    IMPLEMENTATION_REF,
    QUALIFICATION_PROFILE_ID,
    QUALIFICATION_PROFILE_VERSION,
)
from agentmem_ref.qualification import QualificationSubject


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--raw-output", type=Path, required=True)
    parser.add_argument("--normalized-output", type=Path, required=True)
    parser.add_argument("--trace-ref", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    subject = QualificationSubject(
        component_id="evolveai",
        component_version=EVOLVEAI_COMMIT,
        implementation_ref=IMPLEMENTATION_REF,
        capability_id="content_addressed_exact_retrieval",
        capability_version="1.0",
        adapter_id=ADAPTER_ID,
        adapter_version=ADAPTER_VERSION,
        qualification_profile_id=QUALIFICATION_PROFILE_ID,
        qualification_profile_version=QUALIFICATION_PROFILE_VERSION,
    )
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
