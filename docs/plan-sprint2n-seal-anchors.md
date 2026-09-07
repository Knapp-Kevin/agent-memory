# Plan: Sprint 2n — durable seal anchors

**change_class**: hotfix
**Risk Grade**: L2
**Session**: 2026-09-05T1100-c2c873
**Research**: `docs/research-brief-sprint2n-seal-anchors-2026-09-05.md`
**Iteration**: 2 (amended for audit V1-V2)
**Implements**: governance-integrity repair, outstanding since Loop 8

## Objective

Make every Merkle seal in the ledger verifiable from the repository, durably, and make future seals durable by construction.

## Boundaries

**In scope**: `scripts/anchor_seal.py`, `scripts/verify_seals.py`, `refs/seals/entry-<N>` for **every SESSION SEAL entry** — #8, #11–#25 (audit V2: #8 carries a Merkle; #9/#10 are an attestation and an amendment, not seals), a CI workflow that fetches and verifies, a test.

**Out of scope**: any ledger content. The chain hash does not take the Merkle as input (measured), so no entry is amended and no re-seal occurs. Entries that are not SESSION SEALs carry no Merkle and are not-applicable. **Not-applicable is a property of the entry's kind, never of whether a regex matched** (audit V1).

## Design decisions

**LD1 — A parentless commit per seal, not a ref to a bare tree.**
A ref may point at a tree object, but tooling — GitHub's UI, `git log`, most hosting — assumes refs point at commits, and a commit carries the message that binds the anchor to its ledger entry, chain hash and digest. Parentless, because a seal is a snapshot of one staged index, not a point on `main`'s history; a parent would misrepresent it.

**LD2 — The anchor verifies before it creates, and never overwrites.**
`anchor_seal.py` reads the tree oid *from the ledger*, checks the object exists, and only then creates the commit and ref. An existing ref whose `^{tree}` already matches is a no-op. An existing ref that points elsewhere is an **error** — a wrong anchor that verifies is worse than no anchor, and silently correcting one would destroy the evidence that something went wrong.

**LD3 — The verifier iterates seal entries, and a seal without a parseable Merkle is a failure (audit V1).**
It enumerates every entry titled `SESSION SEAL` and, for each, **requires** a parseable Merkle line and a matching ref. A verifier that iterated parsed Merkle lines instead would let a mis-parsed seal drop silently out of the set and pass — the failure most likely to occur as the ledger is hand-edited. The other direction — a ref with no seal entry — is reported too, because a stray anchor is a stray claim.

**LD4 — CI must fetch the namespace or the check is theatre.**
A default checkout does not fetch `refs/seals/*`. A verifier that runs against a checkout with no seal refs and reports "nothing to check" has checked nothing. The workflow fetches explicitly, and the verifier **fails** if the ledger has seals but the namespace is empty.

**LD5 — Seal-time anchoring is part of substantiate, not a follow-up.**
This entry's own tree is anchored before this cycle's push, and the seal procedure records that the anchor step is not optional. Otherwise the repair covers fifteen seals and the sixteenth is unreachable again.

**LD6 — Idempotent, and safe to rerun on every seal.**
Running the anchor for an entry already anchored changes nothing. That is what lets it sit in the seal procedure unconditionally.

## Definition of Done

1. For every SESSION SEAL entry (#8, #11–#25), `git rev-parse refs/seals/entry-<N>^{tree}` equals the recorded tree oid.
1b. **A seal entry whose Merkle line is unparseable fails verification** (LD3, audit V1) — asserted by corrupting one line in a scratch copy of the ledger.
2. All those refs exist on `origin` — `git ls-remote origin 'refs/seals/*'` lists each.
3. `anchor_seal.py` is idempotent: a second run on an anchored entry is a no-op with exit 0.
4. `anchor_seal.py` **refuses** to overwrite a ref that points at a different tree, with exit non-zero and no mutation (LD2).
5. `verify_seals.py` exits 0 on the repaired repository and non-zero if any anchored tree is deleted or any ref is repointed — asserted by a test that does each in a scratch clone.
6. `verify_seals.py` **fails** when the ledger records seals but `refs/seals` is empty (LD4) — asserted in a scratch clone with the namespace removed.
7. A stray `refs/seals/*` ref with no ledger entry is reported (LD3).
8. The CI workflow fetches `refs/seals/*` before verifying, and is green on this PR.
9. Entry #25's own tree is anchored and pushed as part of this cycle (LD5).
10. No ledger entry's content, content hash, or chain hash changes — `verify-ledger` clean, chain identical to before.
11. Full suite green; validators clean; no schema modified.

## CI Commands

```
python scripts/verify_seals.py
python -m unittest discover -s reference/tests -t reference
```

## Rollback

Delete `refs/seals/*` locally and remotely; remove the two scripts, the test and the workflow. The ledger is untouched throughout.

## Next

`/qor-audit`. L2, adversarial: whether a wrong anchor can ever verify; whether the verifier can pass on an empty namespace; whether anything here touches ledger content.
