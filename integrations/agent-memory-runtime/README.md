# Agent Memory Runtime Adapter

A bounded, host-neutral ESM adapter for governed runtime recall and correction/supersession.

It exists to let a runtime host consume Agent Memory doctrine without copying memory semantics into the host. It is intentionally not a complete Agent Memory implementation.

## What this adapter owns

- exact actor/project/task scope validation;
- recall admission after candidate loading;
- rejection of unknown-scope, foreign-scope, disputed, and superseded memory;
- explicit `authority_effect: "none"` on recall;
- correction as an append-only replacement plus supersession linkage;
- evidence and authority requirements for committed correction;
- semantic correction receipts on first commit and idempotent replay;
- stale-state refusal.

## What the storage port owns

The host supplies three persistence methods:

```text
load(scope)
getCorrection(scope, idempotencyKey)
commitCorrection(scope, transaction)
```

The storage port persists mechanics, not Agent Memory's public receipt semantics.

`getCorrection` returns either `null` or the low-level persisted commit record originally produced by `commitCorrection`:

```text
revision
checkpoint
ledger_ref
replacement
  # the exact replacement memory record supplied by Agent Memory
event
  # the exact correction event supplied by Agent Memory
replayed
```

The host must not manufacture `contract_version`, adapter identity, supersession receipts, authority/evidence projection, or other Agent Memory public fields. The Agent Memory adapter reconstructs those semantic fields from the persisted replacement/event record on both first commit and replay.

`commitCorrection` must atomically:

1. return the original persisted commit record with `replayed: true` if the idempotency key already exists;
2. otherwise enforce `expected_revision`;
3. persist the replacement memory and correction event without erasing prior history;
4. advance revision/checkpoint state;
5. bind the idempotency key to the resulting low-level commit record; and
6. return that record.

The idempotency check must also occur inside the atomic commit boundary. A retry racing after the caller's initial `getCorrection` lookup must return the already-committed replacement/event identities rather than apply a second candidate mutation.

A genuinely new correction that sees an old `expected_revision` must fail with:

```js
{ code: 'STALE_REVISION' }
```

The adapter converts that to the semantic `stale_state` refusal.

For the QOR Agent Cloudflare proving ground, this storage port is implemented by a scoped SQLite Durable Object. That Cloudflare implementation belongs to QOR Agent, not this repository.

## Recall

```js
const result = await memory.recall({
  scope: {
    actor_id: 'actor:one',
    project_id: 'project:alpha',
    task_id: 'task:release-marker',
  },
  policy_version: 'policy-v1',
  purpose: 'release_target_recall',
});
```

The result separates `admitted` and `rejected` candidates and reports the storage `revision` and `checkpoint`. Candidate relevance does not grant execution authority, standing permission, or a consumer policy verdict.

## Correction

```js
const receipt = await memory.correct({
  scope,
  memory_id: 'memory-original',
  idempotency_key: 'correction:123',
  policy_version: 'policy-v1',
  evidence_refs: ['evidence:user-correction'],
  authority_refs: ['authority:human-confirmed'],
  replacement: {
    kind: 'correction',
    value_ref: 'value:main',
  },
});
```

The prior memory remains historical. The replacement carries `supersedes: [prior_memory_id]`, and active recall rejects the superseded record.

An idempotent retry returns the same semantic correction identity and commit time, with `replayed: true`; persistence does not recreate that public receipt.

## Doctrine boundary

This package implements the bounded seam described by:

- `docs/34-adapter-contracts.md` runtime memory adapter;
- `docs/34-adapter-contracts.md` correction and dispute adapter;
- the repository's scope, tenancy, authority, and historical-truth distinctions.

It does not implement PAMA, standing authorization, a general retrieval engine, ranking, embeddings, a production approval system, or a universal durable store.

Tracks `MythologIQ-Labs-LLC/agent-memory#333` and defect correction `MythologIQ-Labs-LLC/agent-memory#335`, under the pre-cloud route in `MythologIQ-Labs-LLC/Myth-Tech-Forge#262`.
