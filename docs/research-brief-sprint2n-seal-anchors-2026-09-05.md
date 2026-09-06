# Research Brief: Sprint 2n — durable seal anchors

**Date**: 2026-09-05
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 15.
**Implements**: a governance-integrity repair, outstanding since Loop 8

## 1. The defect, measured

Every SESSION SEAL from entry #11 onward records a Merkle seal: `SHA256` over the `git write-tree` oid of the staged index at seal time. Fifteen such trees are recorded.

| Check | Result |
|---|---|
| Tree objects present in the local object store | **15 of 15** |
| Reachable from any local ref | **0 of 15** |
| Present on `origin` (`git ls-remote origin 'refs/seals/*'`) | **0** |
| gc configuration | defaults — auto-gc, unreachable objects pruned after two weeks |

`git write-tree` creates a tree object but references it from nothing. So every seal is **verifiable only locally, only until the next gc that decides to prune**, and **never verifiable from GitHub at all** — an unreachable object is never pushed. The ledger asserts fifteen Merkle seals that no reviewer of the repository can check.

This was flagged in Loop 8 as "seven Merkle trees are unreferenced git objects that `git gc` will prune". It is now fifteen, and the count of seals a future reader cannot verify has grown with every cycle since.

## 2. Why this needs no re-seal

`ledger_hash.chain_hash(content, prev)` takes the plan's content hash and the previous chain hash. The Merkle seal is **not an input**. Anchoring the trees therefore changes no ledger entry, breaks no chain, and requires no amendment — it makes the existing seals durable rather than replacing them.

## 3. The mechanism

A tree object cannot be a commit's parent, but it can be a commit's **tree**. So each sealed tree is wrapped in a **parentless commit** via `git commit-tree`, whose message records the ledger entry, its chain hash, and the Merkle digest, and that commit is referenced from `refs/seals/entry-<N>`. Then:

- `git rev-parse refs/seals/entry-<N>^{tree}` **equals** the oid the ledger recorded — the seal is verifiable by anyone with the ref.
- The ref is pushed. GitHub stores the object; `git fetch origin 'refs/seals/*:refs/seals/*'` retrieves it.
- The tree is reachable, so gc cannot prune it.

A parentless commit is deliberate: a seal is a snapshot of one staged index, not a point on `main`'s history, and giving it a parent would misrepresent it as one.

## 4. What makes it stay fixed

Repairing fifteen seals once is not the deliverable. The seal-writing step must anchor **by construction**, or entry #26 will be unreachable again. So:

- `scripts/anchor_seal.py <entry>` — reads the ledger, resolves the recorded tree oid, verifies the object exists, creates the commit and ref idempotently (an existing correct ref is a no-op; an existing *wrong* ref is an error, never overwritten).
- `scripts/verify_seals.py` — for every ledger entry with a Merkle seal, asserts a matching ref exists and its `^{tree}` equals the recorded oid. Non-zero on any miss.
- A CI workflow that fetches `refs/seals/*` and runs the verifier — because a default CI checkout does not fetch that namespace, and a check that silently sees nothing is not a check.
- The substantiate step anchors its own entry before the push.

## 5. Blast radius

No production code. No policy. No schema. New refs under a namespace nothing else uses. The repair itself is a set of pushed refs and a repository-internal script.

## 6. Risk grade

**L2.** Nothing behavioural changes, but this is the durability of the evidence chain the whole program rests on, and a wrong anchor — a ref pointing at the wrong tree — would be worse than no anchor because it would *verify*.

## 7. Next

`/qor-plan`.
