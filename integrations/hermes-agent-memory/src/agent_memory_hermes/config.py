"""Configuration and exact Hermes profile detection."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, replace
from pathlib import Path
import shlex
import subprocess
from typing import Any, Mapping, Sequence

from . import HERMES_COMMIT


class IntegrationConfigError(ValueError):
    """Invalid Agent Memory Hermes integration configuration."""


@dataclass(frozen=True)
class IntegrationConfig:
    mode: str = "observe"
    governor_command: tuple[str, ...] = ()
    governor_required: bool = True
    governor_timeout_seconds: float = 10.0
    record_payloads: bool = False
    require_exact_profile: bool = True
    expected_hermes_revision: str = HERMES_COMMIT

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None) -> "IntegrationConfig":
        raw = dict(value or {})
        command = raw.get("governor_command", ())
        if isinstance(command, str):
            command = tuple(shlex.split(command))
        elif isinstance(command, Sequence):
            command = tuple(str(item) for item in command)
        else:
            raise IntegrationConfigError("governor_command must be a string or sequence")
        config = cls(
            mode=str(raw.get("mode", "observe")).strip().lower(),
            governor_command=command,
            governor_required=bool(raw.get("governor_required", True)),
            governor_timeout_seconds=float(raw.get("governor_timeout_seconds", 10.0)),
            record_payloads=bool(raw.get("record_payloads", False)),
            require_exact_profile=bool(raw.get("require_exact_profile", True)),
            expected_hermes_revision=str(raw.get("expected_hermes_revision", HERMES_COMMIT)).strip(),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.mode not in {"observe", "govern", "strict"}:
            raise IntegrationConfigError("mode must be observe, govern, or strict")
        if self.governor_timeout_seconds <= 0 or self.governor_timeout_seconds > 120:
            raise IntegrationConfigError("governor_timeout_seconds must be >0 and <=120")
        if len(self.expected_hermes_revision) != 40 or any(
            ch not in "0123456789abcdef" for ch in self.expected_hermes_revision
        ):
            raise IntegrationConfigError("expected_hermes_revision must be a 40-character lowercase git SHA")

    def with_mode(self, mode: str | None) -> "IntegrationConfig":
        if mode is None:
            return self
        updated = replace(self, mode=mode.strip().lower())
        updated.validate()
        return updated

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["governor_command"] = list(self.governor_command)
        return value


def integration_dir(hermes_home: str | Path) -> Path:
    return Path(hermes_home).expanduser().resolve() / "agent-memory"


def config_path(hermes_home: str | Path) -> Path:
    return integration_dir(hermes_home) / "config.json"


def load_config(hermes_home: str | Path) -> IntegrationConfig:
    path = config_path(hermes_home)
    value: dict[str, Any] = {}
    if path.exists():
        parsed = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(parsed, dict):
            raise IntegrationConfigError(f"{path} must contain a JSON object")
        value.update(parsed)

    env_mode = os.environ.get("AGENT_MEMORY_HERMES_MODE")
    env_command = os.environ.get("AGENT_MEMORY_HERMES_GOVERNOR_COMMAND")
    env_required = os.environ.get("AGENT_MEMORY_HERMES_GOVERNOR_REQUIRED")
    env_revision = os.environ.get("AGENT_MEMORY_HERMES_EXPECTED_REVISION")
    if env_mode:
        value["mode"] = env_mode
    if env_command:
        value["governor_command"] = env_command
    if env_required is not None:
        value["governor_required"] = env_required.strip().lower() in {"1", "true", "yes", "on"}
    if env_revision:
        value["expected_hermes_revision"] = env_revision
    return IntegrationConfig.from_mapping(value)


def save_config(hermes_home: str | Path, config: IntegrationConfig) -> Path:
    config.validate()
    path = config_path(hermes_home)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(config.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    return path


def detect_hermes_revision() -> str:
    """Return the exact Hermes git revision when deterministically discoverable.

    The environment override exists for packaged/test deployments where Hermes
    source is mounted separately. Without exact evidence, return ``unknown``.
    """
    override = os.environ.get("AGENT_MEMORY_HERMES_REVISION", "").strip().lower()
    if override:
        if len(override) == 40 and all(ch in "0123456789abcdef" for ch in override):
            return override
        return "unknown"

    try:
        import agent  # type: ignore
    except Exception:
        return "unknown"

    package_path = Path(getattr(agent, "__file__", "")).resolve()
    for parent in (package_path.parent, *package_path.parents):
        if not (parent / ".git").exists():
            continue
        try:
            result = subprocess.run(
                ["git", "-C", str(parent), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=3,
            )
        except (OSError, subprocess.SubprocessError):
            return "unknown"
        revision = result.stdout.strip().lower()
        if len(revision) == 40 and all(ch in "0123456789abcdef" for ch in revision):
            return revision
        return "unknown"
    return "unknown"
