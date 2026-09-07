#!/usr/bin/env python3
"""Validate repository-native SVG documentation assets.

This intentionally stays small. It checks structural accessibility and light/dark
semantic parity without introducing a visual build system or pretending that
static validation can prove doctrinal accuracy.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def semantic_text(root: ET.Element) -> list[tuple[str, str]]:
    """Return reader-facing SVG text while ignoring theme/style implementation."""
    values: list[tuple[str, str]] = []
    for element in root.iter():
        name = local_name(element.tag)
        if name not in {"title", "desc", "text"}:
            continue
        text = " ".join("".join(element.itertext()).split())
        values.append((name, text))
    return values


def parse_svg(path: Path) -> ET.Element:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"invalid XML: {exc}") from exc


def validate_svg(path: Path) -> tuple[ET.Element | None, list[str]]:
    errors: list[str] = []
    try:
        root = parse_svg(path)
    except ValueError as exc:
        return None, [f"{path}: {exc}"]

    if local_name(root.tag) != "svg":
        errors.append(f"{path}: root element must be <svg>")

    if root.get("role") != "img":
        errors.append(f"{path}: root <svg> must declare role=\"img\"")

    labelled_by = root.get("aria-labelledby", "").split()
    if len(labelled_by) < 2:
        errors.append(f"{path}: aria-labelledby must reference both title and description")

    titles = [e for e in root.iter() if local_name(e.tag) == "title"]
    descs = [e for e in root.iter() if local_name(e.tag) == "desc"]
    if not titles or not " ".join("".join(titles[0].itertext()).split()):
        errors.append(f"{path}: SVG must contain a non-empty <title>")
    if not descs or not " ".join("".join(descs[0].itertext()).split()):
        errors.append(f"{path}: SVG must contain a non-empty <desc>")

    ids = {e.get("id") for e in root.iter() if e.get("id")}
    for ref in labelled_by:
        if ref not in ids:
            errors.append(f"{path}: aria-labelledby references missing id {ref!r}")

    if not root.get("viewBox"):
        errors.append(f"{path}: SVG must declare a viewBox for responsive scaling")

    return root, errors


def paired_path(path: Path) -> Path:
    if path.name.endswith("-light.svg"):
        return path.with_name(path.name.removesuffix("-light.svg") + ".svg")
    return path.with_name(path.stem + "-light.svg")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="?", default="assets/diagrams")
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"visual asset directory does not exist: {directory}", file=sys.stderr)
        return 1

    paths = sorted(directory.glob("*.svg"))
    if not paths:
        print(f"no SVG assets found in {directory}", file=sys.stderr)
        return 1

    roots: dict[Path, ET.Element] = {}
    errors: list[str] = []
    for path in paths:
        root, path_errors = validate_svg(path)
        errors.extend(path_errors)
        if root is not None:
            roots[path] = root

    checked_pairs: set[frozenset[Path]] = set()
    for path, root in roots.items():
        pair = paired_path(path)
        if not pair.exists():
            errors.append(f"{path}: missing light/dark counterpart {pair.name}")
            continue
        pair_key = frozenset({path, pair})
        if pair_key in checked_pairs or pair not in roots:
            continue
        checked_pairs.add(pair_key)
        if semantic_text(root) != semantic_text(roots[pair]):
            errors.append(
                f"{path} and {pair}: light/dark variants must preserve identical reader-facing semantics"
            )

    if errors:
        print("visual asset validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"validated {len(paths)} SVG visual assets in {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
