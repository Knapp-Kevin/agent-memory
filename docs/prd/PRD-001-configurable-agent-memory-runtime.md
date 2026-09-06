# PRD-001: Configurable Agent Memory Runtime

Status: **Draft**

## Product intent

Build the smallest real Agent Memory runtime that proves the architecture as a governed memory system rather than a collection of schemas and adapters.

The runtime must sit between an agent runtime and configurable memory technologies while preserving Agent Memory's own authority, lifecycle, provenance, scope, recall-admission, and evidence semantics.

Memory technologies participate as **components** exposing one or more independently qualified **capabilities**.

The product boundary is:

```text
Agent Runtime
    |
    v
Agent Memory Runtime
    |
    +-- PAMA / governance
    +-- lifecycle / provenance / currentness
    +-- mutation + recall APIs
    +-- component + capability registry
    +-- capability routing / configuration
    +-- component adapter layer
    +-- capability qualification evidence
    +-- durable governance metadata
    +-- evidence / receipts
    |
    +--> memory components / substrates
    |       +--> capabilities[]
    |       +--> maturity/evidence per capability
    |
    +--> governance peer adapters
             |
             +--> DashClaw / AGT / other peers
```

## Current earned baseline

At the 2026-08-14 `main` boundary `773ab1fac8b657e03522677f20740a1d816edf34`, the product is no longer starting from a blank component model.

PR #297 earned:

- machine-readable component declarations;
- independently versioned capability declarations;
- maturity vocabulary/enforcement;
- state/scope/failure posture;
- evidence refs and limitations;
- deterministic provider resolution;
- explicit maturity shortfall failure;
- explicit ambiguity failure;
- preferred/allowed provider enforcement;
- capability routing that has no authority effect;
- a governed procedural-memory capability vertical slice;
- exact skill payload/approval binding;
- Accepted ADR-034.

This means:

```text
configured capability selection
  = real current capability

configured capability selection
  != complete component runtime contract
  != earned provider qualification
  != restart-safe Agent Memory runtime
```

The next product gap is the versioned component adapter + qualification contract under #298/#280.

## Problem

The repository already proves many architectural boundaries, but a production-shaped user story requires one coherent runtime that can:

- accept memory candidates from an agent;
- classify and govern consequential mutation;
- determine required memory capabilities from policy and workload characteristics;
- resolve those capabilities to configured components at sufficient maturity;
- invoke the selected capabilities through versioned adapters;
- preserve raw provider evidence while normalizing only the semantics Agent Memory needs;
- prove capability maturity against exact component/adapter/profile versions rather than manual labels;
- place/represent memory through one or several capabilities;
- persist enough governance metadata to survive restart;
- retrieve candidates from one or several components/capabilities;
- govern admission into later context;
- correct, supersede, delete, rebuild, and migrate state;
- interoperate with external agent-governance peers without surrendering memory semantics;
- reconstruct why later behavior changed.

Without this runtime shape, integrations risk proving provider-specific pipelines rather than proving Agent Memory.

## Primary users

### Agent/runtime developer

Needs a stable API for storing, correcting, recalling, forgetting, and using governed procedural memory without knowing which component implements each capability.

### System operator

Needs to configure components, capabilities, minimum maturity, precedence/composition, scopes, failure postures, migration/rebuild policy, governance peers, source-rights posture, and qualification requirements with deterministic validation.

### Human authority / user

Needs meaningful recommendations and impact previews for consequential structural, scope, correction, or destructive changes without being interrupted for safe low-impact maintenance.

### Component developer

Needs a bounded adapter and qualification contract for contributing one or several storage, retrieval, graph, representation, structural, lifecycle, procedural, or external-memory capabilities without acquiring Agent Memory authority.

## Core product requirements

### R1. Stable Agent Memory API

Expose bounded operations for at least:

