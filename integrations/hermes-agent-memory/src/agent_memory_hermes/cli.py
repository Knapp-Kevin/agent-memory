"""Installed doctor surface for the Agent Memory Hermes integration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .config import IntegrationConfigError, detect_hermes_revision, integration_dir, load_config
from .coverage import build_coverage_report


def _default_home() -> Path:
    try:
        from hermes_constants import get_hermes_home  # type: ignore

        return Path(get_hermes_home()).expanduser().resolve()
    except Exception:
        import os

        return Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser().resolve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-memory-hermes")
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="report exact Hermes integration coverage/readiness")
    doctor.add_argument("--hermes-home", type=Path, default=None)
    doctor.add_argument("--hermes-revision", default=None)
    doctor.add_argument("--mode", choices=["observe", "govern", "strict"], default=None)
    doctor.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "doctor":
        return 2

    home = (args.hermes_home or _default_home()).expanduser().resolve()
    try:
        config = load_config(home).with_mode(args.mode)
    except (IntegrationConfigError, json.JSONDecodeError, OSError) as exc:
        report = {
            "schema_version": "1.0.0",
            "integration": {"ready": False, "mode": args.mode or "unknown"},
            "reasons_not_ready": [f"configuration_error: {exc}"],
            "authority_effect": "none",
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    observed = (args.hermes_revision or detect_hermes_revision()).strip().lower()
    report = build_coverage_report(config, observed_hermes_revision=observed)
    target = integration_dir(home) / "coverage.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"Agent Memory Hermes: mode={config.mode} ready={str(report['integration']['ready']).lower()} "
            f"profile_current={str(report['hermes']['profile_current']).lower()}"
        )
        if report["reasons_not_ready"]:
            for reason in report["reasons_not_ready"]:
                print(f"- {reason}")
        if config.mode == "strict":
            print("- strict blockers: " + ", ".join(report["strict"]["blocking_surfaces"]))
        print(f"coverage: {target}")

    return 0 if report["integration"]["ready"] else 2


if __name__ == "__main__":
    sys.exit(main())
