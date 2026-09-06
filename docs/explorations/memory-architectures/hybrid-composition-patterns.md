# Hybrid Memory Composition Patterns

Status: exploratory baseline for #67 / #224.

Hybrid systems are first-class research subjects because governance failures often occur **between** components rather than inside one component.

## Composition contract

For every pipeline record:

```text
canonical_owner
derived_surfaces
transformation_refs
scope / isolation inheritance
correction propagation
deletion closure
PAMA boundary
recall/admission boundary
observation / receipt points
rebuild triggers
synchronization failure modes
```

Do not assume authority or lifecycle state propagates implicitly through a transformation.

## H1. Files -> chunks -> embeddings

```text
canonical file/document
-> chunk projection
-> embedding
-> vector index
-> candidate retrieval
```

Questions:

- Is chunk identity stable after source edits?
- Does embedding identity bind model/version?
- How are stale chunks and vectors invalidated?
- Can deleted source content remain reconstructable from cached chunks?
- Does a high-similarity vector bypass current source scope or dispute state?

Primary authority boundary:

```text
retrieved vector candidate
-> governed admission against current source/derived state
```

## H2. Files -> entities -> graph

```text
canonical source
-> extraction
-> entity/relation claims
-> graph
-> traversal / summaries
```

Questions:

- Which edges are asserted versus inferred?
- Can one corrected source invalidate only the edges it supported?
- What happens when one edge has multiple sources with different authority states?
- Can graph traversal expose a relation that no current source is permitted to assert?

## H3. Notes -> explicit links -> inferred graph -> GraphRAG

```text
notes
-> human links
-> generated relationships
-> graph communities
-> summaries
-> retrieval index
```

This pattern must distinguish at least four provenance levels:

```text
note statement
human-authored relation
machine-inferred relation
machine-generated summary
```

A summary must not inherit more scope or authority than its supporting sources merely because the graph pipeline produced it automatically.

## H4. Graph -> community summaries -> vector index

```text
graph state
-> clustering/community detection
-> generated summaries
-> embeddings
-> vector retrieval
```

Correction/deletion may require propagation through graph membership, summary generation, embedding, and index state.

A graph edge removal that leaves an old community summary searchable is a lifecycle-residue failure even if the graph itself is correct.

## H5. Event ledger -> current materialized view -> embeddings

```text
append-only history
-> current semantic view
-> chunk/embedding/index
```

Key distinction:

```text
historically valid event
!= current truth
```

The retrieval layer should bind to the current governed view or preserve explicit historical status. Replay of old events cannot silently restore expired authority.

## H6. Local vault -> local graph + remote evidence index

```text
local canonical notes
-> local relationship graph
-> remote privacy-minimized evidence/index surface
```

Questions:

- Which identifiers can cross the remote boundary without exposing low-entropy or sensitive content?
- Can remote search results be re-bound to current local scope/lifecycle state?
- Can remote index deletion be independently verified?
- Does local deletion require remote tombstone, purge, key destruction, or reindexing?

## H7. Episodic store -> semantic consolidation -> graph + vectors

```text
episodic observations
-> consolidation estimator
-> durable semantic candidate
-> graph relations
-> vector retrieval projections
```

This composition is a major authority-laundering risk.

The consolidation estimator may propose a durable semantic memory, but:

```text
repeated observation
!= truth
!= permission to become canonical
```

PAMA must govern the consolidation consequence before downstream graph/vector projections treat it as current memory.

## H8. Shared store -> per-agent derived views

```text
shared canonical/domain state
-> principal-specific filters/projections
-> local cache / vector / graph view
```

Membership revocation or scope reduction must propagate into each derived view. A stale local projection must not remain authoritative because it was once legitimately generated.

## H9. Persistent source -> opaque learned/latent consolidation

```text
governed source memories
-> training/update/consolidation step
-> latent predictive state
-> planning influence
```

This pattern is tracked further by #137.

Required challenge:

```text
source authority later changes
latent state remains predictive
```

Predictive usefulness cannot by itself establish continued scope, currentness, or action authority.

## Cross-composition invariants to test

The following should be treated as hypotheses requiring cross-architecture evidence:

```text
source correction should invalidate unsupported derived state
source scope reduction should not widen through derivation
source deletion should trigger declared dependency closure
rebuild must be independently authorized when it recreates durable state
candidate retrieval should be re-bound to current governance state
probabilistic transformation should not inherit mutation authority
```

## Failure categories

Every composition study should look for:

- stale transformation outputs;
- missing dependency edges;
- provenance laundering;
- scope widening;
- authority laundering;
- resurrection after deletion/revocation;
- cross-system replay;
- partial synchronization;
- unsupported current-state reconstruction;
- privacy leakage through derived identifiers or telemetry.
