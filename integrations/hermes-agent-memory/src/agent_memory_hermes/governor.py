"""External admission command transport for Hermes govern mode."""

from __future__ import annotations

from dataclasses import dataclass
import json
import subprocess
from typing import Any, Mapping, Sequence


class GovernorError(RuntimeError):
    """The configured governor could not return a valid decision."""


@dataclass(frozen=True)
class GovernorDecision:
    decision: str
    reason: str
    evidence_refs: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "GovernorDecision":
        decision = str(value.get("decision", "")).strip().lower()
        if decision not in {"allow", "reject", "stage"}:
            raise GovernorError("governor decision must be allow, reject, or stage")
        reason = str(value.get("reason", "")).strip()
        if not reason:
            raise GovernorError("governor decision requires a non-empty reason")
        raw_refs = value.get("evidence_refs", [])
        if not isinstance(raw_refs, list) or any(not isinstance(item, str) or not item for item in raw_refs):
            raise GovernorError("governor evidence_refs must be a list of non-empty strings")
        return cls(decision=decision, reason=reason, evidence_refs=tuple(raw_refs))


class SubprocessGovernor:
    def __init__(self, command: Sequence[str], *, timeout_seconds: float = 10.0):
        self.command = tuple(command)
        self.timeout_seconds = timeout_seconds

    def evaluate(self, candidate: Mapping[str, Any]) -> GovernorDecision:
        if not self.command:
            raise GovernorError("governor command is not configured")
        try:
            completed = subprocess.run(
                list(self.command),
                input=json.dumps(candidate, sort_keys=True),
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise GovernorError(f"governor unavailable: {exc}") from exc
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            suffix = f": {stderr}" if stderr else ""
            raise GovernorError(f"governor exited with status {completed.returncode}{suffix}")
        try:
            value = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise GovernorError("governor did not return valid JSON") from exc
        if not isinstance(value, dict):
            raise GovernorError("governor response must be a JSON object")
        return GovernorDecision.from_mapping(value)
