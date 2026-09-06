#!/usr/bin/env python3
"""Emit exact-head evidence for the installed Agent Memory CLI/doctor boundary."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.configured_restart import ConfigBoundRestartRuntime  # noqa: E402
from agentmem_ref.doctor import diagnose, validate_configuration_file  # noqa: E402
from agentmem_ref.runtime_behavior import validate_runtime_behavior_contract  # noqa: E402
from agentmem_ref.visibility import VisibilityOperation, VisibilityTracker  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "reference" / "fixtures" / "runtime-configuration"
COMPOSED = FIXTURES / "reference-composed-runtime.json"
ATTACHED = FIXTURES / "attached-existing-stack.json"
QUALIFICATIONS = FIXTURES / "qualification-bindings.json"


def build_report(agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent-memory commit must be an exact 40-character SHA")

    composed_validation = validate_configuration_file(COMPOSED)
    attached_validation = validate_configuration_file(
        ATTACHED,
        qualification_path=QUALIFICATIONS,
    )
    composed_value = json.loads(COMPOSED.read_text(encoding="utf-8"))
    plan = validate_runtime_behavior_contract(composed_value)

    with tempfile.TemporaryDirectory() as directory:
        runtime = ConfigBoundRestartRuntime.create(directory, tenant="tenant-acme", plan=plan)
        recovered = diagnose(COMPOSED, state_dir=directory)

        operation = VisibilityOperation(
            operation_id="visibility:doctor-evidence",
            memory_id="memory:doctor-evidence",
            memory_version=1,
            operation_type="promotion",
            runtime_version=plan.runtime_version,
            profile_version=plan.profile_version,
            agent_memory_commit=agent_memory_commit,
            required_projection_ids=("reference-derived-index",),
        )
        tracker = VisibilityTracker(operation)
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("reference-derived-index")
        runtime.persist_visibility_snapshot(operation.operation_id, tracker.snapshot_for_restart())
        pending = diagnose(COMPOSED, state_dir=directory)

        binding_path = Path(directory) / "configuration-binding.json"
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["configuration_digest"] = "sha256:" + "0" * 64
        binding_path.write_text(json.dumps(binding), encoding="utf-8")
        failed = diagnose(COMPOSED, state_dir=directory)

    with tempfile.TemporaryDirectory() as directory:
        absent = diagnose(COMPOSED, state_dir=Path(directory) / "not-created")

    invariants = {
        "composed_configuration_valid": composed_validation["valid"] is True,
        "attach_existing_stack_configuration_valid_with_independent_qualification": (
            attached_validation["valid"] is True
            and attached_validation["entry_mode"] == "attach_existing_stack"
            and attached_validation["qualification_binding_count"] == 2
        ),
        "configuration_validation_grants_no_authority": (
            composed_validation["authority_effect"] == "none"
            and attached_validation["authority_effect"] == "none"
        ),
        "doctor_reports_uninitialized_state_without_fabricating_recovery": (
            absent["durable_state"]["status"] == "not_initialized"
            and absent["recovery"]["status"] == "not_attempted"
        ),
        "doctor_recovers_exact_configuration": (
            recovered["recovery"]["status"] == "recovered"
            and recovered["durable_state"]["status"] == "recovered"
        ),
        "doctor_never_equates_recovery_with_live_provider_health": (
            recovered["provider_availability"]["status"] == "not_probed"
            and recovered["operational_readiness"] == "provider_availability_not_probed"
        ),
        "doctor_surfaces_pending_currentness": (
            pending["currentness"]["status"] == "pending"
            and pending["currentness"]["pending_operations"] == 1
            and pending["operational_readiness"] == "pending_currentness"
        ),
        "doctor_fails_closed_on_durable_binding_corruption": (
            failed["recovery"]["status"] == "failed_closed"
            and failed["configuration_startable"] is False
            and failed["operational_readiness"] == "blocked_by_recovery_failure"
        ),
        "doctor_grants_no_authority": all(
            report["authority_effect"] == "none"
            for report in (absent, recovered, pending, failed)
        ),
    }
    invariants = {name: bool(value) for name, value in invariants.items()}
    if not all(type(value) is bool for value in invariants.values()):
        raise TypeError("every CLI/doctor structural invariant must be a JSON boolean")

    return {
        "schema_version": "1.0.0",
        "agent_memory_commit": agent_memory_commit,
        "distribution_name": "agent-memory-reference",
        "console_script": "agent-memory",
        "commands": ["config validate", "doctor"],
        "composed_configuration": composed_validation,
        "attached_configuration": attached_validation,
        "doctor_examples": {
            "state_absent": absent,
            "state_recovered": recovered,
            "currentness_pending": pending,
            "corrupt_binding": failed,
        },
        "structural_invariants": invariants,
        "structural_invariants_passed": all(invariants.values()),
        "authority_effect": "none",
        "limitations": [
            "The distribution is installable from the repository but is not claimed to be published to PyPI by this slice.",
            "doctor does not probe live provider health yet and therefore never reports operational readiness as proven from configuration/recovery alone.",
            "No setup wizard, automatic component discovery, package installation, secret resolution, or HTTP service is implemented here.",
            "Durable-state diagnostics are bounded to the existing reference_config_bound_checkpoint_v1 profile.",
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
        print(f"CLI/doctor invariants failed: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
