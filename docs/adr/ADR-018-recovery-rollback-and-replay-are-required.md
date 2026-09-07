# ADR-018: Recovery, Rollback, and Replay Are Required

## Status

Accepted

## Context

Governed memory systems will make mistakes.

A memory may be incorrectly promoted, wrongly corrected, over-pruned, recalled into unsafe context, mutated under insufficient authority, or committed from stale authorization.

If the system cannot recover from these events, governance becomes performative. Performative governance is just theater with YAML.

## Decision

Agent Memory defines recovery, rollback, and replay semantics.

Implementations should be able to reconstruct consequential decision paths, restore or compensate for unsafe mutations when policy allows, demote incorrectly durable memory, revoke certification, and preserve incident evidence.

Exact replay of stochastic cognition is not always required or possible.

The required invariant is reconstruction of:

```text
what was observed/estimated
which policy and authority applied
what actions were permitted/prohibited
what action was selected
what state changed
what recovery path exists
```

## Consequences

### Positive

- makes unsafe transitions recoverable
- supports incident review and conformance debugging
- improves correction and certification trust
- preserves accountability even when model outputs are stochastic

### Negative

- requires ledger integrity and ordering
- requires state/version binding
- may conflict with privacy/deletion requirements unless retention is explicit

## Required recovery capabilities

- reconstruct memory transition history
- identify unsafe transition source
- reject stale authorization at commit
- roll back or compensate for unauthorized mutation
- demote incorrectly crystallized memory
- restore mistakenly pruned memory when retention allows
- revoke certification
- preserve incident evidence within privacy constraints

## Acceptance evidence

Canonical contract:

- [`../31-recovery-rollback-and-replay.md`](../31-recovery-rollback-and-replay.md)

Repository fixtures include:

- `stochastic-replay-reconstruction.json`
- `policy-estimator-version-drift.json`
- `concurrent-conflicting-mutation.json`
- `deletion-residue.json`

Decision-receipt and audit-event schemas preserve the evidence needed for reconstruction.

## Acceptance scope

Accepted establishes recovery/reconstruction as canonical doctrine. It does not claim every runtime already supports automatic rollback or complete dependency repair.

## Doctrine

A governed memory system must recover from its own mistakes without pretending stochastic cognition has to be byte-for-byte replayable.
