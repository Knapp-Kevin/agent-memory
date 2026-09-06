# First-Party Memory Capability Inventory

Status: **evidence-bounded inventory; qualification remains version-scoped**

Program issues: #284, #280, #292, #293, #298

## Purpose

Agent Memory must not classify a first-party subsystem by one convenient headline capability.

EvolveAI and CodeGenome are both **multi-capability memory subsystems**. Their differentiators remain useful, but those differentiators are not mutually exclusive module types.

The governing relationship is:

```text
component identity
!= capability identity

one component -> many capabilities
one capability -> many possible components
```

Agent Memory composes against explicit capability contracts while preserving the identity, version, provenance, failure posture, maturity, and qualification applicability of the component implementing each capability.

## Evidence boundary

This inventory is pinned to:

- **EvolveAI:** `7cd42412ceed2ab638249a1517b2a6dac46f1312`
- **CodeGenome:** `d2578729a46d495369bd7613845002d50cf20f4c`

The inventory is intentionally conservative. It distinguishes documentation/design intent from code existence, supported runtime reachability, executable evidence, and Agent Memory qualification.

Important:

```text
inventory maturity observation
  != permanent qualification
```

#298 defines the executable adapter/qualification contract. `evidence_proven` and `reference_qualified` must bind the exact component/capability/adapter/qualification-profile/runtime identity that earned them.

## Maturity vocabulary

| Maturity | Meaning |
|---|---|
| `declared` | The repository documents or designs the capability. Runtime implementation is not established by this label. |
| `implemented` | Material implementation code exists at the pinned revision. This does not prove the capability is reachable through the supported runtime/product path. |
| `runtime_wired` | The capability is reachable through a supported runtime/product path at the pinned revision, subject to the listed limitations. |
| `evidence_proven` | Reproducible, version-bound evidence demonstrates the claimed behavior against an explicit fixture or acceptance contract. |
| `reference_qualified` | The capability has satisfied the applicable Agent Memory component/capability qualification/conformance profile. |

Maturity is attached to a **capability**, not inherited from repository-wide product status.

## Capability vocabulary posture

```text
graph storage
!= graph traversal
!= graph candidate retrieval
!= GraphRAG / graph-augmented context assembly

vector storage
!= vector similarity
!= vector candidate retrieval
```

This avoids both common errors: calling every graph-backed system GraphRAG, and pretending a system has no GraphRAG architecture merely because graph retrieval is one capability among many.

## EvolveAI inventory

Pinned source: https://github.com/MythologIQ-Labs-LLC/EvolveAI/tree/7cd42412ceed2ab638249a1517b2a6dac46f1312

EvolveAI's README describes a tri-layer system with L1 transient cache, L2 temporal graph, and L3 UOR vault. Its Autopoietic Memory Theory describes L2 as a GraphRAG knowledge graph with vector embeddings. The active Rust rewrite contains an L2 weighted temporal graph and a query path that performs exact L3 content-addressed lookup or vector scan across L1/L2/L3.

Implementation-maturity gaps remain material: the default reachable embedding engine is mock-based, real embeddings are not yet wired into the supported product path, lifecycle/Shadow Genome subsystems are implemented but not integrated into normal runtime execution, and automatic consolidation/pruning/persistence behavior remains incomplete.

### Current audit-integrity blocker

EvolveAI #19 is open at this evidence boundary:

`BUG: L3 forget removes vault entry without recording deletion in hash-chain ledger`

The implemented L3 removal path removes the live entry without appending an explicit delete/tombstone ledger operation. Therefore:

```text
live L3 removal
  != reconstructable audited deletion
  != Agent Memory transitive forgetting completeness
```

This explicitly limits the deletion, persistence/audit, and provenance qualification posture until a repaired revision is re-pinned and executed through #298.

