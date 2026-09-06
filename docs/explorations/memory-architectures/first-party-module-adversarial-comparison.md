# First-Party Component Capability Adversarial Comparison

Status: **superseded exploratory framing**. The prior version of this document remains available in Git history as evidence of the earlier lane-based hypothesis.

## Why this document was superseded

The original #275 comparison separated the first-party repositories too strongly into:

```text
EvolveAI -> adaptive / lifecycle lane
CodeGenome -> code-domain structural / graph lane
```

Direct repository inspection falsified that framing.

Both repositories are **multi-capability memory subsystems**:

```text
component identity != capability identity

one component -> many capabilities
one capability -> many candidate implementations
```

EvolveAI includes graph, vector, exact-retrieval, tiering, lifecycle, consolidation, failure-memory, persistence/audit, and GraphRAG-oriented surfaces at different implementation maturity levels.

CodeGenome includes graph storage/traversal, graph-derived context, impact analysis, embedding persistence, vector similarity, provenance/evidence fusion, freshness, MCP, and evaluation surfaces at different implementation maturity levels.

A useful differentiator is not an exclusive module type.

## Current evidence boundary

The corrected first-party inventory is pinned to:

- **EvolveAI:** `7cd42412ceed2ab638249a1517b2a6dac46f1312`
- **CodeGenome:** `d2578729a46d495369bd7613845002d50cf20f4c`

See:

- [`../../programs/memory-modules/first-party-capability-inventory.md`](../../programs/memory-modules/first-party-capability-inventory.md)
- issue #284 for first-party capability inventory and gap analysis
- issue #275 for the revised capability-by-capability adversarial benchmark
- issue #286 for external capability mapping
- issue #289 for later first-party subsystem-boundary decisions
- issues #292 and #293 for EvolveAI and CodeGenome capability qualification

## Current comparison method

External and first-party systems are now compared against the same generic capability rows and maturity vocabulary rather than against product-specific lanes.

Capability maturity is recorded as:

```text
declared
implemented
runtime_wired
evidence_proven
reference_qualified
```

Graph and vector terminology is intentionally separated:

```text
graph storage
!= graph query / traversal
!= graph candidate retrieval
!= graph-augmented context assembly / GraphRAG

vector representation / storage
!= vector similarity
!= vector candidate retrieval
```

This prevents both overclaiming and underclaiming. A repository can have GraphRAG as a foundational design while still lacking a fully wired end-to-end GraphRAG runtime path. A repository can implement embeddings and k-nearest retrieval without yet exposing them as its primary supported product query path.

## Governing rules retained from the original comparison

The adversarial posture remains unchanged:

```text
first-party ownership
!= architectural superiority
!= capability maturity
!= Agent Memory conformance
!= reference status
!= canonical doctrine
```

Likewise:

```text
retrieval score != recall permission
graph reachability != authority
confidence fusion != truth
learned adaptation != mutation authority
```

EvolveAI and CodeGenome must earn each capability claim against the same currentness, correction, deletion/residue, scope/isolation, failure, provenance, and governance boundaries applied to external implementations.

## Historical note

The previous long-form comparison contained useful system-specific observations about EvolveAI, CodeGenome, Hindsight, MemOS, GitNexus, and Graphify. It is intentionally preserved in repository history rather than copied forward as active guidance because several conclusions were organized around the now-falsified exclusive-lane model and CodeGenome was pinned to an older revision.

Current research should use #275, #284, #286, and the capability inventory above as the active evidence surfaces.
