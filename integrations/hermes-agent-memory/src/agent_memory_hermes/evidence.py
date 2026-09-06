"""Append-only local evidence for Hermes integration events."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Mapping
import uuid

from . import HERMES_COMMIT, INTEGRATION_PROFILE, INTEGRATION_VERSION
from .config import integration_dir


class EvidenceStore:
    """Profile-scoped JSONL evidence store.

    Payloads are hashed by default. ``record_payloads`` must be explicitly
    enabled to persist raw candidate/tool content.
    """

    def __init__(self, hermes_home: str | Path, *, record_payloads: bool = False):
        self.root = integration_dir(hermes_home)
        self.path = self.root / "events.jsonl"
        self.record_payloads = record_payloads
        self._lock = threading.Lock()
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def digest(value: Any) -> str:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    def append(
        self,
        event_type: str,
        *,
        mode: str,
        hermes_revision: str,
        metadata: Mapping[str, Any] | None = None,
        payload: Any = None,
    ) -> dict[str, Any]:
        record: dict[str, Any] = {
            "schema_version": "1.0.0",
            "event_id": str(uuid.uuid4()),
            "observed_at_unix_ms": int(time.time() * 1000),
            "event_type": event_type,
            "mode": mode,
            "integration_profile": INTEGRATION_PROFILE,
            "integration_version": INTEGRATION_VERSION,
            "hermes_revision": hermes_revision,
            "expected_hermes_revision": HERMES_COMMIT,
            "metadata": dict(metadata or {}),
            "payload_digest": self.digest(payload) if payload is not None else None,
            "payload_recorded": bool(payload is not None and self.record_payloads),
            "authority_effect": "none",
        }
        if payload is not None and self.record_payloads:
            record["payload"] = payload
        rendered = json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n"
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(rendered)
                handle.flush()
                os.fsync(handle.fileno())
        return record

    def backup_paths(self) -> list[str]:
        return [str(self.root)]
