# Memory Architecture Taxonomy

Status: exploratory taxonomy for #67 / #224.

The taxonomy classifies **representation and retrieval philosophies**, not products. A named implementation may later serve as a representative substrate, but it must not define the family.

## Taxonomy dimensions

Each family should be characterized by at least:

```text
primary retained-state unit
canonical-state location
identity mechanism
derived-state forms
retrieval mechanism
mutation mechanism
probabilistic components
synchronization model
correction semantics
deletion semantics
```

A system may belong to multiple families simultaneously.

## A. File / document memory

Primary state is represented in human-readable or structured files/documents.

Typical units:

```text
file
document
section / record
content hash / path / version
```

Potential derived surfaces include lexical indexes, embeddings, summaries, backlinks, caches, and graphs.

Do not assume human readability implies provenance completeness, safe mutation, or deletion completeness.

## B. Linked note / vault memory

Canonical or semi-canonical notes are combined with links, backlinks, tags, metadata, transclusion, or generated relationships.

Core distinction:

```text
note content
!= explicit human-authored link
!= inferred/generated relationship
!= retrieval projection
```

Generated links must not silently inherit the authority of the notes they connect.

## C. Lexical retrieval memory

Retained content is discovered through token/term-oriented indexes rather than semantic embedding similarity.

Typical derived state:

- inverted indexes
- token statistics
- ranking metadata
- caches

Lexical retrieval is useful as a distinct comparison because it can separate retrieval/index governance questions from embedding-model drift.

## D. Vector / embedding RAG

Source records or chunks are transformed into embeddings and retrieved by similarity or related estimators.

Typical chain:

```text
source
-> chunk
-> embedding
-> vector index
-> candidate retrieval
-> governed admission
```

Key pressure points include chunk identity, embedding-version drift, stale embeddings, source reconstruction, derived residue, and similarity-versus-permission separation.

## E. Knowledge-graph memory

Retained state is represented as nodes, edges, properties, or claims with explicit relationships.

Important distinctions:

```text
asserted edge
!= inferred edge
!= traversal path
!= summary derived from graph structure
```

Graph reachability does not itself grant traversal or recall authority.

## F. Temporal graph memory

Graph state carries explicit validity intervals, event time, transaction time, versions, or historical relationship state.

This family deserves separate treatment because correction may preserve historical graph truth while changing current truth, and deletion may affect both active and historical projections differently.

## G. GraphRAG / graph + retrieval composition

GraphRAG is treated as a **composition family**, not merely a retrieval algorithm.

Typical chain:

```text
source
-> extraction
-> graph
-> communities / summaries
-> lexical/vector index
-> retrieval
-> context assembly
```

Each stage may have distinct provenance, scope, confidence, lifecycle, and deletion obligations.

## H. Event-log / ledger memory

Durable history is append-oriented. Correction commonly occurs through superseding or compensating events rather than physical overwrite.

Key distinction:

```text
historical event integrity
!= current semantic truth
```

Append-only evidence may conflict with forgetting obligations when content-bearing events themselves are sensitive.

## I. Relational / document-store memory

Structured or semi-structured records live in transactional stores with explicit schemas, indexes, ACLs, queries, and update semantics.

This family provides a useful classical-governance comparison surface for transactions, row/document identity, referential integrity, access control, and materialized views.

## J. Hierarchical / tiered memory

State moves among tiers such as:

```text
ephemeral
working
session
episodic
long-term
archival
remote / inherited
```

Movement between tiers must be decomposed into separate questions:

```text
storage placement
lifecycle meaning
authority consequence
scope change
retention policy
```

Tier movement is not automatically an authority promotion.

## K. Shared / distributed multi-agent memory

Multiple principals read, write, derive, synchronize, or consume overlapping state.

Key concepts:

- writer identity
- membership
- ownership
- principal-specific views
- conflicting updates
- propagation
- revocation
- shared-domain scope
- inherited state

Shared storage is not equivalent to shared authority.

## L. Opaque learned / latent predictive state

Retained or influential state is encoded as learned representations, latent slots, model/checkpoint state, predictive embeddings, or world-model state that may not support proposition-level inspection or correction.

This family is pressure-tested by #137.

Key distinction:

```text
predictive usefulness
!= truth
!= scope freedom
!= action authority
```

Opacity also does not prove privacy or forgetting.

## M. Hybrid compositions

Most serious systems will combine families.

Examples:

```text
file canonical state + vector retrieval
ledger history + relational current view + embeddings
notes + generated graph + GraphRAG summaries
shared document store + per-agent vector projections
persistent episodic store + latent consolidation
```

Hybrid systems are first-class because governance failures often occur at the boundaries between otherwise well-behaved components.

## Classification rule

When evaluating a product or implementation, classify every meaningful state surface independently.

For example:

```text
Markdown files           -> file/document family
backlinks                -> linked-note projection
embeddings               -> vector/RAG derived state
entity graph             -> knowledge-graph derived state
community summaries      -> GraphRAG derived state
local cache              -> materialized projection
```

Do not label the whole system with one family name when governance obligations differ across its internal surfaces.
