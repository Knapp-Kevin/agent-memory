# External Capability Frontier Refresh — 2026-08-14

Status: **Current research snapshot; re-pin before executable qualification**

Tracks: #298, #280, #292, #293

This file refreshes fast-moving external systems after the broader capability frontier in `external-capability-frontier.md` was written. It does not replace historical source pins or convert research observations into dependencies.

## Rules for using this refresh

```text
current research observation
  != permanent dependency pin
  != conformance
  != source-rights approval for every use
```

Before a system enters an executable qualification run, record:

- exact repository/source;
- exact commit or release tag;
- package/runtime version and digest where material;
- license/source-rights posture at that exact source;
- adapter and qualification-profile versions;
- configuration/model/parser versions;
- raw evidence artifact digest.

## Code-graph / structural-memory comparators

### Graphify

Repository: `Graphify-Labs/graphify`

Current release observed through GitHub API on 2026-08-14:

```text
release: v0.9.43
tag commit: 7281f27eac568f77f50910f59f84543458f5dfd1
published: 2026-08-14
```

Current relevant capabilities:

- deterministic local tree-sitter code parsing;
- graph state/traversal;
- explicit `EXTRACTED`, `INFERRED`, and documented ambiguous provenance posture;
- broad language extraction surface;
- local code-only path without LLM or vector store;
- query/path/explain and agent-integration surfaces;
- incremental/update behavior that can be pressure-tested for currentness.

Source-rights development:

- release v0.9.25 changed the active project license from MIT to Apache-2.0;
- upstream retains `LICENSE-MIT` and `NOTICE` for pre-relicense contributions.

Disposition:

`execute/adapt as an external comparator candidate after exact run-time re-pin`

Why it matters for #298:

Graphify is a deliberately different implementation from CodeGenome while exposing matched deterministic code-graph facts. It can pressure the adapter contract without introducing model/API variability.

### GitNexus

Repository: `abhigyanpatwari/GitNexus`

Current package source observed:

```text
package: gitnexus 1.6.9
license: PolyForm-Noncommercial-1.0.0
```

Current relevant capabilities include:

- local code indexing;
- graph-powered query/context/impact surfaces;
- MCP tools;
- agent skills;
- hooks and stale-index detection;
- processes/traces;
- hybrid lexical/semantic code search;
- broad coding-agent integrations.

The richer current product surface increases its value as a **behavioral/source comparator**, but the license remains the controlling stop line for a commercial Agent Memory runtime.

Disposition:

```text
source/behavior comparison and independent synthesis
!= commercial runtime dependency
!= copied implementation material
```

unless separate commercial rights are obtained.

## General memory-system adapter candidates

### Hindsight

Repository: `vectorize-io/hindsight`

Current release observed:

```text
release: v0.9.1
published: 2026-08-14
```

Relevant current shape:

- `Retain`;
- `Recall`;
- `Reflect`;
- world facts;
- experiences;
- mental models;
- parallel semantic/vector retrieval;
- BM25/keyword retrieval;
- graph retrieval;
- temporal retrieval;
- reciprocal-rank fusion and reranking;
- banks/metadata for isolation;
- released package/binary artifacts.

Disposition:

`strong complete-memory-system adapter candidate after exact executable pin`

Pressure value:

Hindsight is useful because it combines multiple retrieval families behind a small API while still requiring Agent Memory to preserve currentness, scope, admission, correction, and governance outside provider relevance.

### MemOS

Repository: `MemTensor/MemOS`

Current release observed:

```text
release: v2.0.30
source commit: f4db521214c29337164ec788bafede7eab236c25
published: 2026-08-14
```

The current local plugin exposes a particularly useful self-evolving memory shape:

```text
L1 trace
L2 policy
L3 world model
Skill
Reflect2Evolve
```

Relevant capability pressure:

- textual/tree/preference/skill memories;
- vector and graph storage;
- scheduling/version management;
- local plugin runtime;
- feedback-driven policy/skill evolution;
- skill -> trace/episode -> world-model retrieval.

Disposition:

`strong procedural/metamemory and complete-system comparator candidate`

Governance boundary:

Reflect2Evolve or learned policy/skill evolution may produce proposals/evidence. It does not gain Agent Memory profile, structural, recall-admission, or action authority merely by being part of the provider runtime.

### Acontext

Repository: `memodb-io/Acontext`

Current research posture:

```text
license: Apache-2.0
model: agent skills as a memory layer
representation: readable/editable skill files
```

Relevant shape:

