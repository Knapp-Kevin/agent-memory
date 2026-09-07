# Mutable Memory Fabric

Agent Memory is the memory system. Graph databases, RAG implementations, vector indexes, learned representations, files, lifecycle engines, and complete first- or third-party memory services are **components** used by that system.

Components expose one or more **capabilities**. Those capabilities are composable roles, not exclusive product categories.

The boundary is:

```text
Agent Runtime
    |
    v
Agent Memory
    |
    +-- memory semantics
    +-- provenance / scope / lifecycle
    +-- PAMA / structural mutation authority
    +-- component + capability configuration
    +-- capability routing / composition
    +-- governed mutation and recall
    +-- evidence / receipts
    |
    +--> configured components
    |       +--> capabilities[]
    |       +--> maturity/evidence per capability
    |
    v
Agent Governance peer(s)
    policy / approval / enforcement systems
```

Agent Governance is a peer. It can tighten consequences or return approval/enforcement evidence, but it does not become the owner of memory semantics.

## Components and capabilities are different things

The fabric uses a many-to-many model:

```text
component identity != capability identity

one component -> many capabilities
one capability -> many possible components
```

A component can be mature in one capability and experimental in another. First-party ownership does not change that rule.

## Capability maturity is explicit

Agent Memory uses the following capability-specific maturity vocabulary:

- `declared` — documented or intended;
- `implemented` — material implementation code exists;
- `runtime_wired` — reachable through the supported runtime/product path;
- `evidence_proven` — reproducible version-bound evidence demonstrates the claim;
- `reference_qualified` — the applicable Agent Memory qualification/conformance profile is satisfied.

```text
component release status
!= capability maturity

qualification for old version
!= qualification for new version
```

A provider version, adapter version, qualification profile, runtime configuration, or material component-profile change can invalidate earlier qualification applicability.

## Capability families are composable

A deployment can compose capabilities such as:

- **storage/persistence:** files, SQL/document stores, graph stores, object/event stores, content-addressed vaults;
- **exact retrieval:** deterministic key/content-addressed lookup;
- **vector:** representation, persistence, similarity, and candidate retrieval;
- **graph:** graph storage, query/traversal, and candidate retrieval;
- **GraphRAG/context assembly:** graph-augmented context construction;
- **representation:** summaries, compressed state, JEPA-style or other learned representations;
- **structural/reasoning:** temporal associations, code reality, impact/blast-radius analysis;
- **lifecycle/maintenance:** decay, consolidation, synthesis, pruning/archival proposals;
- **procedural memory:** retained skills/procedures without standing execution authority;
- **complete memory systems:** first- or third-party systems exposing several capability families at once.

Important separations remain:

```text
graph storage
!= graph traversal
!= GraphRAG/context assembly

vector representation
!= vector candidate retrieval

retrieval result
!= recall permission

provider-native PASS/BLOCK
!= Agent Memory governance authority
```

## Deterministic overlap and composition

Several components may implement the same capability.

The runtime may:

```text
select one implementation
compose several implementations
or reject an ambiguous configuration
```

It may not silently select whichever provider registered first, lower a maturity requirement during fallback, or let overlapping writable components create ambiguous canonical authority.

Capability selection preserves component identity, capability identity, exact version, scope/currentness posture, provenance, and evidence boundaries.

## Current first-party qualification

The initial August 14 inventory remains a historical revision-pinned research artifact. Present maturity is governed by the current qualification profiles.

### EvolveAI

Current qualified provider pin:

```text
MythologIQ-Labs-LLC/EvolveAI@21161ce7b88dbffeb7ed59757b4d02d24a9c2acd
```

EvolveAI is a multi-capability memory subsystem spanning cache, vector, temporal graph, exact retrieval, routing, lifecycle/consolidation, negative/failure memory, persistence, and audit surfaces.

Its current 15-row Agent Memory profile has four bounded `reference_qualified` capabilities:

- content-addressed exact retrieval;
- persistent snapshot/restart;
- audited L3 deletion;
- L3 provenance/audit.

Other capabilities remain at lower independently earned maturity. In particular:

```text
MockEngine evidence
!= real GG-CORE embedding-quality evidence

graph + vector machinery
!= qualified GraphRAG/context assembly

Shadow Genome native Block
!= Agent Memory PASS/BLOCK authority

audited L3 delete
!= transitive forgetting completeness
```

