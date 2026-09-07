"""Configuration-bound restart recovery for Agent Memory issue #282.

This module composes the already-earned #280 runtime configuration contract with
the bounded ``reference_file_checkpoint_v1`` durability profile. It does not
mutate that profile. Instead it adds an outer, versioned binding that fails
closed when the validated runtime plan, qualification interpretation, required
projection set, or underlying checkpoint generation changes unexpectedly.

Provider fallback after restart additionally requires explicit #300
``ProviderFailure`` evidence. Configuration may name a fallback, but a fallback
is not activated merely because a boolean claims the primary is unavailable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, Mapping

from ..contracts.component_fallback import ProviderFailure
from .restart_runtime import (
    CapabilityBinding,
    RecoveryEvidence,
    RestartSafeRuntime,
    RuntimeProfile,
    RuntimeRecoveryError,
)
from .runtime_config import ResolvedRoute, RuntimeConfigurationPlan


CONFIG_BINDING_SCHEMA_VERSION = "1.0.0"
CONFIG_BOUND_DURABILITY_PROFILE = "reference_config_bound_checkpoint_v1"


@dataclass(frozen=True)
class RouteActivation:
    route_id: str
    capability_id: str
    primary_component_id: str
    active_component_id: str
    status: str
    failure_result: str = "none"
    failure_evidence_ref: str = ""
    trace_ref: str = ""

    @property
    def authority_effect(self) -> str:
        return "none"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["authority_effect"] = "none"
        return payload


@dataclass(frozen=True)
class ConfigBoundRecoveryEvidence:
    durability_profile: str
    configuration_digest: str
    plan_digest: str
    base_generation: int
    base_substrate_digest: str
    base_governance_digest: str
    base_interpretation_digest: str
    required_projection_ids: tuple[str, ...]
    route_activations: tuple[RouteActivation, ...]
    recovery_posture: str

    @property
    def authority_effect(self) -> str:
        return "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "durability_profile": self.durability_profile,
            "configuration_digest": self.configuration_digest,
            "plan_digest": self.plan_digest,
            "base_generation": self.base_generation,
            "base_substrate_digest": self.base_substrate_digest,
            "base_governance_digest": self.base_governance_digest,
            "base_interpretation_digest": self.base_interpretation_digest,
            "required_projection_ids": list(self.required_projection_ids),
            "route_activations": [item.to_dict() for item in self.route_activations],
            "recovery_posture": self.recovery_posture,
            "authority_effect": "none",
        }


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _atomic_json_write(path: Path, value: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    payload = _canonical_bytes(value) + b"\n"
    with temporary.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _read_json(path: Path) -> dict:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise RuntimeRecoveryError(f"required configuration-bound state missing: {path.name}") from exc
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeRecoveryError(f"configuration-bound state is corrupt: {path.name}") from exc
    if not isinstance(value, dict):
        raise RuntimeRecoveryError("configuration-bound state must be a JSON object")
    return value


def plan_digest(plan: RuntimeConfigurationPlan) -> str:
    return _digest(plan.to_dict())


def _profile_from_plan(plan: RuntimeConfigurationPlan) -> RuntimeProfile:
    bindings: dict[str, CapabilityBinding] = {}
    for route in plan.resolved_routes:
        resolved = route.primary
        evidence_ref = route.qualification_record_ref or f"configuration:{plan.configuration_digest}"
        binding = CapabilityBinding(
            component_id=resolved.component_id,
            component_version=resolved.component_version,
            capability_id=resolved.capability_id,
            capability_version=resolved.capability_version,
            maturity=resolved.maturity,
            evidence_ref=evidence_ref,
            source_rights_posture="runtime_allowed",
        )
        existing = bindings.get(binding.key)
        if existing is not None and existing != binding:
            raise RuntimeRecoveryError(
                f"configuration resolves one capability to multiple primary interpretations: {binding.key}"
            )
        bindings[binding.key] = binding
    return RuntimeProfile(
        runtime_version=plan.runtime_version,
        profile_id=plan.profile_id,
        profile_version=plan.profile_version,
        bindings=tuple(bindings[key] for key in sorted(bindings)),
    )


def _route_by_primary(plan: RuntimeConfigurationPlan) -> dict[tuple[str, str], ResolvedRoute]:
    result: dict[tuple[str, str], ResolvedRoute] = {}
    for route in plan.resolved_routes:
        key = (route.primary.component_id, route.primary.capability_id)
        if key in result:
            raise RuntimeRecoveryError(
                f"provider failure mapping is ambiguous across configured routes: {key[0]}:{key[1]}"
            )
        result[key] = route
    return result


def _activate_routes(
    plan: RuntimeConfigurationPlan,
    failures: Iterable[ProviderFailure],
) -> tuple[RouteActivation, ...]:
    route_index = _route_by_primary(plan)
    failures_by_key: dict[tuple[str, str], ProviderFailure] = {}
    for failure in failures:
        key = (failure.component_id, failure.capability_id)
        if key not in route_index:
            raise RuntimeRecoveryError(
                f"provider failure does not match any configured primary route: {failure.component_id}:{failure.capability_id}"
            )
        if key in failures_by_key:
            raise RuntimeRecoveryError(
                f"multiple provider failure records are ambiguous for {failure.component_id}:{failure.capability_id}"
            )
        failures_by_key[key] = failure

    activations: list[RouteActivation] = []
    for route in plan.resolved_routes:
        primary = route.primary
        key = (primary.component_id, primary.capability_id)
        failure = failures_by_key.get(key)
        if failure is None:
            activations.append(
                RouteActivation(
                    route_id=route.route_id,
                    capability_id=primary.capability_id,
                    primary_component_id=primary.component_id,
                    active_component_id=primary.component_id,
                    status="primary_active",
                )
            )
            continue

        if not failure.evidence_ref or not failure.trace_ref:
            raise RuntimeRecoveryError(
                f"fallback after restart requires provider failure evidence for route {route.route_id!r}"
            )
        if route.fallback_component_id:
            if not route.fallback_qualification_record_ref:
                raise RuntimeRecoveryError(
                    f"configured fallback lacks independently bound qualification evidence: {route.route_id!r}"
                )
            activations.append(
                RouteActivation(
                    route_id=route.route_id,
                    capability_id=primary.capability_id,
                    primary_component_id=primary.component_id,
                    active_component_id=route.fallback_component_id,
                    status="fallback_active",
                    failure_result=failure.failure_result,
                    failure_evidence_ref=failure.evidence_ref,
                    trace_ref=failure.trace_ref,
                )
            )
        else:
            activations.append(
                RouteActivation(
                    route_id=route.route_id,
                    capability_id=primary.capability_id,
                    primary_component_id=primary.component_id,
                    active_component_id="",
                    status="unavailable",
                    failure_result=failure.failure_result,
                    failure_evidence_ref=failure.evidence_ref,
                    trace_ref=failure.trace_ref,
                )
            )
    return tuple(activations)


def _assert_visibility_matches_plan(
    visibility_snapshots: Mapping[str, dict],
    plan: RuntimeConfigurationPlan,
) -> None:
    allowed = set(plan.required_projection_ids)
    for operation_id, snapshot in visibility_snapshots.items():
        operation = snapshot.get("operation", {}) if isinstance(snapshot, Mapping) else {}
        if not isinstance(operation, Mapping):
            raise RuntimeRecoveryError(f"visibility snapshot operation is malformed: {operation_id}")
        required = set(operation.get("required_projection_ids", ()))
        unknown = sorted(required.difference(allowed))
        if unknown:
            raise RuntimeRecoveryError(
                f"persisted visibility obligation is not required by the recovered configuration: {operation_id}: {unknown}"
            )


class ConfigBindingStore:
    """Outer binding between a validated config plan and one v1 checkpoint generation."""

    def __init__(self, root: str | Path) -> None:
        self.path = Path(root) / "configuration-binding.json"

    def checkpoint(
        self,
        *,
        plan: RuntimeConfigurationPlan,
        base_evidence: RecoveryEvidence,
    ) -> ConfigBoundRecoveryEvidence:
        normalized_plan = plan.to_dict()
        digest = plan_digest(plan)
        record = {
            "schema_version": CONFIG_BINDING_SCHEMA_VERSION,
            "durability_profile": CONFIG_BOUND_DURABILITY_PROFILE,
            "configuration_digest": plan.configuration_digest,
            "plan_digest": digest,
            "plan": normalized_plan,
            "base": {
                "generation": base_evidence.generation,
                "substrate_digest": base_evidence.substrate_digest,
                "governance_digest": base_evidence.governance_digest,
                "interpretation_digest": base_evidence.interpretation_digest,
            },
            "required_projection_ids": list(plan.required_projection_ids),
        }
        _atomic_json_write(self.path, record)
        activations = _activate_routes(plan, ())
        return ConfigBoundRecoveryEvidence(
            durability_profile=CONFIG_BOUND_DURABILITY_PROFILE,
            configuration_digest=plan.configuration_digest,
            plan_digest=digest,
            base_generation=base_evidence.generation,
            base_substrate_digest=base_evidence.substrate_digest,
            base_governance_digest=base_evidence.governance_digest,
            base_interpretation_digest=base_evidence.interpretation_digest,
            required_projection_ids=plan.required_projection_ids,
            route_activations=activations,
            recovery_posture="checkpoint_bound_to_validated_configuration",
        )

    def recover(
        self,
        *,
        plan: RuntimeConfigurationPlan,
        base_evidence: RecoveryEvidence,
        provider_failures: Iterable[ProviderFailure],
    ) -> ConfigBoundRecoveryEvidence:
        record = _read_json(self.path)
        if record.get("schema_version") != CONFIG_BINDING_SCHEMA_VERSION:
            raise RuntimeRecoveryError("unsupported configuration-binding schema")
        if record.get("durability_profile") != CONFIG_BOUND_DURABILITY_PROFILE:
            raise RuntimeRecoveryError("configuration-bound durability profile changed")
        if record.get("configuration_digest") != plan.configuration_digest:
            raise RuntimeRecoveryError(
                "runtime configuration changed after durable state was written; explicit migration is required"
            )
        expected_plan_digest = plan_digest(plan)
        if record.get("plan_digest") != expected_plan_digest:
            raise RuntimeRecoveryError(
                "resolved runtime plan or qualification interpretation changed; explicit migration is required"
            )
        persisted_plan = record.get("plan")
        if not isinstance(persisted_plan, Mapping) or _digest(persisted_plan) != expected_plan_digest:
            raise RuntimeRecoveryError("persisted runtime plan binding is corrupt or inconsistent")

        base = record.get("base")
        if not isinstance(base, Mapping):
            raise RuntimeRecoveryError("configuration binding has no base checkpoint identity")
        comparisons = {
            "generation": base_evidence.generation,
            "substrate_digest": base_evidence.substrate_digest,
            "governance_digest": base_evidence.governance_digest,
            "interpretation_digest": base_evidence.interpretation_digest,
        }
        for key, expected in comparisons.items():
            if base.get(key) != expected:
                raise RuntimeRecoveryError(
                    f"configuration binding does not match recovered base checkpoint: {key}"
                )

        persisted_projections = tuple(record.get("required_projection_ids", ()))
        if persisted_projections != plan.required_projection_ids:
            raise RuntimeRecoveryError("required projection interpretation changed after restart")

        activations = _activate_routes(plan, provider_failures)
        degraded = any(item.status == "unavailable" for item in activations)
        fallback = any(item.status == "fallback_active" for item in activations)
        if degraded:
            posture = "recovered_config_current_but_provider_unavailable"
        elif fallback:
            posture = "recovered_config_current_with_evidence_bound_fallback"
        else:
            posture = "recovered_exact_configuration"
        return ConfigBoundRecoveryEvidence(
            durability_profile=CONFIG_BOUND_DURABILITY_PROFILE,
            configuration_digest=plan.configuration_digest,
            plan_digest=expected_plan_digest,
            base_generation=base_evidence.generation,
            base_substrate_digest=base_evidence.substrate_digest,
            base_governance_digest=base_evidence.governance_digest,
            base_interpretation_digest=base_evidence.interpretation_digest,
            required_projection_ids=plan.required_projection_ids,
            route_activations=activations,
            recovery_posture=posture,
        )


class ConfigBoundRestartRuntime:
    """Validated runtime plan composed with the immutable v1 reference checkpoint."""

    def __init__(
        self,
        *,
        base: RestartSafeRuntime,
        plan: RuntimeConfigurationPlan,
        binding_store: ConfigBindingStore,
        recovery_evidence: ConfigBoundRecoveryEvidence,
    ) -> None:
        self.base = base
        self.plan = plan
        self.binding_store = binding_store
        self.recovery_evidence = recovery_evidence

    @property
    def adapter(self):
        return self.base.adapter

    @property
    def visibility_snapshots(self) -> dict[str, dict]:
        return self.base.visibility_snapshots

    @classmethod
    def create(
        cls,
        root: str | Path,
        *,
        tenant: str,
        plan: RuntimeConfigurationPlan,
        verifier_registry=None,
    ) -> "ConfigBoundRestartRuntime":
        """ADR-037 step 4b-2, DoD 20: forwards host-configured verifier trust."""
        profile = _profile_from_plan(plan)
        base = RestartSafeRuntime.create(
            root, tenant=tenant, profile=profile, verifier_registry=verifier_registry
        )
        binding_store = ConfigBindingStore(root)
        evidence = binding_store.checkpoint(plan=plan, base_evidence=base.recovery_evidence)
        return cls(base=base, plan=plan, binding_store=binding_store, recovery_evidence=evidence)

    @classmethod
    def recover(
        cls,
        root: str | Path,
        *,
        plan: RuntimeConfigurationPlan,
        provider_failures: Iterable[ProviderFailure] = (),
    ) -> "ConfigBoundRestartRuntime":
        profile = _profile_from_plan(plan)
        base = RestartSafeRuntime.recover(root, profile=profile)
        _assert_visibility_matches_plan(base.visibility_snapshots, plan)
        binding_store = ConfigBindingStore(root)
        evidence = binding_store.recover(
            plan=plan,
            base_evidence=base.recovery_evidence,
            provider_failures=provider_failures,
        )
        return cls(base=base, plan=plan, binding_store=binding_store, recovery_evidence=evidence)

    def checkpoint(self) -> ConfigBoundRecoveryEvidence:
        base_evidence = self.base.checkpoint()
        self.recovery_evidence = self.binding_store.checkpoint(
            plan=self.plan,
            base_evidence=base_evidence,
        )
        return self.recovery_evidence

    def commit_proposal(self, proposal, fact_text: str, episode=None, *,
                        evidence=None, attestation=None):
        """Forward the governed commit, including the qualified-evidence channel.

        ADR-037 step 4b-2, DoD 20. This was the wrapper the operator named: the
        capability exists on the adapter underneath, and a wrapper that dropped
        `evidence` would bury it one layer up -- a path that neither forwards
        nor parks honestly. Forwarding only; verifier trust remains with the
        adapter's evaluator-owned registry, and no `verifiers=` escape hatch
        appears here.
        """
        result = self.base.adapter.commit_proposal(
            proposal, fact_text, episode, evidence=evidence, attestation=attestation
        )
        self.checkpoint()
        return result

    def governed_delete(self, proposal, fact_uuid: str, derived_refs: tuple[str, ...] = (),
                        external_verification=None, evidence=None):
        """Forwards the deletion channels too (ADR-037 step 4b-2, DoD 20)."""
        result = self.base.adapter.governed_delete(
            proposal, fact_uuid, derived_refs, external_verification, evidence
        )
        self.checkpoint()
        return result

    def persist_visibility_snapshot(self, operation_id: str, snapshot: dict) -> ConfigBoundRecoveryEvidence:
        _assert_visibility_matches_plan({operation_id: snapshot}, self.plan)
        if not operation_id:
            raise ValueError("visibility operation id is required")
        if not isinstance(snapshot, dict):
            raise ValueError("visibility snapshot must be a mapping")
        self.base.visibility_snapshots[operation_id] = snapshot
        return self.checkpoint()
