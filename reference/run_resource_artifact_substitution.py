#!/usr/bin/env python3
"""Emit real resource_artifact_memory provider substitution evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.resource_provider_substitution import (
    load_component,
    load_qualification_snapshot,
    prove_resource_artifact_substitution,
    qualification_record_from_dict,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--primary-component", type=Path, required=True)
    parser.add_argument("--primary-qualification", type=Path, required=True)
    parser.add_argument("--replacement-component", type=Path, required=True)
    parser.add_argument("--replacement-qualification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    primary_component = load_component(args.primary_component)
    primary_qualification = load_qualification_snapshot(args.primary_qualification)
    replacement_component = load_component(args.replacement_component)
    replacement_report = json.loads(args.replacement_qualification.read_text(encoding="utf-8"))
    if not replacement_report.get("eligible"):
        raise SystemExit("replacement provider qualification is explicitly ineligible")
    replacement_payload = replacement_report.get("qualification")
    if not isinstance(replacement_payload, dict):
        raise SystemExit("replacement provider did not emit a qualification record")
    replacement_qualification = qualification_record_from_dict(replacement_payload)

    result = prove_resource_artifact_substitution(
        primary_component=primary_component,
        primary_qualification=primary_qualification,
        replacement_component=replacement_component,
        replacement_qualification=replacement_qualification,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
