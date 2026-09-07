# UOR-Addr JSON content-reference profile

**Status:** Optional interoperability profile V0.1  
**Issue:** #232  
**Decision context:** ADR-028

## Boundary

This profile tests one narrow claim: Agent Memory can use UOR-Addr v0.2.0 JSON addressing for immutable content references without making UOR identity, lifecycle, or authority semantics canonical.

Ordinary Agent Memory conformance does not require a UOR runtime.

Pinned external source:

- `UOR-Foundation/uor-addr`
- release `v0.2.0`
- tag object `4bdc4ec022bbc99b3c1ec01a67b40a7e25f30de4`
- source commit `d78f82f26034880e91b1d54c21900a33ab73f695`
- Apache-2.0
- JSON realization: RFC 8259 + RFC 8785 JCS + UAX #15 NFC + SHA-256

A verified content address remains distinct from logical memory identity, lifecycle currentness, recall admission, evidence certification, isolation permission, PAMA mutation authority, and deletion/export authority. This profile does not replace `memory_unit.id`.

## Candidate surfaces

Potential bounded uses are immutable evidence content references, receipt artifacts, immutable revision snapshots, derivation/output custody references, and lineage targets that denote content identity rather than logical memory identity.

## Cross-language evidence

The focused workflow compares the released Python package `uor-addr==0.2.0` with the Rust crate at the exact pinned source commit using the same JSON vectors. Exact `sha256:<64hex>` label equality is required.

The vectors cover key order and insignificant whitespace, NFC/NFD Unicode normalization, numeric `42` versus string `"42"`, and materially different canonical content.

## Failure posture

Malformed labels, content/address mismatches, unsupported or unknown profile metadata, invalid typed input, and unavailable UOR bindings are explicit failures. No such condition widens Agent Memory authority. Missing UOR support disables only this optional profile path.

Focused tests also prove that a valid content reference does not discharge existing PAMA review and does not repair an isolation-domain mismatch.

## Dependency and license posture

This slice does not copy UOR implementation code, vendor the runtime, or add UOR as an ordinary Agent Memory dependency. The comparator installs the released Python binding and checks out the pinned Rust source only in CI. Redistribution of UOR implementation artifacts would require a separate attribution/NOTICE review.

## Non-claims

UOR conformance is not Agent Memory conformance. Rust is not the normative Agent Memory language. This slice does not adopt `kappa-registry` or `uor-r4`, and it imports no UOR governance semantics into PAMA or lifecycle doctrine.
