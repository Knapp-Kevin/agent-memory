"""Provider-neutral write-to-readable visibility and quiescence evidence.

A successful mutation response is not proof that every required read path is
current. This module records those boundaries without turning latency into
authority or assuming that all derived state is synchronous.

The contract separates:

* phase observations from correctness obligations;
* canonical durability from projection/read visibility;
* a known terminal state (settled) from fully satisfied currentness
  (quiescent);
* required work from optional residual work;
* monotonic timing segments across process restart so cross-process latency is
  never fabricated from unrelated monotonic clocks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import time
from typing import Callable


PENDING = "pending"
SATISFIED = "satisfied"
FAILED = "failed"
QUARANTINED = "quarantined"
NOT_APPLICABLE = "not_applicable"

TERMINAL_STATUSES = frozenset({SATISFIED, FAILED, QUARANTINED, NOT_APPLICABLE})
QUIESCENT_STATUSES = frozenset({SATISFIED, NOT_APPLICABLE})

CURRENT_VALUE = "current_value"
ABSENCE = "absence"
NO_READ_VISIBILITY = "none"

PHASES = (
    "request_received",
    "policy_decision_complete",
    "canonical_commit_complete",
    "required_projection_refresh_started",
    "required_projection_refresh_complete",
    "governed_recall_current_visible",
    "context_current_visible",
    "settlement_reached",
    "quiescence_reached",
)


@dataclass(frozen=True)
class VisibilityOperation:
    operation_id: str
    memory_id: str
    memory_version: int
    operation_type: str
    runtime_version: str
    profile_version: str
    agent_memory_commit: str
    required_projection_ids: tuple[str, ...] = ()
    optional_projection_ids: tuple[str, ...] = ()
    component_versions: tuple[str, ...] = ()
    capability_versions: tuple[str, ...] = ()
    receipt_ref: str = ""
    correlation_ref: str = ""
    visibility_target: str = CURRENT_VALUE
    environment_ref: str = "reference-runtime"

    def __post_init__(self) -> None:
        if self.memory_version < 0:
            raise ValueError("memory_version must be non-negative")
        if (
            len(self.agent_memory_commit) != 40
            or any(character not in "0123456789abcdef" for character in self.agent_memory_commit)
        ):
            raise ValueError("agent_memory_commit must be an exact 40-character lowercase hex commit SHA")
        if self.visibility_target not in {CURRENT_VALUE, ABSENCE, NO_READ_VISIBILITY}:
            raise ValueError("unsupported visibility_target")
        if len(set(self.required_projection_ids)) != len(self.required_projection_ids):
            raise ValueError("required_projection_ids must be unique")
        if len(set(self.optional_projection_ids)) != len(self.optional_projection_ids):
            raise ValueError("optional_projection_ids must be unique")
        overlap = set(self.required_projection_ids).intersection(self.optional_projection_ids)
        if overlap:
            raise ValueError(f"projection cannot be both required and optional: {sorted(overlap)}")


@dataclass
class Obligation:
    obligation_id: str
    kind: str
    required: bool
    status: str = PENDING
    detail: str = ""


@dataclass
class PhaseObservation:
    phase: str
    status: str
    segment: int
    offset_ns: int | None
    detail: str = ""


class VisibilityTracker:
    """Track one bounded mutation from request through safe read visibility."""

    def __init__(
        self,
        operation: VisibilityOperation,
        *,
        clock_ns: Callable[[], int] | None = None,
        _segment: int = 0,
        _restored_phases: dict[str, PhaseObservation] | None = None,
        _restored_obligations: dict[str, Obligation] | None = None,
    ) -> None:
        self.operation = operation
        self._clock_ns = clock_ns or time.perf_counter_ns
        self._origin_ns = self._clock_ns()
        self._segment = _segment
        self._phases: dict[str, PhaseObservation] = dict(_restored_phases or {})
        self._obligations: dict[str, Obligation] = dict(_restored_obligations or {})

        if not self._obligations:
            self._declare_default_obligations()
        if "request_received" not in self._phases:
            self.observe_phase("request_received")

    def _declare_default_obligations(self) -> None:
        self._obligations["canonical_outcome"] = Obligation(
            obligation_id="canonical_outcome",
            kind="canonical_outcome",
            required=True,
        )
        for projection_id in self.operation.required_projection_ids:
            obligation_id = f"projection:{projection_id}"
            self._obligations[obligation_id] = Obligation(
                obligation_id=obligation_id,
                kind="projection_currentness",
                required=True,
            )
        for projection_id in self.operation.optional_projection_ids:
            obligation_id = f"projection:{projection_id}"
            self._obligations[obligation_id] = Obligation(
                obligation_id=obligation_id,
                kind="projection_currentness",
                required=False,
            )
        if self.operation.visibility_target != NO_READ_VISIBILITY:
            self._obligations["governed_recall_current"] = Obligation(
                obligation_id="governed_recall_current",
                kind="governed_recall_currentness",
                required=True,
            )
            self._obligations["context_current"] = Obligation(
                obligation_id="context_current",
                kind="context_currentness",
                required=True,
            )
            self._obligations["stale_current_blocked"] = Obligation(
                obligation_id="stale_current_blocked",
                kind="stale_current_admission",
                required=True,
            )

    def _offset_ns(self) -> int:
        return self._clock_ns() - self._origin_ns

    def _require_phase(self, phase: str, *, allow_not_applicable: bool = False) -> None:
        observation = self._phases.get(phase)
        if observation is None:
            raise ValueError(f"required prior phase not observed: {phase}")
        if observation.status == NOT_APPLICABLE and not allow_not_applicable:
            raise ValueError(f"required prior phase is not applicable: {phase}")

    def observe_phase(self, phase: str, *, detail: str = "") -> PhaseObservation:
        if phase not in PHASES:
            raise ValueError(f"unsupported phase: {phase}")
        existing = self._phases.get(phase)
        if existing is not None:
            return existing
        observation = PhaseObservation(
            phase=phase,
            status="observed",
            segment=self._segment,
            offset_ns=self._offset_ns(),
            detail=detail,
        )
        self._phases[phase] = observation
        return observation

    def phase_not_applicable(self, phase: str, *, detail: str) -> PhaseObservation:
        if phase not in PHASES:
            raise ValueError(f"unsupported phase: {phase}")
        existing = self._phases.get(phase)
        if existing is not None:
            return existing
        observation = PhaseObservation(
            phase=phase,
            status=NOT_APPLICABLE,
            segment=self._segment,
            offset_ns=None,
            detail=detail,
        )
        self._phases[phase] = observation
        return observation

    def set_obligation(self, obligation_id: str, status: str, *, detail: str = "") -> Obligation:
        if status not in {PENDING, SATISFIED, FAILED, QUARANTINED, NOT_APPLICABLE}:
            raise ValueError(f"unsupported obligation status: {status}")
        obligation = self._obligations.get(obligation_id)
        if obligation is None:
            raise KeyError(f"undeclared obligation: {obligation_id}")
        obligation.status = status
        obligation.detail = detail
        return obligation

    def policy_decided(self) -> None:
        self._require_phase("request_received")
        self.observe_phase("policy_decision_complete")

    def canonical_committed(self) -> None:
        self._require_phase("policy_decision_complete")
        self.observe_phase("canonical_commit_complete")
        self.set_obligation("canonical_outcome", SATISFIED, detail="canonical mutation durable")

    def canonical_refused(self, *, detail: str = "mutation explicitly refused") -> None:
        self._require_phase("policy_decision_complete")
        self.set_obligation("canonical_outcome", SATISFIED, detail=detail)
        self.phase_not_applicable("canonical_commit_complete", detail=detail)
        for obligation_id in tuple(self._obligations):
            if obligation_id == "canonical_outcome":
                continue
            self.set_obligation(obligation_id, NOT_APPLICABLE, detail="no mutation obligations created")
        for phase in (
            "required_projection_refresh_started",
            "required_projection_refresh_complete",
            "governed_recall_current_visible",
            "context_current_visible",
        ):
            self.phase_not_applicable(phase, detail="no mutation obligations created")

    def projection_refresh_started(self, projection_id: str) -> None:
        self._require_phase("canonical_commit_complete")
        obligation_id = f"projection:{projection_id}"
        if obligation_id not in self._obligations:
            raise KeyError(f"undeclared projection: {projection_id}")
        self.observe_phase("required_projection_refresh_started")

    def projection_refresh_satisfied(self, projection_id: str) -> None:
        self._require_phase("required_projection_refresh_started")
        obligation_id = f"projection:{projection_id}"
        self.set_obligation(obligation_id, SATISFIED, detail="projection current")
        if self._all_required_projection_obligations_terminal():
            self.observe_phase("required_projection_refresh_complete")

    def projection_refresh_failed(self, projection_id: str, *, detail: str) -> None:
        self._require_phase("required_projection_refresh_started")
        obligation_id = f"projection:{projection_id}"
        self.set_obligation(obligation_id, FAILED, detail=detail)
        if self._all_required_projection_obligations_terminal():
            self.observe_phase("required_projection_refresh_complete", detail="required refresh reached terminal state")

    def projection_refresh_quarantined(self, projection_id: str, *, detail: str) -> None:
        self._require_phase("required_projection_refresh_started")
        obligation_id = f"projection:{projection_id}"
        self.set_obligation(obligation_id, QUARANTINED, detail=detail)
        if self._all_required_projection_obligations_terminal():
            self.observe_phase("required_projection_refresh_complete", detail="required refresh reached terminal state")

    def governed_recall_current_visible(self) -> None:
        self._require_phase("canonical_commit_complete")
        if "governed_recall_current" not in self._obligations:
            raise ValueError("operation declares no governed recall visibility obligation")
        self.observe_phase("governed_recall_current_visible")
        self.set_obligation("governed_recall_current", SATISFIED)

    def context_current_visible(self) -> None:
        self._require_phase("governed_recall_current_visible")
        if "context_current" not in self._obligations:
            raise ValueError("operation declares no context visibility obligation")
        self.observe_phase("context_current_visible")
        self.set_obligation("context_current", SATISFIED)

    def stale_current_blocked(self) -> None:
        self._require_phase("canonical_commit_complete")
        if "stale_current_blocked" not in self._obligations:
            raise ValueError("operation declares no stale-current admission obligation")
        self.set_obligation("stale_current_blocked", SATISFIED)

    def _required_projection_obligations(self) -> list[Obligation]:
        return [
            obligation
            for obligation in self._obligations.values()
            if obligation.required and obligation.kind == "projection_currentness"
        ]

    def _all_required_projection_obligations_terminal(self) -> bool:
        required = self._required_projection_obligations()
        return bool(required) and all(obligation.status in TERMINAL_STATUSES for obligation in required)

    def evaluate(self) -> dict:
        required = [obligation for obligation in self._obligations.values() if obligation.required]
        pending = [obligation.obligation_id for obligation in required if obligation.status == PENDING]
        failed = [
            obligation.obligation_id
            for obligation in required
            if obligation.status in {FAILED, QUARANTINED}
        ]
        unsatisfied = [
            obligation.obligation_id
            for obligation in required
            if obligation.status not in QUIESCENT_STATUSES
        ]
        optional_residual = [
            obligation.obligation_id
            for obligation in self._obligations.values()
            if not obligation.required and obligation.status in {PENDING, FAILED, QUARANTINED}
        ]

        settled = all(obligation.status in TERMINAL_STATUSES for obligation in required)
        quiescent = settled and not unsatisfied
        if quiescent:
            posture = "quiescent"
            self.observe_phase("settlement_reached")
            self.observe_phase("quiescence_reached")
        elif settled:
            posture = "degraded"
            self.observe_phase("settlement_reached")
        else:
            posture = "pending"

        return {
            "settled": settled,
            "quiescent": quiescent,
            "posture": posture,
            "pending_required_obligations": pending,
            "failed_required_obligations": failed,
            "unsatisfied_required_obligations": unsatisfied,
            "optional_residual_work": optional_residual,
        }

    def _duration(self, start: str, end: str) -> dict:
        first = self._phases.get(start)
        second = self._phases.get(end)
        if first is None or second is None:
            return {"value_ns": None, "reason": "phase_missing"}
        if first.status == NOT_APPLICABLE or second.status == NOT_APPLICABLE:
            return {"value_ns": None, "reason": "not_applicable"}
        if first.segment != second.segment:
            return {"value_ns": None, "reason": "cross_restart_monotonic_segments"}
        assert first.offset_ns is not None and second.offset_ns is not None
        return {"value_ns": max(0, second.offset_ns - first.offset_ns), "reason": "observed"}

    def metrics(self) -> dict:
        required_projections = self._required_projection_obligations()
        if not required_projections:
            projection_metric = {"value_ns": None, "reason": "not_applicable"}
        elif any(obligation.status in {FAILED, QUARANTINED} for obligation in required_projections):
            projection_metric = {"value_ns": None, "reason": "required_obligation_failed"}
        else:
            projection_metric = self._duration("canonical_commit_complete", "required_projection_refresh_complete")
        return {
            "request_to_canonical_durable": self._duration("request_received", "canonical_commit_complete"),
            "canonical_to_required_projections_current": projection_metric,
            "canonical_to_governed_recall_current_visible": self._duration(
                "canonical_commit_complete", "governed_recall_current_visible"
            ),
            "canonical_to_context_current_visible": self._duration(
                "canonical_commit_complete", "context_current_visible"
            ),
            "request_to_quiescence": self._duration("request_received", "quiescence_reached"),
        }

    def evidence(self) -> dict:
        disposition = self.evaluate()
        return {
            "schema_version": "1.0.0",
            "operation": asdict(self.operation),
            "timing": {
                "clock": "process_monotonic_ns",
                "segment": self._segment,
                "cross_restart_duration_policy": "unavailable_between_monotonic_segments",
                "latency_is_observational_only": True,
                "latency_is_not_authority": True,
            },
            "phases": [asdict(self._phases[phase]) for phase in PHASES if phase in self._phases],
            "obligations": [
                asdict(self._obligations[key]) for key in sorted(self._obligations)
            ],
            "disposition": disposition,
            "metrics": self.metrics(),
        }

    def snapshot_for_restart(self) -> dict:
        """Serialize obligation/currentness state without pretending clocks survive restart."""
        return {
            "schema_version": "1.0.0",
            "operation": asdict(self.operation),
            "segment": self._segment,
            "phases": {key: asdict(value) for key, value in self._phases.items()},
            "obligations": {key: asdict(value) for key, value in self._obligations.items()},
        }

    @classmethod
    def restore_after_restart(
        cls,
        snapshot: dict,
        *,
        clock_ns: Callable[[], int] | None = None,
    ) -> "VisibilityTracker":
        operation_raw = dict(snapshot["operation"])
        for field_name in (
            "required_projection_ids",
            "optional_projection_ids",
            "component_versions",
            "capability_versions",
        ):
            operation_raw[field_name] = tuple(operation_raw.get(field_name, ()))
        operation = VisibilityOperation(**operation_raw)
        phases = {
            key: PhaseObservation(**value)
            for key, value in snapshot.get("phases", {}).items()
        }
        obligations = {
            key: Obligation(**value)
            for key, value in snapshot.get("obligations", {}).items()
        }
        return cls(
            operation,
            clock_ns=clock_ns,
            _segment=int(snapshot.get("segment", 0)) + 1,
            _restored_phases=phases,
            _restored_obligations=obligations,
        )
