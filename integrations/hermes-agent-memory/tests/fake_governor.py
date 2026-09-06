#!/usr/bin/env python3
"""Deterministic fake external governor for Hermes integration tests."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys


def main() -> int:
    decision = sys.argv[1] if len(sys.argv) > 1 else "allow"
    capture = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else None
    candidate = json.load(sys.stdin)
    if capture is not None:
        capture.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if decision == "exit-failure":
        print("governor unavailable", file=sys.stderr)
        return 17
    if decision == "invalid-json":
        print("not-json")
        return 0
    if decision == "invalid-decision":
        print(json.dumps({"decision": "maybe", "reason": "invalid fixture"}))
        return 0

    reason = os.environ.get("FAKE_GOVERNOR_REASON", f"fake governor {decision}")
    print(
        json.dumps(
            {
                "decision": decision,
                "reason": reason,
                "evidence_refs": [f"fixture://fake-governor/{decision}"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
