#!/usr/bin/env python3
"""Validate internal links in GitHub-Wiki-compatible Markdown source pages."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)")
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel"}


def iter_markdown_files(root: Path) -> list[Path]:
    return sorted(path for path in root.glob("*.md") if path.is_file())


def normalize_target(raw_target: str) -> str | None:
    target = raw_target.strip().strip("<>")
    if not target or target.startswith("#"):
        return None

    parsed = urlsplit(target)
    if parsed.scheme.lower() in EXTERNAL_SCHEMES or parsed.netloc:
        return None

    path = unquote(parsed.path).strip()
    if not path:
        return None

    return path


def resolve_wiki_target(root: Path, source: Path, target: str) -> Path:
    candidate = (source.parent / target).resolve()

    if candidate.suffix:
        return candidate

    # GitHub Wiki page links are commonly extensionless, e.g. (PAMA).
    return candidate.with_suffix(".md")


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    files = iter_markdown_files(root)

    if not files:
        return [f"No Markdown Wiki source files found in {root}"]

    for source in files:
        text = source.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            label, raw_target = match.groups()
            target = normalize_target(raw_target)
            if target is None:
                continue

            resolved = resolve_wiki_target(root, source, target)
            try:
                resolved.relative_to(root)
            except ValueError:
                errors.append(
                    f"{source.relative_to(root)}: link '{label}' escapes wiki-src: {raw_target}"
                )
                continue

            if not resolved.exists():
                errors.append(
                    f"{source.relative_to(root)}: missing target for '{label}': "
                    f"{raw_target} -> {resolved.relative_to(root)}"
                )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default="wiki-src", help="Wiki source directory")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"Wiki source directory not found: {root}", file=sys.stderr)
        return 2

    errors = validate(root)
    if errors:
        print("Wiki link validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Wiki links valid: {len(iter_markdown_files(root))} Markdown files checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
