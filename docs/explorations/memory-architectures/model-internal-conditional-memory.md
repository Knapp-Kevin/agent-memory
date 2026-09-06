# Model-Internal Conditional Memory and Deterministic Prefetch

Status: **active exploratory research** under #228 and parent #67. This document is not canonical doctrine.

## Exact comparator pin

Primary source:

```text
repository: deepseek-ai/Engram
commit: fb7f84a21f91223715394a33a1dc24bbfb7f788e
license: Apache-2.0
paper: Conditional Memory via Scalable Lookup: A New Axis of Sparsity for Large Language Models
```

At this pin, the official demo is explicitly a simplified architecture demonstration rather than production code. It configures Engram at internal transformer layers `[1, 15]`, normalizes/compresses tokenizer IDs, deterministically mixes N-gram IDs with layer-specific multipliers and XOR, hashes across distinct prime-sized head tables, looks up embeddings, gates their contribution against hidden state, and adds the resulting value before the block's mocked attention/MoE path.

The architectural challenge is therefore concrete:

```text
token state
-> deterministic internal address
-> memory-table lookup
-> hidden-state fusion
-> continued model execution
```

There may be no host-level `retrieve -> admit -> inject` callback at the point where memory influences inference.

## Core finding

Existing Agent Memory provenance/currentness/isolation doctrine can represent a conditional-memory **table as derived state**, but runtime influence requires an implementation profile that binds table currentness and scope **before the table is allowed to contribute to hidden state**.

The key separation is:

```text
address resolves
!= table is current
!= table is in scope
!= influence is admitted
```

Deterministic lookup solves addressing. It does not solve governance.

## Identity

A governed conditional-memory table should be identifiable by evidence such as:

```text
model/checkpoint ref
tokenizer ref + version
normalization/compression ref
hash algorithm/config version
layer IDs
head/table sizes
table digest
scope partition ref
source-root / training-build refs
build/release receipt
```

An individual runtime lookup can be referenced without logging raw hidden state:

```text
table digest
layer ID
opaque address/hash digest
partition ref
gate result
trace/correlation ref
```

Hash address is not logical memory identity.

## Provenance and currentness

Treat table construction as a deterministic/probabilistic derivation from governed source roots.

```text
sources S
-> table artifact T1
-> historical derivation evidence
```

Later source change does not rewrite that history:

```text
source revoked/deleted/corrected
-> T1 derivation remains historical evidence
-> T1 current applicability becomes revalidation_required
```

This maps cleanly to the existing derivation/currentness contracts.

The crucial runtime fact is that the physical table can still answer the same deterministic address after its source basis becomes non-current. Therefore:

```text
lookup still works
!= lookup may still influence the model
```

A currentness/influence gate is required.

## Scope and isolation

A single mixed-scope table is difficult to govern if the implementation cannot prove which partition contributed before hidden-state fusion.

Safe deployment patterns include:

- physically distinct tables per tenant/project/purpose;
- explicit scope partitions inside one table with partition identity bound into lookup;
- a runtime gate that activates only partitions admissible to the current context;
- an overlay/suppression layer that can disable stale entries/partitions before influence.

Unsafe claim:

```text
raw source text is unrecoverable
therefore cross-tenant influence cannot occur
```

Opacity is not isolation evidence.

The representation-neutral harness proves that identical hash slots in different partitions remain separate authority domains and that a partition mismatch blocks influence even when the address is deterministic.

## Correction, revocation, and deletion

Three distinct states must remain visible:

```text
source lifecycle state
conditional-memory table currentness
table bytes still physically capable of lookup
```

A source can be deleted while an old table still contains a source-derived embedding. That table is **derived residue** until one of the deployment-specific remediation paths succeeds:

- table rebuild/replacement;
- scoped overlay/tombstone suppressing the affected slot/partition;
- cryptographic/access revocation that genuinely prevents influence;
- destruction of the table artifact where required.

Deleting the external source alone is not forgetting proof.

