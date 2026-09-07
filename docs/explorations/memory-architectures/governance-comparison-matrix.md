# Governance Comparison Matrix

Status: exploratory baseline for #67 / #224.

This matrix is **not a ranking**. It records bounded architectural observations and hypotheses with explicit evidence status. Empty or uncertain cells are preferable to made-up scores wearing a tie.

Evidence status legend:

```text
AD  architectural_deduction
PR  primary_research_supported
IO  implementation_observed
BC  benchmark_or_conformance_evidence
CR  cross_architecture_reproduced
OH  open_hypothesis
CT  contradicted
NE  not_yet_evaluated
```

## Baseline matrix

| Architecture family | Identity / canonical-state observation | Correction / derived-state observation | Deletion / residue observation | Recall / PAMA observation | Initial evidence status |
|---|---|---|---|---|---|
| File / document | Exact identity can be path-, version-, or content-hash-based, but path identity and content identity are not equivalent. | Direct source correction can be explicit; generated indexes/summaries may remain stale. | Source deletion does not prove removal from indexes, caches, histories, or backups. | Retrieval can be simple, but permission still must be separated from filesystem reachability. | AD; family experiments NE |
| Linked note / vault | Note identity can remain stable while links/tags/transclusions create separate relational projections. | Human-authored and generated relationships require separate provenance and invalidation. | Deleted note content may survive through transclusion, backlinks, indexes, or exports. | Link adjacency or backlink presence is not recall authority. | AD; family experiments NE |
| Lexical retrieval | Source/chunk identity can remain exact independently of ranking metadata. | Index entries may require explicit invalidation after correction. | Index residue is a derived-state deletion problem even without embeddings. | Ranking score != admission permission. | AD; family experiments NE |
| Vector / embedding RAG | Embedding identity depends on source/chunk plus embedding model/version and transformation state. | Corrected source can leave stale embeddings until re-embedded or invalidated. | Vector deletion must include source-to-vector dependency closure and independent residue checks. | Similarity is candidate discovery, not relevance truth or permission. | AD; existing generic poisoning/lifecycle evidence informs hypotheses; direct family experiment NE |
| Knowledge graph | Node/edge identity may represent assertions, inferred relations, or entities; those must not collapse. | Correction may invalidate edges and downstream paths/summaries rather than only one node. | Deleting an assertion may leave inferred edges, cached traversals, or summaries. | Reachability/traversability != authorization. | AD; direct family experiment NE |
| Temporal graph | Identity includes current and historical relationship versions/intervals. | Supersession can preserve historical truth while changing current truth. | Forgetting may conflict with retained historical versions if content-bearing state remains. | Querying a historically valid edge does not make it current or authorized. | AD; direct family experiment NE |
| GraphRAG | No single state surface should be presumed canonical across source, extraction, graph, community summary, and retrieval index. | Correction may need propagation through several transformation layers. | Residue closure can cross graph, summary, embedding, and cache layers. | Graph/retrieval relevance may discover candidates; admission still requires current governance state. | AD; direct family experiment NE |
| Event log / ledger | Event identity is typically strong, while current truth is a derived/materialized interpretation over history. | Correction often means compensating/superseding events rather than overwrite. | Append-only evidence can conflict with content-forgetting unless content minimization or other mechanisms exist. | Replay/history does not grant current authority under changed policy or scope. | AD; direct family experiment NE |
| Relational / document store | Explicit row/document keys, transactions, indexes, and ACLs can support strong state identity. | Transactions help mutation atomicity but do not automatically govern inferred/derived state outside the canonical record. | Secondary indexes/materialized views/backups remain residue surfaces. | Query permission can be distinct from memory admission and PAMA. | AD; direct family experiment NE |
| Hierarchical / tiered | A single logical memory may have multiple placement/lifecycle representations. | Promotion/demotion between tiers can accidentally conflate storage placement with semantic authority. | Deletion obligations may differ by tier and archival policy. | Moving to “long-term” storage must not itself increase downstream authority. | AD; direct family experiment NE |
| Shared / distributed | Identity must include principal/domain/write-version context, not only shared storage key. | Conflicting writers and delayed propagation create correction/reconciliation hazards. | Revocation/deletion propagation across replicas/views can lag or fail. | Shared membership/readability != mutation/export/recall authority. | AD plus #68 cross-domain evidence supports the generic boundary; family-specific distributed experiment NE |
| Opaque learned / latent | Identity likely requires model/checkpoint/source-basis/version context rather than proposition identity. | Proposition-level correction may be unavailable; invalidation/rebuild/retraining may be the governed consequence. | Absence of recoverable source text does not prove derived information is forgotten. | Predictive quality/influence != action authority. | OH/AD; #137 pressure test active |
| Hybrid composition | Canonical ownership must be assigned per surface rather than per product. | Correction obligations follow transformation dependencies across families. | Residue can be transitive across otherwise independent stores/projections. | PAMA/admission must operate at consequence boundaries, not be assumed inherited through the composition. | AD; cross-architecture reproduction NE |

## What this matrix does not yet establish

The matrix does not claim that one family is safer, more accurate, cheaper, or more governable overall.

It also does not establish numeric grades for:

```text
provenance quality
correction quality
deletion difficulty
observability
human inspectability
operational cost
```

Those dimensions can vary substantially by implementation inside the same family.

## Required upgrade path for a matrix claim

A claim should move through evidence depth only when earned:

```text
architectural deduction
-> primary research and/or pinned implementation observation
-> adversarial fixture
-> comparable experiment on another architecture family
-> cross-architecture reproduced invariant or documented counterexample
```

The final step may support doctrine promotion, doctrine clarification, or an explicit no-change result.

## First comparative experiment candidates

After taxonomy review, prioritize experiments where equivalent governance scenarios can be implemented with modest machinery rather than expensive retrieval benchmarks:

1. file/document canonical state + derived lexical/vector projection;
2. relational/document canonical state + materialized/index projection;
3. graph canonical/derived relation state;
4. event-log history + current materialized view;
5. hybrid source -> embedding -> graph/summary composition;
6. opaque latent fixture from #137 without a large model dependency.

The experimental target is **governance behavior under equivalent state transitions**, not retrieval leaderboard performance.