EvolveAI PR #21 repaired the prior L3 delete-audit gap before those persistence/deletion/audit capabilities were allowed to reach reference qualification.

See [EvolveAI multi-capability profile](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/memory-modules/evolveai-multicapability-profile.md).

### CodeGenome

Current qualified provider pin:

```text
MythologIQ-Labs-LLC/CodeGenome@43a6b7147ec78ec5c616723fa1dd30f342174860
```

CodeGenome is a multi-capability code-domain memory subsystem spanning content identity, graph state/traversal, program analysis, impact propagation, embeddings/vector machinery, provenance, multi-language extraction, and agent exposure.

Its current 18-row profile keeps only `code_graph_traversal` above source-level maturity at `evidence_proven`. No CodeGenome capability is currently `reference_qualified`.

GraphRAG/context assembly, LSP, vector runtime exposure, and deletion/rebuild remain bounded or disabled where dedicated evidence is incomplete.

See [CodeGenome multi-capability profile](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/memory-modules/codegenome-multicapability-profile.md).

## Scope, currentness, and deletion remain Agent Memory concerns

Provider-local state does not automatically inherit Agent Memory scope or lifecycle semantics.

Where necessary, Agent Memory uses an explicit external scope bridge:

```text
provider repository/project/domain scope
!= Agent Memory tenant/project/isolation scope
```

Stale or foreign-scope candidates fail closed. Provider-local deletion does not prove derived residue is gone elsewhere. Provider currentness, confidence, graph reachability, or learned signals remain evidence inputs rather than authority.

## Mutable shape with a deterministic authority boundary

Memory structure can evolve after deployment. A system may discover a useful entity, relation, field, projection, or representation that was not known on day one.

The architecture distinguishes:

```text
canonical semantic shape
application / domain ontology
derived / physical representation
```

The safeguard from ADR-032 is:

> **Memory shape may adapt. Authority over canonical structural mutation may not be probabilistic.**

The path is:

```text
learned / probabilistic discovery
    -> structural proposal
    -> deterministic impact analysis
    -> deterministic governance classification
    -> bounded autonomous commit OR human decision
```

Small rebuild-only or tightly bounded additive changes can be automatic under versioned deterministic policy. Semantic migrations, destructive changes, scope widening, isolation changes, or authority-bearing structures require explicit human authority.

## Why removal is harder than addition

Once durable memory depends on a structure or component projection, removal has lifecycle consequences too.

```text
active component/schema
  -> successor/removal proposal
  -> compatibility + dependency analysis
  -> governance decision
  -> migration / rebuild
  -> validation / residue check
  -> retirement only after live dependencies are resolved
```

The component runtime therefore proves disable/removal/rebuild behavior rather than treating uninstall as semantic erasure.

## Program status

The capability-oriented component program under #274 is complete once its documentation closeout passes exact-head validation.

Completed supporting work includes:

- #280 — configurable component/capability runtime and routing fabric;
- #284 — first-party capability inventory;
- #286 — external capability mapping;
- #287 — machine-readable maturity declarations;
- #289 — first-party subsystem boundary decision;
- #290 — deterministic overlap resolution;
- #291 — graph/vector/GraphRAG/hybrid vocabulary;
- #292 — EvolveAI qualification;
- #293 — CodeGenome qualification;
- #295 — governed procedural memory reference slice;
- #298/#300 — common adapter and executable qualification contract;
- #318 — attach-mode read-only provider discovery/probing.

The program conclusion is not “use EvolveAI everywhere” or “use CodeGenome everywhere.” It is that components should be selected and composed by exact capability requirements and evidence, while Agent Memory retains governance over memory consequence.

## Canonical sources

- [Governed Mutable Memory Fabric](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/42-governed-mutable-memory-fabric.md)
- [Memory Component Capability Program](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/memory-modules/README.md)
- [Program closeout crosswalk](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/programs/memory-modules/program-closeout.json)
- [ADR-032: Governed Mutable Memory Structure](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-032-governed-mutable-memory-structure.md)
- [ADR-033: Capabilities are independently declared and deterministically composed](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-033-capabilities-are-independently-declared-and-deterministically-composed.md)
- [PRD-001: Configurable Agent Memory Runtime](https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/prd/PRD-001-configurable-agent-memory-runtime.md)

The Wiki summarizes. The canonical repository sources govern if the two ever disagree.