#!/usr/bin/env python3
"""Emit exact-head evidence for attach-mode discovery and provider availability probes."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.doctor import diagnose, discover_configuration_file  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "reference" / "fixtures" / "runtime-configuration"
COMPOSED = FIXTURES / "reference-composed-runtime.json"
PROBES = FIXTURES / "reference-provider-probes.json"


def _required_missing_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "probes": [
                    {
                        "probe_id": "required-missing-provider",
                        "subject_kind": "component",
                        "subject_id": "reference-governed-memory",
                        "probe_kind": "executable",
                        "target": "agent-memory-definitely-not-a-real-required-provider",
                        "required_for_startability": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def build_report(agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent-memory commit must be an exact 40-character SHA")

    before = COMPOSED.read_bytes()
    discovery = discover_configuration_file(COMPOSED, probe_path=PROBES)
    after = COMPOSED.read_bytes()
    doctor_unprobed = diagnose(COMPOSED)
    doctor_probed = diagnose(COMPOSED, probe=True, probe_path=PROBES)

    with tempfile.TemporaryDirectory() as directory:
        required_missing = Path(directory) / "required-missing.json"
        _required_missing_manifest(required_missing)
        blocked_discovery = discover_configuration_file(COMPOSED, probe_path=required_missing)
        blocked_doctor = diagnose(COMPOSED, probe=True, probe_path=required_missing)

    by_id = {item["probe_id"]: item for item in discovery["results"]}
    invariants = {
        "discovery_observes_only_explicit_declared_signals": (
            discovery["observation_posture"] == "explicit_declared_signals_only"
        ),
        "discovery_does_not_mutate_configuration": (
            before == after and discovery["mutated_configuration"] is False
        ),
        "real_executable_lookup_proves_available_runtime": (
            by_id["reference-python-runtime"]["status"] == "available"
            and by_id["reference-python-runtime"]["evidence"]["resolved"] is True
        ),
        "real_python_import_probe_is_observed": (
            by_id["reference-json-import"]["status"] == "available"
            and by_id["reference-json-import"]["evidence"]["resolved"] is True
        ),
        "missing_optional_provider_is_reported_unavailable": (
            by_id["reference-unavailable-optional"]["status"] == "unavailable"
        ),
        "optional_unavailability_does_not_fabricate_required_failure": (
            discovery["startability"] == "proven_for_declared_probes"
        ),
        "required_missing_provider_blocks_declared_startability": (
            blocked_discovery["startability"] == "blocked_by_required_probe"
            and blocked_doctor["provider_availability"]["status"] == "unavailable"
            and blocked_doctor["operational_readiness"] == "blocked_by_required_provider_probe"
        ),
        "doctor_reports_partial_availability_without_hiding_optional_failure": (
            doctor_unprobed["provider_availability"]["status"] == "not_probed"
            and doctor_probed["provider_availability"]["status"] == "partial"
            and doctor_probed["provider_availability"]["status_counts"]["unavailable"] == 1
            and doctor_probed["provider_availability"]["startability"] == "proven_for_declared_probes"
        ),
        "probe_success_does_not_claim_full_health": (
            doctor_probed["operational_readiness"] == "provider_probe_observed_state_not_checked"
        ),
        "discovery_and_doctor_grant_no_authority": (
            discovery["authority_effect"] == "none"
            and blocked_discovery["authority_effect"] == "none"
            and doctor_probed["authority_effect"] == "none"
            and blocked_doctor["authority_effect"] == "none"
        ),
    }
    invariants = {name: bool(value) for name, value in invariants.items()}
    if not all(type(value) is bool for value in invariants.values()):
        raise TypeError("every provider-discovery structural invariant must be a JSON boolean")

    return {
        "schema_version": "1.0.0",
        "agent_memory_commit": agent_memory_commit,
        "commands": ["discover", "doctor --probe"],
        "probe_kinds": ["executable", "python_import", "filesystem_path"],
        "discovery": discovery,
        "doctor_examples": {
            "unprobed": doctor_unprobed,
            "probed": doctor_probed,
            "required_provider_missing": blocked_doctor,
        },
        "required_provider_missing_discovery": blocked_discovery,
        "structural_invariants": invariants,
        "structural_invariants_passed": all(invariants.values()),
        "authority_effect": "none",
        "limitations": [
            "This slice only probes explicit descriptors bound to already configured subjects; it does not broadly scan the machine.",
            "Executable, Python import, and filesystem-path availability do not prove full provider health or capability correctness.",
            "HTTP/network probing, automatic component installation, secret resolution, and configuration mutation are intentionally excluded.",
            "Discovery evidence does not change qualification maturity, currentness, fallback selection, or authority.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report(args.agent_memory_commit)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    if not report["structural_invariants_passed"]:
        failed = [name for name, passed in report["structural_invariants"].items() if not passed]
        print(f"provider discovery invariants failed: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
