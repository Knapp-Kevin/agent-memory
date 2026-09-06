#!/usr/bin/env python3
"""Build the snapshot-bound Agent Memory Atlas report inventory.

This script intentionally extracts only report frontmatter and exact Git identity.
Narrative recommendations, "steal" prose, and open questions require bounded human
summary plus independent verification before entering the claim ledger.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs/programs/atlas-research/snapshot-manifest.json"
DEFAULT_OUTPUT = ROOT / "docs/programs/atlas-research/report-inventory.jsonl"


def fail(message: str) -> None:
    raise SystemExit(f"atlas-intake: {message}")


def run_git(repo: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        fail(f"cannot verify pinned Git checkout: {exc}")
    return completed.stdout.strip()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def parse_scalar(raw: str) -> Any:
    value = raw.strip()
    if not value:
        return ""
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            fail(f"invalid quoted frontmatter scalar {value!r}: {exc}")
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    if value in {"null", "~"}:
        return None
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        fail(f"{path} has no opening frontmatter delimiter")

    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        fail(f"{path} has no closing frontmatter delimiter")

    result: dict[str, Any] = {}
    current_mapping: dict[str, Any] | None = None
    current_mapping_name: str | None = None

    for line_number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            fail(f"unsupported frontmatter line {path}:{line_number}: {line!r}")
        key, raw_value = stripped.split(":", 1)
        key = key.strip()

        if indent == 0:
            if not raw_value.strip():
                current_mapping = {}
                current_mapping_name = key
                result[key] = current_mapping
            else:
                result[key] = parse_scalar(raw_value)
                current_mapping = None
                current_mapping_name = None
            continue

        if indent >= 2 and current_mapping is not None:
            if not raw_value.strip():
                fail(
                    f"nested mapping deeper than one level is outside the frozen "
                    f"extractor contract: {path}:{line_number} ({current_mapping_name}.{key})"
                )
            current_mapping[key] = parse_scalar(raw_value)
            continue

        fail(f"unsupported frontmatter indentation {path}:{line_number}: {line!r}")

    return result


def verify_snapshot(atlas_root: Path, manifest: dict[str, Any]) -> None:
    expected_commit = manifest["atlas_commit"]
    actual_commit = run_git(atlas_root, "rev-parse", "HEAD")
    if actual_commit != expected_commit:
        fail(f"Atlas checkout is {actual_commit}, expected {expected_commit}")

    identity = manifest["git_object_identity"]
    refs = {
        "root_tree_sha": "HEAD^{tree}",
        "content_tree_sha": "HEAD:content",
        "systems_tree_sha": "HEAD:content/systems",
        "patterns_tree_sha": "HEAD:content/patterns",
        "methodology_tree_sha": "HEAD:content/methodology",
    }
    for field, git_ref in refs.items():
        actual = run_git(atlas_root, "rev-parse", git_ref)
        expected = identity[field]
        if actual != expected:
            fail(f"{field} drift: {actual}, expected {expected}")

    report_files = sorted((atlas_root / "content/systems").glob("*.md"))
    expected_reports = manifest["system_report_count"]["value"]
    if len(report_files) != expected_reports:
        fail(f"system report count is {len(report_files)}, expected {expected_reports}")

    pattern_files = [
        path
        for path in sorted((atlas_root / "content/patterns").glob("*.md"))
        if path.name != "index.md"
    ]
    expected_patterns = manifest["pattern_count"]["value"]
    if len(pattern_files) != expected_patterns:
        fail(f"pattern count is {len(pattern_files)}, expected {expected_patterns}")

    count_record = manifest["system_report_count"]
    count_path = atlas_root / count_record["source"]
    expected_count_blob = count_record.get("source_blob_sha")
    if expected_count_blob and git_blob_sha(count_path) != expected_count_blob:
        fail(f"source count file drift: {count_path}")

    for record in manifest["methodology_files"]:
        path = atlas_root / record["path"]
        actual = git_blob_sha(path)
        if actual != record["blob_sha"]:
            fail(f"methodology file drift: {record['path']}")

    for name, record in manifest["source_digests"].items():
        if name == "digest_type":
            continue
        path = atlas_root / record["path"]
        actual = git_blob_sha(path)
        if actual != record["digest"]:
            fail(f"{name} source digest drift: {record['path']}")


def string_or_none(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def build_record(path: Path, atlas_root: Path, snapshot: str) -> dict[str, Any]:
    frontmatter = parse_frontmatter(path)
    matrix = frontmatter.get("matrix") or {}
    if not isinstance(matrix, dict):
        fail(f"matrix frontmatter is not a mapping: {path}")

    title = string_or_none(frontmatter.get("title"))
    if not title:
        fail(f"missing title in {path}")

    raw_capabilities = string_or_none(frontmatter.get("capabilities")) or ""
    capabilities = sorted(
        {item.strip() for item in raw_capabilities.split(",") if item.strip()}
    )

    relative = path.relative_to(atlas_root).as_posix()
    return {
        "schema_version": "1.0.0",
        "atlas_snapshot": snapshot,
        "report_slug": path.stem,
        "system_name": title,
        "upstream_repo": string_or_none(frontmatter.get("source_name")),
        "atlas_report_path": relative,
        "atlas_report_blob_sha": git_blob_sha(path),
        "atlas_analyzed_revision": string_or_none(frontmatter.get("revision")),
        "atlas_analyzed_at": string_or_none(frontmatter.get("analyzed_at")),
        "capability_marks": capabilities,
        "stack_storage": string_or_none(frontmatter.get("stack_storage")),
        "stack_retrieval": string_or_none(frontmatter.get("stack_retrieval")),
        "stack_source": string_or_none(frontmatter.get("stack_source")),
        "memory_unit_summary": string_or_none(matrix.get("memory_unit")),
        "write_summary": string_or_none(matrix.get("write")),
        "retrieval_summary": string_or_none(matrix.get("retrieval")),
        "update_delete_summary": string_or_none(matrix.get("update_delete")),
        "scope_summary": string_or_none(matrix.get("scoping") or matrix.get("scope")),
        "trust_summary": string_or_none(matrix.get("trust")),
        "background_summary": string_or_none(matrix.get("background")),
        "strengths_summary": string_or_none(matrix.get("strengths")),
        "risks_summary": string_or_none(matrix.get("risks")),
        "steal_claims": [],
        "avoid_claims": [],
        "open_questions": [],
        "exact_evidence_refs": [],
        "claim_enrichment_status": "frontmatter_only",
    }


def render_inventory(atlas_root: Path, snapshot: str) -> str:
    records = [
        build_record(path, atlas_root, snapshot)
        for path in sorted((atlas_root / "content/systems").glob("*.md"))
    ]
    return "".join(
        json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        for record in records
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--atlas-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the checked-in inventory differs from deterministic output",
    )
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    atlas_root = args.atlas_root.resolve()
    verify_snapshot(atlas_root, manifest)
    rendered = render_inventory(atlas_root, manifest["atlas_commit"])

    line_count = len([line for line in rendered.splitlines() if line.strip()])
    expected = manifest["system_report_count"]["value"]
    if line_count != expected:
        fail(f"generated {line_count} records, expected {expected}")

    if args.check:
        if not args.output.exists():
            fail(f"inventory missing: {args.output}")
        existing = args.output.read_text(encoding="utf-8")
        if existing != rendered:
            fail("checked-in inventory differs from pinned deterministic output")
        print(f"atlas-intake: verified {line_count} records at {manifest['atlas_commit']}")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"atlas-intake: wrote {line_count} records to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
