from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from agentmem_ref.cli import main
from agentmem_ref.discovery import DiscoveryInputError, discover_configuration, load_probe_manifest
from agentmem_ref.doctor import diagnose, discover_configuration_file, load_configuration_value


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "reference" / "fixtures" / "runtime-configuration"
COMPOSED = FIXTURES / "reference-composed-runtime.json"
PROBES = FIXTURES / "reference-provider-probes.json"


class ProviderDiscoveryTests(unittest.TestCase):
    def test_discovery_uses_real_declared_signals_without_mutating_configuration(self) -> None:
        before = COMPOSED.read_bytes()
        report = discover_configuration_file(COMPOSED, probe_path=PROBES)
        after = COMPOSED.read_bytes()

        self.assertEqual(before, after)
        self.assertEqual(report["probe_count"], 3)
        self.assertEqual(report["status_counts"]["available"], 2)
        self.assertEqual(report["status_counts"]["unavailable"], 1)
        self.assertEqual(report["startability"], "proven_for_declared_probes")
        self.assertFalse(report["mutated_configuration"])
        self.assertEqual(report["authority_effect"], "none")

        by_id = {item["probe_id"]: item for item in report["results"]}
        self.assertEqual(by_id["reference-python-runtime"]["status"], "available")
        self.assertTrue(by_id["reference-python-runtime"]["evidence"]["resolved"])
        self.assertEqual(by_id["reference-json-import"]["status"], "available")
        self.assertEqual(by_id["reference-unavailable-optional"]["status"], "unavailable")

    def test_required_unavailable_probe_blocks_declared_startability(self) -> None:
        value = load_configuration_value(COMPOSED)
        manifest = {
            "schema_version": "1.0.0",
            "probes": [
                {
                    "probe_id": "required-missing-provider",
                    "subject_kind": "component",
                    "subject_id": "reference-governed-memory",
                    "probe_kind": "executable",
                    "target": "agent-memory-definitely-not-a-real-required-provider",
                    "required_for_startability": True,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probes.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            report = discover_configuration(value, probe_path=path)
        self.assertEqual(report["startability"], "blocked_by_required_probe")
        self.assertEqual(report["results"][0]["status"], "unavailable")
        self.assertFalse(report["results"][0]["startability_satisfied"])

    def test_probe_manifest_cannot_reference_unconfigured_subject(self) -> None:
        value = load_configuration_value(COMPOSED)
        manifest = {
            "schema_version": "1.0.0",
            "probes": [
                {
                    "probe_id": "unknown-component",
                    "subject_kind": "component",
                    "subject_id": "not-configured",
                    "probe_kind": "executable",
                    "target": "python",
                    "required_for_startability": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probes.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(DiscoveryInputError):
                load_probe_manifest(path, config_value=value)

    def test_probe_manifest_rejects_secret_reference_targets(self) -> None:
        value = load_configuration_value(COMPOSED)
        manifest = {
            "schema_version": "1.0.0",
            "probes": [
                {
                    "probe_id": "secret-target",
                    "subject_kind": "component",
                    "subject_id": "reference-governed-memory",
                    "probe_kind": "filesystem_path",
                    "target": "env://MEMORY_DSN",
                    "required_for_startability": False,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "probes.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(DiscoveryInputError):
                load_probe_manifest(path, config_value=value)

    def test_doctor_only_probes_when_explicitly_requested(self) -> None:
        baseline = diagnose(COMPOSED)
        observed = diagnose(COMPOSED, probe=True, probe_path=PROBES)

        self.assertEqual(baseline["provider_availability"]["status"], "not_probed")
        self.assertEqual(observed["provider_availability"]["status"], "partial")
        self.assertEqual(
            observed["provider_availability"]["startability"],
            "proven_for_declared_probes",
        )
        self.assertEqual(observed["provider_availability"]["status_counts"]["unavailable"], 1)
        self.assertEqual(observed["operational_readiness"], "provider_probe_observed_state_not_checked")
        self.assertEqual(observed["authority_effect"], "none")

    def test_cli_discover_is_machine_readable(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([
                "discover",
                "--config",
                str(COMPOSED),
                "--probes",
                str(PROBES),
                "--json",
            ])
        self.assertEqual(code, 0)
        report = json.loads(output.getvalue())
        self.assertEqual(report["command"], "discover")
        self.assertEqual(report["startability"], "proven_for_declared_probes")
        self.assertEqual(report["authority_effect"], "none")

    def test_cli_doctor_rejects_probe_manifest_without_probe_flag(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = main([
                "doctor",
                "--config",
                str(COMPOSED),
                "--probes",
                str(PROBES),
                "--json",
            ])
        self.assertEqual(code, 2)
        report = json.loads(output.getvalue())
        self.assertEqual(report["status"], "refused")
        self.assertEqual(report["authority_effect"], "none")


if __name__ == "__main__":
    unittest.main()
