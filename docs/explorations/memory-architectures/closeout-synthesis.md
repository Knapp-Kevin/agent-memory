# Memory Architecture Research Closeout Synthesis

Status: **closeout candidate for #67**, pending exact-head evidence and repository validation.

Issue #67 was intentionally finite. Its purpose was not to find a single winning memory backend. It was to test whether Agent Memory's governance distinctions survive across materially different ways of retaining, retrieving, deriving, sharing, and evolving memory.

## Evidence boundary

The closeout uses three complementary evidence classes:

1. **Matched local architecture-family experiment** under `reference/agentmem_ref/harness/architecture_family_closeout.py`, exercising equivalent transitions across ten non-latent family surfaces.
2. **Existing model-internal / conditional-memory evidence** in `model-internal-conditional-memory.md` and its executable evidence workflows for opaque learned or behavioral influence.
3. **Existing cross-cutting research/evidence** for hybrid composition, long-horizon behavior, autonomous maintenance, domain-schema evolution, deletion/correction, observability, and adversarial scenarios.

The minimal local fixtures are not product benchmarks. They are deliberately small reproductions of governance failure modes so the same questions can be compared without letting a named product define a family.

## Taxonomy closeout

| Taxonomy family | Closeout evidence | Result |
|---|---|---|
| File / document | matched filesystem canonical + stale index + deletion residue | governed distinctions survive |
| Linked note / vault | generated-link provenance + stale link after source correction | generated relationship remains derived |
| Lexical retrieval | matched stale lexical projection | retrieval remains candidate discovery |
| Vector / embedding RAG | matched stale vector projection | embedding/retrieval state remains derived |
| Knowledge graph | asserted edges + stale cached path | reachability remains non-authoritative |
| Temporal graph | historical validity interval + stale current view | historical truth remains distinct from current truth |
| GraphRAG | graph-derived path/cache composition | multi-stage derivation requires provenance/currentness |
| Event log / ledger | append/supersede/tombstone sequence | historical integrity remains distinct from current truth and forgetting |
| Relational / document store | SQLite canonical row + stale projection | transactionality does not automatically close derived-state lifecycle |
| Hierarchical / tiered | working -> durable tier move | storage placement/retention change does not create authority |
| Shared / distributed | two writers over same base version | membership/read access does not imply conflict-free mutation authority |
| Opaque learned / latent | existing model-internal conditional-memory evidence | behavioral influence requires bounded, source-neutral governance even when proposition-level inspection is weak |
| Hybrid | canonical source + lexical/vector/graph derived surfaces | deletion/currentness/provenance obligations compose across surfaces |

No known taxonomy family remains unexplained at the level required by #67's closure contract.

## What survived unchanged

The research repeatedly reproduced these core distinctions:

```text
identity != truth
retrieval != recall admission
relevance / reachability != permission
derived state != canonical authority
historical integrity != current truth
storage placement != authority
shared membership != mutation authority
delete operation != forgetting completeness
probabilistic / learned influence != durable write authority
```

PAMA remains the consequence boundary. No architecture family provided evidence that similarity, graph reachability, append-only history, transactional storage, tier promotion, shared access, or learned predictive usefulness should bypass that boundary.

## What was refined

### Derived state became a broader category

The research strengthened the need to treat indexes, embeddings, generated links, graph paths, summaries, caches, materialized views, temporal traces, and learned projections as lifecycle-bearing derived state rather than incidental implementation details.

### Currentness became as important as provenance

Exact provenance is insufficient when a source or schema has changed. Derived state needs explicit currentness/rebuild/invalidation evidence.

This refinement directly informed derivation-currentness work and ADR-030's versioned consumer compatibility boundary.

### Historical integrity and temporal meaning separated further

Event/ledger and temporal-graph families reinforced that preserving history is not the same as asserting present truth. Later ADR-031 work extended this into deterministic temporal commitments, signer/witness evidence, and separate lifecycle currentness.

### Schema evolution became a governed mutation class

Architecture research around progressive domain discovery showed that the domain model itself may change over long-lived memory. Discovery may be probabilistic; schema commitment must remain governed and versioned.

### Hybrid systems became the default serious case

The architecture family label is rarely sufficient for a real system. The useful unit of analysis is each state surface and transformation boundary. A system can simultaneously have file canonical state, vector retrieval, graph summaries, a transactional current view, an event history, and shared replicas.

## What remains hypothetical or future work

The following are not reasons to keep #67 open:

- new products that instantiate already-understood families;
- future model architectures with novel latent-memory mechanics but no new governance question;
- production performance comparisons among stores or retrieval engines;
- choosing a preferred vendor/backend;
- broader external peer adapters where no bounded use case exists yet.

A genuinely new architecture class should receive a new bounded issue if it introduces a governance problem that cannot be explained using identity, provenance, currentness, scope, authority, correction, persistence, recall, and forgetting concepts already covered here.

## Remaining owners

The research program transferred specific gaps into bounded work rather than keeping them as permanent #67 backlog:

- domain-schema mutation and compatibility work;
- derivation/currentness evidence;
- shared-write coordination;
- temporal commitment and temporal-policy interoperability;
- external trust/time/transparency evidence where stronger history claims are required.

Those workstreams have or had their own issues/ADRs/evidence programs. They do not require #67 to remain open as a catch-all architecture issue.

## Closeout decision

If the matched architecture-family workflow and full repository validation pass at the exact final head, #67 can close as **research complete**.

The durable conclusion is not that all memory architectures are equivalent. It is that their materially different storage/retrieval representations can be governed through a shared set of explicit boundaries, while family-specific failure modes remain visible in adapters, projections, lifecycle tracking, and evidence.