A rebuilt table is a new derived artifact/version. The old table remains historical evidence and must not silently regain active status.

## Collision and aliasing

Engram's multi-head prime-sized tables reduce practical collision behavior, but hashing does not create semantic identity.

A collision means two inputs address the same physical slot in one head/table. It is a representation-quality and leakage risk to measure, not an authority signal.

Required boundary:

```text
same hash address
!= same source identity
!= same tenant/scope
!= same semantic fact
```

Multi-head agreement can improve representation robustness. It still does not become provenance or permission.

## PAMA placement

### Runtime lookup/influence

A lookup does not create durable state, so ordinary lookup should not manufacture a PAMA mutation decision for every token.

Instead, the runtime must enforce a bounded influence-admission profile based on current table/partition evidence:

```text
table current + partition allowed + not suppressed
-> influence eligible

stale/revoked/deleted basis | scope mismatch | suppression
-> influence blocked / table revalidation required
```

### Table construction/update/release

Creating or replacing a table changes a reusable model/runtime artifact and can affect many future inferences.

The reference pressure test routes ordinary table deployment through existing `promotion` governance and routes scope-partition widening through the stricter existing `scope_expansion` boundary.

No Engram-specific PAMA operation is justified by this research.

## Minimal influence evidence profile

The missing reusable implementation surface is an architecture-neutral **model-internal conditional-memory influence profile**.

It should bind at least:

```text
table_id / digest
model/checkpoint ref
tokenizer/hash config ref
layer/injection point
scope partition
source-currentness evaluation ref
suppression/overlay version
opaque lookup/address ref
gate outcome
trace/correlation ref
```

It should never require raw hidden-state telemetry merely to prove the gate existed.

## Representation-neutral executable cases

The harness covers:

1. identical input/config produces deterministic address;
2. source revocation leaves the address physically resolvable;
3. derivation currentness marks the old table `revalidation_required`;
4. the influence gate blocks stale-table contribution;
5. source deletion still leaves physical table residue until remediation;
6. a rebuilt table under current source evidence creates a new current artifact without rewriting T1;
7. scope partition mismatch blocks influence;
8. the same hash slot in different tenant partitions does not create cross-tenant permission;
9. an explicit overlay/tombstone suppresses influence before fusion;
10. hash collision does not create source/provenance equivalence;
11. high determinism does not create authority;
12. ordinary table deployment remains separately governed from runtime lookup;
13. table partition widening remains subject to existing `scope_expansion` safety.

## Why no full Engram runtime comparator in this slice

The official demo requires PyTorch, Transformers, SymPy, NumPy, and the configured DeepSeek-V3 tokenizer. Its own source states that standard backbone components are mocked/simplified and that it exists to demonstrate Engram data flow.

Executing that demo would reconfirm properties already inspectable in the exact source pin:

- deterministic N-gram addressing;
- internal-layer table lookup;
- hidden-state gating/fusion.

It would **not** test the Agent Memory-specific stale-source, deletion-residue, scope, or influence-admission questions unless we modified/wrapped the runtime.

Therefore the real runtime comparator is deferred until the generic influence profile exists. That is an evidence-efficiency decision, not a claim that the upstream implementation is unimportant.

## Research conclusion

Current Agent Memory representation-agnostic doctrine survives the model-internal-memory pressure test at the semantic layer:

- provenance still matters;
- derived currentness still matters;
- deletion residue still matters;
- scope still matters;
- deterministic relevance/addressing is not permission;
- table release/update remains governed separately from runtime use.

The concrete missing implementation contract is the **pre-influence gate/evidence profile** for a conditional-memory table/partition inside model execution.

No new canonical memory primitive, Engram dependency, or hidden-state logging requirement is justified.

## Non-claims

This slice does not establish:

- Agent Memory support for Engram;
- Engram runtime conformance;
- collision-free addressing;
- deletion from model weights/tables by source deletion alone;
- production enforcement inside arbitrary model runtimes;
- universal ability to suppress one learned entry without rebuild;
- performance equivalence to the Engram paper.