| Capability family | Maturity | Evidence / current posture | Agent Memory note |
|---|---|---|---|
| transient/cache memory | `runtime_wired` | L1 transient cache is part of the active Rust tri-layer runtime. | Candidate storage/cache capability, not authority. |
| temporal graph storage | `runtime_wired` | `crates/evolve-core/src/tiers/l2_graph.rs` stores memory nodes and weighted timestamped edges. | Strong candidate temporal/associative graph capability. |
| graph traversal / association | `implemented` | Active L2 graph exposes neighbor/edge traversal primitives. Supported query path does not currently use graph traversal as its main retrieval assembly path. | Do not claim end-to-end GraphRAG from graph storage alone. |
| GraphRAG / graph-augmented context assembly | `declared` | Theory specifies L2 GraphRAG with vector embeddings and GraphRAG Top-K retrieval; complete runtime assembly is not established. | Requires runtime qualification under #292. |
| vector representation | `runtime_wired` with material limitation | Active query path encodes representations, but reachable default engine is `MockEngine`; real embedding support is not established through the supported product path. | Semantic retrieval quality is not production evidence. |
| vector candidate retrieval | `runtime_wired` with material limitation | Query path performs vector scan across tier candidates; default embeddings remain mock-derived. | Similarity is candidate evidence, not admission. |
| exact/content-addressed retrieval | `runtime_wired` | Active query helper performs L3 exact match using UOR-derived content address. | Exact retrieval remains distinct from Agent Memory logical identity/authority. |
| tier routing | `runtime_wired` | L1/L2/L3 routing exists; MTS inputs remain simplistic in places. | Routing evidence is not mutation authority. |
| temporal decay / weakening | `runtime_wired` | Decay-aware scoring/filtering participates in query behavior; full GC/consolidation loop is incomplete. | Lifecycle signal, not truth/authority. |
| consolidation / REM-style synthesis | `declared` / partial implementation | Central to theory/lifecycle design; active runtime does not drive the complete loop. | Requires explicit runtime and provenance qualification. |
| lifecycle orchestration | `implemented` | Orchestrator exists and is tested, but normal CLI/Tauri paths do not drive it. | Candidate capability below `runtime_wired`. |
| failure / negative memory (Shadow Genome) | `implemented` | Shadow Genome exists and is tested, but supported runtime paths do not meaningfully populate/use it yet. | Similarity/failure evidence must not become governance PASS/BLOCK authority. |
| persistent snapshot/state | `runtime_wired` with limitation | Persistent state exists; snapshot-on-demand, missing robust auto-persistence/WAL, and migration/concurrency gaps remain. | Restart semantics require stronger evidence. |
| deletion / forget operation | `runtime_wired` **with audit-integrity blocker** | CLI exposes `forget`; live removal exists, but EvolveAI #19 shows L3 removal is not recorded as an explicit ledger delete/tombstone at this pin. | MUST NOT be called reconstructable audited deletion or `reference_qualified` forgetting. |
| learned/predictive representation | `declared` / partial | Representation engines/future embedding work exist; no reference-qualified predictive/world-model capability is established. | Learned representation is not authority. |
| provenance / audit | `implemented` **with material blocker** | Hash-chained ledger/accountability mechanisms are substantial, but #19 demonstrates the ledger does not record the current L3 forget mutation. | Qualification must carry the blocker until repaired/retested. |

### EvolveAI conclusion

The label **adaptive/lifecycle module** describes a differentiator, not the subsystem's complete surface.

A more accurate shape is:

```text
EvolveAI
  transient/cache memory
  temporal graph memory
  graph/associative primitives
  GraphRAG-oriented architecture
  vector representation + retrieval
  exact content-addressed retrieval
  tier routing
  temporal decay
  lifecycle / consolidation mechanisms
  failure / negative memory
  persistence + audit mechanisms
```

#292 must qualify each capability independently through #298. It must not convert this inventory into a certification table.

## CodeGenome inventory

Pinned source: https://github.com/MythologIQ-Labs-LLC/CodeGenome/tree/d2578729a46d495369bd7613845002d50cf20f4c

CodeGenome describes itself as a Unified Code Reality Graph: a content-addressed multi-layer program-analysis graph merging syntax, semantics, control/data flow, process traces, runtime observations, and other overlays into one queryable substrate.

The current pin includes two correctness repairs found by Agent Memory #275 before matched runtime evidence was trusted:

- CodeGenome #8 / PR #9: target resolution binds requested file identity as well as line span;
- CodeGenome #10 / PR #11: upstream/downstream/both now control actual traversal semantics.

Those are mandatory regression cases for #293.

CodeGenome also contains embedding persistence plus cosine-similarity k-nearest-neighbor retrieval. That surface is real implementation, but this inventory does not establish it as the primary supported product query path.

| Capability family | Maturity | Evidence / current posture | Agent Memory note |
|---|---|---|---|
| content-addressed code identity | `runtime_wired` | Core graph nodes use BLAKE3/UOR-style content identity across supported code evidence. | Domain identity can inform Agent Memory without becoming universal core identity doctrine. |
| multi-overlay graph storage | `runtime_wired` | Syntax, semantic, flow, process, PDG, runtime, SCIP and related overlays compose into the code-reality graph. | Strong code-domain graph capability. |
| graph query / traversal | `runtime_wired` | Query/traversal and impact propagation are first-class product functions; current pin includes repaired directional semantics. | Strong candidate for first #298 qualification. |
| graph-derived context / GraphRAG readiness | `implemented` / graph-query substrate `runtime_wired` | Graph traversal is operational and agent-exposed. A separately specified end-to-end GraphRAG/context-assembly contract is not established. | Qualify exact claim under #293. |
| embedding storage | `implemented` | Substrate persists embedding vectors bound to addresses/models/timestamps. | Real vector representation storage. |
| vector similarity | `implemented` | Cosine similarity and k-nearest logic exist with tests. | Similarity is candidate evidence, not recall authority. |
| vector candidate retrieval product path | `implemented`, not established `runtime_wired` | k-NN exists in substrate/tests, but primary inspected query surface centers graph traversal. | #293 must prove supported runtime exposure before stronger claim. |
| confidence/evidence fusion | `runtime_wired` | Multi-observer edge confidence fusion using noisy-OR is core behavior. | Correlated observations need pressure; confidence never becomes truth/authority. |
| impact / blast-radius propagation | `runtime_wired` | Signal propagation and directional impact traversal are active capabilities. | Strong code-domain reasoning/structural capability. |
| provenance / observer separation | `runtime_wired` | Graph artifacts retain observation/provenance distinctions. | Align through adapter evidence rather than assuming equivalence. |
| freshness / staleness modeling | `runtime_wired` | Freshness/staleness and propagation are explicit product concepts. | Qualification must add source-mutation/update regression. |
| multi-language extraction | `runtime_wired` | Rust, TypeScript/TSX, and Python share language-neutral extraction IR at this pin. | Domain capability, not core ontology. |
| MCP/agent exposure | `runtime_wired` | MCP server exposes governed tools. | MCP exposure itself is not Agent Memory conformance. |
| experiment / self-evaluation engine | `runtime_wired` | Experiment engine, fitness functions, raw run records, adaptive research loop exist. | Evaluation may improve implementation without self-authorizing memory mutations. |
| LSP overlay | `declared` / stub | README identifies LSP as a stub that detects rust-analyzer but contributes no graph edges. | MUST NOT be counted as active/evidence-proven until runtime evidence changes. |
| deletion / rebuild | `implemented` / evidence incomplete | Store/index lifecycle mechanics exist; Agent Memory-grade deletion-residue/rebuild conformance is not established. | Test explicitly under #293/#298. |

