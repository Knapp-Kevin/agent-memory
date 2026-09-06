"""P8 privacy-minimized telemetry projection tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.telemetry import TelemetryProjector  # noqa: E402


class TelemetryProjectionTests(unittest.TestCase):
    def setUp(self):
        self.projector = TelemetryProjector(b"telemetry-test-key-32-bytes-long")
        self.event = {
            "schema_version": "1.0.0",
            "event_id": "event:secret-decision-42",
            "event_type": "memory.authority_decided",
            "event_version": "1.0.0",
            "timestamp": "2026-08-11T20:00:00Z",
            "memory_id": "memory:user-alice-medical-secret",
            "actor": "employee:alice@example.com",
            "principal": "customer:patient-12345",
            "component": "governed-adapter",
            "correlation_id": "workflow:incident-red-team",
            "causation_id": "event:private-cause",
            "policy_version": "policy:prod-sensitive-v7",
            "sensitivity": ["credential", "medical"],
            "signal": {
                "signal_type": "sensitivity",
                "signal_semantics": "classifier_output",
                "signal_value": "RAW-SECRET-SIGNAL-VALUE",
                "estimator_id": "classifier:private",
                "estimator_version": "v9",
                "uncertainty": {"notes": "SECRET-UNCERTAINTY-NOTES"},
            },
            "authority": {
                "authority_refs": ["authority:secret-admin-role"],
                "permitted_actions": ["read_private_medical_memory"],
                "prohibited_actions": ["export_raw_secret"],
                "selected_action": "read_private_medical_memory",
                "selection_mode": "deterministic",
            },
            "payload": {
                "prompt": "TOP-SECRET-PROMPT-CONTENT",
                "memory_text": "TOP-SECRET-MEMORY-CONTENT",
                "credential": "password=hunter2",
            },
            "receipt_ref": "receipt:secret-42",
            "ledger_ref": "ledger:secret-42",
        }

    def test_projection_contains_only_allowlisted_shape_and_opaque_refs(self):
        projection = self.projector.project(self.event)
        attrs = projection["attributes"]
        self.assertEqual(projection["span_name"], "agent_memory.memory.authority_decided")
        self.assertEqual(attrs["am.event_type"], "memory.authority_decided")
        self.assertEqual(attrs["am.component"], "governed-adapter")
        self.assertTrue(attrs["am.payload_present"])
        self.assertTrue(attrs["am.signal_present"])
        self.assertTrue(attrs["am.authority_present"])
        self.assertEqual(attrs["am.sensitivity_count"], 2)
        for key in (
            "am.event_ref", "am.memory_ref", "am.actor_ref", "am.principal_ref",
            "am.correlation_ref", "am.causation_ref", "am.policy_ref",
            "am.receipt_ref", "am.ledger_ref",
        ):
            self.assertRegex(attrs[key], r"^hmac-sha256:[0-9a-f]{64}$")

    def test_shadow_memory_content_does_not_survive_serialization(self):
        serialized = json.dumps(self.projector.project(self.event), sort_keys=True)
        forbidden = [
            "TOP-SECRET-PROMPT-CONTENT",
            "TOP-SECRET-MEMORY-CONTENT",
            "password=hunter2",
            "RAW-SECRET-SIGNAL-VALUE",
            "SECRET-UNCERTAINTY-NOTES",
            "memory:user-alice-medical-secret",
            "employee:alice@example.com",
            "customer:patient-12345",
            "authority:secret-admin-role",
            "read_private_medical_memory",
            "export_raw_secret",
            "receipt:secret-42",
            "ledger:secret-42",
            "credential",
            "medical",
        ]
        for value in forbidden:
            self.assertNotIn(value, serialized)

    def test_same_identifier_correlates_under_same_key_without_revealing_raw_value(self):
        first = self.projector.project(self.event)
        second = self.projector.project(dict(self.event, event_id="event:other"))
        self.assertEqual(first["attributes"]["am.memory_ref"], second["attributes"]["am.memory_ref"])
        self.assertNotEqual(first["attributes"]["am.event_ref"], second["attributes"]["am.event_ref"])

    def test_different_telemetry_keys_break_cross_domain_linkability(self):
        first = self.projector.project(self.event)
        other = TelemetryProjector(b"different-telemetry-key-32-bytes").project(self.event)
        self.assertNotEqual(first["attributes"]["am.memory_ref"], other["attributes"]["am.memory_ref"])
        self.assertNotEqual(first["attributes"]["am.principal_ref"], other["attributes"]["am.principal_ref"])

    def test_short_hmac_key_is_rejected(self):
        with self.assertRaises(ValueError):
            TelemetryProjector(b"too-short")


if __name__ == "__main__":
    unittest.main()
