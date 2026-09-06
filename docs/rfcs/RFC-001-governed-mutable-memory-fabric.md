# RFC-001: Governed Mutable Memory Fabric

Status: **Proposed**

## Summary

Agent Memory should be implemented as a governed memory fabric between an agent runtime and heterogeneous memory technologies, with external agent-governance systems remaining peer authorities.

Memory technologies participate as **components** that expose one or more independently described **capabilities**. Component identity and capability identity are distinct.

The long-term system boundary is:

```text
Agent Runtime
  acts, plans, invokes tools, requests memory
        |
        v
Agent Memory
  owns memory semantics, lifecycle, provenance, scope,
  structural mutability, mutation authority, recall admission,
  capability routing, and evidence
        |
        +--> configured components
        |       +--> capabilities[]
        |       +--> maturity/evidence per capability
        |
        v
Agent Governance peer(s)
  DashClaw / AGT / other approval, policy, enforcement systems
```

Agent Memory is not one graph database, RAG implementation, vector store, JEPA representation, file layout, or first-party product. Those technologies implement capabilities behind Agent Memory contracts.

## Goals

1. make memory representation and persistence configurable without changing Agent Memory doctrine;
2. allow several components and capability families to participate in one deployment simultaneously;
3. allow one component to expose many capabilities and one capability to have many candidate implementations;
4. allow routing by memory characteristics and capability requirements rather than hard-coding one technology to one retention tier;
5. treat first-party systems such as EvolveAI and CodeGenome as multi-capability candidate components, not privileged doctrine;
6. preserve external memory-system integrations under the same capability/governance boundary;
7. make structural adaptation possible without giving probabilistic systems authority over canonical memory shape;
8. keep Agent Runtime, Agent Memory, and Agent Governance as separately reasoned system boundaries;
9. distinguish configured capability claims from version-bound executable qualification evidence.

## Non-goals

- selecting one universal storage engine;
- making short-, mid-, or long-term memory synonymous with a specific backend;
- forcing each component into one exclusive module type;
- merging every first-party repository into this repository as source code;
- making DashClaw, AGT, EvolveAI, CodeGenome, Graphiti, JEPA, GraphRAG, or any other implementation mandatory;
- allowing component-specific identity, confidence, ontology, or retrieval score to become canonical Agent Memory authority;
- defining a universal physical database schema;
- treating a declared capability as runtime-available merely because documentation mentions it;
- treating a successful component invocation as Agent Memory conformance;
- carrying qualification across component/adapter/profile versions without explicit compatibility evidence.

## Architectural model

```text
                         AGENT MEMORY

  Runtime/API boundary
          |
          v
  memory classification + capability requirements
          |
          v
  PAMA / scope / lifecycle / provenance / authority
          |
          v
  canonical memory semantics + logical state
          |
          v
  deterministic component/capability resolution
          |
          v
  versioned component adapter
          |
          +-------------------------------------+
          |                  |                  |
          v                  v                  v
     component A        component B        component C
      caps [x,y]         caps [y,z]         caps [w]
          |                  |                  |
          +------------------+------------------+
                             |
                             v
               raw provider evidence + normalized result
                             |
                             v
               Agent Memory currentness/scope/lifecycle
                             |
                             v
                   governed recall/admission
                             |
                             v
                      Agent Runtime context
```

A component may implement several capabilities. A capability may be available from several components. Responsibilities, maturity, provenance, adapter identity, and qualification evidence remain typed and inspectable.

## Component/capability model

The core invariant is:

```text
component identity != capability identity
```

A component declaration identifies the deployable implementation boundary. Capability declarations identify what that component claims to provide.

A component may expose, for example:

```text
EvolveAI
  temporal_graph
  vector_candidate_retrieval
  exact_retrieval
  lifecycle_decay
  consolidation

CodeGenome
  code_graph
  graph_traversal
  impact_analysis
  embedding_storage
  vector_similarity
```

The exact capability vocabulary is defined separately in the memory-component program.

## Capability maturity model

Each capability declaration carries an independent maturity state. Current vocabulary:

```text
declared
implemented
runtime_wired
evidence_proven
reference_qualified
```

Meaning:

- `declared`: documented/intended architecture;
- `implemented`: material code exists;
- `runtime_wired`: reachable through a supported runtime/product path;
- `evidence_proven`: reproducible, version-bound qualification evidence demonstrates the claimed behavior;
- `reference_qualified`: the applicable Agent Memory qualification/conformance profile is satisfied.

A component-wide release/version must not silently imply that every capability has the same maturity.

A maturity result is scoped to the exact implementation/adapter/profile evidence that earned it. A changed component, capability, adapter, qualification profile, or materially relevant runtime configuration requires explicit compatibility evidence before the prior result can be reused.

## Capability families