### CodeGenome conclusion

The label **code-domain structural-memory module** also describes a differentiator rather than the complete capability surface.

```text
CodeGenome
  content-addressed code identity
  multi-overlay graph storage
  graph query / traversal
  graph-derived context substrate
  embedding persistence
  vector similarity / k-nearest retrieval
  confidence/evidence fusion
  impact propagation
  freshness / provenance
  multi-language extraction
  MCP exposure
  experiment / self-evaluation
```

#293 must qualify those surfaces independently through #298.

## Overlap is expected, not a defect

| Capability family | EvolveAI | CodeGenome | Interpretation |
|---|---|---|---|
| graph state | temporal/associative memory graph | code-reality multi-overlay graph | Same broad family, materially different domain semantics. |
| graph retrieval/traversal | primitives implemented; full GraphRAG not runtime-qualified | graph query/traversal core runtime behavior | Do not force replacement merely because both use graphs. |
| vector representation | active with mock-engine limitation | embedding storage implemented | Legitimate overlap at different maturity. |
| vector retrieval | active vector scan with mock-default limitation | k-NN implemented but not established product path | Model overlap explicitly and qualify separately. |
| content identity | UOR-backed exact durable memory | content-addressed code artifacts | Related exact-identity mechanisms at different semantic layers. |
| provenance/evidence | ledger/accountability orientation, with current deletion gap | multi-observer graph evidence | Both useful; neither replaces Agent Memory provenance semantics. |
| self-adaptation/evaluation | lifecycle/autopoietic adaptation | adaptive experiment engine | Both may propose changes; neither gets Agent Memory authority. |

The correct architecture permits:

```text
same capability family
  -> several implementations
  -> different domains / costs / strengths / maturity
  -> deterministic profile selects one or composes several
```

Overlap is only a problem when canonical ownership, write authority, precedence, currentness, or qualification applicability becomes ambiguous.

## Capability gaps and current portfolio result

The inventory does **not** justify a new first-party subsystem merely because a capability row is incomplete.

Generic gaps/pressure areas include:

- procedural/skill memory, now proven as Agent Memory semantics by #295 rather than a new database;
- multimodal memory;
- shared/federated memory;
- learned latent/predictive/world-model memory beyond embeddings;
- explicit episodic/event history where existing components do not satisfy the generic contract cleanly;
- archival/cold memory and long-retention economics;
- causal/intervention memory;
- privacy-preserving/confidential-memory substrates;
- high-order/hypergraph relationships;
- other capability families surfaced by external comparators.

For each gap, decide:

```text
extend EvolveAI
extend CodeGenome
implement generic semantics in Agent Memory core
compose existing components
adopt/wrap external implementation
create new first-party subsystem
defer
```

A blank matrix cell is not an argument for a new repository.

## Contract implication

The current architecture is:

```text
component declaration
  identity/version/profile
  capabilities[]
      capability identity/version
      maturity + posture
      evidence refs / limitations
        |
        v
deterministic provider resolution
        |
        v
versioned component adapter
        |
        v
raw provider evidence + normalized result
        |
        v
Agent Memory currentness/scope/lifecycle/governance
        |
        v
version-bound capability qualification record
```

The detailed next-layer contract is:

`docs/programs/memory-modules/component-adapter-qualification-contract.md`

## Next work

- #287 and #290 are complete through PR #297.
- #295 is complete and ADR-034 is Accepted.
- #298 defines the executable adapter + qualification boundary.
- #280 remains open until the broader runtime semantics and real portability proof exist.
- #293 should use CodeGenome + a freshly pinned Graphify run as the first deterministic qualification pressure.
- #292 should wait for the common harness and must preserve EvolveAI #19 as a blocker for strong deletion/audit claims.
- #282 later carries qualification/currentness interpretation through real process restart.

No new ADR is currently indicated by this inventory refresh.