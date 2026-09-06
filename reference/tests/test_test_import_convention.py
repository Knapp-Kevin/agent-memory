"""Sprint 3b: no test module under ``reference/tests/`` uses a package-relative import.

CI loads these modules three ways: ``discover -s reference/tests -t reference``
(as ``tests.X``), ``python -m unittest reference.tests.X``, and ``discover``
without ``-t`` (as top-level ``X``). A relative import resolves under the first
two and fails under the third, which only two path-triggered workflows run --
so a relative import can sit green on ``main`` until one of them fires. This
guard makes the same mistake fail under every style.

Only ``test_*.py`` is scanned: those are the modules unittest imports top-level.
Helpers such as ``qualified_fixtures.py`` are always imported as
``tests.<helper>``, so a relative import inside them resolves everywhere.
"""

from __future__ import annotations

import ast
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent


def relative_imports(path: Path) -> list[str]:
    """The package-relative ``from`` imports in a module, as source statements."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        ast.unparse(node)
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.level > 0
    ]


class TestImportConvention(unittest.TestCase):
    def test_helper_reports_a_relative_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            relative = Path(tmp) / "mod_relative.py"
            relative.write_text("import os\nfrom .helper import x\n", encoding="utf-8")
            absolute = Path(tmp) / "mod_absolute.py"
            absolute.write_text("import os\nfrom tests.helper import x\n", encoding="utf-8")

            self.assertEqual(relative_imports(relative), ["from .helper import x"])
            self.assertEqual(relative_imports(absolute), [])

    def test_no_test_module_uses_a_relative_import(self):
        offenders = [
            f"{path.name}:{statement}"
            for path in sorted(TESTS_DIR.glob("test_*.py"))
            for statement in relative_imports(path)
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
