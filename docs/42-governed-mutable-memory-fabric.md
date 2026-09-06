# Governed Mutable Memory Fabric

## Purpose

Agent Memory is the memory system. Storage engines, retrieval systems, graph technologies, learned representations, lifecycle engines, and complete first- or third-party memory products are **components** inside or behind that system.

Components expose one or more **capabilities**. Capability families such as storage, vector retrieval, graph traversal, GraphRAG context assembly, lifecycle maintenance, or learned representation are not mutually exclusive product categories.

The primary long-term boundaries are:

```text
Agent Runtime
  plans, reasons, acts, invokes tools
        |
        v
Agent Memory
  memory semantics, lifecycle, provenance, scope,
  structural mutability, PAMA authority, routing,
  mutation, recall admission, evidence
        |
        +--> configurable components
        |       +--> declared capabilities[]
        |       +--> maturity / evidence per capability
        |
        v
Agent Governance peer(s)
  policy / approval / enforcement systems such as
  DashClaw, AGT, or other external governance runtimes
```

Agent Governance is a peer authority surface. It is not a memory substrate. A DashClaw or AGT adapter can tighten consequences or return approval/enforcement evidence, but Agent Memory remains responsible for memory-specific semantics and revalidation at commit and recall.

## Agent Memory owns the fabric

Agent Memory MUST remain authoritative for the general memory contract even when most physical work is delegated to components.

It owns at least:

- logical memory identity and currentness;
- provenance/evidence boundaries;
- scope, tenancy, and isolation;
- lifecycle and supersession semantics;
- PAMA mutation authority;
- structural-mutation authority;
- canonical-versus-derived state classification;
- routing policy and component/capability compatibility;
- governed recall admission;
- correction/deletion obligations;
- evidence sufficient to reconstruct consequential changes.

A component can implement several capabilities, but it does not inherit these authorities by installation.

## Component identity is not capability identity

The fabric uses a many-to-many model:

```text
component identity
!= capability identity

one component
  -> may expose many capabilities

one capability
  -> may have many candidate implementations
```

This distinction is required for first-party systems such as EvolveAI and CodeGenome, which are both broader than one convenient role label.

A deployment may therefore configure:

```text
EvolveAI
  -> temporal graph
  -> vector retrieval
  -> exact retrieval
  -> lifecycle / decay
  -> consolidation

CodeGenome
  -> code graph
  -> graph traversal
  -> impact analysis
  -> embedding storage
  -> vector similarity
```

without forcing either component into one exclusive module type.

Overlap is allowed. Ambiguous canonical ownership or conflicting writable authority is not.

## Capability maturity is explicit

A capability claim should distinguish at least:

| Maturity | Meaning |
|---|---|
| `declared` | documented/intended capability |
| `implemented` | material code exists |
| `runtime_wired` | reachable through a supported runtime/product path |
| `evidence_proven` | reproducible evidence demonstrates the claimed behavior |
| `reference_qualified` | applicable Agent Memory conformance profile is satisfied |

A component being mature in one area does not upgrade every capability it advertises.

The initial evidence-bounded EvolveAI/CodeGenome inventory lives at [`programs/memory-modules/first-party-capability-inventory.md`](programs/memory-modules/first-party-capability-inventory.md).

## Configurable capability families

These are capability families, not exclusive module classes.

### Storage and persistence

Files/Markdown, relational/document stores, graph stores, object stores, event logs, content-addressed vaults, and other persistence mechanisms.

### Retrieval and indexing

Lexical search, vector candidate retrieval, exact lookup, graph candidate retrieval, code-graph queries, and other candidate-generation mechanisms.

### Graph and GraphRAG

Graph capabilities must be described precisely:

```text
graph storage
!= graph query/traversal
!= graph candidate retrieval
!= graph-augmented context assembly / GraphRAG
```

A graph database does not become GraphRAG merely because nodes and edges exist. Conversely, a multi-capability subsystem does not stop having GraphRAG architecture because lifecycle or domain-analysis capabilities are also important.

Issue #291 owns the canonical graph/vector/GraphRAG/hybrid vocabulary.

### Representation

Embeddings, summaries, compressed state, JEPA-style or other learned latent representations.

Vector representation/storage is distinct from vector similarity and vector candidate retrieval.

### Structural and reasoning memory

