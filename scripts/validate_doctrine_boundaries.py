#!/usr/bin/env python3
"""Validate native-doctrine and implementation-reference boundaries.

This validator protects two repository decisions:

1. PAMA is native Agent Memory doctrine, not an external source-registry entry.
2. Private/adjacent product references must not drift into active doctrine without
   an explicit, separately reviewed implementation mapping decision.

Historical audit/governance records are excluded so the repository preserves its
actual change history rather than rewriting it to satisfy current terminology.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


TEXT_SUFFIXES = {".md", ".json", ".yml", ".yaml", ".txt"}
EXCLUDED_PREFIXES = (
    "docs/audits/",
    ".failsafe/",
)
EXCLUDED_FILES = {
    "scripts/validate_doctrine_boundaries.py",
}

# Constructed to keep the validator from matching its own source text.
DISALLOWED_ADJACENT_PRODUCT = "bi" + "cameral"


def is_active_text(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    if rel in EXCLUDED_FILES:
        return False
    if any(rel.startswith(prefix) for prefix in EXCLUDED_PREFIXES):
        return False
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    return True


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    pama_entry = root / "docs" / "pama" / "README.md"
    if not pama_entry.exists():
        errors.append("docs/pama/README.md: missing canonical native PAMA entry point")
    else:
        text = pama_entry.read_text(encoding="utf-8")
        required = (
            "Kevin R. Knapp",
            "native Agent Memory doctrine",
            "M0",
            "M5",
            "A0",
            "A5",
        )
        for token in required:
            if token not in text:
                errors.append(f"docs/pama/README.md: missing required native-doctrine marker {token!r}")

    registry_path = root / "sources" / "source-registry.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"sources/source-registry.json: cannot inspect registry: {exc}")
        registry = {}

    for index, record in enumerate(registry.get("sources", []) if isinstance(registry, dict) else []):
        if not isinstance(record, dict):
            continue
        searchable = " ".join(
            str(record.get(field, ""))
            for field in ("source_id", "title", "source_type", "repository", "provenance_note")
        ).lower()
        if "pama" in searchable:
            errors.append(
                f"sources/source-registry.json sources[{index}]: native PAMA doctrine must not be registered as an external source"
            )
        if DISALLOWED_ADJACENT_PRODUCT in searchable:
            errors.append(
                f"sources/source-registry.json sources[{index}]: adjacent private product must not be retained as source provenance without a new explicit value decision"
            )

    # Current decision: the adjacent private product adds no necessary value to
    # active Agent Memory doctrine. Historical audit records remain untouched.
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not is_active_text(path, root):
            continue
        rel = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if DISALLOWED_ADJACENT_PRODUCT in text.lower():
            errors.append(
                f"{rel}: contains an adjacent-product reference in active doctrine; remove it or change this validator through an explicit value-justified review"
            )

    source_index = root / "docs" / "08-source-material-index.md"
    if source_index.exists():
        index_text = source_index.read_text(encoding="utf-8")
        if "## Native Agent Memory doctrine" not in index_text:
            errors.append("docs/08-source-material-index.md: missing native-doctrine separation")
        if "PAMA is native Agent Memory governance doctrine" not in index_text:
            errors.append("docs/08-source-material-index.md: PAMA native provenance is not explicit")

    if errors:
        print("Doctrine-boundary validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Validated native PAMA provenance and active implementation-reference boundaries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
