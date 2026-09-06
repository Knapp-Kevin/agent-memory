# Concurrency conflict evidence

This runtime-evidence slice exercises ADR-020 acceptance item 9 against the existing [`concurrent-conflicting-mutation`](../../../fixtures/concurrent-conflicting-mutation.json) doctrine fixture.

## Question under test

When two actors form incompatible durable mutation proposals from the same prior canonical state, can the later commit silently overwrite the first simply because it arrived last?

The required answer is no.

```text
proposal A observes v0
proposal B observes v0
        |
        +-- A commits against v0 -> canonical state becomes v1
        |
        +-- B attempts commit carrying snapshot v0
                -> current state is re-read as v1
                -> authorization is stale
                -> B is deferred, not committed
                -> conflict is recorded in machine-readable evidence
```

## Executed reference path

`reference/agentmem_ref/concurrency_evidence.py` constructs two proposals before either consequence is committed. Both carry `state_snapshot = v0`.

The reference adapter commits proposal A. Its canonical state version advances to `v1` and exactly one substrate fact is written.

Proposal B then reaches the same governed commit boundary with its original `v0` authorization snapshot. `GovernedMemoryAdapter._is_stale()` compares that signed/recorded proposal snapshot to the current state, sees `v1`, and prevents B's requested mutation from being selected. The receipt records:

- requested state snapshot `v0`;
- observed/before state `v1`;
- unchanged after state `v1`;
- selected action `defer`;
- refusal `stale_authorization`.

The concurrency evidence report then records the winning and rejected proposal IDs, the rejected receipt reference, expected and observed state refs, resolution, and refusal reason.

## Invariants

The run is successful only when its observed behavior exactly matches the independently authored fixture:

```text
silent_last_writer_wins = false
conflict_recorded = true
state_version_revalidated = true
```

It additionally asserts:

- exactly one substrate `write_fact` operation occurred;
- exactly one fact survives;
- final canonical state is `v1`;
- the rejected proposal did not advance state;
- the conflict is reconstructable from the rejected receipt and state references;
- repeated runs at the same exact commit are byte-for-byte equivalent after JSON serialization.

## Machine-readable evidence

Run locally:

```bash
python reference/run_concurrency_evidence.py \
  --agent-memory-commit <exact-40-hex-commit> \
  --output concurrency-evidence.json
```

The output conforms to [`schemas/concurrency-evidence.schema.json`](../../../schemas/concurrency-evidence.schema.json).

CI supplies the exact pull-request head or push commit, fails if the fixture expectations are not met, and uploads the JSON as an artifact.

## What this proves

This demonstrates an optimistic state-version concurrency boundary in the reference implementation:

> Authorization resolved against stale durable state cannot silently commit as though the state were unchanged.

It also converts a pre-existing unit behavior, `stale_authorization`, into explicit fixture-correlated runtime evidence for the concurrent-conflict requirement.

## What this does not prove

This slice does not claim:

- distributed serializable transactions;
- multi-process locks;
- linearizability across independent Agent Memory services;
- database-native compare-and-swap support;
- exhaustive thread-scheduler exploration;
- automatic semantic merge of conflicting mutations;
- acceptance of ADR-020;
- any higher Agent Memory conformance level.

The scenario is deterministically interleaved so both proposals originate from the same prior state. That is sufficient to test the stale-authorization consequence boundary without pretending a single-process reference harness has suddenly become Spanner.
