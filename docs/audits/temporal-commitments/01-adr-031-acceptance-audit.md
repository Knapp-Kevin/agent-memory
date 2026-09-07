# ADR-031 Acceptance Audit

Pre-acceptance head: `1b02d02ef6b1d96a5c7b04515bac62ae86a15fc0`

All 25 repository workflows passed at this head.

Evidence receipts:

- Temporal Commitment Evidence: run `31744205707`, artifact `9198292626`, digest `sha256:66454918179ce3e0e9e887497d59120b1845494a9a7d62e46d2bc6f4ad15c52f`
- UOR Addr Compatibility: run `31744205879`, artifact `9198303010`, digest `sha256:25b067fd2aba43ea1d988e62b767d6c07b2da20c1a13f6cab4dfc56dcf4f8f28`

## Gate map

| Gate | Result | Evidence |
|---|---|---|
| payload mutation changes identity | PASS | temporal adversarial tests |
| temporal-claim mutation changes identity | PASS | event-time mutation test and focused artifact |
| predecessor/order mutation changes identity | PASS | predecessor/reference-profile mutation test |
| schema/profile mutation changes identity | PASS | schema and projection-version mutation tests |
| attestation binds exact commitment/profile | PASS | exact-reference/profile tamper tests |
| false/future claimed time remains distinct from trusted-time evidence | PASS | future-time test |
| untrusted/revoked key may remain cryptographically valid without authority | PASS | signer-trust tests |
| missing/cross-scope predecessor detected | PASS | linear-order negative tests |
| fork represented without automatic branch selection | PASS | fork test; `canonical_child = null` |
| linear chain does not claim completeness or non-equivocation | PASS | evaluator/tests/artifact explicitly return false |
| later supersession/currentness does not rewrite historical commitment | PASS | temporal currentness test and schema |
| UOR/content identity cannot satisfy PAMA | PASS | same-head UOR compatibility/PAMA evidence; authority effect remains none |
| wrong external witness subject/profile rejected | PASS | witness binding tests |
| witnessed time is not event occurrence time | PASS | witness interpretation/test/artifact |
| optional UOR failure is isolated to optional profile | PASS | local injected-address test |
| exact UOR-Addr v0.2.0 temporal-object profile composes without importing UOR authority | PASS | focused temporal run plus independent same-head UOR Python/Rust evidence |

## Review findings resolved before acceptance

The first green implementation was not promoted. Review required:

- reference-profile identity alongside predecessor and witness references;
- recomputation of content-reference bindings during fork detection;
- separate append-only currentness/supersession evidence;
- rejection of null-only temporal claims;
- identical light/dark reader semantics in the documentation visual.

## Boundary

Acceptance establishes the layered temporal-commitment doctrine. It does not establish a production time-witness service, require one algorithm or UOR runtime, prove complete global history, or turn cryptographic validity into currentness or authority.

Promoting the ADR changes the head. The accepted head must therefore rerun the complete validation matrix before merge.
