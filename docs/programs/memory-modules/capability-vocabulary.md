# Memory Capability Vocabulary

Status: **research conclusion / implementation vocabulary candidate**

Issues: #274, #284, #286, #287, #290, #291, #343

## Purpose

Agent Memory needs vocabulary precise enough to describe heterogeneous memory systems without turning product branding into architecture.

The same component may expose several capabilities, and several components may expose the same capability at different maturity levels. Therefore capability names describe **observable memory functions**, not repositories, products, storage engines, or authority.

```text
component identity != capability identity
capability presence != capability maturity
candidate retrieval != recall admission
memory representation != memory truth
memory procedure != execution permission
behavioral compatibility != operational compatibility
operational quality != authority
```

## Capability maturity

The maturity vocabulary remains:

```text
declared
implemented
runtime_wired
evidence_proven
reference_qualified
```

Maturity attaches to one capability on one exact component/version/profile. It is not inherited from a repository-wide release number.

## Capability families

### Retained-content capabilities

These describe what kind of retained state a component can materially represent.

| Capability | Definition | Important boundary |
|---|---|---|
| `transient_memory` | Retained state expected to be short-lived or cheaply disposable. | Transience is lifecycle posture, not a storage technology. |
| `episodic_event_memory` | Event/interaction traces preserving time, sequence, source, or episode context. | An event may be historically true without remaining current guidance. |
| `semantic_fact_memory` | Retained declarative facts, assertions, concepts, or stable summaries. | Consolidated meaning remains derived from evidence unless independently established. |
| `epistemic_belief_memory` | Retained claims, beliefs, hypotheses, confidence, supporting/contradicting evidence, and revision state. | Belief remains distinct from fact, observed history, and authority even when confidence is high. |
| `predictive_counterfactual_memory` | Retained predictions, simulations, expected outcomes, counterfactual trajectories, and later outcome comparisons. | Predicted or simulated history must not become observed history by storage accident. |
| `procedural_skill_memory` | Retained reusable procedures, skills, playbooks, strategies, or action guidance. | Retention/retrieval is not activation or execution authority. |
| `resource_artifact_memory` | Retained files, documents, media, tool outputs, templates, or other reusable artifacts. | Artifact availability does not imply admissibility or execution permission. |
| `negative_failure_memory` | Retained failures, anti-patterns, rejected paths, hazards, or negative precedents. | Similarity to a failure is risk evidence, not an autonomous block/allow verdict. |
| `policy_memory` | Retained policy or policy-like state whose currentness materially affects permitted behavior. | Governed separately by high-authority policy-memory doctrine. |
| `metamemory_policy` | Retained/evolved procedures for how future memory should be extracted, consolidated, routed, retrieved, ranked, pruned, or forgotten. | This changes the memory system's future behavior and is not ordinary procedural memory authority. |

`epistemic_belief_memory` exists because a belief or hypothesis needs revision and contradiction semantics without being laundered into `semantic_fact_memory`. `predictive_counterfactual_memory` exists because simulated or expected trajectories need later comparison with outcomes while retaining an explicit boundary from observation.

`metamemory_policy` is intentionally named as a capability surface rather than a new authority class. MemSkill-style memory skills and EvolveMem-style retrieval evolution demonstrate that memory systems can learn *how to remember* independently from what they remember. Under Agent Memory, those learned outputs remain proposals to a governed configuration/maintenance path.

### Exact and lexical retrieval capabilities

| Capability | Definition |
|---|---|
| `exact_identity_retrieval` | Retrieve by stable exact identifier, content reference, address, or equivalent deterministic key. |
| `lexical_candidate_retrieval` | Produce candidates using lexical/sparse/BM25/FTS-style matching. |

Exact identity does not prove currentness or authority. Lexical relevance does not prove admission.

### Vector capabilities

The vector family is deliberately split:

```text
vector_representation
    !=
vector_similarity
    !=
vector_candidate_retrieval
```

| Capability | Definition |
|---|---|
| `vector_representation` | Produce, persist, or bind vector/embedding representations to retained state or queries. |
| `vector_similarity` | Compute a similarity/distance relation between vector representations. |
| `vector_candidate_retrieval` | Use vector similarity as an operational candidate-generation path over retained state. |

A component may implement vector storage and cosine similarity without exposing a supported end-to-end retrieval path. An embedding existing in a database is not sufficient evidence for `vector_candidate_retrieval` maturity.

### Graph capabilities

The graph family is also split:

```text
graph_state
    !=
graph_query
    !=
graph_traversal
    !=
graph_candidate_retrieval
    !=
graph_augmented_context_assembly
```

