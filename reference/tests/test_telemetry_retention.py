"""P8 telemetry retention, expiry, and rotation-safe deletion tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.telemetry import TelemetryProjector  # noqa: E402
from agentmem_ref.telemetry_retention import TelemetryStore  # noqa: E402


def event(event_id: str, memory_id: str, timestamp: str = "2026-08-11T20:00:00Z") -> dict:
    return {
        "schema_version": "1.0.0",
        "event_id": event_id,
        "event_type": "memory.recalled",
        "event_version": "1.0.0",
        "timestamp": timestamp,
        "memory_id": memory_id,
        "component": "runtime-memory",
        "correlation_id": f"workflow:{event_id}",
        "payload": {"content": f"SECRET:{memory_id}"},
    }


class TelemetryRetentionTests(unittest.TestCase):
    def setUp(self):
        self.old = TelemetryProjector(b"old-telemetry-key-material-0001", key_id="telemetry-2026-07")
        self.new = TelemetryProjector(b"new-telemetry-key-material-0002", key_id="telemetry-2026-08")

    def test_targeted_purge_removes_only_requested_memory(self):
        store = TelemetryStore()
        store.append(self.new.project(event("evt-a", "mem:a")), expires_at="2026-09-01T00:00:00Z")
        store.append(self.new.project(event("evt-b", "mem:b")), expires_at="2026-09-01T00:00:00Z")

        result = store.purge_memory("mem:a", projectors={self.new.key_id: self.new})

        self.assertTrue(result.complete)
        self.assertEqual(result.removed_count, 1)
        remaining = store.records()
        self.assertEqual(len(remaining), 1)
        self.assertEqual(remaining[0].projection["attributes"]["am.memory_ref"], self.new.memory_ref("mem:b"))

    def test_key_rotation_purge_removes_same_memory_from_all_known_generations(self):
        store = TelemetryStore()
        store.append(self.old.project(event("evt-old", "mem:a")), expires_at="2026-09-01T00:00:00Z")
        store.append(self.new.project(event("evt-new", "mem:a")), expires_at="2026-09-01T00:00:00Z")
        store.append(self.old.project(event("evt-other", "mem:b")), expires_at="2026-09-01T00:00:00Z")

        result = store.purge_memory(
            "mem:a",
            projectors={self.old.key_id: self.old, self.new.key_id: self.new},
        )

        self.assertTrue(result.complete)
        self.assertEqual(result.removed_count, 2)
        self.assertEqual(len(store.records()), 1)
        self.assertEqual(store.records()[0].projection["key_id"], self.old.key_id)

    def test_missing_retired_key_generation_makes_purge_incomplete(self):
        store = TelemetryStore()
        store.append(self.old.project(event("evt-old", "mem:a")), expires_at="2026-09-01T00:00:00Z")
        store.append(self.new.project(event("evt-new", "mem:a")), expires_at="2026-09-01T00:00:00Z")

        result = store.purge_memory("mem:a", projectors={self.new.key_id: self.new})

        self.assertFalse(result.complete)
        self.assertEqual(result.removed_count, 1)
        self.assertEqual(result.unresolved_key_ids, (self.old.key_id,))
        self.assertEqual(len(store.records()), 1)
        self.assertEqual(store.records()[0].projection["key_id"], self.old.key_id)

    def test_expiry_removes_records_without_memory_lookup(self):
        store = TelemetryStore()
        store.append(self.new.project(event("evt-expired", "mem:a")), expires_at="2026-08-11T21:00:00Z")
        store.append(self.new.project(event("evt-live", "mem:b")), expires_at="2026-08-13T00:00:00Z")

        removed = store.purge_expired(now="2026-08-12T00:00:00Z")

        self.assertEqual(removed, 1)
        self.assertEqual(len(store.records()), 1)

    def test_store_contains_no_raw_memory_id_or_hmac_key_material(self):
        store = TelemetryStore()
        projection = self.new.project(event("evt-secret", "mem:secret-user-record"))
        store.append(projection, expires_at="2026-09-01T00:00:00Z")

        serialized = json.dumps(
            [
                {"projection": record.projection, "expires_at": record.expires_at}
                for record in store.records()
            ],
            sort_keys=True,
        )
        self.assertNotIn("mem:secret-user-record", serialized)
        self.assertNotIn("SECRET:mem:secret-user-record", serialized)
        self.assertNotIn("new-telemetry-key-material-0002", serialized)
        self.assertIn(self.new.key_id, serialized)


if __name__ == "__main__":
    unittest.main()
