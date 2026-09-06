# Memory-Native Logical State Algebra Research Closeout

Status: **Completed research / #276**

Decision: `no_new_algebra`

ADR disposition: **no new ADR**

## Conclusion

Agent Memory does not currently need a new memory-native logical state algebra or stronger custom state engine above replaceable persistence.

The tested logical responsibilities are already expressible through the existing combination of:

```text
logical identity + provenance
lifecycle / correction / supersession
derivation + currentness + custody
scope / isolation
PAMA consequence authority
maintenance transactions + validation
deletion / residue obligations
conditional-memory influence boundaries
evidence / receipts
component capability + qualification contracts
```

A second algebra would currently duplicate those semantics rather than close a demonstrated correctness gap.

## Evidence basis

### Cross-substrate pressure test

PR #277 mapped the same correction/currentness problem across materially different persistence families:

- relational/document;
- knowledge/temporal graph;
- event-log/ledger.

The physical mechanics differ, but each can preserve the same Agent Memory distinctions without a new universal state engine:

```text
logical identity != physical key
historical evidence != current truth
physical presence != currentness
transaction success != lifecycle closure
derived residue != valid current state
```

The dedicated `Logical State Algebra Pressure` workflow passed at exact research head `9f6bdbc415afdf57823d806312c33bd833cd1cb6`, run `31800258733`.

### Existing primitive inventory

The candidate transition vocabulary was found to map onto existing contracts:

```text
observe / ingest
  -> identity + provenance + proposal/commit evidence

link / derive
  -> derivation + currentness + custody

revise / correct / challenge / supersede
  -> lifecycle + temporal causality

reinforce / weaken
  -> estimator/scoring evidence, not authority

consolidate / semanticize
  -> derived state + maintenance transaction + validation

promote / crystallize
  -> lifecycle + PAMA

invalidate / stale
  -> lifecycle/currentness

rebuild projection
  -> derivation currentness + maintenance transaction

forget / delete / purge
  -> deletion consequence + residue/lifecycle satisfaction

predict / influence
  -> conditional-memory influence gate

re-evidence / revalidate
  -> currentness/evidence transition
```

No candidate operation demonstrated a missing general semantic primitive merely by being renamed as an algebraic transition.

### Component implementation pressure

The #274 implementation program subsequently added real component-facing structure without requiring a new state algebra:

- PR #297 established machine-readable component/capability declarations, maturity, deterministic provider resolution, overlap failure, and a governed procedural-memory vertical slice.
- PR #299 / completed #298 established the version-bound adapter and capability-qualification contract without introducing a new lifecycle/state engine.
- PR #302 exercises two materially different real code-graph providers through the same qualification surface while preserving provider-native evidence, currentness, exact applicability, and authority separation.

The CodeGenome defect exposed by PR #302 was a provider semantic-resolution bug, not evidence of a missing Agent Memory state algebra. It was repaired in CodeGenome #12 / PR #13 by preserving file identity in symbol/span resolution. The qualification contract remained sufficient to detect, refuse, repair, and re-test the provider.

Likewise, Graphify's `links` versus `edges` mismatch was an adapter normalization defect, not a missing state primitive.

This is meaningful falsification pressure: real implementation failures occurred, and neither required inventing a new universal logical engine to resolve them.

## External pressure

Agent Manifest #298 reinforces, rather than overturns, the current result:

```text
state-transition integrity
!= semantic/retrieval correctness
!= lifecycle correctness
!= downstream authority
```

That separation is already represented by Agent Memory's existing currentness, lifecycle, admission, authority, and evidence surfaces.

## Rejected outcomes

### `stronger_engine`

Not justified. No tested case requires Agent Memory to implement a new database-like logical runtime, uniform WAL/MVCC layer, universal conflict engine, or storage-specific transaction system.

### `profile_specific`

Not required as a research conclusion. Backend-specific mechanics remain explicit through component/capability profiles, but they do not require separate competing Agent Memory semantic models.

### `narrow_transition_contract`

Not required now. This remains the only plausible future escalation if at least two materially different component families repeatedly recreate an incompatible envelope equivalent to:

```text
requested transition
+ target logical identity
+ source/currentness basis
+ scope/isolation basis
+ estimator evidence
+ PAMA decision
+ backend transaction result
+ post-write validation
+ lifecycle result
+ reconstructable receipt
```

Mere repetition of adapter boilerplate is insufficient. The gap must cause an actual correctness, recovery, interoperability, or evidence problem.

## Future falsification trigger

Reopen this architectural question only if implementation demonstrates a recurring requirement that existing contracts cannot faithfully express, such as:

- cross-component atomic logical transitions required for correctness;
- uniform durable conflict/reconciliation semantics that cannot remain backend/profile specific;
- recovery/replay semantics that must be shared across materially different substrates;
- shared logical versioning that cannot safely remain represented through current identity/currentness contracts;
- lifecycle closure that must span several physical modules in one indivisible governed transaction.

Until such evidence exists:

```text
recommendation = no_new_algebra
new ADR = not warranted
new physical persistence engine = not warranted
```

The appropriate next work remains implementation and qualification of the existing component/runtime contracts, not creation of another foundational abstraction.
