"""Sprint 3d (#365): runtime_config and discovery resolve their schemas through receipts.schema_dir().

Three states, driven through the two seams ``schema_dir()`` consults --
``receipts._SOURCE_SCHEMAS`` and ``receipts._packaged_schemas`` -- rather than
the filesystem: source tree present; source absent and the packaged copy
present (the installed-wheel state, in-process); neither. The installed-wheel
state is also proven from outside the checkout by ``cli-doctor.yml``'s
``wheel-install`` job; this module proves the resolvers take that path.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.core import receipts  # noqa: E402
from agentmem_ref.runtime import discovery, runtime_config  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "schemas"
RUNTIME_SCHEMA = "runtime-configuration.schema.json"
PROBE_SCHEMA = "provider-probes.schema.json"


@contextmanager
def _seams(source: Path, packaged: Path):
    """Point schema_dir() at explicit source and packaged directories."""
    with mock.patch.object(receipts, "_SOURCE_SCHEMAS", source), mock.patch.object(
        receipts, "_packaged_schemas", lambda: packaged
    ):
        yield


def _canonical(name: str) -> dict:
    return json.loads((SOURCE / name).read_text(encoding="utf-8"))


class SchemaResolution(unittest.TestCase):
    def test_source_tree_resolves_both_schemas(self):
        self.assertEqual(runtime_config._configuration_schema_path(), SOURCE / RUNTIME_SCHEMA)
        self.assertEqual(discovery._probe_schema_path(), SOURCE / PROBE_SCHEMA)
        self.assertTrue(runtime_config._configuration_schema()["$id"].endswith(RUNTIME_SCHEMA))
        self.assertTrue(discovery._probe_schema()["$id"].endswith(PROBE_SCHEMA))

    def test_packaged_copy_resolves_when_source_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            packaged = Path(tmp) / "_schemas"
            packaged.mkdir()
            for name in (RUNTIME_SCHEMA, PROBE_SCHEMA):
                shutil.copy(SOURCE / name, packaged / name)
            with _seams(Path(tmp) / "no-source", packaged):
                self.assertEqual(runtime_config._configuration_schema_path(), packaged / RUNTIME_SCHEMA)
                self.assertEqual(discovery._probe_schema_path(), packaged / PROBE_SCHEMA)
                self.assertEqual(runtime_config._configuration_schema(), _canonical(RUNTIME_SCHEMA))
                self.assertEqual(discovery._probe_schema(), _canonical(PROBE_SCHEMA))

    def test_neither_source_nor_package_raises_the_module_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _seams(Path(tmp) / "no-source", Path(tmp) / "no-package"):
                with self.assertRaises(runtime_config.RuntimeConfigurationError) as rc:
                    runtime_config._configuration_schema()
                with self.assertRaises(discovery.DiscoveryInputError) as di:
                    discovery._probe_schema()
        self.assertIn("install", str(rc.exception))
        self.assertIn("install", str(di.exception))


if __name__ == "__main__":
    unittest.main()