| Capability | Definition |
|---|---|
| `graph_state` | Persist or materialize nodes/edges/hyperedges/relationships as graph-structured state. |
| `graph_query` | Execute explicit graph-pattern/property/path queries over graph state. |
| `graph_traversal` | Navigate relationships from one or more starting points according to graph topology. |
| `graph_candidate_retrieval` | Use graph structure/traversal to produce memory candidates for downstream use. |
| `graph_augmented_context_assembly` | Compose agent context using graph-derived candidates/relationships plus any additional retrieval or ranking mechanism. This is the capability family referred to here as **GraphRAG**. |

A graph database alone is not GraphRAG. Graph traversal exposed to an agent is not automatically GraphRAG. GraphRAG requires an operational graph-augmented retrieval/context-assembly consequence.

Hypergraphs and high-order association models fit inside these graph/structural capabilities unless evidence demonstrates a governance invariant that ordinary relationship models cannot express.

### Temporal and historical capabilities

| Capability | Definition |
|---|---|
| `temporal_validity_state` | Represent validity intervals, event time, transaction time, supersession time, or equivalent temporal state. |
| `historical_query` | Query state as-of or across historical time/versions. |
| `temporal_candidate_retrieval` | Use temporal relationships/currentness as part of candidate generation. |

Historical availability never bypasses Agent Memory currentness/admission rules.

### Structural and causal capabilities

| Capability | Definition |
|---|---|
| `structural_reasoning` | Produce relationship-, dependency-, topology-, or domain-structure-derived conclusions/candidates. |
| `impact_propagation` | Estimate downstream/upstream/blast-radius consequences through retained structural state. |
| `causal_model_memory` | Represent explicit causal/intervention hypotheses or models distinct from ordinary association. |

`causal_model_memory` remains a frontier capability. Current graph relationship systems should not be relabeled causal merely because edges imply dependency or sequence.

### Context-composition capabilities

| Capability | Definition |
|---|---|
| `hybrid_candidate_fusion` | Combine candidate sets from distinct retrieval methods while preserving per-source/component provenance. |
| `candidate_reranking` | Reorder candidates using an additional estimator or rule. |
| `context_assembly` | Construct the candidate context package presented to Agent Memory recall admission or directly to an authorized consumer profile. |
| `context_resident_memory` | Keep mutable retained state directly in an agent's active/system context across interactions. |

Fusion and reranking remain epistemic/relevance operations. They do not grant recall permission.

### Lifecycle and self-organization capabilities

| Capability | Definition |
|---|---|
| `decay_weakening` | Reduce retention/retrieval influence based on time, use, policy, or other bounded signals. |
| `reinforcement_strengthening` | Increase retention/retrieval influence based on bounded evidence/signals. |
| `consolidation_synthesis` | Derive higher-level retained state from lower-level events/memories. |
| `pruning_archival` | Propose or perform governed movement/removal from active retention tiers. |
| `self_organization` | Reorganize derived memory structure or placement in response to workload/state. |
| `retrieval_policy_evolution` | Propose/evaluate changes to retrieval configuration or strategy from observed performance. |

These capabilities may generate recommendations or maintenance proposals. They do not acquire PAMA authority from optimization quality.

### Model-coupled / latent capabilities

| Capability | Definition |
|---|---|
| `latent_model_memory` | Persistent or reusable learned/model-internal state that influences later behavior without being ordinary explicit records. |
| `long_context_memory_mechanism` | Architecture-level model/context mechanism for retaining or attending over very long histories. |

These are optional model-coupled capabilities. They remain subject to Agent Memory influence/admission and provenance boundaries wherever their effects cross into governed memory consequences. Model weight or KV state is not automatically canonical Agent Memory state.

### Scope and sharing capabilities

| Capability | Definition |
|---|---|
| `shared_memory_space` | Expose retained memory to multiple agents/users/projects under explicit membership and scope semantics. |
| `federated_memory_exchange` | Exchange memory across independent stores/domains without requiring one physical store. |

These capabilities are constrained by ADR-022 isolation and governed boundary crossing. Shared availability is not shared authority.

### Multimodal capabilities

| Capability | Definition |
|---|---|
| `multimodal_ingestion` | Ingest non-text modalities while retaining source/provenance bindings. |
| `multimodal_representation` | Maintain modality-specific or cross-modal derived representations. |
| `multimodal_candidate_retrieval` | Retrieve candidates across or within modalities. |

Multimodal support is not one yes/no capability because ingestion, representation, and retrieval may mature independently.

## Capability Contract v3: behavior and operation remain separate

`component-capability-v2` made lifecycle behavior explicit. `component-capability-v3` preserves that contract and adds a separate substrate operational contract.

```text
behavior_contract
  operation support
  currentness
  invalidation
  correction
  deletion
  residue
  migration / rebuild
  structural mutation requirement

!=

operational_contract
  write atomicity
  concurrency control
  idempotency
  restart recovery
  reconciliation
```

This distinction is required for replaceability. Two providers can both expose `graph_state`, `epistemic_belief_memory`, or another identical capability while having materially different transaction, replay, and recovery guarantees.

