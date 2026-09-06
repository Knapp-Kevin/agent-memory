#!/usr/bin/env python3
"""Prepare the minimal Python Worker bundle from canonical Agent Memory sources.

The Worker must use the exact Agent Memory/PAMA provider semantics rather than a
second implementation. This script copies the canonical stdlib-only sources into
the Worker source tree and applies one packaging-only change: the stateful
``GovernedMemoryAdapter`` import becomes type-checking-only so Cloudflare does
not pull the unrelated runtime dependency graph into a decision-only Worker.

The transformation is deliberately exact-match and fail-closed. If the
canonical provider import shape changes, this script refuses to prepare a
bundle until a human reviews the new boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

EXAMPLE_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXAMPLE_DIR.parents[1]
CANONICAL_DIR = REPO_ROOT / "reference" / "agentmem_ref"
OUTPUT_DIR = EXAMPLE_DIR / "src" / "agentmem_ref"

SOURCE_FILES = (
    "policy.py",
    "dashclaw_external_verdict.py",
    "dashclaw_authority.py",
)

_TYPING_IMPORT = "from typing import Any, Callable, Iterable, Mapping\n"
_PORTABLE_TYPING_IMPORT = "from typing import TYPE_CHECKING, Any, Callable, Iterable, Mapping\n"
_ADAPTER_IMPORT = "from .adapter import GovernedMemoryAdapter\n"
_PORTABLE_ADAPTER_IMPORT = "if TYPE_CHECKING:\n    from .adapter import GovernedMemoryAdapter\n"


def _sha256(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def _portable_provider(source: str) -> str:
    if source.count(_TYPING_IMPORT) != 1:
        raise RuntimeError("canonical provider typing import changed; review packaging boundary")
    if source.count(_ADAPTER_IMPORT) != 1:
        raise RuntimeError("canonical provider adapter import changed; review packaging boundary")
    source = source.replace(_TYPING_IMPORT, _PORTABLE_TYPING_IMPORT)
    source = source.replace(_ADAPTER_IMPORT, _PORTABLE_ADAPTER_IMPORT)
    return source


def _render_sources() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    rendered: dict[str, str] = {}
    manifest: dict[str, dict[str, str]] = {}

    for name in SOURCE_FILES:
        source_path = CANONICAL_DIR / name
        raw = source_path.read_bytes()
        text = raw.decode("utf-8")
        prepared = _portable_provider(text) if name == "dashclaw_external_verdict.py" else text
        compile(prepared, str(source_path), "exec")
        rendered[name] = prepared
        manifest[name] = {
            "canonical_sha256": _sha256(raw),
            "prepared_sha256": _sha256(prepared.encode("utf-8")),
        }

    return rendered, manifest


def _write_package(target: Path) -> dict[str, dict[str, str]]:
    rendered, manifest = _render_sources()
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    (target / "__init__.py").write_text(
        '"""Generated minimal Agent Memory provider package for Cloudflare proving."""\n',
        encoding="utf-8",
    )
    for name, content in rendered.items():
        (target / name).write_text(content, encoding="utf-8")
    (target / "SOURCE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _is_agentmem_module(module_name: str) -> bool:
    return module_name == "agentmem_ref" or module_name.startswith("agentmem_ref.")


def _import_check(root: Path) -> None:
    """Import the prepared portable copies, then leave `sys.modules` as found.

    The prepared copies must not linger in `sys.modules` — they shadow the
    canonical package. But evicting every `agentmem_ref` module without putting
    the originals back is not neutral either: any caller that already holds a
    reference to a canonical function keeps the *old* module's globals, while a
    later `mock.patch("agentmem_ref.x.y")` re-imports and patches a *new* module
    object. The patch then targets something the running code never consults.

    That is not hypothetical. Run in one process with the rest of the suite, the
    purge made five `test_temporal_trust` cases fail: they patch
    `agentmem_ref.temporal_trust.public_key_digest`, the patch landed on a fresh
    module, and the stale bound function called the real digest with a dummy key.

    So snapshot what was loaded, and restore it afterwards.
    """
    preserved = {
        name: module for name, module in sys.modules.items() if _is_agentmem_module(name)
    }
    sys.path.insert(0, str(root))
    try:
        for module_name in (
            "agentmem_ref.policy",
            "agentmem_ref.dashclaw_external_verdict",
            "agentmem_ref.dashclaw_authority",
        ):
            sys.modules.pop(module_name, None)
            importlib.import_module(module_name)
    finally:
        sys.path.remove(str(root))
        for module_name in list(sys.modules):
            if _is_agentmem_module(module_name):
                sys.modules.pop(module_name, None)
        sys.modules.update(preserved)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify portable preparation/import without changing the working tree",
    )
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="agent-memory-dashclaw-cf-") as temp:
            root = Path(temp)
            manifest = _write_package(root / "agentmem_ref")
            _import_check(root)
    else:
        manifest = _write_package(OUTPUT_DIR)
        _import_check(EXAMPLE_DIR / "src")

    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
