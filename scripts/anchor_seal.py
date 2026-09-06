#!/usr/bin/env python
"""Anchor a ledger SESSION SEAL's Merkle tree under refs/seals/entry-<N>.

Every SESSION SEAL in docs/META_LEDGER.md records the `git write-tree` oid of
the staged index at seal time. `write-tree` creates a tree object but references
it from nothing: unreachable, never pushed, pruned by the next gc. So a seal is
verifiable only locally and only for a while -- and never from the remote.

This wraps the sealed tree in a **parentless** commit (a seal is a snapshot of
one staged index, not a point on main's history) and references it from
`refs/seals/entry-<N>`. Then `git rev-parse refs/seals/entry-<N>^{tree}` equals
the ledger's oid, the object is reachable, and `git push origin
'refs/seals/*:refs/seals/*'` makes it durable.

Idempotent: an existing ref whose tree already matches is a no-op. An existing
ref pointing at a DIFFERENT tree is an error and is never overwritten -- a wrong
anchor that verifies is worse than no anchor, and silently correcting it would
destroy the evidence that something went wrong.

Usage:
    python scripts/anchor_seal.py 25          # one entry
    python scripts/anchor_seal.py --all       # every SESSION SEAL
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs" / "META_LEDGER.md"


def ledger_path(repo: Path | None = None) -> Path:
    return (repo or ROOT) / "docs" / "META_LEDGER.md"

ENTRY_RE = re.compile(r"^### Entry #(\d+): (.*)$", re.M)
TREE_RE = re.compile(r"write-tree` of the staged index ([0-9a-f]{40})")
CHAIN_RE = re.compile(r"\*\*Chain Hash\*\*: `([0-9a-f]{64})`")
MERKLE_RE = re.compile(r"\*\*Merkle Seal\*\*[^\n]*\n`([0-9a-f]{64})`")

FETCH_HINT = "git fetch origin 'refs/seals/*:refs/seals/*'"


def _git(*args: str, check: bool = True, repo: Path | None = None) -> str:
    proc = subprocess.run(["git", *args], cwd=repo or ROOT, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout.strip()


def seal_entries(text: str | None = None, repo: Path | None = None) -> dict[int, dict]:
    """Every SESSION SEAL entry, keyed by number, with what it records.

    A seal whose Merkle line does not parse is reported with tree=None so the
    caller can FAIL on it. Not-applicable is a property of the entry's kind
    (not a seal), never of whether a regex matched.
    """
    text = ledger_path(repo).read_text(encoding="utf-8") if text is None else text
    parts = ENTRY_RE.split(text)
    seals: dict[int, dict] = {}
    # parts: [preamble, num, title, body, num, title, body, ...]
    for i in range(1, len(parts), 3):
        number, title, body = int(parts[i]), parts[i + 1], parts[i + 2]
        if "SESSION SEAL" not in title:
            continue
        tree = TREE_RE.search(body)
        chain = CHAIN_RE.search(body)
        merkle = MERKLE_RE.search(body)
        seals[number] = {
            "title": title.strip(),
            "tree": tree.group(1) if tree else None,
            "chain": chain.group(1) if chain else None,
            "merkle": merkle.group(1) if merkle else None,
        }
    return seals


def ref_for(number: int) -> str:
    return f"refs/seals/entry-{number}"


def anchor(number: int, seals: dict[int, dict], repo: Path | None = None) -> str:
    """Anchor one seal. Returns 'created', 'already-anchored', or raises."""
    if number not in seals:
        raise SystemExit(f"entry #{number} is not a SESSION SEAL; nothing to anchor")
    seal = seals[number]
    if seal["tree"] is None:
        raise SystemExit(f"entry #{number} is a SESSION SEAL with no parseable Merkle line")
    tree = seal["tree"]
    if _git("cat-file", "-t", tree, check=False, repo=repo) != "tree":
        raise SystemExit(
            f"entry #{number}: sealed tree {tree} is not present as a tree object. "
            "It may already have been pruned; the seal cannot be anchored."
        )

    ref = ref_for(number)
    existing = _git("rev-parse", "--verify", "--quiet", f"{ref}^{{tree}}", check=False, repo=repo)
    if existing:
        if existing == tree:
            return "already-anchored"
        raise SystemExit(
            f"{ref} already exists and points at tree {existing}, not the ledger's "
            f"{tree}. Refusing to overwrite: a wrong anchor that verifies is worse "
            "than no anchor. Investigate before touching this ref."
        )

    message = (
        f"seal: META_LEDGER entry #{number}\n\n"
        f"{seal['title']}\n"
        f"tree:   {tree}\n"
        f"chain:  {seal['chain']}\n"
        f"merkle: {seal['merkle']}\n\n"
        "Parentless by design: a seal is a snapshot of one staged index, not a "
        "point on main's history. See scripts/anchor_seal.py."
    )
    commit = _git("commit-tree", tree, "-m", message, repo=repo)
    _git("update-ref", ref, commit, repo=repo)
    return "created"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("entry", nargs="?", type=int, help="ledger entry number")
    parser.add_argument("--all", action="store_true", help="anchor every SESSION SEAL")
    parser.add_argument("--repo", type=Path, default=None, help="repository root (default: this checkout)")
    args = parser.parse_args(argv)
    if bool(args.entry) == args.all:
        parser.error("give exactly one of <entry> or --all")

    seals = seal_entries(repo=args.repo)
    targets = sorted(seals) if args.all else [args.entry]
    for number in targets:
        result = anchor(number, seals, repo=args.repo)
        print(f"entry #{number}: {result} -> {ref_for(number)}")
    print(f"\npush with: git push origin 'refs/seals/*:refs/seals/*'")
    print(f"fetch with: {FETCH_HINT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
