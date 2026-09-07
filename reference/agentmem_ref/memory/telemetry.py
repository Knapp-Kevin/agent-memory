"""Privacy-minimized telemetry projection for Agent Memory audit events.

Canonical audit events remain the reconstructable evidence surface. Telemetry is
an explicitly lossy derived projection for operational correlation. It carries
no raw memory content and is not authoritative for memory semantics, lifecycle,
or governance decisions.
"""

from __future__ import annotations

import hashlib
import hmac

from ..core import receipts

PROFILE = "agent-memory-telemetry-minimized"
VERSION = "1.0.0"


def _opaque_ref(key: bytes, value: str) -> str:
    digest = hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"hmac-sha256:{digest}"


class TelemetryProjector:
    """Project a canonical audit event into a strict content-free span shape."""

    def __init__(self, key: bytes, key_id: str = "local") -> None:
        if len(key) < 16:
            raise ValueError("telemetry HMAC key must be at least 16 bytes")
        if not key_id:
            raise ValueError("telemetry key_id must be non-empty")
        self._key = key
        self.key_id = key_id

    def memory_ref(self, memory_id: str) -> str:
        """Resolve one raw memory id into this key generation's opaque reference."""
        if not memory_id:
            raise ValueError("memory_id must be non-empty")
        return _opaque_ref(self._key, memory_id)

    def project(self, event: dict) -> dict:
        receipts.validate("memory-audit-event.schema.json", event)

        attrs: dict[str, object] = {
            "am.event_ref": _opaque_ref(self._key, event["event_id"]),
            "am.event_type": event["event_type"],
            "am.event_version": event["event_version"],
            "am.component": event["component"],
            "am.payload_present": "payload" in event,
            "am.signal_present": "signal" in event,
            "am.authority_present": "authority" in event,
            "am.sensitivity_count": len(event.get("sensitivity", ())),
        }

        for source_key, target_key in (
            ("memory_id", "am.memory_ref"),
            ("actor", "am.actor_ref"),
            ("principal", "am.principal_ref"),
            ("correlation_id", "am.correlation_ref"),
            ("causation_id", "am.causation_ref"),
            ("policy_version", "am.policy_ref"),
            ("receipt_ref", "am.receipt_ref"),
            ("ledger_ref", "am.ledger_ref"),
        ):
            value = event.get(source_key)
            if isinstance(value, str) and value:
                attrs[target_key] = _opaque_ref(self._key, value)

        projection = {
            "profile": PROFILE,
            "version": VERSION,
            "key_id": self.key_id,
            "span_name": f"agent_memory.{event['event_type']}",
            "timestamp": event["timestamp"],
            "attributes": attrs,
        }
        receipts.validate("telemetry-projection.schema.json", projection)
        return projection
