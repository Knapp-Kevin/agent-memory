# External Memory Capability Frontier

Status: **research conclusion for #286; executable comparator work remains separately gated by #275**

This report maps external memory-system directions against the capability vocabulary in [`capability-vocabulary.md`](capability-vocabulary.md). It is an architecture comparison, not a product ranking and not a claim that every advertised capability is Agent Memory-conformant.

## Evidence discipline

The comparison uses primary project repositories and papers, with exact repository pins where practical. External benchmark claims are treated as leads unless independently reproduced.

| System | Exact source pin used | Rights posture for this research | Material frontier |
|---|---|---|---|
| Hindsight | `vectorize-io/hindsight@2e8c221c54b1dd2f6cc003f63accf3a01a077332` | MIT; independent synthesis | facts + experiences + mental models; graph/temporal/vector/sparse hybrid recall |
| Graphiti | `getzep/graphiti@b2ff2eadd9a6b75a261a5cf0b19557883a13f752` | Apache-2.0; already registered external comparator | temporal knowledge graph, episode provenance, validity-aware graph retrieval |
| MemOS | `MemTensor/MemOS@f4db521214c29337164ec788bafede7eab236c25` | Apache-2.0; independent synthesis | multi-type memory OS, multimodal, memory cubes, scheduling, procedural skills |
| MIRIX | `Mirix-AI/MIRIX@51f3342d5366b0e215439581f92e0323227146af` | comparator only; verify exact license obligations before reuse | core/episodic/semantic/procedural/resource/vault memory; multimodal and local memory |
| EverOS / EverMind | `EverMind-AI/EverOS@f07ad99d1a7b8069944bc2984023c550a392ce5f` | comparator only; verify exact component license before reuse | self-organizing long-horizon memory, hypergraph/high-order association, benchmarks |
| Cognee | `topoteretes/cognee@4b9dd362625dfd3621c344e571a86f5bc7a55ee8` | comparator only; verify exact component license before reuse | external memory control-plane pattern, graph/vector/session memory, isolation and traceability |
| Letta | `letta-ai/letta@56ba9c25552605eec89de8ed3dc6394b625c1993` | Apache-2.0; independent synthesis | mutable in-context memory blocks, archival memory, file/git-backed memory, skills |
| Acontext | `memodb-io/Acontext@259d73bfdebeed35ec2d4211ddc060a2d4126bc6` | Apache-2.0; independent synthesis | agent skills as a memory layer, human-editable skill artifacts, skill generation |
| MemSkill | `ViktorAxelsen/MemSkill@9907c35f8cc71684d06a1f00e0b9c5c4a7b12c4c` | Apache-2.0; independent synthesis | learned **metamemory** skills controlling what/how to remember and forget |
| EvoMemBench | `DSAIL-Memory/EvoMemBench@aa4cea8fd936b76b2d3591d3ef897030617dc43a` | benchmark comparator; verify dataset-level rights separately | execution-oriented vs knowledge-oriented, in-episode vs cross-episode memory evaluation |

No implementation code or distinctive documentation prose from these systems is incorporated here.

## Major frontier finding 1: graph/vector is no longer the useful top-level taxonomy

Across Hindsight, Graphiti, MemOS, EverMind, Cognee, and the first-party systems, graph/vector/lexical are increasingly **retrieval and representation capabilities inside broader memory systems**.

The differentiating questions are becoming:

- what classes of retained state exist;
- how memory is consolidated and corrected;
- whether procedures/skills are retained as reusable assets;
- how historical validity and source evidence survive derivation;
- how context is assembled from several retrieval families;
- whether the system can alter its own memory-management strategy;
- whether multimodal and shared memory preserve the same governance invariants.

Agent Memory should therefore avoid a roadmap shaped as “build graph, then vector, then GraphRAG.” Those are important capabilities, not the complete memory product boundary.

## Major frontier finding 2: procedural/skill memory is a real missing capability family

Several materially different systems converge on procedures or skills as retained memory:

- MemOS separates task traces, environment/world understanding, and mature skills, with a skill retrieval tier at task entry;
- MIRIX explicitly names procedural memory as one of its memory types;
- Letta treats reusable skills/files as durable agent memory surfaces;
- Acontext stores reusable skill packages with human-readable instructions/scripts/resources and can generate skills from experience;
- research systems such as MUSE/SESA and execution-oriented memory benchmarks treat procedural memory as materially different from ordinary fact recall.

The implementations disagree about storage and representation. That disagreement is evidence **against** selecting one canonical skill substrate.

The stable cross-system semantic boundary is instead:

```text
retained procedure / skill
  != activation into the current plan/context
  != authority to execute the described actions
```

This maps unusually well to Agent Memory doctrine:

```text
memory != procedure
procedure != permission
permission != governance
```

That makes procedural/skill memory a strong first implementation vertical slice.

## Major frontier finding 3: metamemory is separate from procedural task memory

MemSkill explicitly learns reusable routines about **how to remember**: what to extract, where to focus, and what to preserve or forget. EvolveMem similarly exposes retrieval configuration as an evolvable action space, diagnoses failures, proposes changes, and guards changes with regression rollback.

This is not ordinary task skill memory.

```text
procedural skill
  "how to perform task X"

metamemory policy
  "how this memory system should extract / consolidate / retrieve / forget"
```

A metamemory change alters future memory formation and recall behavior. Under Agent Memory, it therefore intersects:

- ADR-020 probabilistic discovery / deterministic consequence;
- ADR-032 governed structural mutability;
- PAMA policy/maintenance authority;
- component/routing profile compatibility;
- regression and rollback evidence.

The safe architecture is:

```text
learned memory-management insight
  -> proposed metamemory/profile change
  -> deterministic compatibility + regression + authority evaluation
  -> bounded authorized configuration change OR human review
```

not:

```text
learned memory skill
  -> silently rewrite how Agent Memory remembers
```

No separate third ADR is required yet. The procedural-memory ADR can name metamemory as a stricter sub-class, while ADR-032 remains controlling for structural consequences.

## Major frontier finding 4: temporal validity and derived-state residue are broadly load-bearing

Graphiti's temporal graph, EverMind's consolidation model, Hindsight's temporal structures, and Agent Memory's existing Graphiti runtime evidence all reinforce the same lesson: historical availability, current validity, and derived projection are different claims.

Likewise, current external project discussions around deletion and consolidation drift reinforce Agent Memory's existing doctrine that:

```text
delete action != forgetting completeness
summary / graph / embedding / foresight residue must be tracked separately
```

This is not a newly missing core primitive. Agent Memory is already ahead of many implementations here. The implementation opportunity is conformance enforcement across components, not another architectural reinvention.

## Major frontier finding 5: hypergraphs are an implementation capability, not yet a new canonical semantic requirement

EverMind/HyperMem and related systems make a strong case for high-order associations when several entities/events jointly form one relation.

However, no governance counterexample found in this research requires Agent Memory's canonical logical memory model to adopt hyperedges. Higher-arity relations can currently be modeled as domain/derived structure while preserving Agent Memory identity, provenance, scope, lifecycle, and authority contracts.

Recommendation: keep hypergraph support under `graph_state` / `structural_reasoning` capability profiles until an executable scenario demonstrates a missing canonical invariant.

## Major frontier finding 6: latent/model-internal memory is important but a poor first implementation lane

Long-context latent-memory systems and prior JEPA/predictive-state research show meaningful value in model-coupled retained state. But this capability tends to require model architecture/training coupling and makes provenance, correction, deletion, and exact replay harder.

Agent Memory should support a future `latent_model_memory` capability profile, with influence bounded by the same authority/admission rules, but should not make model-coupled memory the first proof of the configurable fabric.

The first implementation needs to prove the fabric, not require training a memory model merely to demonstrate that configuration exists.

## Major frontier finding 7: multimodal memory is a real capability gap, but not one capability

MemOS, MIRIX, SimpleMem/Omni-SimpleMem and other systems increasingly treat images, screenshots, tool traces, voice, and artifacts as memory inputs.

Agent Memory should represent multimodality as independent maturity surfaces:

```text
multimodal_ingestion
multimodal_representation
multimodal_candidate_retrieval
```

