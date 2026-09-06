from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from agentmem_ref.component_fallback import ProviderFailure
from agentmem_ref.configured_restart import ConfigBoundRestartRuntime
from agentmem_ref.restart_runtime import RuntimeRecoveryError
from agentmem_ref.runtime_config import QualificationBinding, validate_runtime_configuration
from agentmem_ref.visibility import VisibilityOperation, VisibilityTracker


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "reference" / "fixtures" / "runtime-configuration"
COMMIT = "192a9ebb15ac32ab89d50bb99857f3d53e452347"


def _inputs() -> tuple[dict, tuple[QualificationBinding, ...]]:
    config = json.loads((FIXTURE_ROOT / "attached-existing-stack.json").read_text(encoding="utf-8"))
    binding_doc = json.loads((FIXTURE_ROOT / "qualification-bindings.json").read_text(encoding="utf-8"))
    bindings = tuple(QualificationBinding(**row) for row in binding_doc["bindings"])
    return config, bindings


def _plan():
    config, bindings = _inputs()
    return validate_runtime_configuration(config, qualification_bindings=bindings)


def _route(evidence, route_id: str):
    return next(item for item in evidence.route_activations if item.route_id == route_id)


class ConfigBoundRestartTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = _plan()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_exact_validated_plan_survives_restart(self) -> None:
        created = ConfigBoundRestartRuntime.create(
            self.root,
            tenant="tenant-acme",
            plan=self.plan,
        )
        self.assertEqual(created.recovery_evidence.configuration_digest, self.plan.configuration_digest)
        self.assertEqual(created.recovery_evidence.required_projection_ids, ("code-graph",))

        recovered = ConfigBoundRestartRuntime.recover(self.root, plan=self.plan)
        self.assertEqual(recovered.recovery_evidence.recovery_posture, "recovered_exact_configuration")
        self.assertEqual(_route(recovered.recovery_evidence, "derived-code-graph").status, "primary_active")
        self.assertEqual(
            _route(recovered.recovery_evidence, "derived-code-graph").active_component_id,
            "codegenome",
        )

    def test_configuration_digest_drift_requires_explicit_migration(self) -> None:
        ConfigBoundRestartRuntime.create(self.root, tenant="tenant-acme", plan=self.plan)
        config, bindings = _inputs()
        config["evidence"]["receipt_store_ref"] = "state://agent-memory/changed-receipts"
        changed = validate_runtime_configuration(config, qualification_bindings=bindings)
        self.assertNotEqual(changed.configuration_digest, self.plan.configuration_digest)

        with self.assertRaisesRegex(
            RuntimeRecoveryError,
            "runtime configuration changed|runtime profile/component interpretation changed",
        ):
            ConfigBoundRestartRuntime.recover(self.root, plan=changed)

    def test_torn_outer_binding_is_detected_after_base_checkpoint_moves(self) -> None:
        runtime = ConfigBoundRestartRuntime.create(self.root, tenant="tenant-acme", plan=self.plan)
        old_generation = runtime.recovery_evidence.base_generation

        # Simulate a crash/bug between the inner v1 checkpoint and the outer
        # configuration binding update. Recovery must not silently pair a newer
        # durable memory image with the older configuration binding.
        runtime.base.checkpoint()
        self.assertGreater(runtime.base.recovery_evidence.generation, old_generation)

        with self.assertRaisesRegex(RuntimeRecoveryError, "configuration binding does not match"):
            ConfigBoundRestartRuntime.recover(self.root, plan=self.plan)

    def test_provider_failure_evidence_activates_only_configured_fallback(self) -> None:
        ConfigBoundRestartRuntime.create(self.root, tenant="tenant-acme", plan=self.plan)
        failure = ProviderFailure(
            component_id="codegenome",
            capability_id="code_graph_traversal",
            failure_result="provider_unavailable",
            evidence_ref="artifact://failure/codegenome-missing-executable",
            trace_ref="trace:restart-codegenome-unavailable",
        )
        recovered = ConfigBoundRestartRuntime.recover(
            self.root,
            plan=self.plan,
            provider_failures=(failure,),
        )
        route = _route(recovered.recovery_evidence, "derived-code-graph")
        self.assertEqual(route.status, "fallback_active")
        self.assertEqual(route.primary_component_id, "codegenome")
        self.assertEqual(route.active_component_id, "graphify")
        self.assertEqual(route.failure_result, "provider_unavailable")
        self.assertEqual(route.failure_evidence_ref, failure.evidence_ref)
        self.assertEqual(
            recovered.recovery_evidence.recovery_posture,
            "recovered_config_current_with_evidence_bound_fallback",
        )
        self.assertEqual(route.authority_effect, "none")

    def test_unconfigured_failure_evidence_is_rejected(self) -> None:
        ConfigBoundRestartRuntime.create(self.root, tenant="tenant-acme", plan=self.plan)
        failure = ProviderFailure(
            component_id="mystery-provider",
            capability_id="code_graph_traversal",
            failure_result="provider_unavailable",
            evidence_ref="artifact://failure/mystery",
            trace_ref="trace:mystery",
        )
        with self.assertRaisesRegex(RuntimeRecoveryError, "does not match any configured primary route"):
            ConfigBoundRestartRuntime.recover(
                self.root,
                plan=self.plan,
                provider_failures=(failure,),
            )

    def test_required_provider_without_fallback_recovers_as_explicitly_unavailable(self) -> None:
        ConfigBoundRestartRuntime.create(self.root, tenant="tenant-acme", plan=self.plan)
        failure = ProviderFailure(
            component_id="existing-canonical-store",
            capability_id="memory_record_store",
            failure_result="provider_unavailable",
            evidence_ref="artifact://failure/canonical-store-unavailable",
            trace_ref="trace:canonical-store-unavailable",
        )
        recovered = ConfigBoundRestartRuntime.recover(
            self.root,
            plan=self.plan,
            provider_failures=(failure,),
        )
        route = _route(recovered.recovery_evidence, "canonical-record-store")
        self.assertEqual(route.status, "unavailable")
        self.assertEqual(route.active_component_id, "")
        self.assertEqual(
            recovered.recovery_evidence.recovery_posture,
            "recovered_config_current_but_provider_unavailable",
        )

    def test_currentness_snapshot_must_match_configured_required_projection(self) -> None:
        runtime = ConfigBoundRestartRuntime.create(self.root, tenant="tenant-acme", plan=self.plan)
        operation = VisibilityOperation(
            operation_id="visibility:code-graph",
            memory_id="memory:release-branch",
            memory_version=1,
            operation_type="promotion",
            runtime_version=self.plan.runtime_version,
            profile_version=self.plan.profile_version,
            agent_memory_commit=COMMIT,
            required_projection_ids=("code-graph",),
            component_versions=("codegenome@43a6b7147ec78ec5c616723fa1dd30f342174860",),
            capability_versions=("code_graph_traversal@1.0",),
        )
        tracker = VisibilityTracker(operation)
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("code-graph")
        runtime.persist_visibility_snapshot(operation.operation_id, tracker.snapshot_for_restart())

        recovered = ConfigBoundRestartRuntime.recover(self.root, plan=self.plan)
        self.assertIn(operation.operation_id, recovered.visibility_snapshots)
        self.assertFalse(
            VisibilityTracker.restore_after_restart(
                recovered.visibility_snapshots[operation.operation_id]
            ).evaluate()["quiescent"]
        )

    def test_unconfigured_projection_obligation_is_refused_before_checkpoint(self) -> None:
        runtime = ConfigBoundRestartRuntime.create(self.root, tenant="tenant-acme", plan=self.plan)
        operation = VisibilityOperation(
            operation_id="visibility:unknown",
            memory_id="memory:release-branch",
            memory_version=1,
            operation_type="promotion",
            runtime_version=self.plan.runtime_version,
            profile_version=self.plan.profile_version,
            agent_memory_commit=COMMIT,
            required_projection_ids=("not-configured",),
        )
        tracker = VisibilityTracker(operation)
        tracker.policy_decided()
        tracker.canonical_committed()
        tracker.projection_refresh_started("not-configured")

        with self.assertRaisesRegex(RuntimeRecoveryError, "not required by the recovered configuration"):
            runtime.persist_visibility_snapshot(operation.operation_id, tracker.snapshot_for_restart())

    def test_changed_qualification_interpretation_cannot_rebind_same_configuration(self) -> None:
        ConfigBoundRestartRuntime.create(self.root, tenant="tenant-acme", plan=self.plan)
        config, bindings = _inputs()
        changed_bindings = list(bindings)
        original = changed_bindings[0]
        changed_bindings[0] = QualificationBinding(
            **{**original.__dict__, "record_ref": "artifact://replacement-qualification-record"}
        )
        changed_plan = validate_runtime_configuration(
            copy.deepcopy(config),
            qualification_bindings=changed_bindings,
        )
        self.assertEqual(changed_plan.configuration_digest, self.plan.configuration_digest)

        with self.assertRaisesRegex(
            RuntimeRecoveryError,
            "runtime profile/component interpretation changed|resolved runtime plan",
        ):
            ConfigBoundRestartRuntime.recover(self.root, plan=changed_plan)


if __name__ == "__main__":
    unittest.main()
