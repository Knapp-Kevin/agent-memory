"""Sprint 3a: the layered package layout is real, and the old paths are the same objects.

The layer order, the module table and the top-level residents are read from
``scripts/restructure_package.py`` -- the mover -- so this test cannot be
written to a different layout than the one the mover produces.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PACKAGE = REPO / "reference" / "agentmem_ref"
sys.path.insert(0, str(REPO / "reference"))


def _mover():
    spec = importlib.util.spec_from_file_location(
        "restructure_package", REPO / "scripts" / "restructure_package.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MOVER = _mover()
TABLE = MOVER.assignment()
ORDER = MOVER.LAYER_ORDER


def _relative_targets(path: Path, layer: str) -> set[str]:
    """Layers reached by the module's relative imports (incl. lazy, in-function ones)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    layers: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or node.level == 0:
            continue
        if node.level == 1:  # from . import x / from .x import y  -> same layer
            base = node.module.split(".")[0] if node.module else None
            if base is None:
                for alias in node.names:
                    layers.add(TABLE.get(alias.name, layer))
            else:
                layers.add(TABLE.get(base, layer))
        elif node.level == 2:  # from ..<layer> import x / from .._paths import y
            base = node.module.split(".")[0] if node.module else None
            if base in ORDER:
                layers.add(base)
            elif base == "_paths":
                continue
            else:
                raise AssertionError(f"{path.name}: unexpected relative import {ast.dump(node)}")
        else:
            raise AssertionError(f"{path.name}: relative import too deep")
    return layers


class LayoutMatchesMover(unittest.TestCase):
    def test_check_reports_layout_matches_table(self):
        self.assertEqual(MOVER.problems(PACKAGE), [])

    def test_every_alias_is_the_identical_object(self):
        for mod, layer in TABLE.items():
            with self.subTest(module=mod):
                try:
                    old = importlib.import_module(f"agentmem_ref.{mod}")
                except ModuleNotFoundError as exc:
                    if exc.name is None or exc.name.split(".")[0] == "agentmem_ref":
                        raise
                    # The real module needs an optional third-party dependency that
                    # this environment does not carry (e.g. the numpy benchmarks under
                    # the pinned CI requirements). The alias cannot be imported, so
                    # identity is proven statically: the alias file is byte-for-byte
                    # the mover's alias source, which is a sys.modules rebind.
                    alias = (PACKAGE / f"{mod}.py").read_text(encoding="utf-8")
                    self.assertEqual(alias, MOVER.alias_source(mod, layer))
                    self.skipTest(f"optional dependency not installed: {exc.name}")
                new = importlib.import_module(f"agentmem_ref.{layer}.{mod}")
                self.assertIs(old, new)
                self.assertIs(getattr(importlib.import_module("agentmem_ref"), mod), new)

    def test_monkeypatch_through_alias_reaches_the_evaluator(self):
        import agentmem_ref.policy as via_alias
        from agentmem_ref.core import policy as real

        saved = via_alias._HIGH_RISK
        try:
            via_alias._HIGH_RISK = ("medium", "high", "critical")
            self.assertEqual(real.strength_ladder_for("medium"), real.strength_ladder_for("high"))
        finally:
            via_alias._HIGH_RISK = saved

    def test_no_layer_imports_a_later_layer(self):
        rank = {layer: i for i, layer in enumerate(ORDER)}
        offenders = []
        for mod, layer in TABLE.items():
            for target in _relative_targets(PACKAGE / layer / f"{mod}.py", layer):
                if rank[target] > rank[layer]:
                    offenders.append(f"{layer}/{mod} -> {target}")
        self.assertEqual(offenders, [])

    def test_init_does_not_route_through_aliases(self):
        tree = ast.parse((PACKAGE / "__init__.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.level:
                self.assertIn(node.module.split(".")[0], ORDER, ast.dump(node))
        import agentmem_ref

        self.assertEqual(
            agentmem_ref.__all__, ["adapter", "governance_projection", "policy", "receipts", "substrate", "surface"]
        )

    def test_top_level_residents(self):
        for name in MOVER.STAYS:
            self.assertTrue((PACKAGE / f"{name}.py").is_file(), name)
            self.assertNotIn(name, TABLE)
        # _schemas/ is build-time package data (setup.py copies schemas/ into the wheel);
        # its resolution is proven out of tree by the wheel smoke, not here.

    def test_no_depth_coupled_path_resolution_remains(self):
        offenders = [
            p.relative_to(PACKAGE)
            for p in PACKAGE.rglob("*.py")
            if p.stem != "_paths" and "Path(__file__).resolve().parents[" in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(offenders, [])
        from agentmem_ref import receipts

        self.assertEqual(receipts.schema_dir(), REPO / "schemas")

    def test_crg_states_its_doctrine(self):
        doc = importlib.import_module("agentmem_ref.crg").__doc__
        self.assertIn("Code Reality Graph", doc)
        self.assertIn("CodeGenome", doc)
        self.assertIn("first-party", doc)


if __name__ == "__main__":
    unittest.main()