- propose memory;
- commit governed mutation;
- correct/supersede memory;
- recall current admissible memory;
- retain/version/activate governed procedural memory;
- inspect history/provenance;
- request forgetting/deletion;
- inspect decision/receipt evidence;
- inspect configured component/capability posture;
- inspect adapter/qualification posture for a selected capability.

The API must distinguish proposal, decision, approval, commit, retrieval candidate, recall admission/activation, action authority, and execution evidence where those stages exist.

### R2. Component registry and capability discovery

The runtime must load one or more component profiles and expose:

```text
component identity + version
configuration/profile version
deployment/failure posture
capabilities[]
```

Each capability must independently declare at least:

- capability identity/version;
- maturity;
- maturity/evidence references where applicable;
- canonical/derived/historical/learned posture;
- scope/isolation behavior;
- read/write/candidate behavior;
- currentness/invalidation semantics;
- correction/deletion behavior;
- failure posture where capability-specific;
- migration/rebuild support.

The current reference declaration schema implements the identity/maturity/posture/routing subset. #298/#280 owns the remaining executable semantics.

A component must not be usable merely because it imports successfully.

### R3. Capability maturity

The runtime must distinguish at least:

```text
declared
implemented
runtime_wired
evidence_proven
reference_qualified
```

A route requiring a capability at one maturity level must reject an implementation below that level.

Component-level release/version must not implicitly promote capability maturity.

An `evidence_proven` or `reference_qualified` claim must bind the exact implementation/adapter/qualification-profile/runtime identity that earned it. Version drift requires explicit compatibility evidence or renewed qualification.

### R4. Configurable capability routing

Routing must be based on memory characteristics, capability requirements, minimum maturity, and deployment policy rather than hard-coded backend-to-tier assignments.

A memory may use several capabilities from one component or from several components.

One component may provide several capabilities. Several components may provide the same capability.

When overlap exists, deterministic configuration must define precedence, composition, or explicit ambiguity failure.

Routing is not mutation authority, recall admission, or capability qualification.

### R5. Component adapter invocation

A selected capability must be invoked through a versioned adapter boundary.

The adapter may use a library, CLI, MCP server, local process, sidecar, remote API, or another transport, but the semantic evidence must make reconstructable at least:

```text
adapter identity/version
component identity/exact implementation ref
capability identity/version
operation/invocation kind
runtime/configuration identity
input refs/digests
raw provider output/evidence refs
normalized Agent Memory result refs
currentness/scope signals where available
failure/unavailable outcome
trace/correlation ref
```

Provider-native evidence must not be discarded merely because normalization succeeded.

The adapter must not translate provider-specific identity, confidence, ontology, PASS/BLOCK, or reachability into canonical Agent Memory authority.

### R6. Capability qualification evidence

Installation declaration and qualification evidence must be separate product surfaces.

A qualification record must bind enough information to answer:

```text
what exact capability behavior was proven
by which exact component implementation
through which adapter
under which qualification profile/configuration
against which fixture/workload
with which positive and negative results
```

At minimum bind:

- component repository/package/runtime identity;
- exact commit/release/package digest;
- source-rights/license posture;
- capability identity/version;
- adapter identity/version;
- qualification profile identity/version;
- fixture/workload identity/digest;
- runtime/dependency/model/parser configuration where material;
- operations exercised;
- raw provider evidence;
- normalized evidence;
- currentness/scope/correction/deletion/rebuild/failure results as applicable;
- authority/admission negative paths;
- claimed and earned maturity;
- limitations/blockers;
- evidence/artifact digests.

The first common qualification contract is specified by #298 and `docs/programs/memory-modules/component-adapter-qualification-contract.md`.

### R7. Canonical state authority

The runtime must have an explicit owner for canonical logical memory state and governance metadata.

No derived index, graph projection, embedding store, remote component, adapter, or provider-native “canonical” claim may become Agent Memory canonical state by accident.

Overlapping writable capabilities must not create dual authority.

### R8. Governed structural mutability

Implement ADR-032.

The system may receive structural proposals from learned or deterministic components. The commit path must classify the change using deterministic policy and either:

