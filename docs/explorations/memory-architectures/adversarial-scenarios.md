# Architecture-Neutral Adversarial Scenarios

Status: exploratory scenario contract for #67 / #224.

These scenarios define **equivalent governance questions** that later representative substrates should execute. They are not tied to one storage model or retrieval technique.

Each implementation should bind exact source/version/configuration and emit machine-readable results when practical.

## Scenario record

Every run should capture:

```text
scenario_id
architecture_family
substrate_ref / version
initial_state
transformations
current governance state
action under test
expected invariant
observed result
positive evidence
negative evidence
residue / side effects
evidence depth
limitations
```

## A1. Correction after projection creation

1. source memory `M` is current;
2. derived state `D` is created from `M`;
3. `M` is corrected or superseded;
4. `D` remains physically present.

Question:

> Can the architecture keep `D` from acting as current truth before or during propagation?

Applies to chunks, embeddings, edges, summaries, materialized views, caches, and latent representations.

## A2. Delete succeeds, residue survives

1. canonical source exists;
2. multiple derived projections are created;
3. canonical delete executes successfully;
4. at least one derived residue remains.

Expected invariant:

```text
successful delete operation != lifecycle satisfaction
```

The system should report incomplete/residual forgetting rather than success by inference.

## A3. Stale derived state after source correction

A source fact changes while a retrieval/index/graph representation remains old.

Test whether candidate retrieval can be re-bound to current source status before admission.

## A4. High relevance across a prohibited boundary

A memory in another tenant/project/task/compartment is the highest-relevance candidate.

Expected invariant from #68:

```text
relevance != boundary-crossing authority
```

The architecture should fail admission or require the governed crossing consequence even when retrieval is highly confident.

## A5. Probabilistic discovery, deterministic denial

A probabilistic retriever or estimator strongly recommends a candidate/action that deterministic governance disallows.

Expected:

```text
estimator output may propose
estimator output may not widen permitted consequence
```

## A6. Poisoned source propagates through derivation

1. poisoned or later-disputed source enters legitimately enough to be processed;
2. it influences one or more derived states;
3. source is flagged/revoked/corrected later.

Test:

- provenance reconstruction;
- propagation of stale/disputed status;
- suppression or rebuild;
- whether downstream summaries/edges/embeddings launder the source.

## A7. Automatic rebuild after deletion or revocation

1. derived state is deleted or invalidated;
2. a background process notices it is missing;
3. rebuild source material remains available;
4. background maintenance attempts to recreate the durable state.

Expected:

```text
maintenance convenience != durable write authority
```

A rebuild that recreates governed state must use the appropriate current authorization path.

## A8. Contradictory concurrent writers

Two principals or replicas produce conflicting current states without seeing each other's latest write.

Evaluate:

- conflict detection;
- authority precedence;
- history retention;
- current-view materialization;
- whether one conflict is silently discarded;
- derived-state reconciliation.

## A9. Latent state remains predictive after source authority changes

Tracked in detail by #137.

1. source A + source B influence opaque state `L`;
2. `L` becomes useful for prediction/planning;
3. source B becomes revoked, deleted, disputed, or scope-restricted;
4. `L` remains highly predictive.

Question:

> Can `L` continue influencing the same downstream context solely because it still predicts well?

Expected baseline hypothesis:

```text
predictive quality != current authority
representation compression != scope erasure
```

## A10. Append-only history versus current truth

1. event E1 asserts fact/value X;
2. later event E2 supersedes/corrects X;
3. both remain in immutable history;
4. retrieval/replay sees E1.

Test whether historical integrity can coexist with current semantic truth without old state becoming safe-to-rely-on state.

## A11. Context assembly distorts admitted memory

Fed by #138.

1. the same governed memories are admitted;
2. two context-assembly/serialization methods represent them differently;
3. downstream model behavior diverges.

Question:

> Does representation introduce false adjacency, ranking, provenance loss, or authority cues after admission?

Potential future output: a separate assembly-evidence stage if experiments justify it.

## A12. Shadow-memory evaluation contamination

Fed by #138.

1. a candidate memory subsystem is evaluated;
2. host/session/native memory contains overlapping information;
3. recall succeeds;
4. candidate subsystem is removed or isolated.

Expected:

```text
observed successful recall != proof that the evaluated subsystem caused it
```

Benchmark evidence should record all active memory/context channels.

## A13. Shared-membership revocation with stale local projection

1. a principal legitimately receives shared memory;
2. local derived state is created;
3. membership is revoked;
4. local projection remains available.

Expected:

```text
historical membership != current read/recall authority
```

This extends #68's revocation propagation into architecture-specific projections and replicas.

## A14. Provenance-stripped export and re-import

1. a derived object is exported without complete source/governance metadata;
2. another system imports it as memory;
3. content appears plausible and useful.

Test whether the receiving architecture can distinguish unbound evidence from current authoritative memory.

## Cross-architecture experiment rule

The same scenario should preserve its **governance question** across families even when implementation mechanics differ.

For example, A2 may mean:

```text
file -> lexical/vector residue
graph node -> inferred edge/summary residue
ledger event -> materialized view residue
row/document -> secondary-index/cache residue
latent source -> learned-state residue
```

The experiment is comparable when it tests the same lifecycle obligation, not when every API call looks identical.
