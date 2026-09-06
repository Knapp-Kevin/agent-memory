# ADR-027: Rejected Values Require Governed Re-Admission

Status: Proposed

Date: 2026-08-12

## Context

ADR-023 proposes that durable corrections preserve history through supersession rather than destructive deletion. That protects auditability and prevents the superseded row from remaining current.

A separate failure remains possible in principle: a later extractor, import, background process, or agent may propose the same rejected value under a fresh record identity. If the write path considers only record identity and current retrieval state, the old proposition can become current again even though the original row remains correctly superseded.

Agent Memory Atlas surfaced this as a candidate external failure pattern. Atlas is not authority for this ADR. Issue #147 requires the repository to reproduce or falsify the failure directly against the reference adapter before this ADR can advance.

## Candidate decision

If a durable value has been explicitly rejected through a governed correction, a later materially equivalent value must not silently regain current status solely because it arrives under a new proposal, record, source, or extraction identity.

Re-admission must be a governed lifecycle transition.

For an exact, deterministically identifiable rejected value, the default write-path consequence should fail closed into a non-committing state such as:

```text
defer
require reconciliation
require new evidence
require review
```

The prior rejection is **not** an eternal ban. A later reversal may be legitimate when new evidence and appropriate authority justify it.

Therefore the intended invariant is:

> **Rejected value != permanently forbidden value. Rejected value == value that cannot silently become current again.**

## Deterministic and probabilistic boundary

Exact or structured identity may be enforced deterministically where the representation supports it.

Semantic equivalence is different. A probabilistic matcher may identify that a new proposal resembles previously rejected content, but estimator similarity must not independently authorize either rejection or re-admission.

A semantic matcher may route a proposal to reconciliation or review. The governed consequence remains deterministic under the applicable authority policy.

## Required evidence state

A conforming implementation may use different schemas, but it must preserve enough state to reconstruct:

- which memory/proposition was corrected;
- which value identity was rejected;
- which correction established the rejection;
- evidence and authority supporting that correction;
- scope/isolation context;
- whether the rejection is currently active;
- any later authorized re-admission or reversal;
- the decision receipt for blocked or permitted re-admission.

The repository should avoid storing duplicate raw sensitive content solely to implement rejection history when a stable scoped fingerprint or structured identity is sufficient.

## Relationship to ADR-023

ADR-023 and this ADR solve different problems:

```text
ADR-023
old record must not remain current after correction

ADR-027
old value must not silently become current again as a fresh record
```

A system may satisfy one and fail the other.

Deletion, erasure, retention expiry, and safety removal remain separate lifecycle paths.

## Consequences

### Positive

- Correction survives fresh-identity re-extraction.
- Read-path suppression is no longer mistaken for write-path protection.
- Legitimate reversals remain explicit and auditable.
- Re-admission can compose with PAMA rather than creating a hidden blacklist authority.
- Exact-value protection can remain deterministic while semantic similarity remains an estimator input.

### Negative

- Durable correction requires additional lifecycle metadata or an equivalent rejection registry.
- Value identity is architecture/domain dependent and cannot be reduced safely to one universal string hash.
- Semantic equivalence remains an open problem and may require review-oriented estimators.
- Rejection history itself becomes governed state with privacy, retention, and deletion implications.

## Validation and acceptance

This ADR must remain Proposed until #147 demonstrates all of the following with executable evidence:

- the pre-fix reference behavior can reproduce fresh-identity re-admission under the controlled scenario;
- supersession of the original row is proven separately from the re-admission failure;
- the write path blocks exact rejected-value re-entry after the implementation change;
- the block emits reconstructable evidence rather than silently dropping the proposal;
- an explicitly approved, evidence-backed reversal can re-admit the value;
- the prior rejection remains historically reconstructable after reversal;
- a probabilistic semantic matcher, if introduced, cannot independently authorize durable mutation;
- tests clearly state that exact-value evidence does not prove architecture-independent semantic equivalence handling.

## Related

- #147
- #142
- #148
- #146
- ADR-010: Conflict Resolution Is a Separate Component
- ADR-015: Retention, Deletion, and Tombstones Are Required
- ADR-020: Probabilistic Discovery, Deterministic Governance
- ADR-023: Corrections Are Supersession, Not Deletion