Capability families are composable roles, not exclusive product classes.

### Storage and persistence

Examples: files/Markdown, SQLite/Postgres, graph database, object store, event log, content-addressed vault.

Owns physical persistence mechanics. Does not own memory authority.

### Exact retrieval

Examples: content-addressed lookup, key-addressed lookup, deterministic indexed lookup.

Exact identity retrieval is distinct from semantic similarity.

### Vector representation and retrieval

Distinguish at least:

```text
vector representation/storage
vector similarity
vector candidate retrieval
```

Embeddings or cosine similarity alone do not prove a supported vector-retrieval product path.

### Graph and GraphRAG

Distinguish at least:

```text
graph storage
graph query/traversal
graph candidate retrieval
graph-augmented context assembly / GraphRAG
```

Graph existence does not prove end-to-end GraphRAG. GraphRAG also does not cease to be a valid component capability merely because the same component implements lifecycle, code analysis, or vector retrieval.

### Procedural / skill memory

ADR-034 is Accepted. A component may retain, version, retrieve, or learn procedures/skills, but:

```text
skill retention
  != retrieval
  != recall admission / activation
  != action authority
  != execution evidence
```

A procedural-memory capability can be qualified for retention/retrieval behavior without acquiring standing authority over the actions described by the skill.

### Representation

Examples: embeddings, learned latent state, JEPA-style representations, summaries/compression.

Produces a representation or influence surface. Representation quality is not truth or authority.

### Structural/reasoning capability

Examples: code reality graphs, domain graph traversal, association engines, impact/blast-radius analysis.

May expose observed and inferred relationships with provenance/currentness. Reachability is not permission.

### Lifecycle/maintenance capability

Examples: decay, weakening, reinforcement signals, consolidation, synthesis, archive/prune candidacy.

May propose lifecycle consequences. Maintenance signals do not self-authorize durable mutation.

### Complete memory-system integration

A first- or third-party memory service may expose several capability families simultaneously. Imported state is not automatically admitted, trusted, or authorized.

## First-party integrated subsystems

EvolveAI and CodeGenome are first-party candidate components. Neither should be reduced to one exclusive module category.

At the current first-party inventory boundary:

```text
EvolveAI
  spans temporal graph, vector retrieval, exact retrieval,
  tiering, lifecycle/decay, consolidation, failure memory,
  persistence/audit, and GraphRAG-oriented design

CodeGenome
  spans graph storage/traversal, graph-derived code context,
  impact analysis, embedding storage, vector similarity,
  confidence/evidence fusion, provenance, MCP exposure,
  and experiment/evaluation
```

Capabilities are at different maturity levels. The pinned inventory is:

`docs/programs/memory-modules/first-party-capability-inventory.md`

First-party ownership changes packaging and maintenance posture, not authority semantics or maturity.

Qualification is tracked independently under #292/#293 and the common executable qualification contract under #298.

## Memory tiers are policy characteristics, not backends

The architecture MUST NOT define:

```text
short-term = Markdown
mid-term = JEPA
long-term = graph
```

Instead routing evaluates memory characteristics such as:

```text
retention horizon
scope / tenant / isolation domain
sensitivity
current lifecycle state
reversibility
retrieval pattern
relationship density
exactness requirements
latency / cost budget
availability / offline constraints
rebuild cost
provenance requirements
```

These characteristics produce **capability requirements**, not product names.

A profile may then resolve required capabilities to one or several configured components.

Illustrative profile:

```yaml
working:
  requires:
    - capability: ephemeral_storage
    - capability: lexical_retrieval

episodic:
  requires:
    - capability: event_storage
    - capability: vector_candidate_retrieval

durable_project:
  requires:
    - capability: canonical_persistence
    - capability: graph_candidate_retrieval
    - capability: exact_retrieval
```

These names are illustrative, not canonical configuration keys.

## Canonical versus derived state

Every capability instance MUST declare whether it stores or produces:

- canonical memory state;
- historical evidence;
- derived projection/index state;
- learned/latent influence state;
- cache/ephemeral state.

A single component may have different postures for different capabilities.

Derived or physical state MUST remain rebuildable or explicitly non-rebuildable. Component replacement MUST NOT silently change canonical logical identity, provenance, lifecycle, scope, or currentness.

## Structural mutability

ADR-032 governs structural adaptation.

The fabric may discover and propose new memory shapes at runtime. Structural proposals may come from learned systems, domain components, workload pressure, or deterministic maintenance observations.

Commit authority is separate:

```text
probabilistic / learned discovery
  -> structural proposal
  -> deterministic semantic + dependency + migration analysis
  -> deterministic governance classification
  -> autonomous bounded commit OR explicit human decision
```

No confidence score, embedding similarity, learned utility estimate, or model recommendation can directly authorize canonical structural mutation.