Domain graphs, code-reality graphs, temporal associations, relationship traversal, impact/blast-radius analysis, and other structured evidence surfaces.

### Lifecycle and maintenance

Decay, weakening, consolidation, synthesis, archival, pruning candidacy, reinforcement signals, and other memory-metabolism capabilities.

### Complete memory-system integration

A first- or third-party memory service may expose several capability families simultaneously. Agent Memory should integrate the component through explicit capabilities rather than flattening it into a single role.

Imported or retrieved state remains subject to Agent Memory provenance, scope, currentness, lifecycle, and admission rules.

## First-party multi-capability systems

### EvolveAI

EvolveAI is not merely a lifecycle component.

At the current evidence boundary its architecture and implementation span, at different maturity levels:

- transient/cache memory;
- vector representation and candidate retrieval;
- temporal graph storage and associative graph primitives;
- GraphRAG-oriented L2 architecture;
- exact/content-addressed L3 retrieval;
- tier routing;
- temporal decay/weakening;
- lifecycle/consolidation mechanisms;
- failure/negative memory;
- persistence and audit mechanisms.

Its differentiator remains adaptive/autopoietic memory metabolism, but that does not erase its graph or vector capabilities.

The current Rust runtime does **not** yet justify an unqualified claim that every designed GraphRAG or real-embedding path is production-wired. Capability maturity is tracked independently under #284/#292.

EvolveAI's learned or heuristic signals may propose consequences but do not acquire Agent Memory mutation authority.

### CodeGenome

CodeGenome is not merely a graph-storage component.

At the current evidence boundary its architecture and implementation span, at different maturity levels:

- content-addressed code identity;
- multi-overlay code-reality graph storage;
- graph query/traversal;
- graph-derived structural context and GraphRAG-ready retrieval substrate;
- embedding persistence;
- vector similarity/k-nearest retrieval;
- confidence/evidence fusion;
- freshness and staleness modeling;
- impact/blast-radius propagation;
- provenance;
- multi-language extraction;
- MCP exposure;
- experiment/self-evaluation capability.

Its differentiator remains code-domain reality, but that does not erase its vector or retrieval capabilities.

CodeGenome's code ontology, confidence, and graph reachability do not become canonical Agent Memory truth or authority merely because the component is first-party.

## Memory horizon is not backend identity

The architecture does not define fixed mappings such as:

```text
short-term = Markdown
mid-term = JEPA
long-term = knowledge graph
```

Those may be reasonable deployment choices, but they are configuration, not doctrine.

Instead the system evaluates memory characteristics such as:

```text
retention horizon
scope and isolation
sensitivity
semantic/relationship density
exactness and audit requirements
lifecycle state
reversibility
latency and cost budget
local/offline requirements
rebuild cost
provenance requirements
```

A deployment profile then requests required capabilities and minimum maturity/posture constraints, and deterministically selects or composes configured component implementations.

This permits different instances to use different combinations while preserving the same Agent Memory behavior and conformance boundaries.

## Capability routing is not authority

Routing should conceptually operate as:

```text
memory characteristics
  -> required capability set
  -> minimum maturity + scope/posture constraints
  -> deterministic component/capability resolution
  -> candidate write / projection / retrieval work
  -> Agent Memory governance remains controlling
```

A learned or heuristic signal may recommend a capability or implementation. It may not silently lower maturity requirements, widen scope, change canonical ownership, or turn routing into mutation authority.

If multiple configured components expose the same capability, precedence or composition must be explicit. Hidden first-match behavior is not a governance model.

## Mutable shape, governed authority

Agent Memory allows memory structures to evolve because useful domain shape is not always knowable at design time.

The system distinguishes:

```text
canonical semantic shape
application / domain ontology
derived / physical representation
```

Changing a vector index is not necessarily changing memory meaning. Adding a project-local entity type is more consequential. Reinterpreting existing durable memory or changing isolation/authority semantics is more consequential still.

ADR-032 establishes the safeguard:

> **Memory shape may adapt. Authority over canonical structural mutation may not be probabilistic.**

Learned, heuristic, or probabilistic systems may discover pressure and propose a new structure. A canonical structural consequence is committed only by:

- a versioned deterministic policy proving the change falls inside an explicitly authorized bounded envelope; or
- an explicitly authorized human decision.

## Structural consequence classes