- task completion/failure -> distillation -> skill agent -> skill update;
- Markdown/file-oriented skill memory;
- no required vector-store ontology for skill recall;
- export/reuse across agents/frameworks;
- self-hosting and API surfaces.

Disposition:

`procedural-memory adapter/comparator candidate`

Pressure value:

Acontext tests whether Agent Memory's identity/currentness/scope/correction/evidence contract remains useful when the provider is human-readable file memory rather than a graph/vector database.

### MIRIX

Repository: `Mirix-AI/MIRIX`

Current upstream release/docs posture:

```text
v0.1.6+
main line described as a pure memory system API
legacy desktop-agent line deprecated
```

Relevant memory families include Core, Episodic, Semantic, Procedural, Resource, and Knowledge Vault style surfaces plus hybrid retrieval.

Disposition:

`complete-memory-system adapter candidate`

The provider taxonomy remains provider-local. MIRIX categories do not become canonical Agent Memory ontology through integration.

### Memento-Skills

Repository: `Memento-Teams/Memento-Skills`

Current latest GitHub release observed:

```text
release: v0.3.8
source/target: e7687d9c14b87c424d39498a1e8e91afd7c57d9f
license: MIT
```

Current architectural pressure:

```text
Read
  -> retrieve or create skill
Execute
  -> act using skill/tool runtime
Reflect
  -> attribute success/failure and utility
Write
  -> revise/create skills
```

Disposition:

`strong ADR-034 adversarial comparator`

Why it matters:

Memento-Skills deliberately collapses deployment learning into a tight self-evolving loop. Agent Memory must preserve the useful learning behavior while separating:

```text
retained skill
!= admitted skill
!= action permission
!= authorization to rewrite future memory/profile behavior
```

### EverOS / HyperMem

Repository family: `EverMind-AI/EverOS`, `EverMind-AI/HyperMem`

Current research posture:

- EverOS: Apache-2.0;
- runnable memory architectures/benchmarks;
- EverCore general memory path;
- HyperMem high-order relationship path;
- EverMemBench and EvoAgentBench evaluation surfaces.

HyperMem exposes a three-level structure:

```text
topic
  -> episode
  -> fact
```

with weighted hyperedges and coarse-to-fine retrieval.

Disposition:

`later high-order-relationship / benchmark comparator`

Current conclusion remains:

```text
hypergraph capability may be useful
!= hypergraph topology should become canonical Agent Memory ontology
```

## First-party reference points

### CodeGenome

Repository: `MythologIQ-Labs-LLC/CodeGenome`

Current pin used by the first-party inventory and qualification planning:

`d2578729a46d495369bd7613845002d50cf20f4c`

Important qualification history:

- #275 found file+line target-resolution defect CodeGenome #8;
- #275 found traversal-direction defect CodeGenome #10;
- both were repaired before the current pin was trusted for matched runtime evidence.

This makes the repaired regressions mandatory qualification cases rather than historical trivia.

### EvolveAI

Repository: `MythologIQ-Labs-LLC/EvolveAI`

Current pin:

`7cd42412ceed2ab638249a1517b2a6dac46f1312`

Open blocker:

- EvolveAI #19: L3 `forget` removes the live vault entry without recording an explicit deletion/tombstone in the hash-chain ledger.

Qualification consequence:

```text
native live removal
!= reconstructable audited delete
!= complete Agent Memory forgetting
```

## Recommended comparator order

Do not execute every interesting system at once. That produces an expensive zoo and weak evidence.

Recommended order:

1. CodeGenome + Graphify for deterministic code-graph adapter portability;
2. add update/currentness and raw-evidence preservation to that same harness;
3. qualify CodeGenome broader surfaces under #293;
4. repair/re-pin EvolveAI #19, then qualify EvolveAI under #292;
5. choose one complete general-memory adapter, with Hindsight or MemOS the strongest current candidates;
6. choose Acontext or Memento-Skills when specifically pressure-testing procedural/metamemory behavior;
7. use EverOS/HyperMem only when high-order relationship capability is the actual research question.

## Research conclusion

The current external field strengthens the existing Agent Memory architecture rather than forcing a new one.

The recurring need across graph, hybrid retrieval, complete memory systems, skill files, and self-evolving skill runtimes is not one shared storage ontology. It is a shared adapter/qualification boundary for:

```text
identity
version applicability
provenance
currentness
scope
correction
residue/deletion
failure posture
maturity evidence
governed admission/consequence
```

That is the work tracked in #298.