## Component declaration contract

A component installation/profile should expose at least:

```text
component_id
implementation_ref
component_version
configuration_version
deployment posture
failure / unavailable posture
dependency + license metadata
observability / evidence hooks
capabilities[]
```

Each capability declaration should expose at least:

```text
capability_id
capability_version
maturity
maturity_evidence_refs
canonical_or_derived_posture
supported scopes / isolation behavior
read / write / candidate behavior
currentness / invalidation semantics
correction / supersession behavior
deletion / residue behavior
migration / rebuild behavior
failure behavior when capability-specific
structural mutation requirements
```

PR #297 implements the first subset of this declaration surface: identity/version, independent maturity, state/scope/failure posture, evidence refs/limitations, enablement, and deterministic provider resolution. The remaining executable semantics stay owned by #280/#298.

Unsupported or incompatible configurations must fail deterministically rather than degrade into guessed behavior.

## Component adapter contract

Selection does not invoke or qualify a component by itself.

A component adapter is a versioned semantic boundary between provider-native behavior and Agent Memory. It may be implemented over a library, CLI, MCP server, process, sidecar, HTTP API, or other transport.

A versioned adapter should expose or make reconstructable equivalents of:

```text
adapter_id
adapter_version
component_id
exact component implementation ref
capability_id / capability_version
operation / invocation kind
runtime/configuration identity
input reference(s) / digest(s)
raw provider output/evidence reference(s)
normalized Agent Memory result reference(s)
currentness/freshness signal where available
scope/partition signal where available
failure/unavailable result
trace/correlation reference
```

The adapter MUST preserve enough provider-native evidence to reconstruct the normalized claim.

Normalization MUST NOT silently translate provider-specific semantics into Agent Memory authority:

```text
provider canonical != Agent Memory canonical
provider confidence != Agent Memory truth
provider PASS/BLOCK != PAMA authority
provider reachability != recall admission
provider success != capability qualification
```

## Capability qualification contract

Installation declaration and qualification are separate surfaces.

```text
installation profile
  -> what this deployment claims/configures

qualification record
  -> what exact behavior was actually proven
     for an exact component/capability/adapter/profile/runtime identity
```

The qualification applicability identity should bind equivalents of:

```text
component_id
component implementation version / exact source ref
capability_id
capability_version
adapter_id
adapter_version
qualification_profile_id
qualification_profile_version
runtime/dependency configuration identity
```

A qualification record should bind:

- exact subject/version identities;
- source-rights/license posture;
- fixture/workload identity and digest;
- runtime/dependency/model/parser configuration where material;
- operations exercised;
- raw provider evidence/artifact refs;
- normalized evidence refs;
- scope/isolation outcomes;
- currentness/invalidation outcomes;
- correction/supersession outcomes;
- deletion/residue outcomes where applicable;
- rebuild/removal outcomes where applicable;
- unavailable/failure outcomes;
- authority/admission negative paths;
- claimed and earned maturity;
- limitations/blockers;
- evidence/artifact digests.

A prior `evidence_proven` or `reference_qualified` result does not silently survive version drift. Compatibility must be explicit.

The detailed research contract is:

`docs/programs/memory-modules/component-adapter-qualification-contract.md`

## Capability resolution and routing contract

Routing itself is not authority.

A route should conceptually resolve:

```text
memory characteristics
  -> required capabilities
  -> minimum maturity + posture constraints
  -> matching configured component capability instances
  -> deterministic selection/composition
```

A router MAY use learned or heuristic signals to recommend candidate capabilities or implementations, but any routing consequence that changes canonical durability, scope, authority, lifecycle, or structural semantics must pass normal governance.

When several components provide the same capability, configuration MUST define precedence, composition, or an explicit ambiguity failure. Hidden registration order or first-match behavior is unacceptable.

Fallback MUST NOT silently lower required maturity, scope/isolation guarantees, or canonical/derived requirements.

Low-impact placement or derived-projection choices may be automatic when a versioned deterministic profile explicitly allows them.

## Agent Governance boundary

Agent governance remains a peer system, not a memory substrate.

```text
Agent Memory
  -> memory-specific proposal/verdict/context evidence
  -> governance adapter
  -> DashClaw / AGT / other governance peer
```

External governance may tighten a consequence or supply approval/enforcement evidence. It does not redefine Agent Memory semantics, and returned approval does not become reusable standing memory authority.

DashClaw #279 remains the first concrete proof of this peer boundary.

## Acceptance scenarios

### Product-shaped memory scenario

The first minimal fabric should prove a cross-session project-memory workload:

1. Agent Runtime learns a project fact.
2. Agent Memory classifies and proposes durable promotion.
3. External governance governs the consequential mutation where configured.
4. Agent Memory independently revalidates and commits through its governed mutation path.
5. A later session recalls the memory and changes behavior because of it.
6. A correction is proposed, reviewed where required, committed, and supersedes the old current value.
7. A later session uses the corrected value.
8. stale approval, scope widening, and cross-tenant recall fail.
9. evidence distinguishes decision, approval, mutation, lifecycle, and recall.
10. the report states whether process-restart durability was proven or only cross-session reuse.
11. the same behavioral contract can be rerun with a different component/capability composition.

### Component portability / qualification scenario

Before first-party capability qualification is considered complete, the fabric should also prove:

1. one generic capability requirement resolves to two materially different real providers under separate configurations;
2. each provider is invoked through its own versioned adapter;
3. raw provider outputs are preserved;
4. the same provider-neutral behavioral facts can be evaluated without erasing meaningful provider differences;
5. stale/currentness behavior is exercised after source mutation;
6. component failure/unavailability has explicit posture;
7. component or adapter version drift invalidates or requires explicit compatibility for prior qualification;
8. provider confidence/relevance/ontology never becomes Agent Memory authority;
9. qualification evidence records source-rights posture;
10. no scalar benchmark winner is mistaken for architecture.

The first selected deterministic pair is CodeGenome + Graphify under #298 because both expose local code-graph behavior without requiring an LLM/model service.

## Open design questions

- should capability composition be static per deployment, dynamically resolved per memory, or both;
- which canonical state surfaces may be shared across several writable capability implementations without introducing dual authority;
- how component migration and shadow/canary operation should work;
- which structural S1 changes deserve an autonomous PAMA envelope;
- how first-party components are packaged: libraries, processes, sidecars, or remote services;
- how restart-safe governance metadata is reconstructed independently from a physical substrate;
- which exact qualification profiles are required before a capability can be called `reference_qualified`;
- which version changes may reuse prior qualification through explicit compatibility evidence;
- when overlap between EvolveAI and CodeGenome should remain domain-specialized versus move to a shared component;
- whether any uncovered capability family justifies a new first-party subsystem after the current capability frontier.

## Relationship to current work

- #274 owns the capability-oriented memory-component program.
- #275 completed the initial adversarial first-party/external comparison and exposed real CodeGenome defects before qualification.
- #276 currently finds no need for a new universal logical-state algebra in the tested scenarios.
- #279 proves the Agent Memory <-> Agent Governance peer seam against DashClaw.
- #280 owns the full common component/capability runtime contract and routing fabric.
- #287 completed machine-readable capability declarations/maturity.
- #290 completed deterministic capability selection/overlap resolution.
- #292 qualifies EvolveAI capabilities through the common qualification contract.
- #293 qualifies CodeGenome capabilities through the common qualification contract.
- #295 / PR #297 proved governed procedural memory and supplied the first real new capability path; ADR-034 is Accepted.
- #298 defines the missing executable component adapter + version-bound qualification contract.
- #282 owns restart-safe runtime behavior and the end-to-end acceptance harness.
- ADR-032 defines structural mutation authority and schema lifecycle.
- ADR-033 defines independent capability maturity and deterministic composition.
- ADR-034 defines procedural memory as retained state, not execution authority.

## Current implementation sequence

The earlier sequence is partially complete. The next sequence is now:

1. **Completed:** capability vocabulary, machine-readable capability maturity, and deterministic overlap resolution (#287/#290/PR #297).
2. **Completed:** first governed procedural-memory capability vertical slice and Accepted ADR-034 (#295/PR #297).
3. define and implement the versioned component adapter + capability qualification record/harness (#298 -> #280);
4. prove deterministic portability with freshly pinned CodeGenome + Graphify, harvesting the useful fixture/evidence design from stale draft PR #278 rather than merging it wholesale;
5. qualify CodeGenome capability-by-capability through the common harness (#293);
6. repair/re-pin EvolveAI's current deletion-ledger blocker, then qualify EvolveAI through the same harness (#292);
7. prove the DashClaw governed durable-memory peer-governance scenario (#279) without allowing external approval to become standing memory authority;
8. make governance/currentness metadata restart-safe and rerun product acceptance across materially different component compositions (#282);
9. add one complete external general-memory adapter, with current Hindsight/MemOS/Acontext/MIRIX candidates evaluated under the same qualification contract;
10. decide whether any remaining capability gap justifies extending an existing subsystem, adopting an external implementation, extracting a shared component, or creating a new first-party subsystem.

## ADR disposition for the qualification layer

Current recommendation: `no_new_adr`.

The adapter/qualification work is an implementation and conformance specialization of accepted ADR-020, ADR-022, ADR-028, ADR-030, ADR-032, ADR-033, and ADR-034.

Create or amend canonical doctrine only if executable adapters expose a stable representation-neutral contradiction those decisions cannot express.