from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from agentmem_ref.code_graph_qualification import codegenome_subject
from agentmem_ref.component_failure_probe import ProviderProbeError, probe_missing_executable


class ComponentFailureProbeTests(unittest.TestCase):
    def test_missing_executable_preserves_real_os_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            missing = root / "provider-that-does-not-exist"
            raw = root / "raw.json"
            normalized = root / "normalized.json"
            probe = probe_missing_executable(
                subject=codegenome_subject(),
                executable=missing,
                args=("--version",),
                raw_path=raw,
                normalized_path=normalized,
                trace_ref="trace:test-unavailable",
            )

            raw_payload = json.loads(raw.read_text())
            normalized_payload = json.loads(normalized.read_text())
            self.assertEqual(raw_payload["exception_type"], "FileNotFoundError")
            self.assertEqual(raw_payload["errno"], 2)
            self.assertEqual(normalized_payload["failure_result"], "provider_unavailable")
            self.assertEqual(normalized_payload["currentness"], "unavailable")
            self.assertEqual(normalized_payload["authority_effect"], "none")
            self.assertEqual(probe.failure.failure_result, "provider_unavailable")
            self.assertEqual(probe.adapter_result.failure_result, "provider_unavailable")
            self.assertEqual(probe.adapter_result.currentness, "unavailable")
            self.assertEqual(probe.adapter_result.authority_effect, "none")

    def test_available_executable_cannot_be_laundered_into_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaises(ProviderProbeError):
                probe_missing_executable(
                    subject=codegenome_subject(),
                    executable=Path(sys.executable),
                    args=("--version",),
                    raw_path=root / "raw.json",
                    normalized_path=root / "normalized.json",
                    trace_ref="trace:test-available",
                )
            self.assertFalse((root / "raw.json").exists())
            self.assertFalse((root / "normalized.json").exists())


if __name__ == "__main__":
    unittest.main()
