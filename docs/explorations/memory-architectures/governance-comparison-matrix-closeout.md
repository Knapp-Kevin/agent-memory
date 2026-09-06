# Governance Comparison Matrix: Executable Closeout Overlay

Status: **closeout overlay for #67**. This file supplements the earlier research matrix with matched executable evidence. It does not erase the historical research-status table.

Legend:

- **E**: direct matched executable evidence in the #67 closeout harness.
- **X**: existing executable evidence elsewhere in the repository.
- **R**: research/documentary evidence only.

| Architecture surface | Identity / provenance | Stale derived state | Correction / currentness | Deletion / residue | Recall / admission | Mutation authority | Evidence class |
|---|---|---|---|---|---|---|---|
| File / document | E | E | E | E | E | E | matched local fixture |
| Linked note / vault | E | E | E | E | E | E | generated-link fixture |
| Lexical retrieval | E | E | E | E | E | E | matched retrieval fixture |
| Vector / embedding RAG | E | E | E | E | E | E | matched retrieval fixture |
| Knowledge graph | E | E | E | E | E | E | asserted/derived path fixture |
| Temporal graph | E | E | E | E | E | E | validity/current-view fixture |
| GraphRAG | E | E | E | E | E | E | graph-derived/cache fixture |
| Event log / ledger | E | E | E | E | E | E | append/supersede/tombstone fixture |
| Relational / document store | E | E | E | E | E | E | SQLite + derived projection fixture |
| Hierarchical / tiered | E | E | E | E | E | E | tier-movement fixture |
| Shared / distributed | E | E | E | E | E | E | competing-writer fixture plus existing shared-write evidence |
| Opaque learned / latent | X | X | X | X/R | X | X | model-internal conditional-memory evidence |
| Hybrid composition | E | E | E | E | E | E | multi-surface dependency fixture |

## Reproduced cross-family invariants

The executable overlay reproduces the following across materially different state representations:

```text
retrieval / reachability != permission
derived state != durable write authority
storage / tier placement != authority
historical integrity != current truth
shared membership != mutation authority
delete operation != forgetting proof
```

The latent/model-internal family has a different observability profile, but it does not overturn those boundaries. Its existing evidence instead strengthens the rule that opaque influence still requires source-neutral governance and consequence containment.

## Family-specific pressures that remain visible

Common governance does not mean identical implementation mechanics.

| Family pressure | Required explicit treatment |
|---|---|
| File / note | path/version identity, generated links, secondary indexes |
| Vector / lexical | model/index version, candidate provenance, rebuild currentness |
| Graph / GraphRAG | asserted vs inferred edges, path provenance, cached summaries |
| Temporal graph / event log | historical vs current truth, validity intervals, tombstones |
| Relational | transaction boundary vs external/materialized projections |
| Tiered | retention/storage movement vs scope and authority |
| Shared / distributed | membership, writer identity, conflict/pre-write coordination |
| Latent / learned | weak proposition-level inspectability, behavioral influence containment |
| Hybrid | dependency closure across all derived surfaces |

## Closeout interpretation

The matrix no longer has a material architecture family for which the core questions of identity, provenance, recall, correction/currentness, persistence, forgetting, and authority are unexplained.

That is sufficient for #67 closeout if exact-head workflow and repository validation pass. It is not a claim that every product, database, embedding model, graph engine, or learned-memory implementation is conformant.
