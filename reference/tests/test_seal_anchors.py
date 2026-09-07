"""Every SESSION SEAL's Merkle tree is anchored, reachable, and matches.

Written against the plausible wrong verifier: one that iterates parsed Merkle
lines (so a mis-parsed seal silently drops out and passes), one that reports
"nothing to check" on an unfetched namespace, and an anchor that overwrites a
ref pointing somewhere else.

The live-repository assertions skip with an explicit reason when refs/seals/
has not been fetched into this checkout -- a skip is visible; a false pass is
not. CI fetches the namespace explicitly (see seal-anchors.yml) so it never
skips there.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import anchor_seal  # noqa: E402
import verify_seals  # noqa: E402


def _git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True).stdout.strip()


def _namespace_fetched() -> bool:
    return bool(_git("for-each-ref", "refs/seals/"))


class LedgerParsing(unittest.TestCase):
    """The parser is the source of truth for what must be anchored."""

    def test_every_session_seal_is_found_and_only_session_seals(self):
        seals = anchor_seal.seal_entries()
        self.assertIn(8, seals, "entry #8 (Sprint 1 seal) carries a Merkle and must be included")
        self.assertNotIn(9, seals, "entry #9 is a MIGRATION ATTESTATION, not a seal")
        self.assertNotIn(10, seals, "entry #10 is an AMENDMENT, not a seal")
        for n in range(11, 25):
            self.assertIn(n, seals, f"entry #{n}")

    def test_every_found_seal_has_a_parseable_tree(self):
        for n, seal in anchor_seal.seal_entries().items():
            self.assertIsNotNone(seal["tree"], f"entry #{n}")
            self.assertRegex(seal["tree"], r"^[0-9a-f]{40}$")

    def test_a_seal_with_an_unparseable_merkle_line_fails_verification(self):
        """DoD 1b / audit V1. Not-applicable is a property of kind, not of regex."""
        text = anchor_seal.LEDGER.read_text(encoding="utf-8")
        seal24 = "write-tree` of the staged index 5be07a02a9a10ab5d86bd87e2455d19da87af953"
        self.assertIn(seal24, text)
        corrupted = text.replace(seal24, "write-tree` of the staged index (redacted)", 1)

        seals = anchor_seal.seal_entries(corrupted)
        self.assertIn(24, seals, "the seal entry must still be enumerated")
        self.assertIsNone(seals[24]["tree"], "...with its tree marked unparseable")

        if _namespace_fetched():
            failures = verify_seals.verify(corrupted)
            self.assertTrue(any("entry #24" in f and "no parseable" in f for f in failures), failures)


class AnchorsMatchTheLedger(unittest.TestCase):
    """DoD 1 -- live repository, when the namespace is present."""

    def setUp(self):
        if not _namespace_fetched():
            self.skipTest(f"refs/seals/ not fetched into this checkout: {anchor_seal.FETCH_HINT}")

    def test_every_session_seal_is_anchored_and_matches(self):
        self.assertEqual(verify_seals.verify(), [])

    def test_anchor_commits_are_parentless(self):
        """LD1: a seal is a snapshot of one staged index, not history."""
        for n in anchor_seal.seal_entries():
            parents = _git("rev-list", "--parents", "-n", "1", anchor_seal.ref_for(n)).split()
            self.assertEqual(len(parents), 1, f"entry #{n} anchor has a parent")

    def test_anchoring_again_is_a_no_op(self):
        """DoD 3 / LD6."""
        seals = anchor_seal.seal_entries()
        before = {n: _git("rev-parse", anchor_seal.ref_for(n)) for n in seals}
        for n in seals:
            self.assertEqual(anchor_seal.anchor(n, seals), "already-anchored")
        after = {n: _git("rev-parse", anchor_seal.ref_for(n)) for n in seals}
        self.assertEqual(before, after)


class FailureModesInAScratchClone(unittest.TestCase):
    """DoD 4-7. Each failure is produced for real, in a clone, and observed."""

    def setUp(self):
        if not _namespace_fetched():
            self.skipTest(f"refs/seals/ not fetched into this checkout: {anchor_seal.FETCH_HINT}")
        self.tmp = tempfile.TemporaryDirectory()
        self.clone = Path(self.tmp.name) / "clone"
        subprocess.run(["git", "clone", "-q", "--no-local", str(ROOT), str(self.clone)], check=True)
        subprocess.run(
            ["git", "fetch", "-q", str(ROOT), "refs/seals/*:refs/seals/*"], cwd=self.clone, check=True
        )

    def tearDown(self):
        self.tmp.cleanup()

    def _verify_in_clone(self) -> tuple[int, str]:
        # The working-tree script, pointed at the clone: the clone is of the
        # committed HEAD and need not contain these scripts at all.
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "verify_seals.py"), "--repo", str(self.clone)],
            capture_output=True, text=True,
        )
        return proc.returncode, proc.stdout + proc.stderr

    def test_clean_clone_with_namespace_verifies(self):
        code, out = self._verify_in_clone()
        self.assertEqual(code, 0, out)

    def test_empty_namespace_fails_rather_than_passing_vacuously(self):
        """DoD 6 / LD4. A check that sees nothing has checked nothing."""
        for ref in _git("for-each-ref", "--format=%(refname)", "refs/seals/", cwd=self.clone).split():
            subprocess.run(["git", "update-ref", "-d", ref], cwd=self.clone, check=True)
        code, out = self._verify_in_clone()
        self.assertNotEqual(code, 0)
        self.assertIn("refs/seals/ is empty", out)
        self.assertIn(anchor_seal.FETCH_HINT, out, "the failure must say how to fetch")

    def test_a_repointed_ref_fails(self):
        """DoD 5. The wrong anchor is the one that matters most."""
        wrong = _git("rev-parse", "HEAD", cwd=self.clone)  # a commit whose tree is not the seal
        subprocess.run(["git", "update-ref", anchor_seal.ref_for(24), wrong], cwd=self.clone, check=True)
        code, out = self._verify_in_clone()
        self.assertNotEqual(code, 0)
        self.assertIn("entry #24", out)
        self.assertIn("points at tree", out)

    def test_a_missing_ref_fails(self):
        subprocess.run(["git", "update-ref", "-d", anchor_seal.ref_for(8)], cwd=self.clone, check=True)
        code, out = self._verify_in_clone()
        self.assertNotEqual(code, 0)
        self.assertIn("entry #8", out)
        self.assertIn("missing", out)

    def test_a_stray_anchor_is_reported(self):
        """DoD 7 / LD3. A stray anchor is a stray claim."""
        head = _git("rev-parse", "HEAD", cwd=self.clone)
        subprocess.run(["git", "update-ref", "refs/seals/entry-999", head], cwd=self.clone, check=True)
        code, out = self._verify_in_clone()
        self.assertNotEqual(code, 0)
        self.assertIn("entry-999", out)
        self.assertIn("no matching SESSION SEAL", out)

    def test_anchor_refuses_to_overwrite_a_wrong_ref(self):
        """DoD 4 / LD2. Never silently correct; that destroys the evidence."""
        wrong = _git("rev-parse", "HEAD", cwd=self.clone)
        subprocess.run(["git", "update-ref", anchor_seal.ref_for(24), wrong], cwd=self.clone, check=True)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "anchor_seal.py"), "24", "--repo", str(self.clone)],
            capture_output=True, text=True,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("Refusing to overwrite", proc.stdout + proc.stderr)
        self.assertEqual(_git("rev-parse", anchor_seal.ref_for(24), cwd=self.clone), wrong,
                         "the wrong ref must be left exactly as found")


if __name__ == "__main__":
    unittest.main()
