#!/usr/bin/env python3
"""Emit machine-readable matched architecture-family evidence for issue #67."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from agentmem_ref.architecture_family_closeout import run_closeout_evidence


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="architecture-family-closeout-evidence.json")
    args = parser.parse_args()
    report = run_closeout_evidence()
    Path(args.output).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
