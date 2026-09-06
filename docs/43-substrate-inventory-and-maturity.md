# Substrate Inventory and Maturity

**Purpose**: a single answer to "which memory substrates exist, where does each live, and how mature is it" — for first-party substrates and for the external systems people reach for as equivalents.

**Method**: derived from code and from committed qualification artifacts, not from intent. Every maturity value below is either read from a qualification artifact on disk or stated as absent.

---

## 1. The distinction this document exists to make

"Substrate", "capability", "architectural role", and "persistence mechanism" are four different things, and the names people use conversationally cut across all four. Conflating them is how a component acquires maturity it never earned.

| Kind | Definition here | Example |
|---|---|---|
| **Substrate** | A concrete implementation of `TemporalGraphPort` — `add_episode`, `write_fact`, `invalidate_fact`, `get_fact`, `delete_fact`, `search` | `InMemoryTemporalGraph` |
| **Capability** | A named, versioned, qualifiable function a component provides | `resource_artifact_memory v1.0` |
| **Architectural role** | A position in the layer model that some component may be proposed to fill | Code Reality Graph |
| **Persistence mechanism** | Storage technology a substrate or provider may use underneath | Markdown, Postgres, object store |

`docs/42-governed-mutable-memory-fabric.md:131` already states the governing rule: *"A graph database does not become GraphRAG merely because nodes and edges exist."* The same applies in every direction. **Postgres underneath a provider is not a substrate, and a substrate is not a capability.**

---

## 2. First-party substrates — there are exactly two

Verified by enumerating classes implementing the full `TemporalGraphPort` surface.