A v3 provider therefore declares both contracts. A routing requirement may constrain operational properties in addition to capability identity, maturity, state/scope posture, and behavior. If a provider cannot satisfy the required operational posture, it is ineligible even when it exposes the requested capability.

An explicitly preferred provider that is operationally ineligible fails resolution. Agent Memory does not silently fall back merely to make a configuration appear successful. Equally qualified providers remain ambiguous unless an explicit preference resolves the choice.

Operational quality remains non-authoritative:

```text
atomic write != permission
idempotent replay != permission
restart recovery != correctness
reconciliation != lifecycle completion
provider selection != PAMA authority
```

Persistent state is not sufficient evidence that governance-critical interpretation survived reconstruction. Likewise, successful readback or reconciliation is evidence about substrate behavior, not proof that a memory consequence was authorized or that its lifecycle completed correctly.

### Operational contract vocabulary

| Dimension | Values | Meaning |
|---|---|---|
| `write_atomicity` | `none`, `process_local`, `single_record_atomic`, `transactional_multi_record` | What atomic write boundary the provider can establish. |
| `concurrency_control` | `none`, `process_local`, `optimistic_revision`, `pessimistic_lock`, `serializable` | How conflicting concurrent mutations are detected or ordered. |
| `idempotency` | `none`, `process_local`, `durable_keyed` | Whether repeated operations can be recognized safely across the relevant persistence boundary. |
| `restart_recovery` | `none`, `process_local_only`, `reconstructable`, `checkpoint_replay` | Whether governance-relevant runtime state can be reconstructed after process loss. |
| `reconciliation` | `none`, `process_local_only`, `deterministic_readback`, `authoritative_rebuild` | Whether persisted/materialized state can be independently checked and repaired against its authority/source basis. |

A process-local-only provider cannot satisfy a requirement for durable restart reconstruction or independent reconciliation simply because its in-process tests are tidy. Processes, regrettably, do eventually stop.

### Operational/evidence capabilities

These help qualify components but are not themselves memory authority:

| Capability | Definition |
|---|---|
| `durable_persistence` | Persist claimed state across process/runtime restart. |
| `incremental_update` | Update materialized/derived state without full rebuild. |
| `rebuild_projection` | Reconstruct derived state from canonical/source state. |
| `provenance_binding` | Bind retained/derived state to source/evidence identities. |
| `evaluation_harness` | Execute repeatable quality/fitness experiments against a component or memory strategy. |
| `agent_protocol_exposure` | Expose component operations through MCP or equivalent agent-facing protocol. |

These capability names remain useful for describing supplied functions. The v3 `operational_contract` is different: it describes execution guarantees that may make a provider eligible or ineligible for a requested capability operation.

## Core responsibilities that are not delegated capabilities

The following remain Agent Memory responsibilities even if a component supplies useful evidence or machinery:

```text
logical memory identity/currentness
scope and isolation authority
PAMA mutation authority
canonical vs derived classification
correction/supersession obligations
deletion/forgetting completeness
recall admission
structural mutation authority
component/capability compatibility validation
consequential routing authority
receipt/provenance reconstruction requirements
```

A component may help implement these responsibilities. Installing the component does not transfer the responsibility.

## Cross-capability composition

One memory operation may legitimately use several capabilities:

```text
source episode
  -> episodic_event_memory
  -> consolidation_synthesis
  -> semantic_fact_memory + epistemic_belief_memory + procedural_skill_memory
  -> vector_representation
  -> graph_state
  -> lexical/vector/graph candidate retrieval
  -> hybrid_candidate_fusion
  -> Agent Memory recall admission
```

Predictive/counterfactual state may participate in planning or comparison, but it remains explicitly typed as predictive/counterfactual until later evidence records an observed outcome.

Each stage must retain enough provenance/currentness information that stale, superseded, foreign-scope, deleted, hypothetical, or predicted source state cannot be laundered through a later representation.

## Implications for current first-party systems

### EvolveAI

EvolveAI spans transient memory, temporal graph state, vector representation/retrieval, exact retrieval, tier routing, decay, lifecycle/consolidation, negative memory, persistence, and audit surfaces at differing maturity. Its differentiation in memory metabolism does not make the other capabilities disappear.

### CodeGenome

CodeGenome spans code-domain graph state/query/traversal, structural reasoning, impact propagation, vector representation/similarity, provenance, freshness, MCP exposure, and evaluation at differing maturity. Its code-reality differentiation does not make it a generic canonical graph ontology.

## Research implication

Future comparisons should score **capability behavior, operational posture, and maturity**, not whole products. A system can outperform another in vector candidate retrieval while underperforming it in lifecycle correction, restart recovery, idempotency, or procedural memory. A single product leaderboard erases exactly the architectural information this program needs.

External providers should be qualified against this contract in later adaptor slices. No external SDK is required to prove v3 itself.
