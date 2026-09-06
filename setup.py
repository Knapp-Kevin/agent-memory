"""Build hook: copy the canonical root schemas into the package so wheels are self-contained.

Project metadata lives in pyproject.toml; this file only registers the build_py override.
"""

import shutil
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


class build_py(_build_py):
    def run(self):
        root = Path(__file__).resolve().parent
        target = root / "reference" / "agentmem_ref" / "_schemas"
        target.mkdir(exist_ok=True)
        copied = 0
        for schema in sorted((root / "schemas").glob("*.json")):
            shutil.copy2(schema, target / schema.name)
            copied += 1
        if copied == 0:
            raise RuntimeError(
                "no schema files found under schemas/; refusing to build an empty _schemas package"
            )
        super().run()


setup(cmdclass={"build_py": build_py})
