# Plan: ledger markup repair and commitment amendment

**change_class**: hotfix
**Risk Grade**: L2
**Session**: 2026-09-04T1541-bbb157
**Research**: `docs/research-brief-ledger-markup-repair-2026-09-04.md`
**Iteration**: 2 (amended for audit attempt 1 grounds V1-V5)

## Objective

Make `docs/META_LEDGER.md` verify under `qor-logic 0.169.0` (`verify-ledger` exit 0), and correct the stale artifact commitment on Entry #2, without changing any recorded hash value or fabricating history.

## Boundaries

**In scope**: `docs/META_LEDGER.md` markup and two appended entries; `docs/GOVERNANCE_INDEX.md` Tier 1 freshness marker; closure of five remaining shadow events.

**Out of scope**: the `/qor-bootstrap` template that produced the defective markup (upstream, GH #404, reopened); the `ledger_commitment` extraction defect (upstream, GH #408, reopened); the `verify_post_anchor` anchor-selection defect (upstream, GH #430); any code, schema, CI, or dependency change; anything in `reference/`; Sprint 2 work.

**Explicitly forbidden**: recomputing any existing content, previous, or chain hash; retrofitting a chain hash onto Entry #1; editing the body of any sealed entry beyond the hash-field delimiters named in LD1.

## Design decisions

**LD1 — Normalize only the field that fails, and only its delimiters.**
Replace `**Previous Hash**: <bare hex>` with ``**Previous Hash**: `<bare hex>` ``, matched by `^(\*\*Previous Hash\*\*:\s*)([0-9a-f]{64})\s*$` under `re.MULTILINE` so nothing else in the file can match. `Content Hash` and `Chain Hash` already parse via the dialect's `= <hex>` branch and are left alone: F2 proves prev-hash is the whole failure, and a wider rewrite would touch sealed bytes for no verification gain.

**Exactly seven lines match, and they are not all in entries #2-#7** (V1). Six are the prev-hash lines of entries #2-#7; the seventh is at `docs/META_LEDGER.md:185`, inside Entry #8's *secondary* hash block — Entry #8 carries a single-line backticked block at its head and a duplicate legacy block below it:

| Line | Value | Entry |
|---|---|---|
| 40 | `41e5730727c4...` | #2 |
| 65 | `8f260d40b14b...` | #3 |
| 87 | `da74f30e6d06...` | #4 |
| 109 | `87e3f3e9d58a...` | #5 |
| 131 | `98a284dd5557...` | #6 |
| 154 | `b14d48b4e945...` | #7 |
| 185 | `8bd16fbc3eba...` | #8, secondary block |

Normalizing line 185 is in scope and intended. It is the same value already recorded in backticked form at Entry #8's head, so the substitution makes the entry internally consistent rather than changing anything. `_resolve_recorded` takes the first match per field, so Entry #8's verification is governed by its head block either way; leaving line 185 bare would preserve the one remaining instance of the markup this cycle exists to eliminate.

Entry #1's `**Previous Hash**: GENESIS (no predecessor)` contains no hex and is not matched.

Implementation asserts the match count is exactly 7 before substituting, and aborts otherwise.

**LD2 — Close Entry #1 by attestation, not by fabrication.**
Append a `MIGRATION ATTESTATION` entry carrying `**Attested Entries**:` with a `#1=<digest12>` line, where `<digest12>` is `_legacy_body_digest` of Entry #1's body. This records genesis as a pre-convention entry and digest-binds it, so any later edit to it becomes a hard failure. Rejected alternative: giving Entry #1 a zeros previous-hash and a computed chain hash, which would write a value into sealed history that was never computed at genesis.

**The digest is computed against the file after LD1, not before** (V3). `_legacy_body_digest` runs over Entry #1's body as it stands at read time, and Entry #1's body under `ENTRY_RE.split` runs to the next `### Entry` header. LD1 does not touch Entry #1, so the value is expected to be `38bcc1339da0` — but the implementation recomputes it after LD1 rather than writing that literal, and the DoD verifies it through `verify-ledger` reporting `OK Entry #1: attested by migration entry #9` rather than by trusting the constant.

**LD2b — Entry #9's content hash is the attested band** (V4). A MIGRATION ATTESTATION commits no file, so its `**Content Hash**` is defined as the LF-normalized SHA-256 of its own `**Attested Entries**:` block — the exact text `#1=<digest12>`, one line, no trailing newline. This is the payload the entry asserts, so hashing it is what the field means for this entry kind. The definition is recorded in the entry body itself so a later reader can recompute it without this plan.

**LD3 — Write the AMENDMENT in the format the new gate can read.**
The `ledger_commitment` module returns `stale: []` on this ledger (F4), so an amendment in the practiced convention would be as invisible as the commitment it corrects. The AMENDMENT entry therefore carries, each on its own line: `**Artifact**: `docs/research-brief-sprint1-install-correctness-2026-09-01.md``, ``**Content Hash**: `b899b5e6...` `` (same-line backticked), and ``**Superseded Content Hash**: `4386c8f0...` ``. Verification is that `latest_commitments` returns the corrected hash for that artifact and `stale_commitments` returns empty for it.

**LD4 — Both new entries carry full parseable markup.**
Each names Content, Previous, and Chain Hash in the inline-backtick form, chaining from Entry #8's chain hash `810f42db...`. An entry that names a hash field must parse, or it becomes the exact defect being repaired.

Chain hashes use `ledger_hash.chain_hash`, the Phase 23 separator form `SHA256(content + "|" + previous)`. Verified against Entry #8: `chain_hash(f3a1d786..., 8bd16fbc...)` reproduces the recorded `810f42db...` exactly, while `legacy_chain_hash` does not. The existing entry bodies describe this in prose as `SHA256(content_hash + previous_hash)`, which is shorthand for the separator form and must not be taken literally when computing new entries.

**LD5 — Entry numbering and order.**
`#9` MIGRATION ATTESTATION, then `#10` AMENDMENT. Contiguous after #8, so `_report_sequence` stays clean. Attestation first because it closes the oldest debt.

## Affected files

| File | Change |
|---|---|
| `docs/META_LEDGER.md` | 7 prev-hash delimiter normalizations (LD1 table); append Entry #9 and Entry #10 |
| `docs/GOVERNANCE_INDEX.md` | Tier 1 ledger row: entry range and freshness marker; **Tier 4: register this plan and its research brief** (V5) |
| `docs/PROCESS_SHADOW_GENOME.md` | 5 event closures (written by the closure step, not hand-edited) |

**LD6 — Register the plan before the security lint can scan it** (V5). The GH #407 fix admits "any index-registered active plan", which makes registration in `docs/GOVERNANCE_INDEX.md` a *precondition* for `prompt_injection_canaries` to accept a plan path at all. On iteration 1 the lint refused this plan outright:

```
ERROR: path not in governance allowlist: 'docs/plan-ledger-markup-repair.md'
  (governance path not registered in index)
```

Registering both artifacts in Tier 4 is therefore the first implementation step, not a bookkeeping afterthought — otherwise the cycle seals with its own plan never scanned, which is the silent-skip shape this cycle exists to remove.

## Feature Inventory Touches

None. This cycle touches no user-facing feature; `docs/FEATURE_INDEX.md` is unchanged and its 3 verified rows are unaffected.

## Definition of Done

1. `qor-logic-plus verify-ledger` exits 0, with `OK` for entries #2-#10 and `OK ... attested by migration entry #9` for #1. No `FAIL`, no `TAINTED`, no `Skipped`. **This is the discriminating check**: it exits 1 today.
2. `qor-logic-plus verify-ledger --post-anchor` exits 0 **and emits zero `DISCLOSED_PRE_ANCHOR` lines** — nothing is being tolerated. Exit 0 alone is not sufficient: it already exits 0 today with seven `DISCLOSED_PRE_ANCHOR` lines and `boundary=#8` (V2). The boundary itself is not a useful assertion, because it is by construction the highest verifying entry and will read `#10` after the repair for the same structural reason it reads `#8` before it (GH #430).
3. ~~`governance-health` reports OK~~ — **struck** (V2). It reports OK on the unrepaired ledger via the GH #430 anchor defect and cannot demonstrate this repair. It is still run, and a *regression* to `DAMAGED` would be a failure, but its passing proves nothing and is not counted as evidence.
4. `ledger_commitment.latest_commitments` returns `b899b5e6...` for the research brief; `stale_commitments` returns empty for both the brief and the plan. Today it returns the plan only and cannot see the brief at all.
5. Every hash value present before the change is still present and unchanged. Verified by diffing the sorted multiset of 64-hex strings in the file before and after: the only permitted difference is the two new entries' own hashes.
6. `governance-index --cross-check-ledger` exits 0.
7. `prompt_injection_canaries --files <plan> <research brief>` runs and exits 0 — it must *run*, not be refused for an unregistered path (V5).
8. Shadow severity sum stays below 10 and `.qor/remediate-pending` stays absent.
9. `python -m unittest discover -s reference/tests -t reference` reports 868 tests, unchanged, proving this cycle touched no runtime.

## CI Commands

```
qor-logic-plus verify-ledger
qor-logic-plus verify-ledger --post-anchor
qor-logic-plus governance-health --profile skill-entry
qor-logic-plus governance-index --cross-check-ledger --repo-root .
python -m unittest discover -s reference/tests -t reference
```

The test suite is run to prove this cycle changed nothing in the runtime: 868 tests, expected unchanged.

## CI Coverage Exemptions

This cycle touches only `docs/`. No workflow trigger path includes it, so no repository CI job exercises this change and none can regress from it.

- `.*` — every `.github/workflows/**` command is exempt. The changed files are governance markdown; the schema, fixture, wheel-install, provider-discovery, and visibility jobs all operate on `schemas/`, `fixtures/`, `reference/`, and `pyproject.toml`, none of which this plan modifies. DoD 9 runs the full 868-test suite anyway as a negative control, which is a stronger claim than per-job coverage.

## Rollback

`git checkout -- docs/META_LEDGER.md docs/GOVERNANCE_INDEX.md`. Nothing is committed by this cycle; the Review Boundary holds. Shadow-event closures are reversed by re-running the closure step with the prior field values, recorded in the implement gate artifact.

## Next

`/qor-audit`, invoked with `reviews-remediate:.qor/gates/2026-09-02T0158-2a109f/remediate.json` so a PASS also closes the five remaining shadow events.