- autonomously commit a bounded S0/S1 change only when current executable policy explicitly permits it; or
- require explicit authorized human decision for S2/S3 changes.

Current PAMA 1.2 remains conservatively review-first for `domain_schema_mutation` until #281 earns any narrower autonomous envelope.

Probabilistic estimates may not be the structural commit authority.

### R9. Durable governance metadata

Process restart must not reset state required to enforce currentness, scope, supersession, rejection, authority, lifecycle, component interpretation, or qualification applicability rules.

At minimum, restart-safe state must reconstruct whichever implementation-specific equivalents are required for:

- memory logical identity/current version;
- current/superseded mapping;
- state/version counters or equivalent concurrency identity;
- scope/isolation bindings;
- rejection/readmission state;
- tombstone/deletion obligations;
- schema/component/capability/profile versions affecting interpretation;
- selected capability implementations where needed for reconstruction;
- adapter/qualification applicability where relied on at runtime;
- outstanding migration/rebuild obligations;
- receipt/provenance linkage sufficient for reconstruction.

### R10. Governed recall and procedural activation

Component retrieval returns candidates, not admitted context.

Recall admission must re-check currentness, scope/isolation, lifecycle, sensitivity/purpose policy, and relevant authority/context constraints before memory can influence the agent.

The system must preserve which component/capability/adapter produced each candidate.

For procedural memory, Accepted ADR-034 additionally requires:

```text
retention
  != retrieval
  != recall admission / activation
  != action authority
  != execution evidence
```

A provider that returns an executable skill does not grant standing execution authority.

### R11. External governance peer adapters

The runtime must support optional peer governance adapters without placing consumer-specific policy vocabulary into canonical core.

DashClaw is the first required proof under #279.

External governance may tighten or supply bounded approval/enforcement evidence. It does not become standing reusable memory authority.

### R12. Correction and supersession

A correction must preserve historical reconstruction while removing superseded state from current admission.

Affected derived capabilities must be invalidated, rebuilt, or explicitly marked stale according to their contract.

A component that continues to return stale pre-correction state must not remain qualified as current-state evidence merely because retrieval still succeeds.

### R13. Deletion and residue

Successful deletion from one component/capability must not imply lifecycle completion. The runtime must track declared derived/component residue and report incomplete forgetting honestly.

Qualification must distinguish:

```text
provider local removal
provider audited deletion
Agent Memory logical suppression/tombstone
transitive residue satisfaction
complete forgetting claim
```

These are not interchangeable.

### R14. Observability and evidence

For a consequential memory path, an operator must be able to reconstruct:

```text
runtime request
memory proposal
required capability set
component/capability resolution
component + capability + adapter version
qualification evidence/currentness
raw provider result reference
normalized result reference
PAMA decision
external governance decision/approval where applicable
commit/refusal
component consequences
current state
later recall candidates + producing capabilities
recall admission/activation
agent-visible memory reference
action governance/execution evidence where applicable
```

### R15. Deterministic configuration validation

Unsupported component combinations, capability/version mismatches, maturity shortfalls, stale qualification, ambiguous canonical ownership, unsafe writable duplication, undefined overlap precedence, unavailable required dependencies, or disallowed source-rights posture must fail explicitly.

Fallback must not silently reduce maturity, scope/isolation, canonical/derived posture, qualification requirements, or governance requirements.

## Capability vocabulary requirements

The runtime must not collapse related capabilities merely because they use the same technology family.

At minimum the model must distinguish concepts such as:

```text
graph storage
graph query/traversal
graph candidate retrieval
graph-augmented context assembly / GraphRAG

vector representation/storage
vector similarity
vector candidate retrieval

exact/content-addressed retrieval
procedural/skill memory
context assembly
lifecycle maintenance
structural reasoning
```

The memory-component program contains the representation-neutral vocabulary.

## First-party component posture

### EvolveAI