| Substrate | Location | Maturity | Notes |
|---|---|---|---|
| `InMemoryTemporalGraph` | `reference/agentmem_ref/substrate.py:92` | **reference implementation** — the executable definition, not a qualified component | Deliberately permissive: `write_fact` is documented as "Direct write. No authority check, by design and by observation." Governance lives in the adapter above it. Owns the identifier counter as of ledger entry #12. |
| `GraphitiSubstrate` | `reference/agentmem_ref/graphiti_driver.py:64` | **`declared`** — no qualification artifact exists | Implements the port over `graphiti-core`. **Not a declared dependency**, and targets deprecated Kuzu. Cannot be checkpointed: `JsonRuntimeStateStore` reaches into `InMemoryTemporalGraph` privates (`_episodes`, `_facts`, `write_log`). Tracked as [#363](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/363). |

**No other substrate exists in this repository.** Any additional substrate is prospective work, not an implementation with a location.

---

## 2b. First-party memory implementations

**Correction.** The first draft of this document scoped itself to `TemporalGraphPort` implementations and so answered "which substrates exist" while missing "which functional memory implementations exist". Those are not the same question, and the second is the more useful one. Agent Memory carries a family of governed memory implementations in-repo today:

| Implementation | Location | What it is |
|---|---|---|
| Epistemic belief memory | `reference/agentmem_ref/epistemic_memory.py` | Bounded `epistemic_belief_memory` runtime surface, Capability Contract v3 |
| Procedural / skill memory | `reference/agentmem_ref/procedural_memory.py` | ADR-034 vertical slice; a skill is bounded JSON metadata plus human-readable procedure, not a specialized skill store |
| Predictive / counterfactual memory | `reference/agentmem_ref/predictive_memory.py` | Bounded `predictive_counterfactual_memory` surface, Capability Contract v3 |
| Conditional memory influence | `reference/agentmem_ref/conditional_memory_influence.py` | Vendor-neutral admission evidence for model-internal conditional memory |
| Code-graph qualification | `reference/agentmem_ref/code_graph_qualification.py` | Provider-neutral CodeGenome/Graphify normalizer (#300) |

These are **memory implementations**, not substrates: they sit above `TemporalGraphPort` and use a substrate for persistence. A substrate is where facts live; a memory implementation is a governed surface with its own contract, lifecycle, and admission semantics.

### Maturity ladder

Schema-enforced in `schemas/component-capability-qualification.schema.json`:

```
declared -> implemented -> runtime_wired -> evidence_proven -> reference_qualified
```

A component sits at `declared` until evidence moves it. Nothing self-promotes.

---

## 3. Qualified external components

These are **capability providers**, not substrates. They provide a named capability under a qualified contract; neither implements `TemporalGraphPort`.

| Component | Capability | Earned maturity | Authority effect | Artifact |
|---|---|---|---|---|
| `hindsight-v0.9.0` | `resource_artifact_memory v1.0` | **`evidence_proven`** | `none` | `reference/fixtures/component-qualification/hindsight-v0.9.0-resource-artifact-qualified-v12.json` |
| `memos-local-plugin-v2.0.17` | `resource_artifact_memory v1.0` | **`evidence_proven`** | `none` | `.../memos-local-plugin-v2.0.17-resource-artifact-qualified-v12.json` |

Both qualifications are **narrow by construction** and say so. Hindsight carries 5 recorded limitations, MemOS 7. Two worth repeating because they are the kind of thing that gets dropped in summary:

- *"Only chunk-backed `resource_artifact_memory` is qualified; richer LLM-backed Hindsight modes are outside this evidence."*
- *"PostgreSQL underneath Hindsight is not evidence that the Hindsight operation exposed to Agent Memory has a particular atomic or concurrency guarantee."* (`docs/programs/memory-modules/hindsight-v090-qualification.md:149`)

`authority_effect: none` on both: a qualified provider supplies memory, never authority.

---

## 4. Named concepts that are not substrates

Each of these is real and each lives somewhere — just not as a substrate. This section exists so nobody has to rediscover that.

### Code Reality Graph

**Agent Memory owns this contract. That is a decided and accepted position, not an open question.**

- `docs/39-implementation-ownership-map.md:28` — *"Reality Graphs | **Agent Memory contract**; CodeGenome candidate implementation | Runtime Memory | declared"*
- `ADR-035` (**Accepted**) `:272` — *"CodeGenome is the initial first-party implementation of the Code Reality Graph"*, and `:661` — mapped *"without promoting its domain ontology to universal memory semantics"*

So the ownership split is settled: **Agent Memory owns the contract and the naming; CodeGenome is the initial implementation of it.** A Code Reality Graph derived from CodeGenome is an Agent Memory artifact under an Agent Memory name, not a CodeGenome export.

**Status: `declared`** — the contract is owned and the implementation candidate is named; no module has been built yet.

**CodeGenome is adoptable wholesale** ([ADR-036](adr/ADR-036-same-owner-components-are-first-party-modules.md)): it shares Agent Memory's owner, so it is a first-party module candidate rather than an attributed provider. Adopted work is named **Agent Memory's Code Reality Graph (CRG) module** — no provider label, no originating-repository name, no attribution obligation. It will therefore never earn a qualification artifact here, because qualifying your own module against your own contract measures nothing; its maturity is ordinary module maturity.

**What exists here now**: `reference/agentmem_ref/code_graph_qualification.py` is a provider-neutral CodeGenome/Graphify qualification normalizer (issue #300). It preserves provider-native outputs as separate artifacts and normalizes only the shared factual surface, and its docstring states it "cannot grant Agent Memory authority". Profiles live at `docs/programs/memory-modules/codegenome-multicapability-profile.md` and `codegenome-scope-residue-closeout.md`.

**What does not exist here**: a named, Agent-Memory-owned Code Reality Graph *module*. See §6.

External equivalents: code-property-graph and code-knowledge-graph tooling (Sourcegraph SCIP, Glean, CodeQL's database). None is qualified against a capability contract here.

### GraphRAG

A **capability family**, not a store (`docs/42:7,120-131`). The doctrine spends a section distinguishing graph storage from graph-augmented context assembly precisely because the two get conflated.

**Maturity: doctrine-defined; no GraphRAG capability is declared or qualified in this repository.**

External equivalents: Microsoft GraphRAG, LlamaIndex property-graph retrievers, Neo4j GraphRAG. A substrate could underlie any of them; none is one.

### Markdown / files

A **persistence mechanism** (`docs/42:114`, `docs/rfcs/RFC-001:164`). `ADR-034:71` states procedural memory MAY use Markdown, and `:236` states doing so does not make Markdown canonical. `docs/42:209` uses `short-term = Markdown` as an illustration of a lifecycle-to-mechanism mapping, not a specification.

**Maturity: named as an example; no Markdown substrate exists.**

### Postgres / SQLite

A **persistence mechanism** (`RFC-001:164`), and the subject of an explicit anti-inference rule: durability of the storage engine is not evidence about the capability contract above it (`federated-resource-exchange.md:48`, `hindsight-v090-qualification.md:149`).

**Maturity: named as an example; no relational substrate exists.** Hindsight uses PostgreSQL underneath, which is a property of Hindsight, not a Postgres substrate in this repository.

External equivalents: pgvector, Supabase, Timescale for temporal workloads. Any of these could back a future substrate; none is one today.

---

## 5. Structural finding — there is no modular structure to own a named module

`reference/agentmem_ref/` contains **122 modules and zero subdirectories**. It is entirely flat.

That is the concrete obstacle to the stated intent that a derived Code Reality Graph be "Agent Memory owned and named within a modular structure". There is no package boundary for a named memory module to occupy, so every implementation — epistemic, procedural, predictive, conditional, code-graph qualification — sits in the same undifferentiated namespace as `receipts`, `policy`, and 100+ comparator, harness, and evidence-emitter modules.

The ownership decision (§4, Code Reality Graph) is settled and documented. The **structure to express it is not built**. Those are different gaps and only the second is open:

| | State |
|---|---|
| Agent Memory owns the Code Reality Graph contract | **decided**, ADR-035 Accepted + `docs/39:28` |
| CodeGenome named as initial implementation | **decided**, same sources |
| Named Agent-Memory-owned Code Reality Graph module | **not built** |
| Modular package structure to hold it | **not built** — `agentmem_ref/` is flat |

This interacts directly with [#362](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/362) (no public consumer API): a module structure and a public surface are the same design conversation, and Sprint 4's boundary freeze is where both belong.

---

## 6. Summary — what actually exists

| | Count | At what maturity |
|---|---|---|
| First-party substrates | **2** | one reference implementation, one `declared` |
| First-party memory implementations | **5** | in-repo, above the substrate layer (§2b) |
| Qualified external components | **2** | both `evidence_proven`, both `authority_effect: none` |
| Contracts Agent Memory owns whose module is not yet built | 1 (Code Reality Graph) | **ownership decided**; module and structure open |
| Capability families with no declaration here | 1 (GraphRAG) | doctrine-defined |
| Persistence mechanisms named as examples | 4+ (Markdown, files, Postgres/SQLite, object stores, event logs) | not substrates |

**The gap between what the doctrine names and what the runtime implements is intentional and is the honest state.** The layer model describes an architecture; the reference runtime implements the parts that have been built and proven. This document exists so the difference stays visible rather than being read as a claim.

---

## 7. Maintenance

Update in the same change that adds a substrate, declares a capability, or lands a qualification artifact. A substrate added without a row here is a `docs/GOVERNANCE_INDEX.md` Tier 1 drift bug.
