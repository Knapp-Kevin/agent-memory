"""Canonical schema resolution for receipts: source tree first, packaged copy second."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentmem_ref import receipts

ROOT = Path(__file__).resolve().parents[2]


class SchemaDirTests(unittest.TestCase):
    def test_schema_dir_prefers_source_tree(self):
        resolved = receipts.schema_dir()
        self.assertEqual(resolved, ROOT / "schemas")
        self.assertTrue((resolved / "decision-receipt.schema.json").is_file())

    def test_schema_dir_falls_back_to_packaged_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            packaged = Path(tmp) / "pkg"
            packaged.mkdir()
            (packaged / "t.schema.json").write_text("{}", encoding="utf-8")
            with patch.object(receipts, "_SOURCE_SCHEMAS", Path(tmp) / "missing"), patch.object(
                receipts, "_packaged_schemas", return_value=packaged
            ):
                self.assertEqual(receipts.schema_dir(), packaged)

    def test_schema_dir_raises_when_neither_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(receipts, "_SOURCE_SCHEMAS", Path(tmp) / "missing"), patch.object(
                receipts, "_packaged_schemas", return_value=Path(tmp) / "also-missing"
            ):
                with self.assertRaisesRegex(FileNotFoundError, "install the distribution"):
                    receipts.schema_dir()

    def test_validator_loads_through_schema_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            schema_root = Path(tmp)
            (schema_root / "t.schema.json").write_text(
                json.dumps({"type": "object", "required": ["x"]}), encoding="utf-8"
            )
            receipts._validator.cache_clear()
            self.addCleanup(receipts._validator.cache_clear)
            with patch.object(receipts, "schema_dir", return_value=schema_root):
                with self.assertRaisesRegex(ValueError, "x"):
                    receipts.validate("t.schema.json", {})
                self.assertIsNone(receipts.validate("t.schema.json", {"x": 1}))


if __name__ == "__main__":
    unittest.main()
