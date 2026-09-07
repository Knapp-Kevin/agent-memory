#!/usr/bin/env python3
"""Validate local Markdown links in selected repository documents.

External URLs, mailto links, and same-document anchors are intentionally ignored.
The check verifies that relative file or directory targets exist in the repository.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote

LINK_RE = re.compile(r"!?(?<!\\)\[[^\]]*\]\(([^)]+)\)")


def normalize_target(raw: str) -> str | None:
    target = raw.strip()
    if not target:
        return None

    # Markdown may use <target> syntax and may append an optional title.
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    elif " " in target and not target.startswith(("http://", "https://")):
        target = target.split(" ", 1)[0]

    if target.startswith(("http://", "https://", "mailto:", "tel:", "data:")):
        return None
    if target.startswith("#"):
        return None

    target = target.split("#", 1)[0].split("?", 1)[0]
    target = unquote(target)
    return target or None


def validate_file(root: Path, markdown_path: Path) -> list[str]:
    errors: list[str] = []
    text = markdown_path.read_text(encoding="utf-8")

    for line_number, line in enumerate(text.splitlines(), start=1):
        for match in LINK_RE.finditer(line):
            target = normalize_target(match.group(1))
            if target is None:
                continue

            resolved = (markdown_path.parent / target).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                errors.append(
                    f"{markdown_path.relative_to(root)}:{line_number}: link escapes repository: {target}"
                )
                continue

            if not resolved.exists():
                errors.append(
                    f"{markdown_path.relative_to(root)}:{line_number}: missing local target: {target}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate local Markdown links.")
    parser.add_argument("paths", nargs="+", help="Markdown files to validate.")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    errors: list[str] = []

    for raw in args.paths:
        path = (root / raw).resolve()
        if not path.exists():
            errors.append(f"{raw}: file does not exist")
            continue
        if not path.is_file():
            errors.append(f"{raw}: expected a file")
            continue
        errors.extend(validate_file(root, path))

    if errors:
        print("Markdown link validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated local links in {len(args.paths)} Markdown file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
