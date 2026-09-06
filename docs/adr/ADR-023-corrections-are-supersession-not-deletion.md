# ADR-023: Corrections Are Supersession, Not Deletion

Status: Proposed

Date: 2026-08-12

## Context

Issues #137 and #138 examine durable memory governance boundaries around what becomes memory, who may change durable state, and how memory changes remain auditable.

Correction handling sits directly on that boundary. If a corrected memory is deleted, the current state may look clean, but the system loses the causal trail that explains why the decision, preference, instruction, or fact changed. That weakens auditability, replay, rollback, and governance review.

The repository already separates memory lifecycle, scoring and decay, temporal causality, retention/deletion, audit events, PAMA mutation authority, and conflict resolution. This ADR does not replace those components. It makes the correction-specific decision explicit so implementation issues can compose with the existing doctrine rather than inventing a parallel mutation model.

## Decision

Ordinary correction of durable memory must be modeled as append-only supersession, not destructive deletion.

A correction creates a new durable memory record that identifies the earlier record it supersedes. The earlier record remains available for audit, provenance, and causal reconstruction unless a separate deletion, erasure, or safety policy requires removal.

The superseded record must no longer compete as current truth. It must be marked as corrected, superseded, or equivalent; linked to the replacement where available; and excluded from ordinary recall or demoted strongly enough that it cannot silently win over the correcting record.

Deletion and erasure remain distinct lifecycle paths. User-requested deletion, legal erasure, safety-driven removal, and retention expiry are not reclassified as correction.

## Rationale

Auditability requires explaining why durable state changed, not merely presenting the latest value.

Append-only supersession preserves the old record, the correcting record, the relationship between them, and the authority evidence that allowed the change. This supports temporal causality, replay, rollback, governance review, and negative-path testing.

Destructive correction is attractive because it reduces surface area. It is also a convenient way to make uncomfortable history vanish, which is precisely why it is not acceptable as the default correction path.

## Consequences

### Positive

- Correction history remains auditable.
- Durable memory can explain how and why a prior belief, preference, instruction, or decision changed.
- Recall can avoid stale truth while preserving provenance.
- Conformance tests can verify both current recall behavior and historical reconstruction.
- Deletion and erasure policy remain separate and explicit.

### Negative

- Storage systems must retain more records.
- Retrieval systems must understand lifecycle state and supersession links.
- User interfaces and APIs must avoid presenting superseded records as current truth.
- Implementations need clear boundaries between correction, retention expiry, tombstoning, and erasure.

## Implementation notes

A conforming implementation should represent at least:

- the correcting memory record;
- the superseded memory record;
- a `supersedes`, `superseded_by`, or equivalent relationship;
- lifecycle state indicating corrected or superseded status;
- authority evidence for the correction;
- recall policy that excludes or heavily demotes superseded records in ordinary retrieval;
- audit policy that can still surface superseded records as historical evidence.

The exact field names are implementation-specific, but the semantics are not optional.

## Validation and acceptance

This ADR should not advance beyond Proposed until the repository includes evidence for:

- a fixture where a corrected record remains auditable after supersession;
- a recall test where the superseded record does not win ordinary retrieval;
- a negative-path test where superseded content cannot silently overwrite the replacement;
- documentation updates distinguishing correction/supersession from deletion/erasure;
- scoring or recall documentation defining demotion or exclusion behavior for superseded records.

## Related

- #137
- #138
- #142
- ADR-011: Temporal Causality Is Required for Memory Evolution
- ADR-015: Retention, Deletion, and Tombstones Are Required
- ADR-017: Memory Observability and Audit Events Are Required
- ADR-020: Probabilistic Discovery, Deterministic Governance
