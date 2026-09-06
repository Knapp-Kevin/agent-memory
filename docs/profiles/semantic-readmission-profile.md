# Semantic Re-Admission Review Profile

## Purpose

This optional profile extends the exact rejected-value protection of ADR-027 into cases where a later proposal may be a paraphrase or semantically equivalent restatement of an actively rejected value.

It does **not** redefine memory identity and does not claim that semantic equivalence is deterministic, architecture-independent, or universally decidable.

The governing split is:

```text
exact / structured rejected identity
  -> deterministic rejection lookup
  -> exact write-path protection

semantic similarity
  -> estimator signal with provenance
  -> deterministic reconciliation routing
  -> ordinary governance / review / PAMA
```

A semantic estimator proposes that reconciliation may be needed. It does not decide whether the earlier rejection was correct, whether the new proposal is truly equivalent, or whether durable state may change.

## Why this is a profile

Raw string normalization can safely collapse presentation differences such as case and repeated whitespace. It cannot safely collapse arbitrary paraphrase, domain-specific equivalence, translation, inference, or changed factual context.

Different implementations may use:

- domain-specific structured keys;
- proposition/value schemas;
- embeddings;
- classifiers;
- LLM adjudication candidates;
- hybrid retrieval over prior correction evidence.

Those techniques have different calibration, privacy, portability, and failure properties. None belongs in canonical identity merely because it can find similar text.

The profile therefore standardizes the **authority boundary**, not the estimator.

## Rejection record

The reference rejection record retains no raw rejected content. It records:

```text
rejection_id
memory_id
normalized-value fingerprint
superseded fact reference
correction proposal reference
evidence refs
authority refs
scope
rejected_at
lifecycle state
readmission metadata, when exact re-admission occurs
```

`rejection_id` is deterministic over the scoped exact fingerprint and correction proposal identity. It lets later evidence refer to the rejection without making the fingerprint itself a global identifier.

The lifecycle states exercised by the reference are:

```text
rejected
readmitted
```

Permanent deletion may purge the registry entry entirely. A deletion receipt/audit event may remain according to ordinary evidence/retention policy, but the rejection registry is not permitted to retain a fingerprint forever merely because it once served governance.

## Semantic similarity signal

A semantic signal contains estimator evidence only:

```text
memory_id
rejection_ref
estimator_id
estimator_version
candidate_match
confidence, when supplied
evidence_refs
```

It intentionally contains no:

```text
allow
block
approve
reject
readmit
permission
```

The reference signal semantics are:

```text
candidate_match_for_reconciliation_not_authority
```

A matched signal maps deterministically to:

```text
require_reconciliation
```

A non-match maps to:

```text
no_semantic_reconciliation_signal
```

`no_semantic_reconciliation_signal` is not `allow`. It means only that this optional semantic gate added no extra review requirement. The ordinary write path and PAMA still decide whether anything may commit.

## Signal binding

Before a semantic signal may affect routing, the reference profile requires:

- signal `memory_id` matches the proposal target;
- `rejection_ref` names a currently active rejection for that memory;
- estimator id/version are present;
- confidence, when reported, is bounded to 0..1.

An unbound/stale rejection reference fails closed as invalid governance evidence. This is not a semantic judgment about the proposed value. It is a failure to prove what rejection the estimator claims to have compared against.

## Ordinary semantic re-entry

For an ordinary promotion/import-like proposal:

```text
semantic candidate match
  -> reconciliation required
  -> proposal does not reach durable commit through this profile
```

The estimator is not performing the block. The configured profile applies a deterministic rule that a claimed semantic match to an active rejection must be reconciled before ordinary re-entry.

Implementations that do not enable a semantic profile still retain the deterministic exact-value protection. They must not claim semantic-equivalence coverage merely because exact fingerprints are protected.

## Approved reversal

A prior rejection is not an eternal ban.

If a proposal is already an externally approved correction with reconstructable approval evidence and no self-approval, the semantic gate may allow that proposal to continue to the ordinary PAMA path:

```text
semantic match
  + explicit approved correction
  -> semantic review requirement satisfied for routing
  -> PAMA still evaluates
  -> commit or refusal according to current authority
```

The semantic estimator still does not authorize the reversal. Human/external approval and PAMA do.

A semantic reversal does not necessarily mark the old **exact fingerprint** as readmitted. A paraphrase can be accepted while the historically rejected exact value remains a distinct rejection record. Implementations should merge those identities only if a stronger structured identity model proves that equivalence under its domain contract.

## Non-match behavior

A semantic non-match must not create permission.

Adversarial case:

```text
semantic estimator says no match
PAMA says block
```

Expected:

```text
committed == false
```

The absence of a semantic warning is not an authority grant.

## Privacy and retention

Rejected-value metadata can still be sensitive. A deterministic fingerprint can support correlation and dictionary attacks when the underlying value space is small or guessable.

Required posture:

- do not store raw rejected content merely to implement the exact registry;
- scope fingerprints by memory identity rather than treating them as universal content identity;
- minimize estimator evidence to references/metadata where practical;
- apply ordinary retention/deletion policy to rejection history;
- permanent deletion should remove rejection fingerprints/history when no separate legal/policy obligation requires them;
- audit evidence should record that purge occurred without copying the rejected content into telemetry.

Hashing is minimization, not anonymization.

## Reference implementation

The reference profile lives in:

```text
reference/agentmem_ref/readmission.py
reference/agentmem_ref/semantic_readmission_adapter.py
reference/tests/test_semantic_readmission.py
reference/tests/test_semantic_readmission_adapter.py
fixtures/rejected-value-semantic-reentry.json
```

The profile subclasses the governed adapter so it shares the same rejection registry and PAMA path while remaining optional and replaceable.

## Conformance cases

### Exact rejected value

Expected:

```text
exact normalized fingerprint match
-> rejected_value_requires_reconciliation
-> no durable commit
```

### Semantic paraphrase

Expected:

```text
active rejection exists
semantic estimator emits candidate_match=true
-> require_reconciliation
-> no ordinary durable commit
```

### Semantic non-match plus PAMA block

Expected:

```text
semantic candidate_match=false
PAMA block
-> no durable commit
```

### Invalid rejection reference

Expected:

```text
semantic signal does not bind to current active rejection
-> semantic_reconciliation_signal_invalid
-> no durable mutation
```

### Approved semantic reversal

Expected:

```text
semantic candidate_match=true
external correction approval current
-> proceed to PAMA
-> PAMA determines commit/refusal
```

### Permanent deletion

Expected:

```text
permanent deletion commits
-> rejection fingerprints/history for that memory purged
-> purge event records count/reason without raw rejected content
```

## Explicit non-claims

This profile does not prove:

- universal semantic equivalence;
- architecture-independent paraphrase detection;
- calibration of any particular embedding or language model;
- that a non-match means the proposal is safe;
- that an old exact rejection and an approved paraphrase are the same identity;
- that every backend must enable semantic re-admission matching.

## Doctrine boundary

The reusable invariant is not "semantic similarity blocks memory."

It is:

> **Uncertain similarity may identify a reconciliation candidate. Only governed authority may decide whether rejected state becomes durable again.**
