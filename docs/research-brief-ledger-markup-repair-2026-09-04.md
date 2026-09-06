# Research Brief: ledger markup repair and commitment amendment

**Date**: 2026-09-04
**Session**: 2026-09-04T1541-bbb157
**Analyst**: The Qor-logic Analyst
**Scope**: Loop 1.6, governance debt closure. Make `docs/META_LEDGER.md` verify under `qor-logic 0.169.0`, and close the stale artifact commitment recorded as V-2.
**Toolkit**: qor-logic 0.169.0 / qor-logic-plus 2.42.0 (upgraded from 0.163.1 on 2026-09-03)

## 1. Why this is open

`/qor-validate` on 2026-09-02 found that 7 of 8 ledger entries were unverifiable and that Entry #2's artifact commitment had gone stale. Both were reported upstream (GH #404, #408). The 0.169.0 upgrade changed the local situation materially:

```
$ qor-logic-plus verify-ledger
FAIL Entry #1..#7: hash field labeled but its value matches no recognized form
TAINTED Entry #8: depends on failed predecessor #7
EXIT=1
```

Before the upgrade this was a silent skip and exit 0. GH #363 plus the GH #404 fix drew the intended line: an entry that *names* a hash field is making a claim, and a value the dialect cannot read is a broken claim regardless of entry number. The failure is correct and the debt is local.

## 2. Verified findings

**F1 — the only unparseable field is `**Previous Hash**`.** `ledger_dialect._HASH_VALUE` accepts three forms: inline-backtick `` `<hex>` ``, `= <hex>`, and a bare hex alone on its own line. Entries #1-#7 write `**Previous Hash**: <bare hex>` inline, which matches none: the bare-hex form is anchored to its own line. `Content Hash` and `Chain Hash` already parse via the `= <hex>` branch.

Per-entry parse state before repair (`content / prev / chain`):

| Entry | content | prev | chain |
|---|---|---|---|
| #1 | yes | no | absent |
| #2-#7 | yes | **no** | yes |
| #8 | yes | yes | yes |

**F2 — backticking the recorded values repairs #2-#7 completely.** Verified on a scratch copy (`ledger_probe.py`): after `**Previous Hash**: <hex>` becomes ``**Previous Hash**: `<hex>` ``, entries #2-#8 all resolve and their chain math verifies. No hash input changes: the values are already recorded, and `chain_hash` is computed over the hex strings, not over the markup around them.

**F3 — Entry #1 cannot be repaired by markup and must not be repaired by fabrication.** Genesis carries a Content Hash and `**Previous Hash**: GENESIS (no predecessor)`, and no Chain Hash. It predates the chain-hash convention by design. Two options were considered:

- *Retrofit the genesis convention* (previous = 64 zeros, chain = `chain_hash(content, zeros)`). Rejected: it fabricates a chain hash that was never computed and writes it into sealed history. `is_placeholder_pattern` exempts all-zeros precisely so this is *possible*, which is not the same as it being honest here.
- *MIGRATION ATTESTATION* (Phase 193, GH #278). `verify()` accepts a pre-convention entry when a later entry carries `**Attested Entries**:` with a `#<num>=<digest12>` line matching `_legacy_body_digest(body)`. This records genesis as what it is -- a pre-convention entry, digest-bound so a later edit to it is a hard failure rather than a silent skip.

The second is the designed mechanism for exactly this shape. Entry #1's current digest is `38bcc1339da0`.

**F4 — the V-2 stale commitment is still open, and the upstream gate does not detect it.** `docs/research-brief-sprint1-install-correctness-2026-09-01.md` hashes `b899b5e6...`; Entry #2 commits `4386c8f0...`. The Phase 251 `ledger_commitment` module shipped for GH #408 returns `stale: []` on this ledger. Isolated cause (`commitment_probe.py`): its `_CONTENT_RE` accepts only same-line backticked hashes, and its `_ARTIFACT_RE` requires an `**Artifact|Plan|Brief**:` citation line that historical entries do not carry. Both conditions must hold; the practiced convention satisfies neither. Reported on GH #408, which is reopened.

The consequence for this plan: the amendment must be written in the format the new gate can read, or it will be as invisible as the commitment it corrects.

**F5 — amendment format is now codified.** `ledger_commitment._COMMITTING_KINDS` recognizes `RESEARCH BRIEF`, `IMPLEMENTATION`, `SESSION SEAL`, `AMENDMENT`. A conforming AMENDMENT entry needs, on their own lines: `**Artifact**: `<path>``, ``**Content Hash**: `<hex>` `` (same-line backticked), and ``**Superseded Content Hash**: `<hex>` ``. A `Superseded Content Hash` present but not a full 64-char digest raises `MalformedCommitmentError`.

## 3. Drifts found

**D1** — The GOVERNANCE_INDEX Tier 1 row for META_LEDGER reads "Entries #1-#7; Sprint 1 seal Entry #8"; it will need the two new entries after implementation.

**D2** — `docs/PROCESS_SHADOW_GENOME.md` events `ca1663258aeb` (V-1) and `ab8613deed58` (V-2) are `addressed_pending` and describe the pre-upgrade situation. Their remediation is this cycle's work; their closure requires an audit PASS carrying `reviews_remediate_gate`.

**D3** — Five events were closed `deferred_upstream` before this brief (issues 411, 406, 409, verified shipped in 0.169.0). Shadow severity is now 7, below the threshold of 10, and `.qor/remediate-pending` is cleared. This cycle is not running under a threshold breach.

## 4. Risk grade

**L2.** The change is confined to governance documentation. It alters no code, no schema, no CI, no dependency, and no security path. Every recorded hash value is preserved; the edit is to markup delimiters and two appended entries. The success criterion is machine-checkable and binary (`verify-ledger` exit 0). It is not L1 because it edits sealed ledger history, where an error is expensive to detect later.

## 5. Open questions for the plan

1. Should the markup normalization touch `Content Hash` / `Chain Hash` as well, for one consistent dialect, or only the fields that fail? (Minimal change argues for prev-hash only; F4 shows the commitment gate needs same-line backticked Content Hash on *committing* entries specifically.)
2. Does the MIGRATION ATTESTATION entry come before or after the AMENDMENT entry, and do both need Content/Previous/Chain markup of their own? (They do: they are entries at/after the compat boundary in behavior, and an entry that names a hash field must parse.)

## 6. Next

`/qor-plan`.
