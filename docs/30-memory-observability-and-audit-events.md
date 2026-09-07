# Memory Observability and Audit Events

> Canonical requirement: [ADR-017](adr/ADR-017-memory-observability-and-audit-events-are-required.md)

## Purpose

Governed memory requires more than logs that say something happened.

A consequential memory event should make it possible to reconstruct:

```text
what was observed or estimated
which state existed
which policy and authority applied
what was permitted and prohibited
what was selected
what changed
what recovery path exists
```

## Event classes

Canonical event families include:

- `memory.created`
- `memory.linked`
- `memory.signal_computed`
- `memory.state_transition_proposed`
- `memory.state_changed`
- `memory.retrieval_candidate`
- `memory.recall_admission_decided`
- `memory.recalled`
- `memory.mutation_requested`
- `memory.authority_decided`
- `memory.action_selected`
- `memory.certification_requested`
- `memory.certification_completed`
- `memory.dispute_opened`
- `memory.corrected`
- `memory.archived`
- `memory.pruned`
- `memory.tombstoned`
- `memory.deleted`
- `memory.scope_changed`
- `memory.component_handoff`
- `memory.recovery_started`
- `memory.recovery_completed`
- `conformance.fixture_run`

Implementations may add events but should map them to the canonical families when claiming interoperability.

## Common event envelope

```text
event_id
event_type
event_version
timestamp
memory_id
actor
principal
component
correlation_id
causation_id
policy_version
state_snapshot
sensitivity
payload
```

## Governed-uncertainty fields

When an estimate materially affects consequence, events should preserve:

```text
signal_type
signal_semantics
signal_value
estimator_id
estimator_version
calibration_ref
uncertainty
```

When policy acts on that estimate:

```text
authority_refs
permitted_actions
prohibited_actions
selected_action
selection_mode
```

## Correlation and causation

Use `correlation_id` to group events from one operation or workflow.

Use `causation_id` to identify the event that directly caused another event when that relation is known.

Do not use temporal adjacency as proof of causation.

## Event privacy

Audit events can themselves contain sensitive memory.

Prefer references, hashes, categorical summaries, and redacted fields when full content is unnecessary.

Event retention must follow privacy and deletion policy rather than becoming an undeletable shadow copy of the memory store.

## Replayability

Observability should support reconstruction of authority and state consequence even when an estimator cannot reproduce the exact sampled output.

A receipt may record the original estimate instead of requiring the model to regenerate it.

## Integrity

High-consequence audit records should support tamper evidence where practical, such as:

- append-only storage
- content hashes
- signed receipts
- immutable event IDs
- chained references

The doctrine does not require one ledger technology.

## Minimum events by consequence

### Ephemeral cognition

Detailed persistent audit may be unnecessary.

### Durable mutation

Require state, policy, authority, before/after state, evidence, and receipt references.

### Sensitive disclosure

Require requester, destination, scope/sensitivity decision, policy version, and result without unnecessarily duplicating sensitive content.

### Irreversible deletion

Require deletion request, authority, mode, dependencies, verification, residual copies, and result.

## Conformance cases

- policy version missing from durable mutation receipt
- estimator version missing from high-consequence classifier decision
- audit event leaks raw credential unnecessarily
- stochastic selection event omits permitted action set
- state transition cannot be tied to its authorization
- deletion event claims success while derived residue remains

## Schema

The canonical machine-readable envelope is:

```text
schemas/memory-audit-event.schema.json
```

## Doctrine

Observability is not the number of log lines.

It is whether the system can reconstruct the evidence, uncertainty, authority, and consequence that produced durable memory behavior.
