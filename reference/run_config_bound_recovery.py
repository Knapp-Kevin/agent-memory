#!/usr/bin/env python3
"""Emit exact-head evidence for #280/#282 configuration-bound restart recovery."""

from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.component_fallback import ProviderFailure  # noqa: E402
from agentmem_ref.configured_restart import ConfigBoundRestartRuntime  # noqa: E402
from agentmem_ref.restart_runtime import RuntimeRecoveryError  # noqa: E402
from agentmem_ref.runtime_config import (  # noqa: E402
    QualificationBinding,
    validate_runtime_configuration,
)
from agentmem_ref.visibility import VisibilityOperation, VisibilityTracker  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "reference" / "fixtures" / "runtime-configuration"


def _inputs() -> tuple[dict, tuple[QualificationBinding, ...]]:
    config = json.loads((FIXTURE_ROOT / "attached-existing-stack.json").read_text(encoding="utf-8"))
    binding_doc = json.loads((FIXTURE_ROOT / "qualification-bindings.json").read_text(encoding="utf-8"))
    bindings = tuple(QualificationBinding(**row) for row in binding_doc["bindings"])
    return config, bindings


def _route(evidence, route_id: str):
    return next(item for item in evidence.route_activations if item.route_id == route_id)


def build_report(agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent-memory commit must be an exact 40-character SHA")

    config, bindings = _inputs()
    plan = validate_runtime_configuration(config, qualification_bindings=bindings)

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        created = ConfigBoundRestartRuntime.create(root, tenant="tenant-acme", plan=plan)

        operation = VisibilityOperation(
            operation_id="visibility:code-graph",
            memory_id="memory:release-branch",
            memory_version=1,
            operation_type="promotion",
            runtime_version=plan.runtime_version,
            profile_version=plan.profile_version,
            agent_memory_commit=agent_memory_commit,
            required_projection_ids=("code-graph",),
            component_versions=("codegenome@43a6b7147ec78ec5c616723fa1dd30f342174860",),
            capability_versions=("code_graph_traversal@1.0",),
        )
        tracker = VisibilityTracker(operation)
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("code-graph")
        created.persist_visibility_snapshot(operation.operation_id, tracker.snapshot_for_restart())

        exact = ConfigBoundRestartRuntime.recover(root, plan=plan)
        exact_route = _route(exact.recovery_evidence, "derived-code-graph")
        restored_visibility = VisibilityTracker.restore_after_restart(
            exact.visibility_snapshots[operation.operation_id]
        ).evaluate()

        failure = ProviderFailure(
            component_id="codegenome",
            capability_id="code_graph_traversal",
            failure_result="provider_unavailable",
            evidence_ref="artifact://failure/codegenome-missing-executable",
            trace_ref="trace:restart-codegenome-unavailable",
        )
        fallback = ConfigBoundRestartRuntime.recover(
            root,
            plan=plan,
            provider_failures=(failure,),
        )
        fallback_route = _route(fallback.recovery_evidence, "derived-code-graph")

        changed_config = copy.deepcopy(config)
        changed_config["evidence"]["receipt_store_ref"] = "state://agent-memory/changed-receipts"
        changed_plan = validate_runtime_configuration(changed_config, qualification_bindings=bindings)
        config_drift_refused = False
        try:
            ConfigBoundRestartRuntime.recover(root, plan=changed_plan)
        except RuntimeRecoveryError:
            config_drift_refused = True

    with tempfile.TemporaryDirectory() as directory:
        torn_root = Path(directory)
        torn = ConfigBoundRestartRuntime.create(torn_root, tenant="tenant-acme", plan=plan)
        torn.base.checkpoint()
        torn_binding_refused = False
        try:
            ConfigBoundRestartRuntime.recover(torn_root, plan=plan)
        except RuntimeRecoveryError:
            torn_binding_refused = True

    invariants = {
        "configuration_digest_bound": created.recovery_evidence.configuration_digest == plan.configuration_digest,
        "exact_restart_uses_primary": (
            exact_route.status == "primary_active" and exact_route.active_component_id == "codegenome"
        ),
        "required_projection_survives_restart": (
            exact.recovery_evidence.required_projection_ids == ("code-graph",)
            and restored_visibility["quiescent"] is False
            and "projection:code-graph" in restored_visibility["pending_required_obligations"]
        ),
        "provider_failure_evidence_selects_configured_fallback": (
            fallback_route.status == "fallback_active"
            and fallback_route.active_component_id == "graphify"
            and fallback_route.failure_evidence_ref == failure.evidence_ref
        ),
        "fallback_grants_no_authority": fallback_route.authority_effect == "none",
        "configuration_drift_requires_migration": config_drift_refused,
        "torn_config_binding_fails_closed": torn_binding_refused,
        "base_checkpoint_profile_remains_v1": exact.base.recovery_evidence.durability_profile == "reference_file_checkpoint_v1",
        "outer_profile_is_versioned_separately": (
            exact.recovery_evidence.durability_profile == "reference_config_bound_checkpoint_v1"
        ),
    }

    return {
        "schema_version": "1.0.0",
        "agent_memory_commit": agent_memory_commit,
        "configuration_digest": plan.configuration_digest,
        "configuration_contract": "schemas/runtime-configuration.schema.json@1.0.0",
        "base_durability_profile": "reference_file_checkpoint_v1",
        "config_bound_durability_profile": "reference_config_bound_checkpoint_v1",
        "exact_recovery": exact.recovery_evidence.to_dict(),
        "fallback_recovery": fallback.recovery_evidence.to_dict(),
        "structural_invariants": invariants,
        "structural_invariants_passed": all(invariants.values()),
        "limitations": [
            "This slice composes validated configuration with the bounded reference file checkpoint; it is not a production HA claim.",
            "Fallback activation requires explicit ProviderFailure evidence but this runner reuses a structurally valid failure record rather than reproducing the #300 missing-executable probe again.",
            "Configuration migration is intentionally fail-closed and has no automatic migration path in this slice.",
            "A process/service CLI and interactive setup remain future product surfaces over the same contract.",
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
        print(f"configuration-bound recovery invariants failed: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
