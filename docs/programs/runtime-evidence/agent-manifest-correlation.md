# P4.5b Agent Manifest memory checkpoint correlation

Status: **Executable interoperability evidence**. This slice correlates Agent Memory portable governance evidence with the existing Agent Manifest v0.2 memory checkpoint/delta protocol. It does not adopt Agent Manifest as Agent Memory doctrine, does not duplicate its checkpoint protocol, and does not change repository conformance level.

Parent implementation issue: #63.

## Pinned external comparator

The executable comparator is pinned to:

```text
repository: https://github.com/agentrust-io/agent-manifest
spec:       Agent Manifest v0.2
package:    agent-manifest==0.11.2
tag commit: 9d26ac84461e829dba8ff97ca35748eeb874debe
```

Pinned upstream source surfaces:

- [v0.2 memory checkpoint/delta implementation](https://github.com/agentrust-io/agent-manifest/blob/9d26ac84461e829dba8ff97ca35748eeb874debe/python/src/agent_manifest/_memory_delta.py)
- [v0.2 RFC 9162 Merkle implementation](https://github.com/agentrust-io/agent-manifest/blob/9d26ac84461e829dba8ff97ca35748eeb874debe/python/src/agent_manifest/_merkle.py)
- [v0.2 specification](https://github.com/agentrust-io/agent-manifest/blob/9d26ac84461e829dba8ff97ca35748eeb874debe/spec/agent-manifest-spec-v0.2.md)

The upstream package is a **test comparator**, not an Agent Memory runtime dependency. P4.5b deliberately calls the upstream checkpoint verifier instead of copying its Merkle, sequence, TTL, drift, or delta-budget logic into this repository.

## Ownership boundary

Agent Manifest v0.2 models evolving memory as an append-only operation log. A checkpoint binds:

```text
memory_root
tree_size
seq
approved_at
ttl_seconds
```

Its verifier owns whether a checkpoint advance is a valid append-only delta under its consistency-proof, monotonic-sequence, TTL, and delta-budget rules.

Agent Memory owns:

```text
what the memory action means
whether PAMA permitted it
what canonical receipt records it
whether execution was authorized
whether correction/deletion lifecycle obligations are satisfied
whether declared or undeclared derived residue remains
```

The composition is therefore:

```text
Agent Manifest delta verdict
        |
        | integrity of memory-log evolution
        v
content-addressed checkpoint reference
        |
        | canonical receipt evidence_refs
        v
Agent Memory canonical receipt
        |
        | P4.5a receipt hash + before/after state refs
        v
portable Agent Memory governance evidence
        |
        v
P4.5b correlation artifact
```

No arrow reverses semantic ownership.

## Correlation contract

Schema: `../../../schemas/agent-manifest-memory-correlation.schema.json`.

The canonical Agent Memory decision receipt already has a generic `evidence_refs` array. P4.5b therefore does not modify the receipt schema. The new checkpoint tuple is projected without operation content and content-addressed with Agent Memory canonical JSON:

```text
checkpoint_ref = sha256(canonical({
  memory_root,
  tree_size,
  seq,
  approved_at,
  ttl_seconds
}))
```

That `checkpoint_ref` is placed in the canonical receipt's `evidence_refs`.

P4.5a portable evidence then binds:

```text
canonical_receipt_ref
memory_action
state.before_ref = previous checkpoint_ref
state.after_ref  = new checkpoint_ref
```

P4.5b validates all four relationships:

1. the portable evidence signature resolves to the supplied canonical receipt;
2. canonical receipt `selected_action` equals signed portable `memory_action`;
3. the receipt contains the new checkpoint reference in `evidence_refs`;
4. the portable before/after state references match the previous/new checkpoint references.

The correlation artifact also records the pinned upstream spec/package/commit identity and the **upstream verifier's** `accepted/rejected` verdict and reason.

Checkpoint projection is deliberately strict at the boundary: hash values must use a supported algorithm plus a 64-character lowercase hexadecimal digest, counters must be non-negative integers rather than booleans masquerading as integers, TTL must be positive, and approval time must be timezone-aware.

## What is not duplicated

Agent Memory does not reproduce:

- RFC 9162 consistency proof generation or verification
- Agent Manifest Merkle leaf construction
- Agent Manifest sequence monotonicity rules
- checkpoint TTL evaluation
- delta-budget evaluation
- Agent Manifest drift classification

Those are executed by `agent-manifest==0.11.2` in CI. The local correlation layer only binds the resulting checkpoint identity and verdict to Agent Memory evidence.

## DEL is not forgetting

Agent Manifest encodes a key-value deletion as an appended `DEL` operation. The P4.5b test constructs the upstream operation log with an actual `DEL` and then executes the upstream checkpoint verifier against that log.

A crucial boundary follows: **the checkpoint root and consistency proof do not, by themselves, let a third party infer the semantic class of the appended operation without additional operation or inclusion evidence.** The correlation artifact therefore does not claim `operation_kind = DEL`. The deletion semantic is carried by signed Agent Memory `memory_action = permanent_deletion`; the fact that the executed comparator vector used a real upstream `DEL` remains an executable test fact.

This avoids turning a known test input into a portable proof claim the checkpoint protocol does not make.

P4.5b executes the same upstream-accepted checkpoint advance, whose test input contains `DEL`, in two Agent Memory outcomes:

```text
Agent Manifest: accepted checkpoint advance
Test input:     appended DEL
Agent Memory:   committed permanent_deletion
Lifecycle:      residual
```

and:

```text
Agent Manifest: accepted checkpoint advance
Test input:     appended DEL
Agent Memory:   committed permanent_deletion
Lifecycle:      satisfied
```

Both correlation artifacts are valid. The difference is Agent Memory lifecycle evidence, not Agent Manifest checkpoint integrity.

This is the executable version of:

```text
accepted checkpoint containing DEL != forgetting
```

## Negative outcomes remain evidence

A failed Agent Manifest consistency proof produces the upstream `drift` verdict. P4.5b records that as:

```text
correlation_integrity = valid
agent_manifest.delta_verification = rejected
agent_manifest.delta_reason = drift
```

The correlation itself is valid because it correctly binds a negative external result. It does not mutate the negative result into an Agent Memory governance denial.

By contrast, these are correlation-integrity failures:

- the portable evidence does not verify against the canonical receipt;
- canonical receipt `selected_action` disagrees with signed portable `memory_action`;
- the receipt does not reference the new checkpoint;
- portable `before_ref` does not identify the previous checkpoint;
- portable `after_ref` does not identify the new checkpoint.

## Privacy boundary

The correlation artifact contains checkpoint roots and metadata, not operation payloads. The executed deletion vector intentionally uses a memory key and value that are absent from the emitted correlation object.

The upstream verifier receives the operation log because it owns checkpoint verification. P4.5b does not copy those operations into Agent Memory portable evidence or the correlation artifact. Avoiding an `operation_kind` claim also prevents the compact artifact from pretending to reveal semantics its root alone cannot establish.

## Executed vectors

`../../../reference/tests/test_agent_manifest_correlation.py` executes:

- the exact `agent-manifest==0.11.2` package identity
- the pinned upstream commit identity
- the Agent Manifest v0.2 normative KV root vector
- a valid RFC 9162 checkpoint advance whose upstream operation log contains `DEL`
- canonical receipt to checkpoint-reference binding
- portable before/after state to checkpoint-reference binding
- canonical receipt action to signed portable memory-action binding
- accepted checkpoint + signed Agent Memory `permanent_deletion` + lifecycle `residual`
- accepted checkpoint + signed Agent Memory `permanent_deletion` + lifecycle `satisfied`
- rejected consistency proof surfaced as Agent Manifest `drift`
- missing receipt checkpoint reference
- mismatched receipt/portable action
- tampered portable after-state binding
- malformed checkpoint root and timezone-less timestamp rejection
- schema validation of the content-free correlation artifact
- absence of the raw deleted key/value from the correlation artifact
- absence of an unproven `operation_kind` claim from the correlation artifact

Run:

```bash
python -m pip install \
  jsonschema==4.26.0 \
  cryptography==50.0.0 \
  agent-manifest==0.11.2
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
```

## What this slice proves

P4.5b demonstrates that Agent Memory can correlate its canonical receipt and P4.5a portable evidence to Agent Manifest's existing memory checkpoint/delta protocol without duplicating that protocol or delegating memory semantics to it.

It also executes the key non-escalation claim: a checkpoint advance built from an upstream log containing `DEL` and accepted by the Agent Manifest verifier can coexist with either residual or satisfied Agent Memory lifecycle evidence.

## What remains unproven

This slice does not yet prove:

- a content-free third-party proof that a checkpoint's newly appended operation was specifically `DEL`; that would require an additional operation/inclusion-evidence convention rather than inference from the checkpoint root
- TRACE/AgenTrust external action-evidence interoperability (P4.5c)
- production Agent Manifest trust/attestation deployment
- hardware attestation of Agent Memory runtime state
- multi-party checkpoint approval
- a generic cross-standard checkpoint URI or registry
- production key/trust-anchor distribution
- any Agent Memory conformance level increase
- acceptance of ADR-020, ADR-021, or ADR-022

Those remain separate evidence gates.
