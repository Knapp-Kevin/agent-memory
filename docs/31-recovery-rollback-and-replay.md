# Recovery, Rollback, and Replay

> Canonical requirement: [ADR-018](adr/ADR-018-recovery-rollback-and-replay-are-required.md)

## Purpose

Governed memory must assume that some accepted writes, recalls, corrections, and deletions will later prove wrong or unsafe.

Recovery defines how the system detects, contains, reconstructs, and repairs those failures.

## Recovery goals

A recovery-capable implementation should be able to:

- reconstruct a consequential decision
- identify the affected memory and dependents
- block continued unsafe use
- roll back when rollback is valid
- compensate when exact rollback is impossible
- revoke certification or authority
- preserve incident evidence where policy allows
- respect deletion/privacy constraints during recovery

## Replay versus regeneration

Replay means reconstructing the recorded decision path.

It does **not** require a stochastic model to emit the same tokens or score when rerun.

Required reconstruction:

```text
recorded observation/estimate
estimator/version
policy/version
authority
permitted actions
selected action
state before
state after
evidence
```

## Recovery modes

### Rollback

Restore a prior valid state when the mutation is reversible and dependencies permit it.

### Compensating transition

Create a new corrective state when historical mutation cannot or should not be erased.

### Demotion

Move incorrectly durable/canonical memory into stale, disputed, pending verification, or another lower-authority state.

### Certification revocation

Invalidate a prior certificate while preserving why it was revoked.

### Recall quarantine

Prevent unsafe memory from entering context while investigation proceeds.

### Dependency repair

Recompute or dispute derived memories that depended on corrupted state.

Recomputation is itself a governed transition where the derivation involves an estimator, because it commits new content rather than restoring old content. Repair triggered automatically by staleness detection would let an estimator write whenever it can cause a version change. See [`programs/runtime-evidence/canonical-and-derived-state.md`](programs/runtime-evidence/canonical-and-derived-state.md), which is design work rather than adopted doctrine.

## State/version binding

Authorization should bind to the state version it evaluated.

```text
authorized_at_version = 12
current_version = 13
=> commit requires revalidation
```

This prevents stale authorization from mutating newer state.

## Concurrent mutation

Durable memory must not silently use last-writer-wins when two authorized proposals conflict materially.

Possible strategies:

- compare-and-swap/version check
- explicit merge
- conflict record
- retry/re-evaluate
- human or policy escalation

The chosen strategy is implementation-specific; silent conflict erasure is not.

## Recovery graph

Incident analysis should identify:

```text
root_or_suspected_memory
incoming evidence
outgoing derivations
retrieval uses
state transitions
certificates
downstream actions
exports/shares
```

This enables blast-radius analysis.

## Privacy conflict

Recovery evidence can conflict with deletion requirements.

Policy should define whether to retain:

- redacted incident metadata
- content hashes
- restricted legal/audit copy
- no content at all

A deleted memory should not be resurrected merely to make debugging convenient.

## Recovery receipts

```text
recovery_id
incident_ref
affected_memory_refs
detected_at
containment_actions
state_before
state_after
policy_version
authority_refs
rollback_or_compensation
certification_changes
dependency_actions
residual_risk
completed_at
```

## Failure cases

- incorrect crystallization
- malicious correction
- stale policy authorization
- cross-tenant recall
- poisoned summary
- procedure drift
- derived-memory deletion residue
- concurrent conflicting writes
- mistaken pruning
- unsafe inherited memory

## Conformance cases

### Stale authorization

Expected: version mismatch prevents commit until re-evaluated.

### Incorrect crystallization

Expected: certificate can be revoked and memory demoted without erasing audit history.

### Concurrent mutation

Expected: conflict is explicit; no silent last-writer-wins.

### Stochastic estimator replay

Expected: original recorded estimate and policy decision can be reconstructed even if rerun differs.

### Deleted memory incident

Expected: recovery respects deletion policy and does not casually restore erased content.

## Doctrine

Recovery is not an admission that governance failed.

Pretending governed systems never fail would be the failure.
