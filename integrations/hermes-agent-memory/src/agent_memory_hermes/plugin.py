"""Hermes general plugin for observe/govern interception."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import threading
from typing import Any, Mapping, Optional

from . import HERMES_COMMIT, INTEGRATION_PROFILE, INTERCEPTABLE_TOOLS, STRICT_BLOCKERS
from .config import IntegrationConfig, detect_hermes_revision, load_config
from .evidence import EvidenceStore
from .governor import GovernorDecision, GovernorError, SubprocessGovernor


@dataclass(frozen=True)
class PendingDecision:
    proposal_event_id: str
    decision: str
    reason: str
    tool_name: str
    args_digest: str


class HermesPluginRuntime:
    def __init__(
        self,
        hermes_home: str | Path,
        *,
        config: IntegrationConfig | None = None,
        observed_hermes_revision: str | None = None,
    ):
        self.hermes_home = Path(hermes_home).expanduser().resolve()
        self.config = config or load_config(self.hermes_home)
        self.observed_hermes_revision = observed_hermes_revision or detect_hermes_revision()
        self.store = EvidenceStore(self.hermes_home, record_payloads=self.config.record_payloads)
        self._pending: dict[str, PendingDecision] = {}
        self._lock = threading.Lock()

    def _profile_current(self) -> bool:
        return (
            self.observed_hermes_revision
            == self.config.expected_hermes_revision
            == HERMES_COMMIT
        )

    @staticmethod
    def _operation(tool_name: str, args: Mapping[str, Any]) -> str:
        if tool_name == "memory":
            return str(args.get("action") or "unknown")
        if tool_name == "skill_manage":
            return str(args.get("action") or args.get("mode") or "unknown")
        return "not_applicable"

    @staticmethod
    def _target(tool_name: str, args: Mapping[str, Any]) -> str:
        if tool_name == "memory":
            return str(args.get("target") or "memory")
        if tool_name == "skill_manage":
            return str(args.get("name") or args.get("skill_name") or args.get("file_path") or "skill")
        return "unknown"

    def _candidate(self, tool_name: str, args: Mapping[str, Any], metadata: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "kind": "hermes_durable_state_candidate",
            "integration_profile": INTEGRATION_PROFILE,
            "hermes_revision": self.observed_hermes_revision,
            "expected_hermes_revision": self.config.expected_hermes_revision,
            "tool_name": tool_name,
            "operation": self._operation(tool_name, args),
            "target": self._target(tool_name, args),
            "origin_hint": str(metadata.get("origin_hint") or "unknown_model_tool"),
            "origin_precision": "hook_does_not_expose_background_review_origin",
            "scope": {
                key: str(metadata.get(key) or "")
                for key in (
                    "task_id",
                    "session_id",
                    "tool_call_id",
                    "turn_id",
                    "api_request_id",
                )
            },
            "lineage_refs": list(args.get("lineage_refs", []))
            if isinstance(args.get("lineage_refs"), list)
            else [],
            "provenance_refs": list(args.get("provenance_refs", []))
            if isinstance(args.get("provenance_refs"), list)
            else [],
            "args": dict(args),
            "args_digest": EvidenceStore.digest(args),
            "authority_effect": "none",
        }

    def _remember(self, tool_call_id: str, pending: PendingDecision) -> None:
        if not tool_call_id:
            return
        with self._lock:
            self._pending[tool_call_id] = pending

    def _pop(self, tool_call_id: str) -> PendingDecision | None:
        if not tool_call_id:
            return None
        with self._lock:
            return self._pending.pop(tool_call_id, None)

    @staticmethod
    def _block(message: str) -> dict[str, str]:
        return {"action": "block", "message": message}

    def _record_proposal(
        self,
        candidate: Mapping[str, Any],
        *,
        decision: str,
        reason: str,
        evidence_refs: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        scope = candidate["scope"]
        metadata = {
            "tool_name": candidate["tool_name"],
            "operation": candidate["operation"],
            "target": candidate["target"],
            "origin_hint": candidate["origin_hint"],
            "origin_precision": candidate["origin_precision"],
            "args_digest": candidate["args_digest"],
            "task_id": scope["task_id"],
            "session_id": scope["session_id"],
            "tool_call_id": scope["tool_call_id"],
            "turn_id": scope["turn_id"],
            "api_request_id": scope["api_request_id"],
            "decision": decision,
            "reason": reason,
            "evidence_refs": list(evidence_refs),
            "profile_current": self._profile_current(),
        }
        return self.store.append(
            "durable_tool_proposal",
            mode=self.config.mode,
            hermes_revision=self.observed_hermes_revision,
            metadata=metadata,
            payload=candidate if self.config.record_payloads else None,
        )

    def on_pre_tool_call(
        self,
        tool_name: str = "",
        args: Optional[Mapping[str, Any]] = None,
        **metadata: Any,
    ) -> Optional[dict[str, str]]:
        if tool_name not in INTERCEPTABLE_TOOLS:
            return None
        safe_args: Mapping[str, Any] = args if isinstance(args, Mapping) else {}
        candidate = self._candidate(tool_name, safe_args, metadata)
        tool_call_id = candidate["scope"]["tool_call_id"]

        if self.config.mode == "observe":
            record = self._record_proposal(
                candidate,
                decision="observe_allow",
                reason="observe mode records the proposal without changing Hermes execution",
            )
            self._remember(
                tool_call_id,
                PendingDecision(
                    proposal_event_id=record["event_id"],
                    decision="observe_allow",
                    reason="observe mode",
                    tool_name=tool_name,
                    args_digest=candidate["args_digest"],
                ),
            )
            return None

        if self.config.mode == "strict":
            reason = (
                "Agent Memory strict mode is unsupported for this Hermes profile; "
                "known uncovered durable mutation surfaces: " + ", ".join(STRICT_BLOCKERS)
            )
            record = self._record_proposal(candidate, decision="reject", reason=reason)
            self._remember(
                tool_call_id,
                PendingDecision(record["event_id"], "reject", reason, tool_name, candidate["args_digest"]),
            )
            return self._block(reason)

        if self.config.require_exact_profile and not self._profile_current():
            reason = (
                "Agent Memory Hermes govern profile is not current; "
                f"observed={self.observed_hermes_revision} expected={self.config.expected_hermes_revision}"
            )
            record = self._record_proposal(candidate, decision="reject", reason=reason)
            self._remember(
                tool_call_id,
                PendingDecision(record["event_id"], "reject", reason, tool_name, candidate["args_digest"]),
            )
            return self._block(reason)

        governor: SubprocessGovernor | None = None
        if self.config.governor_command:
            governor = SubprocessGovernor(
                self.config.governor_command,
                timeout_seconds=self.config.governor_timeout_seconds,
            )

        if governor is None:
            reason = "Agent Memory governor command is not configured"
            decision_name = "reject" if self.config.governor_required else "allow_unqualified"
            record = self._record_proposal(candidate, decision=decision_name, reason=reason)
            self._remember(
                tool_call_id,
                PendingDecision(record["event_id"], decision_name, reason, tool_name, candidate["args_digest"]),
            )
            return self._block(reason) if self.config.governor_required else None

        try:
            decision: GovernorDecision = governor.evaluate(candidate)
        except GovernorError as exc:
            reason = str(exc)
            decision_name = "reject" if self.config.governor_required else "allow_governor_unavailable"
            record = self._record_proposal(candidate, decision=decision_name, reason=reason)
            self._remember(
                tool_call_id,
                PendingDecision(record["event_id"], decision_name, reason, tool_name, candidate["args_digest"]),
            )
            return self._block(reason) if self.config.governor_required else None

        if decision.decision == "allow":
            record = self._record_proposal(
                candidate,
                decision="allow",
                reason=decision.reason,
                evidence_refs=decision.evidence_refs,
            )
            self._remember(
                tool_call_id,
                PendingDecision(record["event_id"], "allow", decision.reason, tool_name, candidate["args_digest"]),
            )
            return None

        if decision.decision == "stage":
            reason = (
                "Agent Memory governor requested stage, but the pinned Hermes pre_tool_call hook "
                "cannot create a native staged durable mutation; blocking instead. "
                f"Governor reason: {decision.reason}"
            )
            record = self._record_proposal(
                candidate,
                decision="stage_unsupported_block",
                reason=reason,
                evidence_refs=decision.evidence_refs,
            )
            self._remember(
                tool_call_id,
                PendingDecision(record["event_id"], "stage_unsupported_block", reason, tool_name, candidate["args_digest"]),
            )
            return self._block(reason)

        record = self._record_proposal(
            candidate,
            decision="reject",
            reason=decision.reason,
            evidence_refs=decision.evidence_refs,
        )
        self._remember(
            tool_call_id,
            PendingDecision(record["event_id"], "reject", decision.reason, tool_name, candidate["args_digest"]),
        )
        return self._block(decision.reason)

    def on_post_tool_call(
        self,
        tool_name: str = "",
        args: Optional[Mapping[str, Any]] = None,
        result: Any = None,
        tool_call_id: str = "",
        status: str = "",
        error_type: str = "",
        error_message: str = "",
        **metadata: Any,
    ) -> None:
        if tool_name not in INTERCEPTABLE_TOOLS:
            return
        pending = self._pop(tool_call_id)
        safe_args: Mapping[str, Any] = args if isinstance(args, Mapping) else {}
        self.store.append(
            "durable_tool_execution_receipt",
            mode=self.config.mode,
            hermes_revision=self.observed_hermes_revision,
            metadata={
                "proposal_event_id": pending.proposal_event_id if pending else None,
                "proposal_decision": pending.decision if pending else "unmatched",
                "tool_name": tool_name,
                "operation": self._operation(tool_name, safe_args),
                "target": self._target(tool_name, safe_args),
                "args_digest": EvidenceStore.digest(safe_args),
                "result_digest": EvidenceStore.digest(result),
                "tool_call_id": tool_call_id,
                "task_id": str(metadata.get("task_id") or ""),
                "session_id": str(metadata.get("session_id") or ""),
                "status": status or ("failed" if error_type or error_message else "completed"),
                "error_type": error_type or None,
                "error_message_digest": EvidenceStore.digest(error_message) if error_message else None,
                "admission_is_not_execution": True,
            },
            payload={"args": dict(safe_args), "result": result} if self.config.record_payloads else None,
        )


_RUNTIME_CACHE: dict[str, HermesPluginRuntime] = {}
_RUNTIME_LOCK = threading.Lock()


def _current_home() -> Path:
    try:
        from hermes_constants import get_hermes_home  # type: ignore

        return Path(get_hermes_home()).expanduser().resolve()
    except Exception:
        import os

        return Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser().resolve()


def runtime_for_current_home() -> HermesPluginRuntime:
    home = _current_home()
    key = str(home)
    with _RUNTIME_LOCK:
        runtime = _RUNTIME_CACHE.get(key)
        if runtime is None:
            runtime = HermesPluginRuntime(home)
            _RUNTIME_CACHE[key] = runtime
        return runtime


def _pre_tool_hook(tool_name: str = "", args: Optional[Mapping[str, Any]] = None, **kwargs: Any):
    return runtime_for_current_home().on_pre_tool_call(tool_name=tool_name, args=args, **kwargs)


def _post_tool_hook(tool_name: str = "", args: Optional[Mapping[str, Any]] = None, **kwargs: Any):
    return runtime_for_current_home().on_post_tool_call(tool_name=tool_name, args=args, **kwargs)


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _pre_tool_hook)
    ctx.register_hook("post_tool_call", _post_tool_hook)


def _clear_runtime_cache_for_tests() -> None:
    with _RUNTIME_LOCK:
        _RUNTIME_CACHE.clear()
