"""Installed command surface for the Agent Memory reference runtime."""

from __future__ import annotations

import argparse
import json
import sys

from .discovery import DiscoveryInputError
from .doctor import (
    DiagnosticInputError,
    diagnose,
    discover_configuration_file,
    validate_configuration_file,
)
from .runtime_config import RuntimeConfigurationError


def _emit(value: dict, *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(value, indent=2, sort_keys=True))
        return
    if value.get("command") == "config_validate":
        print("Configuration: valid")
        print(f"Digest: {value['configuration_digest']}")
        print(f"Entry mode: {value['entry_mode']}")
        print(
            "Canonical owner: "
            f"{value['canonical_owner_component_id']} / {value['canonical_owner_capability_id']}"
        )
        print(f"Routes: {value['route_count']}")
        print(f"Required projections: {', '.join(value['required_projection_ids']) or 'none'}")
        print("Authority effect: none")
        return
    if value.get("command") == "discover":
        print(f"Entry mode: {value['entry_mode']}")
        print(f"Configured components: {len(value['configured_subjects']['components'])}")
        print(f"Configured governance peers: {len(value['configured_subjects']['governance_peers'])}")
        print(f"Declared probes: {value['probe_count']}")
        print(f"Startability from declared probes: {value['startability']}")
        for result in value["results"]:
            print(
                f"- {result['probe_id']}: {result['subject_id']} "
                f"{result['probe_kind']} -> {result['status']}"
            )
        print("Configuration mutated: false")
        print("Authority effect: none")
        return
    print(f"Configuration: {value['configuration']['status']}")
    print(f"Durable state: {value['durable_state']['status']}")
    print(f"Recovery: {value['recovery']['status']}")
    print(f"Currentness: {value['currentness']['status']}")
    print(f"Provider availability: {value['provider_availability']['status']}")
    print(f"Configuration startable: {str(value['configuration_startable']).lower()}")
    print(f"Operational readiness: {value['operational_readiness']}")
    print("Authority effect: none")


def _failure(command: str, exc: Exception, *, json_output: bool) -> int:
    value = {
        "schema_version": "1.0.0",
        "command": command,
        "valid": False,
        "status": "refused",
        "error": str(exc),
        "authority_effect": "none",
    }
    if json_output:
        print(json.dumps(value, indent=2, sort_keys=True))
    else:
        print(f"Refused: {exc}", file=sys.stderr)
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-memory",
        description="Validate, discover, and diagnose the Agent Memory reference runtime.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    config = subcommands.add_parser("config", help="runtime configuration operations")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    validate = config_sub.add_parser("validate", help="validate one portable runtime configuration")
    validate.add_argument("--config", required=True, help="path to a JSON serialization of the runtime contract")
    validate.add_argument("--qualifications", help="path to normalized independent qualification bindings")
    validate.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    discover = subcommands.add_parser(
        "discover",
        help="observe explicitly declared existing-stack signals without mutating configuration",
    )
    discover.add_argument("--config", required=True, help="path to a JSON serialization of the runtime contract")
    discover.add_argument("--probes", required=True, help="path to an explicit read-only provider probe manifest")
    discover.add_argument("--qualifications", help="path to normalized independent qualification bindings")
    discover.add_argument("--json", action="store_true", help="emit machine-readable JSON")

    doctor = subcommands.add_parser("doctor", help="diagnose configuration and bounded durable-state recovery")
    doctor.add_argument("--config", required=True, help="path to a JSON serialization of the runtime contract")
    doctor.add_argument("--qualifications", help="path to normalized independent qualification bindings")
    doctor.add_argument("--state-dir", help="Agent Memory bounded reference state directory to inspect/recover")
    doctor.add_argument("--probe", action="store_true", help="execute explicitly declared read-only provider probes")
    doctor.add_argument("--probes", help="path to an explicit read-only provider probe manifest")
    doctor.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    json_output = bool(getattr(args, "json", False))
    try:
        if args.command == "config" and args.config_command == "validate":
            value = validate_configuration_file(
                args.config,
                qualification_path=args.qualifications,
            )
            _emit(value, json_output=json_output)
            return 0
        if args.command == "discover":
            value = discover_configuration_file(
                args.config,
                probe_path=args.probes,
                qualification_path=args.qualifications,
            )
            _emit(value, json_output=json_output)
            if value["startability"] == "blocked_by_required_probe":
                return 1
            return 0
        if args.command == "doctor":
            if args.probes and not args.probe:
                raise DiagnosticInputError("doctor --probes requires --probe")
            value = diagnose(
                args.config,
                qualification_path=args.qualifications,
                state_dir=args.state_dir,
                probe_path=args.probes,
                probe=args.probe,
            )
            _emit(value, json_output=json_output)
            if value["recovery"].get("status") == "failed_closed":
                return 1
            if value["currentness"].get("status") == "degraded":
                return 1
            if value["provider_availability"].get("startability") == "blocked_by_required_probe":
                return 1
            return 0
    except (
        DiagnosticInputError,
        DiscoveryInputError,
        RuntimeConfigurationError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        return _failure(args.command, exc, json_output=json_output)
    raise AssertionError("unreachable command")


if __name__ == "__main__":
    raise SystemExit(main())
