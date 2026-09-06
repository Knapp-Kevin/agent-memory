# Graphiti Conformance Mapping

> Status: **documentation-verified, not runtime-verified.** Every row below was checked against the substrate's public source tree. Nothing here has been executed against a running instance, so no row constitutes runtime evidence under [`README.md`](README.md). This document scopes the adapter work; it does not discharge it.

## Subject and evidence basis

| Field | Value |
|---|---|
| Substrate | Graphiti, a temporal knowledge-graph framework (`getzep/graphiti`) |
| Version examined | `graphiti-core` 0.29.3 |
| Tree examined | `main` at `401c59a65bdeb22a44136901ff30231e6998a7fe` |
| Licence | Apache-2.0 |
| Storage backends | Neo4j 5.26+, FalkorDB 1.1.2+, Amazon Neptune; Kuzu deprecated upstream |
| Source record | `sources/source-registry.json` → `graphiti-temporal-graph` |

Evidence was taken from the source tree in preference to the documentation site, because the two disagree in at least two places (bulk-path invalidation, and the `group_id` search parameter's arity). Where they disagree, this mapping follows the code and flags the discrepancy.

## Why this substrate first

Graphiti is the strongest first mapping target because its native concerns overlap Agent Memory's time, provenance, and retrieval concerns directly: it models source episodes, event-time validity separate from ingestion time, supersession without deletion, and hybrid retrieval. That gives the adapter something substantial to wrap rather than a toy store built so the doctrine can agree with itself.

It is a **substrate and comparator**. Per the program's comparator discipline, it is not doctrine authority, and a capability it lacks is a classified gap rather than a defect — Graphiti does not claim to be a governance layer.

## Classification vocabulary

```text
NATIVE               the substrate provides it directly with compatible semantics
CONFIGURABLE         available, but correctness depends on how the caller drives it
WRAPPER_REQUIRED     the adapter must supply it; the substrate cannot
NOT_REPRESENTABLE    no place to put it without abusing an untyped escape hatch
UNKNOWN_NEEDS_TEST   could not be determined from source; requires an executed probe
```

## Conformance map

| # | Agent Memory concern | Classification | Basis |
|---|---|---|---|
| 1 | Memory identity | **WRAPPER_REQUIRED** | Nodes carry a random UUID4, not a content-derived address, and identity *resolution* is LLM-mediated with a narrow exact-name fast path. Merges rewrite a `uuid_map` rather than preserving the losing identity, and no confidence is persisted about how the merge was decided. ADR-001 requires deterministic identity that no estimator may mint. |
| 2 | Source evidence | **NATIVE** | Episodic nodes retain raw source content verbatim with a typed source and description, and are first-class graph objects. |
| 3 | Provenance | **NATIVE** (episode-granular) | Bidirectional: facts list the episodes that produced or reinforced them, episodes list the facts they yielded, and facts carry a reference timestamp from their episode. Caveat: provenance resolves to an episode, not to the span within it. |
| 4 | Valid time | **NATIVE for edges, PARTIAL for nodes** | Edges carry a genuine bi-temporal record: event-time validity (`valid_at`/`invalid_at`) separate from transaction time (`created_at`/`expired_at`). Entity and community nodes carry only `created_at` — bi-temporality is an edge-level property. |
| 5 | Supersession | **NATIVE** | Supersession marks, never deletes: the superseded edge's event-time end is set from the superseding fact and transaction-time expiry is stamped. The interval arithmetic is deterministic. |
| 6 | Contradiction | **CONFIGURABLE** | Detection is an LLM judgment over a *retrieved candidate set*; resolution is then deterministic. The governing limitation is structural: a contradiction whose counterpart was not retrieved is silently not detected. Recall of the candidate set bounds contradiction detection. |
| 7 | Lifecycle state | **NOT_REPRESENTABLE** | No status, state, confidence, or review field exists on any node or edge type. The only expressible states derive from the temporal fields — roughly {valid, event-invalid, transaction-expired}. The 13-state lifecycle would have to live in an untyped attributes dictionary, which is storage, not modelling. |
| 8 | Scope and tenancy | **WRAPPER_REQUIRED** | Every object carries a partition identifier, but isolation is a *query-filter convention*: the caller passes group filters per call, there is no database-level enforcement, and the default on search is permissive (no filter). Cross-tenant leakage is caller discipline. Agent Memory treats tenancy as an enforced boundary. |
| 9 | Recall admission | **WRAPPER_REQUIRED** | Retrieval is strong and genuinely hybrid — keyword, semantic, and graph traversal across four target types, with several rerankers and a library of named recipes. But all of it is *candidate generation*. There is no admission stage between retrieval and use, which is precisely the distinction doctrine draws. |
| 10 | Mutation authority | **NOT_REPRESENTABLE** | The substrate has no authorization, permissions, or access-control layer; a scoped code search returns nothing. No actor identity is recorded on any mutation and no mutation is gated. Anyone who can reach the API can write, invalidate, or delete anything in any partition. This is the sharpest gap and the adapter's primary responsibility. |
| 11 | Deletion and tombstones | **WRAPPER_REQUIRED** | Deletion is physical detach-delete, with no tombstoning — distinct from invalidation, which does preserve the row. Episode removal performs a conservative cascade, removing only facts and entities exclusive to that episode. Reversible-tombstone semantics must come from the adapter. |
| 12 | Derived projections | **CONFIGURABLE, weak by default** | Embeddings, indices, and communities all exist. None self-invalidate: an embedding attached to changed text is not refreshed automatically, index building is explicit, and community updating is off by default on ingestion. Communities are clustered by label propagation and then *named and summarized by an LLM*. |
| 13 | Decision receipts | **NOT_REPRESENTABLE** | Nothing records why a mutation happened, by whom, or on what evidence. The model captures that a fact was invalidated and when, on both time axes, but the reasoning that drove it is consumed and discarded. What exists is ephemeral runtime logging, which is stdout, not queryable state. |
| 14 | Telemetry hooks | **NATIVE (opt-in)** | The client accepts an OpenTelemetry tracer with a configurable span prefix; without one, tracing is a zero-overhead no-op. A separate, unrelated product-analytics channel exists and is independently disableable. |

## The estimator boundary

This is the mapping's most consequential finding, because it determines whether the substrate can be governed at all.

Graphiti's ordinary ingestion path is **LLM-mediated end to end**. In Agent Memory terms, these are probabilistic estimators, not deterministic operations:

```text
entity extraction
relationship extraction
entity deduplication / identity resolution
edge deduplication and contradiction nomination
event-time validity extraction from episode text
entity and community summarization
```

Deterministic, by contrast: identifier assignment and transaction-time stamping, the supersession interval arithmetic (given candidates and dates supplied by the LLM), exact-match fast paths, all retrieval and reranking, and the community clustering itself.

Doctrine's position follows directly and without strain: **the ordinary ingestion path is an estimator, so it may propose but must not commit consequential memory.** Letting it commit would be the confidence-becomes-authority failure with a knowledge graph attached.

### The seam that makes this tractable

The substrate exposes **direct-write paths that call no LLM at all** — a triplet writer and a bulk writer that persist pre-built objects, including pre-computed embeddings, temporal fields, and provenance, invoking the embedder only when an embedding is absent.

That is the adapter's opening. The governed path can therefore be:

```text
evidence
  -> Agent Memory estimators propose (optionally including the substrate's own extraction, treated as one estimator among others)
  -> governance resolves the authority envelope
  -> permitted action selected
  -> deterministic direct write into the substrate
  -> receipt recorded by the adapter
  -> retrieval candidates from the substrate's hybrid search
  -> governed admission by the adapter
  -> active context
```

The substrate keeps what it is genuinely good at — temporal fact storage, provenance linkage, supersession, hybrid retrieval — and never holds the authority decision. This is a wrapper relationship, not an integration, and that is the correct shape.

## What the adapter must supply

Everything classified WRAPPER_REQUIRED or NOT_REPRESENTABLE above, concretely:

1. **Deterministic identity** above the substrate's UUIDs, with the substrate identifier stored as a reference rather than treated as the identity.
2. **An authority gate** in front of every write, invalidation, and delete, since the substrate has none and will faithfully execute whatever reaches it.
3. **Enforced scope filtering** on every read and write, never relying on the permissive default — the adapter must make the unfiltered query unreachable.
4. **An admission stage** between retrieval candidates and context, applying scope, sensitivity, dispute, and policy state.
5. **Lifecycle state** external to the substrate, keyed by memory identity.
6. **Tombstones and deletion propagation**, including declared handling of derived state.
7. **Decision receipts**, recorded by the adapter because the substrate discards its reasoning.
8. **Projection invalidation**, since nothing self-invalidates on source change.

## Adapter status: bound and executed

The wrapper is implemented in [`../../../reference/README.md`](../../../reference/README.md) and **is now bound to this substrate and executed against it**, not only against a model.

The binding runs `graphiti-core` 0.29.3 over the embedded backend with **no LLM, no embedder, no API key, and no database server**, confirming the estimator-boundary argument below is not merely theoretical: pre-computed vectors are supplied, so the bulk writer's embedder call never fires, and the driver-level API is reached without the facade. Seven governance paths execute against the live graph, including cross-partition refusal, supersession that marks without deleting, and a physical delete.

Execution verified three things source reading alone had not:

1. **The no-LLM write path works end to end.** A bulk write with a null embedder and pre-supplied embeddings persists facts with provenance and both temporal axes intact.
2. **The facade forces an LLM client.** Constructing the top-level client instantiates an OpenAI client even when every operation in use is LLM-free, and fails without credentials. A governed adapter must therefore bind at the driver level. This is an integration constraint, not a documentation detail.
3. **An empty partition raises rather than returning empty.** The partition query signals absence by exception, so a wrapper must treat "no edges here" as a normal condition rather than an error.

It also partially resolves open question 3: invalidated edges **are** returned by the partition query, so an adapter that does not filter them would admit superseded facts as current. The hybrid-search path remains untested because ranking needs an embedder.

What remains unproven is stated plainly: the doctrine fixture corpus is not driven through the adapter, retrieval ranking is not exercised, and the backend used is deprecated upstream — chosen because it is embedded and therefore self-contained. No governance behavior under test depends on the backend.

## Negative paths this substrate makes testable

The mapping is useful precisely because the gaps are sharp. These existing fixtures become executable against a wrapped substrate, and several would fail against the bare substrate — which is the point of measuring:

| Fixture | What the wrapped run must show |
|---|---|
| `cross-tenant-relevance-trap` | high semantic relevance from another partition is retrieved as a candidate and refused at admission |
| `unauthorized-mutation-attempt` | a write the substrate would happily accept is blocked before reaching it |
| `high-confidence-false-promotion` | LLM-extracted high-confidence content cannot self-authorize durability |
| `stochastic-retrieval-policy-envelope` | varying candidate generation never yields a prohibited admission |
| `deletion-residue` | detach-delete plus declared derived-state handling leaves no undeclared recoverable residue |
| `policy-estimator-version-drift` | policy version and extraction-model version remain distinguishable in receipts |
| `governed-promotion-audit-trace` | the adapter emits the full event chain the substrate does not record |

## Open questions requiring an executed probe

Recorded as unknowns rather than assumed, per the mapping's own honesty rules:

1. Whether episode removal prunes dangling references from surviving facts' episode lists and from community membership. If it does not, deletion leaves referential residue the adapter must handle.
2. Whether any hook refreshes communities or embeddings when a source changes or an edge is invalidated. No such hook was found, but the absence was not exhaustively traced.
3. Whether invalidated edges remain retrievable through hybrid search by default, and under what filter they are excluded — this determines whether stale-fact admission is a real risk in the retrieval path.
4. Whether the partition filter is genuinely honoured across every search recipe, including the traversal-seeded ones, or only on the primary paths.
5. Embedding staleness in practice: whether changed fact text with a pre-existing embedding is silently retrievable under its old vector.

Items 1, 2, 3, and 5 all bear on derived-state correctness, which is the projections workstream's core question. Item 4 bears directly on tenancy enforcement and should be probed first, because a partition-filter miss in any recipe would make the wrapper's scope enforcement mandatory at a lower level than expected.

## Non-adoption statement

Mapping is not adoption. This document does not make Graphiti a dependency, a reference implementation, or an ownership candidate in [`../../39-implementation-ownership-map.md`](../../39-implementation-ownership-map.md). It is a comparator and a candidate substrate, measured against doctrine that was written before it was examined and that this examination did not alter.

Where the substrate is excellent — bi-temporal facts, provenance linkage, supersession, hybrid retrieval — Agent Memory should wrap it rather than rebuild it. Where it is absent — authority, lifecycle, receipts, enforced scope — Agent Memory should supply it rather than pretend the gap is a configuration detail.
