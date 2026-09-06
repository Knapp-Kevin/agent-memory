"""Bounded restart-safe Agent Memory runtime for issue #282.

This module is intentionally conservative. It persists the reference substrate
and governance envelope as separate payloads, then binds both to a manifest by
SHA-256 digest. Recovery refuses missing, corrupt, torn, or interpretation-
ambiguous state.

The file-backed store is the first executable durability profile, not canonical
storage doctrine. A production implementation may use a database, WAL, object
store, or another transactional substrate while preserving the same recovery
obligations.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable

from .adapter import Clock, GovernedMemoryAdapter
from ..core.readmission import RejectedValueRegistry, RejectionRecord
from ..state.substrate import Episode, Fact, InMemoryTemporalGraph


SCHEMA_VERSION = "1.0.0"
DURABILITY_PROFILE = "reference_file_checkpoint_v1"


class RuntimeRecoveryError(RuntimeError):
    """Durable runtime state cannot be reconstructed safely."""


@dataclass(frozen=True)
class CapabilityBinding:
    """Exact component interpretation required to recover a runtime safely."""

    component_id: str
    component_version: str
    capability_id: str
    capability_version: str
    maturity: str
    evidence_ref: str
    source_rights_posture: str = "runtime_allowed"

    def __post_init__(self) -> None:
        for name, value in asdict(self).items():
            if not value:
                raise ValueError(f"capability binding requires {name}")
        if self.source_rights_posture != "runtime_allowed":
            raise ValueError("restart runtime requires runtime-allowed source rights")

    @property
    def key(self) -> str:
        return f"{self.capability_id}@{self.capability_version}"


@dataclass(frozen=True)
class RuntimeProfile:
    runtime_version: str
    profile_id: str
    profile_version: str
    bindings: tuple[CapabilityBinding, ...]

    def __post_init__(self) -> None:
        if not self.runtime_version or not self.profile_id or not self.profile_version:
            raise ValueError("runtime/profile identity is required")
        keys = [binding.key for binding in self.bindings]
        if len(keys) != len(set(keys)):
            raise ValueError("runtime profile capability bindings must be unique")

    def to_dict(self) -> dict:
        return {
            "runtime_version": self.runtime_version,
            "profile_id": self.profile_id,
            "profile_version": self.profile_version,
            "bindings": [asdict(binding) for binding in self.bindings],
        }

    @property
    def interpretation_digest(self) -> str:
        return _digest(self.to_dict())


@dataclass(frozen=True)
class RecoveryEvidence:
    generation: int
    durability_profile: str
    substrate_digest: str
    governance_digest: str
    interpretation_digest: str
    recovered_visibility_operations: tuple[str, ...]
    recovery_posture: str = "recovered_exact_interpretation"

    def to_dict(self) -> dict:
        return asdict(self)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _read_json(path: Path) -> dict:
    try:
        raw = path.read_bytes()
    except FileNotFoundError as exc:
        raise RuntimeRecoveryError(f"required runtime state missing: {path.name}") from exc
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeRecoveryError(f"runtime state is corrupt: {path.name}") from exc
    if not isinstance(value, dict):
        raise RuntimeRecoveryError(f"runtime state must be a JSON object: {path.name}")
    return value


def _atomic_json_write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    payload = _canonical_bytes(value) + b"\n"
    with tmp.open("wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _snapshot_substrate(substrate: InMemoryTemporalGraph) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "episodes": [asdict(value) for _, value in sorted(substrate._episodes.items())],
        "facts": [asdict(value) for _, value in sorted(substrate._facts.items())],
        "write_log": [list(item) for item in substrate.write_log],
    }


def _restore_substrate(snapshot: dict) -> InMemoryTemporalGraph:
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeRecoveryError("unsupported substrate state schema")
    substrate = InMemoryTemporalGraph()
    try:
        substrate._episodes = {
            raw["uuid"]: Episode(**raw)
            for raw in snapshot.get("episodes", [])
        }
        facts: dict[str, Fact] = {}
        for raw in snapshot.get("facts", []):
            value = dict(raw)
            value["episode_uuids"] = tuple(value.get("episode_uuids", ()))
            facts[value["uuid"]] = Fact(**value)
        substrate._facts = facts
        substrate.write_log = [tuple(item) for item in snapshot.get("write_log", [])]
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeRecoveryError("substrate state cannot be reconstructed") from exc
    return substrate


def _snapshot_rejections(registry: RejectedValueRegistry) -> list[dict]:
    rows: list[dict] = []
    for (_memory_id, _fingerprint), records in sorted(registry._records.items()):
        rows.extend(record.as_dict() for record in records)
    rows.sort(key=lambda row: row["rejection_id"])
    return rows


def _restore_rejections(rows: Iterable[dict]) -> RejectedValueRegistry:
    registry = RejectedValueRegistry()
    try:
        for raw in rows:
            record = RejectionRecord(
                memory_id=raw["memory_id"],
                value_fingerprint=raw["value_fingerprint"],
                superseded_fact_uuid=raw["superseded_fact_uuid"],
                correction_proposal_id=raw["correction_proposal_id"],
                evidence_refs=tuple(raw.get("evidence_refs", ())),
                authority_refs=tuple(raw.get("authority_refs", ())),
                scope=raw["scope"],
                rejected_at=raw["rejected_at"],
                active=bool(raw.get("active", True)),
                lifecycle_state=raw.get("lifecycle_state", "rejected"),
                readmitted_at=raw.get("readmitted_at"),
                readmission_proposal_id=raw.get("readmission_proposal_id"),
            )
            key = (record.memory_id, record.value_fingerprint)
            registry._records.setdefault(key, []).append(record)
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeRecoveryError("rejected-value state cannot be reconstructed") from exc
    return registry


def _snapshot_governance(
    adapter: GovernedMemoryAdapter,
    *,
    profile: RuntimeProfile,
    visibility_snapshots: dict[str, dict],
) -> dict:
    selector_mode = getattr(adapter._selector, "mode", "unknown")
    if selector_mode != "deterministic":
        raise RuntimeRecoveryError(
            "reference durability profile currently supports only deterministic selector recovery"
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "tenant": adapter._tenant,
        "profile": profile.to_dict(),
        "interpretation_digest": profile.interpretation_digest,
        "adapter": {
            "selector_mode": selector_mode,
            "clock_tick": adapter._clock._t,
            "id_counter": adapter._ids._n,
            "state_version": dict(sorted(adapter._state_version.items())),
            "disputed": sorted(adapter._disputed),
            "tombstones": adapter._tombstones,
            "fact_scope": adapter._fact_scope,
            # GAP-SEC-03 (LD2b): without this the binding map restores empty and
            # every post-restart delete refuses target_binding_unknown.
            "fact_memory": dict(sorted(adapter._fact_memory.items())),
            "shared_domain_members": {
                key: sorted(value) for key, value in sorted(adapter._shared_domain_members.items())
            },
            "current_fact_by_memory": dict(sorted(adapter._current_fact_by_memory.items())),
            "rejected_values": _snapshot_rejections(adapter._rejected_values),
            "containment_violations": list(adapter.containment_violations),
            "events": list(adapter.events),
        },
        "visibility_snapshots": visibility_snapshots,
    }


def _restore_adapter(substrate: InMemoryTemporalGraph, snapshot: dict, verifier_registry=None) -> tuple[GovernedMemoryAdapter, dict[str, dict]]:
    if snapshot.get("schema_version") != SCHEMA_VERSION:
        raise RuntimeRecoveryError("unsupported governance state schema")
    tenant = snapshot.get("tenant")
    if not isinstance(tenant, str) or not tenant:
        raise RuntimeRecoveryError("governance state has no tenant identity")
    raw = snapshot.get("adapter")
    if not isinstance(raw, dict):
        raise RuntimeRecoveryError("governance adapter state is missing")
    if raw.get("selector_mode") != "deterministic":
        raise RuntimeRecoveryError("selector recovery is unsupported or ambiguous")

    adapter = GovernedMemoryAdapter(substrate, tenant=tenant, verifier_registry=verifier_registry)
    try:
        adapter._clock = Clock(start=int(raw.get("clock_tick", 0)))
        # GAP-SEC-08 (LD6): do NOT rebind to a private counter -- that detaches
        # the adapter from the substrate counter and silently reverts the
        # collision fix on the first restart. Advance the shared counter
        # instead. `max` because a multi-tenant restore runs this once per
        # adapter against one substrate, and plain assignment would rewind the
        # counter below another tenant's restored identifiers.
        adapter._ids._n = max(adapter._ids._n, int(raw.get("id_counter", 0)))
        adapter._state_version = {str(key): int(value) for key, value in raw.get("state_version", {}).items()}
        adapter._disputed = set(raw.get("disputed", ()))
        adapter._tombstones = dict(raw.get("tombstones", {}))
        fact_scope = {}
        for key, value in raw.get("fact_scope", {}).items():
            restored = dict(value)
            restored["domain_refs"] = tuple(restored.get("domain_refs", ()))
            restored["required_domain_refs"] = tuple(restored.get("required_domain_refs", ()))
            fact_scope[key] = restored
        adapter._fact_scope = fact_scope
        adapter._fact_memory = {str(k): str(v) for k, v in raw.get("fact_memory", {}).items()}
        adapter._shared_domain_members = {
            key: set(value) for key, value in raw.get("shared_domain_members", {}).items()
        }
        adapter._current_fact_by_memory = dict(raw.get("current_fact_by_memory", {}))
        adapter._rejected_values = _restore_rejections(raw.get("rejected_values", ()))
        adapter.containment_violations = list(raw.get("containment_violations", ()))
        adapter.events = list(raw.get("events", ()))
    except (TypeError, ValueError) as exc:
        raise RuntimeRecoveryError("governance adapter state cannot be reconstructed") from exc

    visibility = snapshot.get("visibility_snapshots", {})
    if not isinstance(visibility, dict):
        raise RuntimeRecoveryError("visibility snapshot state is malformed")
    return adapter, visibility


def _profile_from_dict(raw: dict) -> RuntimeProfile:
    try:
        return RuntimeProfile(
            runtime_version=raw["runtime_version"],
            profile_id=raw["profile_id"],
            profile_version=raw["profile_version"],
            bindings=tuple(CapabilityBinding(**binding) for binding in raw.get("bindings", ())),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeRecoveryError("persisted runtime profile is malformed") from exc


def _assert_profile_compatible(
    persisted: RuntimeProfile,
    expected: RuntimeProfile,
    available_bindings: Iterable[CapabilityBinding],
) -> None:
    if persisted.to_dict() != expected.to_dict():
        raise RuntimeRecoveryError(
            "runtime profile/component interpretation changed; explicit compatibility evidence or migration is required"
        )
    available = {binding.key: binding for binding in available_bindings}
    for required in persisted.bindings:
        candidate = available.get(required.key)
        if candidate is None:
            raise RuntimeRecoveryError(f"required capability unavailable after restart: {required.key}")
        if candidate != required:
            raise RuntimeRecoveryError(
                f"required capability interpretation changed after restart: {required.key}"
            )


class JsonRuntimeStateStore:
    """Atomic-manifest checkpoint store with separate substrate/governance payloads."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.substrate_path = self.root / "substrate.json"
        self.governance_path = self.root / "governance.json"
        self.manifest_path = self.root / "runtime-manifest.json"

    def exists(self) -> bool:
        return self.manifest_path.exists()

    def checkpoint(
        self,
        adapter: GovernedMemoryAdapter,
        *,
        profile: RuntimeProfile,
        visibility_snapshots: dict[str, dict],
    ) -> RecoveryEvidence:
        previous_generation = 0
        if self.manifest_path.exists():
            previous = _read_json(self.manifest_path)
            previous_generation = int(previous.get("generation", 0))

        substrate = _snapshot_substrate(adapter._substrate)
        governance = _snapshot_governance(
            adapter,
            profile=profile,
            visibility_snapshots=visibility_snapshots,
        )
        substrate_digest = _digest(substrate)
        governance_digest = _digest(governance)
        generation = previous_generation + 1

        _atomic_json_write(self.substrate_path, substrate)
        _atomic_json_write(self.governance_path, governance)
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "durability_profile": DURABILITY_PROFILE,
            "generation": generation,
            "substrate_digest": substrate_digest,
            "governance_digest": governance_digest,
            "interpretation_digest": profile.interpretation_digest,
        }
        # The manifest is replaced last. A crash before this point leaves a
        # digest mismatch that recovery treats as a torn checkpoint.
        _atomic_json_write(self.manifest_path, manifest)
        return RecoveryEvidence(
            generation=generation,
            durability_profile=DURABILITY_PROFILE,
            substrate_digest=substrate_digest,
            governance_digest=governance_digest,
            interpretation_digest=profile.interpretation_digest,
            recovered_visibility_operations=tuple(sorted(visibility_snapshots)),
        )

    def recover(
        self,
        *,
        expected_profile: RuntimeProfile,
        available_bindings: Iterable[CapabilityBinding],
        verifier_registry=None,
    ) -> tuple[GovernedMemoryAdapter, dict[str, dict], RecoveryEvidence]:
        manifest = _read_json(self.manifest_path)
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise RuntimeRecoveryError("unsupported runtime manifest schema")
        if manifest.get("durability_profile") != DURABILITY_PROFILE:
            raise RuntimeRecoveryError("runtime durability profile changed")

        substrate_raw = _read_json(self.substrate_path)
        governance_raw = _read_json(self.governance_path)
        substrate_digest = _digest(substrate_raw)
        governance_digest = _digest(governance_raw)
        if substrate_digest != manifest.get("substrate_digest"):
            raise RuntimeRecoveryError("substrate checkpoint digest mismatch; recovery fails closed")
        if governance_digest != manifest.get("governance_digest"):
            raise RuntimeRecoveryError("governance checkpoint digest mismatch; recovery fails closed")

        persisted_profile_raw = governance_raw.get("profile")
        if not isinstance(persisted_profile_raw, dict):
            raise RuntimeRecoveryError("persisted runtime profile is missing")
        persisted_profile = _profile_from_dict(persisted_profile_raw)
        if persisted_profile.interpretation_digest != manifest.get("interpretation_digest"):
            raise RuntimeRecoveryError("runtime interpretation digest mismatch")
        _assert_profile_compatible(persisted_profile, expected_profile, available_bindings)

        substrate = _restore_substrate(substrate_raw)
        adapter, visibility = _restore_adapter(substrate, governance_raw)
        evidence = RecoveryEvidence(
            generation=int(manifest.get("generation", 0)),
            durability_profile=DURABILITY_PROFILE,
            substrate_digest=substrate_digest,
            governance_digest=governance_digest,
            interpretation_digest=persisted_profile.interpretation_digest,
            recovered_visibility_operations=tuple(sorted(visibility)),
        )
        return adapter, visibility, evidence


