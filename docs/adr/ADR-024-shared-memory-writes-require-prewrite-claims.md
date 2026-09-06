# ADR-024: Shared Memory Writes Require Pre-Write Claims

Status: Accepted

Date: 2026-08-12

## Context

Issues #137 and #138 identify durable memory mutation as more than a retrieval problem. Shared agent memory must answer both what becomes memory and who may change durable state.

In multi-agent systems, uncoordinated writes can create silent overwrites, stale updates, authority laundering, and conflict resolution after the damage has already been committed. The existing repository doctrine already includes PAMA mutation authority, conflict resolution, temporal causality, audit events, and concurrency evidence. This ADR makes the pre-write coordination requirement explicit.

## Decision

Shared durable memory writes require a pre-write claim, lock, lease, compare-and-swap guard, single-writer queue, transactional reservation, or equivalent coordination mechanism before durable state changes.

The coordination mechanism must bind the actor, task, scope, proposed mutation class, authority basis, timestamp, and expiration or validity behavior before commit.

Conflicting writes must fail closed or route into conflict resolution before commit. The system must not rely on post-hoc cleanup as the primary protection against unauthorized or conflicting shared-state mutation.

Failed, rejected, expired, superseded, or unauthorized claims remain governance evidence.

A valid coordination claim is not mutation authority. PAMA or the applicable mutation-authority policy still evaluates the proposed durable consequence after coordination succeeds.

## Rationale

Shared memory is trust infrastructure. Trustworthy mutation requires deciding authority and conflict boundaries before durable state changes, not after competing agents have already overwritten each other.

This ADR does not require a specific distributed locking primitive. Different runtimes may use leases, transactions, compare-and-swap, optimistic concurrency, queue ownership, or database-native locks. The architectural requirement is that durable mutation is coordinated and auditable before commit.

## Consequences

### Positive

- Concurrent writers have an explicit coordination boundary.
- Conflict resolution happens before durable mutation.
- Stale and unauthorized claims become testable negative paths.
- Audit trails include both successful and failed write attempts.
- PAMA can evaluate mutation authority against a bounded claim rather than an already-mutated state.

### Negative

- Implementations must manage claim expiry and abandoned work.
- Systems must avoid deadlock, stale locks, and over-broad claims.
- Claim granularity becomes an architectural decision.
- Runtime adapters need evidence formats for both successful and failed claims.

## Implementation notes

A conforming implementation should record at least:

- claim identifier;
- actor identity;
- task or operation identifier;
- memory scope or affected record set;
- requested mutation class;
- authority basis;
- timestamp and expiry or lease terms;
- current claim status;
- conflict disposition;
- commit receipt or rejection reason.

The claim must be narrow enough to prevent accidental broad authority and durable enough to support audit review.

Immediately before durable commit, implementations must revalidate claim validity against the current proposal and state. A claim that has expired, become stale, lost its authority basis, or no longer matches actor/task/scope/target/mutation must not be treated as current coordination authority.

## Acceptance evidence

ADR-024 advanced from Proposed to Accepted only after the repository added executable evidence for every acceptance condition named below.

### Successful claimed write

`shared-write-valid-claim.json` and the reference claim-coordinator tests prove that an authorized, current, unexpired claim can acquire the coordination boundary and then proceed through the ordinary governed adapter to a committed mutation.

### Concurrent conflict before commit

`shared-write-conflicting-claim.json` proves a second active claim for the same shared scope/target is rejected before either writer can silently win through durable overwrite.

### Stale and expired claims

`shared-write-stale-claim.json` proves stale state is rejected. Reference tests separately prove both an already-expired claim and a lease that expires after acquisition but before commit fail closed without substrate mutation.

### Unauthorized claim

`shared-write-unauthorized-claim.json` proves a claim whose authority basis cannot be resolved is rejected before durable mutation.

### Audit evidence

The reference coordinator emits schema-valid audit events for:

```text
memory.write_claim_acquired
memory.write_claim_rejected
memory.write_claim_expired
memory.write_claim_committed
```

Successful and failed claim outcomes therefore remain reconstructable governance evidence.

### PAMA composition

A dedicated negative test proves a valid coordination claim cannot override a later PAMA `block`. Coordination grants only the bounded opportunity to attempt the write; it never grants the durable consequence itself.

### Doctrine integration

`docs/17-conflict-resolution-engine.md` now defines concurrent write conflict as a pre-commit concern and records the ordering:

```text
proposal intent
  -> pre-write coordination claim
  -> conflict / lease / state validation
  -> PAMA authority envelope
  -> permitted action selection
  -> durable mutation or refusal
  -> audit / conflict evidence
```

This composes ADR-024 with PAMA, conflict resolution, temporal/state validity, and observability without introducing a parallel authority model.

The reference `SharedWriteCoordinator` is evidence for the contract, not the normative implementation. Agent Memory continues to permit any coordination primitive that satisfies the accepted boundary.

## Acceptance boundary

Acceptance means the architectural requirement has satisfied its named repository evidence gate. It does not claim:

- distributed serializability across arbitrary runtimes;
- one universal lock or lease algorithm;
- deadlock freedom for every implementation;
- production conformance merely because the reference mechanism passes;
- that acquiring a claim authorizes a durable mutation.

Those claims require their own evidence.

## Related

- #137
- #138
- #143
- ADR-004: PAMA Controls Mutation Authority
- ADR-010: Conflict Resolution Is a Separate Component
- ADR-011: Temporal Causality Is Required for Memory Evolution
- ADR-017: Memory Observability and Audit Events Are Required
- ADR-020: Probabilistic Discovery, Deterministic Governance
