#!/usr/bin/env python
"""Verify that every SESSION SEAL's Merkle tree is anchored and matches.

The ledger is the source of truth. For every entry titled SESSION SEAL, this
requires: a parseable Merkle line, a ref `refs/seals/entry-<N>`, and that the
ref's `^{tree}` equals the tree the ledger recorded. A ref under refs/seals/
with no seal entry is reported too -- a stray anchor is a stray claim.

Two failure modes are deliberately loud:

* A SESSION SEAL whose Merkle line does not parse FAILS. Iterating parsed lines
  instead would let a mis-parsed seal drop silently out of the set and pass.
* A ledger with seals but an empty refs/seals/ namespace FAILS. A default
  `git clone` and a default CI checkout do not fetch this namespace, and a
  verifier that sees nothing and reports "nothing to check" has checked nothing.

Exit 0 only when every seal is anchored and matches.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from anchor_seal import FETCH_HINT, LEDGER, ROOT, ref_for, seal_entries  # noqa: E402


def _git(*args: str, repo: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=repo or ROOT, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


def verify(ledger_text: str | None = None, repo: Path | None = None) -> list[str]:
    """Return a list of failures; empty means every seal verifies."""
    failures: list[str] = []
    seals = seal_entries(ledger_text, repo=repo)
    if not seals:
        return ["no SESSION SEAL entries found in the ledger; nothing to verify is itself a failure"]

    _, listing = _git("for-each-ref", "--format=%(refname)", "refs/seals/", repo=repo)
    present = set(listing.split()) if listing else set()
    if not present:
        return [
            f"the ledger records {len(seals)} SESSION SEAL(s) but refs/seals/ is empty. "
            f"Fetch the namespace first: {FETCH_HINT}"
        ]

    for number, seal in sorted(seals.items()):
        ref = ref_for(number)
        if seal["tree"] is None:
            failures.append(f"entry #{number}: SESSION SEAL with no parseable Merkle line")
            continue
        code, anchored = _git("rev-parse", "--verify", "--quiet", f"{ref}^{{tree}}", repo=repo)
        if code != 0 or not anchored:
            failures.append(f"entry #{number}: {ref} is missing ({FETCH_HINT})")
            continue
        if anchored != seal["tree"]:
            failures.append(
                f"entry #{number}: {ref} points at tree {anchored}, ledger records {seal['tree']}"
            )

    expected = {ref_for(n) for n in seals}
    for stray in sorted(present - expected):
        failures.append(f"{stray}: anchor with no matching SESSION SEAL entry")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="verify every SESSION SEAL is anchored")
    parser.add_argument("--repo", type=Path, default=None, help="repository root (default: this checkout)")
    args = parser.parse_args()
    failures = verify(repo=args.repo)
    seals = seal_entries(repo=args.repo)
    if failures:
        print("seal verification FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"seal verification OK: {len(seals)} SESSION SEAL(s) anchored and matching")
    return 0


if __name__ == "__main__":
    sys.exit(main())