class RestartSafeRuntime:
    """Smallest durable runtime wrapper around the governed reference adapter."""

    def __init__(
        self,
        *,
        store: JsonRuntimeStateStore,
        profile: RuntimeProfile,
        adapter: GovernedMemoryAdapter,
        visibility_snapshots: dict[str, dict] | None = None,
        recovery_evidence: RecoveryEvidence | None = None,
    ) -> None:
        self.store = store
        self.profile = profile
        self.adapter = adapter
        self.visibility_snapshots = dict(visibility_snapshots or {})
        self.recovery_evidence = recovery_evidence

    @classmethod
    def create(
        cls,
        root: str | Path,
        *,
        tenant: str,
        profile: RuntimeProfile,
        verifier_registry=None,
    ) -> "RestartSafeRuntime":
        """ADR-037 step 4b-2, DoD 20: the host configures verifier trust here."""
        store = JsonRuntimeStateStore(root)
        if store.exists():
            raise RuntimeRecoveryError("runtime state already exists; use recover()")
        adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=tenant, verifier_registry=verifier_registry)
        runtime = cls(store=store, profile=profile, adapter=adapter)
        runtime.recovery_evidence = runtime.checkpoint()
        return runtime

    @classmethod
    def recover(
        cls,
        root: str | Path,
        *,
        profile: RuntimeProfile,
        available_bindings: Iterable[CapabilityBinding] | None = None,
        verifier_registry=None,
    ) -> "RestartSafeRuntime":
        """ADR-037 step 4b-2, DoD 20: a recovered runtime carries host-configured
        verifier trust too, so restart is not a way to lose the channel."""
        available = tuple(available_bindings if available_bindings is not None else profile.bindings)
        store = JsonRuntimeStateStore(root)
        adapter, visibility, evidence = store.recover(
            expected_profile=profile,
            available_bindings=available,
            verifier_registry=verifier_registry,
        )
        return cls(
            store=store,
            profile=profile,
            adapter=adapter,
            visibility_snapshots=visibility,
            recovery_evidence=evidence,
        )

    def checkpoint(self) -> RecoveryEvidence:
        evidence = self.store.checkpoint(
            self.adapter,
            profile=self.profile,
            visibility_snapshots=self.visibility_snapshots,
        )
        self.recovery_evidence = evidence
        return evidence

    def commit_proposal(self, proposal, fact_text: str, episode=None, *,
                        evidence=None, attestation=None):
        """Forward the governed commit, including the qualified-evidence channel.

        ADR-037 step 4b-2, DoD 20: a wrapper that dropped `evidence` would leave
        the capability present underneath and unreachable from here -- a path
        that neither forwards nor parks honestly. It forwards; it does **not**
        become an alternate trust authority. Verifier trust stays with the
        adapter's evaluator-owned registry, and there is deliberately no
        `verifiers=` parameter here either.
        """
        result = self.adapter.commit_proposal(
            proposal, fact_text, episode, evidence=evidence, attestation=attestation
        )
        self.checkpoint()
        return result

    def governed_delete(self, proposal, fact_uuid: str, derived_refs: tuple[str, ...] = (),
                        external_verification=None, evidence=None):
        """Forwards the deletion channels too (ADR-037 step 4b-2, DoD 20)."""
        result = self.adapter.governed_delete(
            proposal, fact_uuid, derived_refs, external_verification, evidence
        )
        self.checkpoint()
        return result

    def persist_visibility_snapshot(self, operation_id: str, snapshot: dict) -> RecoveryEvidence:
        if not operation_id:
            raise ValueError("visibility operation id is required")
        if not isinstance(snapshot, dict):
            raise ValueError("visibility snapshot must be a mapping")
        self.visibility_snapshots[operation_id] = snapshot
        return self.checkpoint()