EvolveAI is a multi-capability candidate component, not merely a lifecycle module.

Current qualification planning pin:

`MythologIQ-Labs-LLC/EvolveAI@7cd42412ceed2ab638249a1517b2a6dac46f1312`

The inventory identifies graph, vector, exact-retrieval, tiering, lifecycle, consolidation, failure-memory, persistence/audit, and GraphRAG-oriented capability surfaces at different maturity levels.

Open EvolveAI #19 is a material qualification blocker for strong deletion/audit claims: current L3 `forget` removes the live vault entry without recording an explicit delete/tombstone operation in the hash-chain ledger.

Until repaired and re-qualified:

- live L3 removal is not reconstructable audited deletion;
- deletion/audit/persistence claims must carry the limitation;
- relevant capabilities must not be `reference_qualified` from the current path;
- even a repaired native delete remains distinct from Agent Memory transitive forgetting completeness.

Documented GraphRAG design and graph/vector implementation must not be misreported as already reference-qualified end-to-end GraphRAG.

### CodeGenome

CodeGenome is a multi-capability candidate component, not merely a graph module.

Current qualification planning pin:

`MythologIQ-Labs-LLC/CodeGenome@d2578729a46d495369bd7613845002d50cf20f4c`

This revision includes the #275 repairs for:

