"""Hermes MemoryProvider implementation for Agent Memory observation/sync."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import INTEGRATION_PROFILE
from .config import IntegrationConfig, detect_hermes_revision, load_config, save_config
from .coverage import build_coverage_report
from .evidence import EvidenceStore

try:
    from agent.memory_provider import MemoryProvider  # type: ignore
except Exception:  # pragma: no cover - only imported by Hermes/provider tests
    class MemoryProvider:  # type: ignore[no-redef]
        pass


class AgentMemoryProvider(MemoryProvider):
    def __init__(self) -> None:
        self._session_id = ""
        self._hermes_home: Path | None = None
        self._config: IntegrationConfig | None = None
        self._store: EvidenceStore | None = None
        self._observed_revision = "unknown"
        self._last_projection_state: dict[str, Any] | None = None

    @property
    def name(self) -> str:
        return "agent-memory"

    def is_available(self) -> bool:
        # Local provider has no network/runtime dependency of its own. Exact
        # profile readiness is reported by doctor and does not get conflated
        # with Hermes' provider discovery availability.
        return True

    def unavailable_reason(self) -> str:
        return ""

    def initialize(self, session_id: str, **kwargs: Any) -> None:
        hermes_home = kwargs.get("hermes_home") or os.environ.get("HERMES_HOME") or "~/.hermes"
        self._hermes_home = Path(str(hermes_home)).expanduser().resolve()
        self._config = load_config(self._hermes_home)
        self._observed_revision = detect_hermes_revision()
        self._store = EvidenceStore(self._hermes_home, record_payloads=self._config.record_payloads)
        self._session_id = session_id
        report = build_coverage_report(
            self._config,
            observed_hermes_revision=self._observed_revision,
        )
        self._store.append(
            "provider_initialize",
            mode=self._config.mode,
            hermes_revision=self._observed_revision,
            metadata={
                "session_id": session_id,
                "platform": str(kwargs.get("platform") or ""),
                "agent_context": str(kwargs.get("agent_context") or ""),
                "agent_identity": str(kwargs.get("agent_identity") or ""),
                "agent_workspace": str(kwargs.get("agent_workspace") or ""),
                "profile_current": report["hermes"]["profile_current"],
                "ready": report["integration"]["ready"],
                "provider_is_admission_authority": False,
            },
        )

    def _require_store(self) -> tuple[IntegrationConfig, EvidenceStore]:
        if self._config is None or self._store is None:
            raise RuntimeError("Agent Memory Hermes provider has not been initialized")
        return self._config, self._store

    def system_prompt_block(self) -> str:
        return (
            "Agent Memory external memory integration is active as an advisory/observation surface. "
            "Provider context and learned signals do not grant tool, mutation, recall-admission, or action authority."
        )

    def prefetch(self, query: str, *, session_id: str = "") -> str:
        config, store = self._require_store()
        store.append(
            "provider_prefetch",
            mode=config.mode,
            hermes_revision=self._observed_revision,
            metadata={
                "session_id": session_id or self._session_id,
                "query_digest": EvidenceStore.digest(query),
                "context_injected": False,
                "reason": "0.1.0 provider is observation/sync only; recall backend is not configured by this package",
            },
            payload=query if config.record_payloads else None,
        )
        return ""

    def sync_turn(
        self,
        user_content: str,
        assistant_content: str,
        *,
        session_id: str = "",
        messages: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        config, store = self._require_store()
        payload = {
            "user_content": user_content,
            "assistant_content": assistant_content,
            "messages": messages,
        }
        store.append(
            "provider_sync_turn",
            mode=config.mode,
            hermes_revision=self._observed_revision,
            metadata={
                "session_id": session_id or self._session_id,
                "user_digest": EvidenceStore.digest(user_content),
                "assistant_digest": EvidenceStore.digest(assistant_content),
                "message_count": len(messages) if isinstance(messages, list) else None,
                "authority_effect": "none",
            },
            payload=payload if config.record_payloads else None,
        )

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        config, store = self._require_store()
        common = {
            "action": action,
            "target": target,
            "content_digest": EvidenceStore.digest(content),
            "provider_callback_is_post_commit": True,
            "canonical_builtin_state": "committed",
            "provider_is_admission_authority": False,
        }
        if os.environ.get("AGENT_MEMORY_HERMES_TEST_MIRROR_FAILURE") == "1":
            self._last_projection_state = {
                "canonical_builtin_state": "committed",
                "external_projection": "failed",
                "settled": False,
                "quiescent": False,
                "rollback_claimed": False,
            }
            store.append(
                "provider_memory_mirror_failed",
                mode=config.mode,
                hermes_revision=self._observed_revision,
                metadata={**common, **self._last_projection_state},
                payload={"content": content, "metadata": metadata} if config.record_payloads else None,
            )
            raise RuntimeError("injected Agent Memory provider mirror failure")

        self._last_projection_state = {
            "canonical_builtin_state": "committed",
            "external_projection": "observed",
            "settled": True,
            "quiescent": True,
            "rollback_claimed": False,
        }
        store.append(
            "provider_memory_mirror_observed",
            mode=config.mode,
            hermes_revision=self._observed_revision,
            metadata={**common, **self._last_projection_state},
            payload={"content": content, "metadata": metadata} if config.record_payloads else None,
        )

    def on_session_end(self, messages: List[Dict[str, Any]]) -> None:
        config, store = self._require_store()
        store.append(
            "provider_session_end",
            mode=config.mode,
            hermes_revision=self._observed_revision,
            metadata={"session_id": self._session_id, "message_count": len(messages)},
        )

    def on_session_switch(
        self,
        new_session_id: str,
        *,
        parent_session_id: str = "",
        reset: bool = False,
        rewound: bool = False,
        **kwargs: Any,
    ) -> None:
        config, store = self._require_store()
        store.append(
            "provider_session_switch",
            mode=config.mode,
            hermes_revision=self._observed_revision,
            metadata={
                "old_session_id": self._session_id,
                "new_session_id": new_session_id,
                "parent_session_id": parent_session_id,
                "reset": reset,
                "rewound": rewound,
            },
        )
        self._session_id = new_session_id

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        return []

    def backup_paths(self) -> List[str]:
        if self._store is not None:
            return self._store.backup_paths()
        if self._hermes_home is not None:
            return [str(self._hermes_home / "agent-memory")]
        return []

    def shutdown(self) -> None:
        if self._config is None or self._store is None:
            return
        self._store.append(
            "provider_shutdown",
            mode=self._config.mode,
            hermes_revision=self._observed_revision,
            metadata={"session_id": self._session_id},
        )

    def get_config_schema(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": "mode",
                "description": "Agent Memory integration mode. Strict is reported unsupported at this Hermes profile.",
                "required": True,
                "default": "observe",
                "choices": ["observe", "govern", "strict"],
                "type": "text",
            },
            {
                "key": "governor_command",
                "description": "External JSON admission command used by govern mode.",
                "required": False,
                "default": "",
                "type": "text",
            },
            {
                "key": "governor_required",
                "description": "Fail closed when the governor is absent, unavailable, or invalid.",
                "required": True,
                "default": True,
                "type": "boolean",
            },
            {
                "key": "record_payloads",
                "description": "Persist raw memory/skill payloads in local evidence instead of hashes only.",
                "required": True,
                "default": False,
                "type": "boolean",
            },
        ]

    def save_config(self, values: Dict[str, Any], hermes_home: str) -> None:
        config = IntegrationConfig.from_mapping(values)
        save_config(hermes_home, config)

    @property
    def last_projection_state(self) -> dict[str, Any] | None:
        return dict(self._last_projection_state) if self._last_projection_state else None


def register_memory(ctx) -> None:
    ctx.register_memory_provider(lambda: AgentMemoryProvider())