| Class | Typical change | Default authority posture |
|---|---|---|
| **S0** | rebuild-only derived/index/representation change | autonomous under deterministic maintenance policy |
| **S1** | bounded additive local extension with preserved meaning and rollback | autonomous only when deterministic policy proves the bounded envelope |
| **S2** | semantic reinterpretation or migration-bearing change | user-visible proposal and authorized human decision |
| **S3** | destructive, cross-scope, isolation-, policy-, or authority-bearing change | explicit authorized human decision; stricter PAMA rules may block |

The class is determined by impact, not by how confident the proposing model sounds.

## Schema has lifecycle

Once durable state depends on a shape, that shape cannot be removed casually.

```text
active version
  -> successor proposed
  -> semantic / compatibility / dependency analysis
  -> authority decision
  -> successor activated
  -> migration / rebuild
  -> validation / residue check
  -> old version superseded
  -> retirement only after live dependencies are resolved
```

Historical interpretation should remain reconstructable where it matters. Structural supersession is preferred to pretending the previous model never existed.

## Probabilistic discovery remains useful

The safeguard is not a ban on adaptive discovery.

A model or learned component may observe:

```text
"these memories repeatedly need a release_channel relationship"
```

and produce:

- a candidate entity/relation definition;
- supporting examples and source roots;
- a migration proposal;
- expected retrieval benefit;
- uncertainty and alternatives.

Agent Memory then performs deterministic compatibility, dependency, scope, reversibility, and authority classification before any structural consequence is committed.

```text
probabilistic discovery
  -> candidate structural change
  -> deterministic impact analysis
  -> deterministic governance classification
  -> autonomous bounded commit OR human decision
```

## Three-system responsibility model

### Agent Runtime

Uses memory. It may propose memory operations but does not become memory authority simply because it is the consumer.

### Agent Memory

Owns retained-state semantics and the configured component/capability fabric. It decides what memory is current, admissible, correctable, forgettable, and structurally mutable under PAMA and related doctrine.

### Agent Governance

Owns broader policy, approval, and enforcement concerns outside the memory-specific authority boundary. It may tighten a memory consequence or supply approval/evidence through an adapter without redefining memory semantics.

The interfaces among these systems may evolve. Their responsibilities should remain explicit so an integration does not collapse decision, approval, execution, and memory state into one ambiguous token.

## First implementation target

The first product-shaped acceptance test is deliberately concrete:

1. an agent learns a project-specific release-branch fact;
2. Agent Memory governs and commits it;
3. another session recalls it and changes behavior because of it;
4. new evidence corrects the fact;
5. DashClaw supplies the external governance/approval portion where required;
6. Agent Memory revalidates and supersedes the old current value;
7. another session uses the corrected value;
8. stale approval, authority widening, and cross-scope recall fail;
9. process restart eventually preserves currentness and governance state;
10. the same behavioral contract is rerun with different component/capability compositions.

This is the difference between proving an adapter and proving a memory system.

## Related architecture work

- [`adr/ADR-032-governed-mutable-memory-structure.md`](adr/ADR-032-governed-mutable-memory-structure.md)
- [`rfcs/RFC-001-governed-mutable-memory-fabric.md`](rfcs/RFC-001-governed-mutable-memory-fabric.md)
- [`prd/PRD-001-configurable-agent-memory-runtime.md`](prd/PRD-001-configurable-agent-memory-runtime.md)
- [`programs/memory-modules/first-party-capability-inventory.md`](programs/memory-modules/first-party-capability-inventory.md)
- [`explorations/memory-architectures/progressive-domain-schema-discovery.md`](explorations/memory-architectures/progressive-domain-schema-discovery.md)
- [`profiles/pama-1-2-domain-schema-compatibility.md`](profiles/pama-1-2-domain-schema-compatibility.md)
- issue #274: modular memory profiles program
- issue #275: first-party/external adversarial comparison
- issue #280: component/capability configuration and routing implementation
- issue #284: first-party capability inventory and subsystem-gap analysis
- issue #285: capability-oriented taxonomy correction
- issue #286: external capability mapping
- issue #287: machine-readable capability maturity declarations
- issue #289: first-party subsystem boundary decision
- issue #290: capability-based routing and overlap resolution
- issue #291: graph/vector/GraphRAG/hybrid vocabulary
- issue #292: EvolveAI capability qualification
- issue #293: CodeGenome capability qualification
