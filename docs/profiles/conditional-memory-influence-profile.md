# Conditional Memory Influence Profile

V0.1 defines a vendor-neutral admission record for memory lookup that occurs inside model execution.

Core boundary:

```text
address resolves != table current != partition match != influence admitted
```

The record binds the lookup/address digest, table/model/checkpoint/tokenizer/configuration refs, injection point, partition, derivation/currentness/overlay/build refs, requested scope, trace correlation, observation time, and enforcement posture. Raw token sequences, hidden states, embedding vectors, and memory content are not required.

Gate results are `allow`, `block_stale`, `block_scope`, `block_suppressed`, and `block_unknown`.

`block_unknown` covers unavailable partition/currentness/suppression evidence and unsupported table configuration. `allow` means eligible under the represented gate; it is not proof that a cooperative runtime mechanically enforced the result.

Currentness uses `current`, `stale`, `revoked`, `deleted_residue`, or `unknown`. External source deletion does not prove removal from an already-built internal table.

Physical address equality does not merge provenance or scope. The profile preserves `same slot != same source identity`, `same slot != same partition`, and `collision != semantic equivalence`.

Table replacement requires a distinct table identity and digest. Historical evidence for the old table remains unchanged, while runtime evidence identifies the active table.

Lookup/influence is not a durable PAMA mutation. Building, promoting, replacing, or widening a reusable table remains separately governed; scope widening retains existing `scope_expansion` and M5/A5 boundaries.

Every record states that address is not identity, prefetch is not admission, external deletion is not internal forgetting, influence is not mutation authority, collision is not equivalence, and configured gating is not enforcement proof.

Evidence:
- `schemas/conditional-memory-influence.schema.json`
- `reference/agentmem_ref/conditional_memory_influence.py`
- `reference/tests/test_conditional_memory_influence_gate.py`
- `reference/tests/test_conditional_memory_influence_identity.py`
- the existing #228 conditional-memory harness

Related: #228 and #240. The pinned Engram source remains a comparator, not a V0.1 dependency.