- file-bound target identity (#8 / PR #9);
- traversal direction semantics (#10 / PR #11).

Those regressions are mandatory qualification cases.

The inventory identifies graph traversal, graph-derived context, impact analysis, embeddings, vector similarity, confidence/evidence fusion, provenance, multi-language extraction, MCP, and self-evaluation surfaces at different maturity levels.

Its embedding/k-nearest implementation must not be misreported as a fully integrated general vector-retrieval product path until the common adapter invokes a supported runtime path and evidence proves it.

CodeGenome's code-domain graph identity/ontology remains implementation/domain state, not canonical Agent Memory ontology.

## External component posture

External systems are valuable when they pressure the common contract rather than donate their ontology to core.

The current fast-moving refresh is:

`docs/programs/memory-modules/external-capability-frontier-refresh-2026-08-14.md`

Immediate dispositions:

- Graphify: first deterministic external code-graph adapter/comparator candidate; current active license Apache-2.0;
- GitNexus: rich behavioral/source comparator but PolyForm Noncommercial 1.0.0, so no commercial runtime dependency absent separate rights;
- Hindsight: strong complete-memory-system adapter candidate;
- MemOS: strong complete-system plus procedural/metamemory pressure candidate;
- Acontext: file/skill-memory adapter candidate;
- MIRIX: pure memory-system adapter candidate;
- Memento-Skills: ADR-034 self-evolving procedural-memory comparator;
- EverOS/HyperMem: later high-order relationship/benchmark candidate.

Every executable run must refresh exact source/version/license posture first.

## Minimal v0 deployment profile

The first runtime does not need glamorous infrastructure. It needs falsifiable behavior.

```text
Agent Runtime fixture
    |
Agent Memory runtime
    |
    +-- existing PAMA
    +-- existing GovernedMemoryAdapter semantics
    +-- durable governance metadata implementation
    +-- component/capability registry
    +-- deterministic capability resolution
    +-- component adapter layer
    +-- qualification evidence registry
    +-- simple explicit/file or local canonical capability
    +-- optional derived component capability
    +-- governed recall
    +-- DashClaw external-verdict adapter
```

A model is optional. Core acceptance must not require stochastic model behavior to pass.

## Canonical acceptance workload

Use the release-branch project-memory scenario established under #279:

1. Session A learns `release_branch = release`.
2. Agent Memory promotes it through governance and commits it.
3. Session B starts without Session A conversation state, recalls the memory, and forms a plan targeting `release`.
4. New authoritative evidence changes the value to `main`.
5. Agent Memory proposes a correction; external governance records/returns bounded approval where policy requires it.
6. Agent Memory revalidates current state and commits the correction as supersession.
7. Session C recalls only `main` as current and forms the corrected plan.
8. stale approval replay fails.
9. scope/authority expansion fails.
10. a foreign tenant/project cannot admit the memory.
11. restart occurs; current state, governance metadata, qualification applicability, and recall behavior remain correct.

## Capability adapter / qualification workload

Before first-party qualification is treated as product evidence, run a provider-neutral portability workload.

First selected pair:

```text
CodeGenome
Graphify
```

Reason: both expose deterministic local code-graph behavior, allowing the contract to be tested without LLM/API variability.

The workload must prove:

1. same generic capability requirement resolves to each provider under separate profiles;
2. exact provider/component and adapter versions are recorded;
3. raw provider output remains preserved;
4. provider-neutral facts are evaluated without erasing meaningful provider differences;
5. CodeGenome file-identity and direction regressions remain covered;
6. initial graph facts are correct;
7. source is mutated/corrected;
8. each supported update/rebuild path removes or marks stale obsolete structure;
9. currentness is recomputed rather than inferred from successful retrieval;
10. component unavailable/failure posture is explicit;
11. provider confidence/relevance/ontology never becomes authority;
12. source-rights/license posture is part of the qualification record;
13. component/adapter/profile version drift invalidates or explicitly revalidates prior qualification.

Draft PR #278 is prior design/evidence input for this workload, not a branch to merge wholesale.

## Capability-composition conformance workload

Once the v0 runtime passes, rerun the same behavioral workload while changing component/capability composition.

Examples:

- replace graph implementation while retaining the same graph-candidate contract;
- add/remove vector retrieval;
- add a JEPA-style representation capability;
- use EvolveAI for temporal graph + lifecycle in one profile;
- use EvolveAI for vector + graph capabilities only when earned maturity permits it;
- use CodeGenome graph traversal plus vector-neighbor capability for a code-domain fixture only when separately qualified;
- use different components for graph and vector capabilities;
- wrap an external complete memory system exposing several capabilities;
- use a procedural-memory provider while preserving ADR-034 action-authority separation.

The acceptance behavior must remain invariant where the changed capability implementation does not legitimately alter semantics.

The suite must include overlap cases:

- two configured implementations satisfy the same capability with explicit precedence;
- two configured implementations satisfy the same capability without precedence and fail deterministically;
- a capability below required maturity is rejected;
- stale qualification is rejected;
- fallback cannot silently select a weaker capability posture.

## Structural-mutation UX requirements

For S2/S3 proposals, present a human decision package containing:

- recommendation;
- why the change was proposed;
- exact semantic diff;
- affected memory/scope count;
- dependent components/capabilities/consumers;
- migration and information-loss analysis;
- authority/isolation impact;
- rollback boundary;
- residue/rebuild requirements.

For any future policy-authorized autonomous S0/S1 change, record the same class of evidence in a machine-readable receipt without forcing human interruption.

Current PAMA 1.2 remains review-first until #281 changes the executable envelope with evidence.

## Success metrics

Hard gates:

- zero unauthorized canonical mutations in adversarial cases;
- zero cross-tenant admitted-memory leaks;
- zero stale-decision commits;
- zero probabilistic structural self-authorization;
- zero silent capability-maturity downgrades;
- zero stale qualification reuse across unverified version drift;
- zero accidental provider selection under ambiguous overlap;
- zero provider-native output promoted to authority merely by adapter normalization;
- process restart preserves governance-currentness behavior;
- corrections supersede rather than silently overwrite history;
- component/capability replacement does not change logical identity without an explicit migration;
- decision/activation/action/execution evidence remains distinguishable;
- license/source-rights posture is known for every materially executed external component.

Optimization metrics after hard gates:

- recall latency;
- mutation latency;
- capability resolution latency;
- adapter invocation overhead;
- qualification execution cost;
- component rebuild cost;
- operator interruption rate;
- storage overhead of governance metadata;
- migration time;
- component failure recovery time.

## Out of scope for v0

- universal hosted multi-tenant control plane;
- training a new foundation model;
- selecting one canonical graph/vector/latent technology;
- automatic S2/S3 structural migration;
- making EvolveAI or CodeGenome mandatory;
- creating new proprietary memory repositories merely to own the adapter layer;
- AGT/ACS as the first governance integration target;
- treating a benchmark winner as architecture;
- copying noncommercial comparator implementation material into Agent Memory.

## Release gates and current status

### Gate A: architecture + declaration contract

Status: **Partially earned / substantially advanced**

Earned:

- RFC-001 architecture defined;
- ADR-032 integrated;
- ADR-033 Accepted;
- ADR-034 Accepted;
- component/capability declaration schema exists;
- capability maturity model executable;
- deterministic overlap resolution executable;
- canonical ownership rules explicit.

Remaining:

- adapter + qualification contract implementation under #298/#280.

### Gate B: minimal runtime

Status: **Partial**

Earned slices:

- governed mutation/recall reference paths;
- procedural-memory vertical slice;
- deterministic capability resolution.

Remaining:

- one coherent runtime assembly;
- persistent canonical/governance state;
- component adapter layer;
- qualification evidence registry;
- restart-safe interpretation.

### Gate C: governance peer proof

Status: **Open**

- #279 DashClaw v1 external-verdict integration passes the real memory workload;
- decision/approval/commit evidence remains distinct.

### Gate D: restart and correction proof

Status: **Open**

Owned by #282:

- restart-safe currentness;
- correction/supersession across restart;
- stale replay refusal;
- component/capability/adapter/profile interpretation survives or fails safe after restart.

### Gate E: capability portability + qualification proof

Status: **Next implementation gate**

Requires:

- #298 adapter/qualification contract implemented;
- at least two materially different real providers satisfy the same generic qualification profile where appropriate;
- raw provider evidence preserved;
- overlap resolution deterministic;
- maturity/qualification gating enforced;
- currentness/update behavior proven;
- removal/rebuild and failure posture proven;
- version drift does not inherit qualification silently;
- source-rights posture recorded.

First deterministic pair: CodeGenome + freshly pinned Graphify.

### Gate F: first-party qualification

Status: **Open, gated by Gate E**

- #293 CodeGenome profile advertises capabilities independently by earned maturity and preserves #8/#10 regressions;
- #292 EvolveAI profile advertises capabilities independently by earned maturity;
- EvolveAI #19 repaired before strong deletion/audit/persistence qualification;
- graph/vector/GraphRAG claims match actual runtime evidence;
- first-party ownership grants no authority or conformance shortcut.

### Gate G: complete external memory-system portability

Status: **Future after deterministic adapter proof**

At least one complete external memory system should be qualified behind the same adapter/evidence contract without importing its ontology into core.

Current strongest candidates: Hindsight or MemOS; Acontext/Memento-Skills are strong targeted procedural-memory alternatives.

## Dependencies

Active/current:

- #274 capability-oriented memory-component program;
- #276 logical-state conclusion (`no_new_algebra` remains current for tested scenarios);
- #279 DashClaw provider integration;
- #280 component/capability runtime contract and routing fabric;
- #281 structural-mutation classification/schema lifecycle;
- #282 restart-safe runtime and acceptance harness;
- #292 EvolveAI qualification;
- #293 CodeGenome qualification;
- #298 executable adapter + capability qualification contract.

Completed inputs:

- #275 initial first-party/external adversarial comparison;
- #287 capability maturity declarations;
- #290 capability-based overlap resolution;
- #295 governed procedural-memory vertical slice.

Controlling doctrine:

- ADR-020 governed uncertainty;
- ADR-022 isolation domains;
- ADR-028 implementation portability;
- ADR-030 compatible/current projections;
- ADR-032 governed mutable memory structure;
- ADR-033 independent capability maturity and deterministic composition;
- ADR-034 procedural memory is retained state, not execution authority.