The stable core rules already exist: source binding, sensitivity, scope, currentness, derived-state residue, and admission. A multimodal implementation lane is valuable later, after the component/capability registry can express it correctly.

## Major frontier finding 8: shared/federated memory is mostly an isolation problem before it is a storage problem

Memory cubes, banks, spaces, projects, users, and agents appear across external systems as ways to group or share memory.

ADR-022 already provides the stronger invariant:

```text
same agent / same store != same authorized memory domain
```

Therefore shared/federated memory should be implemented as a capability profile under explicit boundary crossing rather than introducing a second tenancy doctrine.

## Major frontier finding 9: simple baselines remain architecturally important

Current benchmark work repeatedly shows that increasingly elaborate memory machinery does not dominate every workload. Long context, entity-filtered facts, lexical retrieval, and simple explicit memories remain competitive in meaningful settings.

Agent Memory conformance should therefore require every sophisticated component to justify its value against a simple control where practical.

Examples:

```text
GraphRAG vs lexical + exact facts
vector fusion vs lexical retrieval
procedural skill vs plain documented playbook
learned routing vs deterministic profile
consolidated summary vs raw episodic evidence
```

Complexity is not a capability maturity level.

## Capability-gap classification

| Candidate gap | Research conclusion | Recommended treatment |
|---|---|---|
| procedural / skill memory | **genuine generic capability gap** | implement first as governed vertical slice; no new backend required |
| metamemory / learned memory-management policy | genuine frontier, governance-sensitive | represent as capability/proposal surface; govern through PAMA + ADR-032; defer autonomous mutation |
| multimodal memory | genuine capability family | add capability contract now; implementation after first fabric proof |
| shared/federated memory | real deployment capability | implement through ADR-022 boundary-crossing profile; no new tenancy doctrine |
| latent/predictive/model-internal memory | genuine advanced capability | optional model-coupled profile; defer first implementation |
| hypergraph/high-order association | useful representation capability | compose/adopt within graph/structural profile; no core ontology change yet |
| causal/world-model memory | insufficiently proven as a distinct canonical requirement | research/defer; distinguish causal claims from association |
| archival/cold memory | mostly lifecycle/economics/profile gap | extend component profiles; no new first-party subsystem justified yet |
| privacy/confidential substrate | deployment/security capability | compose with existing scope/sensitivity doctrine; evaluate separately |
| graph/vector/GraphRAG | existing capability families with maturity gaps | qualify EvolveAI/CodeGenome and external adapters; no new proprietary subsystem |

## First-party boundary implications

### EvolveAI

Retain the broad first-party subsystem boundary for now. Its graph/vector/exact/lifecycle capabilities are cohesive around adaptive general-purpose retained memory. The largest problems are runtime maturity gaps, not evidence that these capabilities need to be split into new repositories.

Procedural/skill memory may later integrate with EvolveAI lifecycle/consolidation, but should not initially be implemented by forcing EvolveAI's tier ontology into Agent Memory core.

### CodeGenome

Retain the code-domain subsystem boundary. Its graph/vector/provenance/impact/evaluation capabilities are cohesive around code reality and program structure. Generic vector or graph helpers should not be extracted merely because they overlap with EvolveAI; domain semantics and correctness matter more than deduplicating every data structure.

CodeGenome can later become an excellent source of procedural skill provenance for code tasks, for example binding a learned repair/release procedure to exact code/repository evidence and impact state.

## No new first-party repository is justified yet

The research does **not** satisfy the #284 gate for creating another proprietary subsystem.

Procedural memory is distinct enough to implement, but the strongest external evidence shows that it can be represented as ordinary human-readable/declarative artifacts behind Agent Memory contracts. A new database/product repository would add ownership cost before demonstrating a missing substrate.

The correct first move is to implement the governed semantic boundary in Agent Memory using a deliberately simple reference representation. If later evidence shows EvolveAI, CodeGenome, files, SQL, or external skill stores cannot satisfy the required capability, the build-new decision can be revisited with evidence rather than appetite.

## Research closure vs executable validation

This report is sufficient to close the **mapping** question in #286 and feed #284/#289. It does not close #275's executable adversarial benchmark. Source inspection is not runtime conformance, and the repository should continue being annoyingly precise about that distinction.
