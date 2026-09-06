# Component Architecture

## Purpose

This document defines Agent Memory as a larger system composed of bounded components.

The doctrine should not collapse every concept into one mega-concept. That would make the architecture sound unified while making implementation worse. A real system needs a shared spine and segmented responsibilities.

Component boundaries must also preserve the difference between uncertain inference and governed consequence. A probabilistic output crossing a component boundary must not quietly become authority because the receiving component forgot what kind of signal it was.

## Core decision

Agent Memory is one overall architecture made of multiple governed components.

It is not one monolithic product, library, database, score, graph, vault, protocol, or model.

PAMA is a native governance component of this architecture, not an external product dependency.

## Proposed cognitive-framework extension

> **Status:** Proposed by [ADR-035](adr/ADR-035-agent-memory-is-a-governed-cognitive-framework.md). This section describes the candidate system topology. Existing Accepted ADR boundaries remain controlling until ADR-035 satisfies its acceptance requirements.

ADR-035 proposes making explicit what the existing component architecture only implies: the bounded components participate in one persistent cognitive system rather than merely surrounding a collection of memory providers.

The proposed top-level architecture is:

```text
Agent Memory
|
+-- Cognitive Plane
|   +-- Cognitive Mesh
|   +-- Working Memory & Attention
|   +-- Cognitive Metabolism
|   +-- Consolidation & Abstraction
|   +-- Procedural Memory & Skills
|   +-- Predictive / World Modeling
|   +-- Metacognitive Signals
|
+-- Reality Plane
|   +-- Reality Graphs
|       +-- Code Reality Graph
|       +-- Environment Reality Graph
|       +-- Task Reality Graph
|       +-- Social Reality Graph
|       +-- Organizational Reality Graph
|
+-- Authority Plane
    +-- PAMA
    +-- Governed Recall Admission
    +-- Certification & Durable Commit
    +-- Scope / Privacy / Isolation
    +-- Correction / Supersession
    +-- Deletion / Forgetting Authority
    +-- Inheritance / Multi-Agent Crossing

Cross-cutting:
  Identity & Continuity
  Evidence & Provenance
  Conformance / Calibration / Evaluation
```

The planes are logical responsibility groupings, not exclusive component categories or deployment boundaries.

ADR-033 remains controlling for composition:

```text
module identity != component identity
component identity != capability identity

one component -> many capabilities
one capability -> many candidate implementations
```

Under the proposed mapping:

- **EvolveAI** is the initial first-party reference/research implementation for **Cognitive Metabolism**, while its retrieval, graph, persistence, provenance, and other capabilities continue to mature independently;
- **CodeGenome** is the initial first-party implementation of the **Code Reality Graph**, while its graph, retrieval, structural-reasoning, provenance, freshness, and evaluation capabilities continue to mature independently;
- **Agent Memory core** owns the Cognitive Mesh contract, cross-module semantics, governance boundaries, and conformance requirements rather than adopting either implementation's internal ontology as canonical doctrine.

This mapping is architectural responsibility, not capability promotion. First-party ownership does not confer `reference_qualified` maturity.

### Proposed Cognitive Mesh

The Cognitive Mesh is the candidate shared substrate through which persistent cognitive objects and typed relationships can participate in multiple bounded modules without losing their semantic type, provenance, uncertainty, scope, lifecycle, or authority posture.

Candidate object classes include:

```text
Experience
Observation
Episode
Concept
Fact
Preference
Relationship
Procedure
Skill
Goal
Task
Prediction
Failure
Decision
Policy
Person
CodeArtifact
EnvironmentState
Correction
Evidence
DerivedState
```

Candidate typed relationships include:

```text
supports
contradicts
derived_from
supersedes
associated_with
caused_by
part_of
depends_on
predicts
performed_by
applies_to
learned_from
similar_to
evidenced_by
invalidates
```

The mesh must not collapse unlike semantics:

```text
common mesh != common behavior
relationship != truth
activation != authority
confidence != permission
persistence != correctness
```

### Proposed module responsibilities

| Module | Candidate responsibility | Initial implementation / source | Must not silently own |
|---|---|---|---|
| Cognitive Mesh | Shared cognitive identity and typed relation substrate | Agent Memory core contract/reference substrate | universal truth, mutation authority |
| Cognitive Metabolism | salience, decay, reinforcement, persistence pressure, consolidation candidacy, adaptive restructuring proposals | EvolveAI | truth, deletion authority, crystallization authority |
| Working Memory & Attention | active admitted cognitive state | Agent Memory reference implementation | bypass of recall admission |
| Consolidation & Abstraction | candidate semantic/procedural/generalized structures | Agent Memory contract + qualified provider mechanisms | canonicality from repetition alone |
| Predictive / World Modeling | expectations about future or latent state | pluggable; no canonical implementation yet | factual truth or action authority |
| Procedural Memory & Skills | retained reusable procedures | Agent Memory procedural-memory profile | execution permission |
| Reality Graphs | domain-specific external/operational reality | pluggable domain implementations | memory permanence or downstream authority |
| Code Reality Graph | code-domain identity, structure, evidence, freshness, impact | CodeGenome | universal Cognitive Mesh ontology |
| PAMA | mutation/consequence authority | Agent Memory native doctrine | factual truth |
| Conformance / Evaluation | module and composition evidence | Agent Memory | product claims without evidence |

## Current accepted system shape

Until ADR-035 is accepted, the current canonical component decomposition remains:

```text
Agent Memory System
├── Identity Substrate
├── Evidence and Provenance Substrate
├── Reality Graphs
├── Lifecycle Engine
├── Saturation and Decay Engine
├── Governance and Mutation Authority (PAMA)
├── Certification and Crystallization Gate
├── Runtime Memory Space
├── Context Assembly Surface
├── Correction and Dispute Surface
├── Durable Decision Memory
├── Governance Context Projection
├── Conformance and Calibration Harness
└── Product and Agent Integrations
```

ADR-035 proposes a system-level composition of these responsibilities. It does not erase their distinct failure modes.

## Component map

| Component | Canonical role | Owns | Must not own | Typical control character |
|---|---|---|---|---|
| Identity Substrate | Stable object identity | UOR address, deterministic resolution, exact lookup identity | lifecycle policy, truth, promotion | deterministic substrate |
| Evidence and Provenance Substrate | Why something is believed | source records, observations, witnesses, evidence bundles, estimator provenance | permanence decisions by itself | deterministic records + uncertain evidence |
| Reality Graphs | Domain-specific structured reality | code graph, decision graph, task graph, relation graph | runtime memory authority | deterministic identity + probabilistic relations |
| Lifecycle Engine | Memory state transitions | transient, observed, linked, candidate, disputed, pruned, crystallized | identity semantics | governed state machine |
| Saturation and Decay Engine | Persistence pressure | calibrated sigma, decay, pressure, routing candidacy | correctness, certification | probabilistic / heuristic / learned estimates |
| Governance and Mutation Authority | Permission to change memory or downstream authority | native PAMA outcomes, M0-M5 target classes, A0-A5 authority ceilings, risk, reversibility | raw scoring, factual truth | deterministic or formally bounded governance envelope |
| Certification and Crystallization Gate | Durable transition approval | verification, approval, certificate, scope | ongoing truth forever | governed consequence |
| Runtime Memory Space | Operational use | Vault, Neurospace, context recall, graph traversal | canonical doctrine ownership | hybrid retrieval + enforced scope |
| Context Assembly Surface | What the agent sees now | prompt context, retrieved memories, active constraints | memory mutation without authority | probabilistic ranking inside governed admission |
| Correction and Dispute Surface | How memory changes safely | user correction, contradiction, reconciliation | silent overwrite | mixed inference + governed commit |
| Durable Decision Memory | Decision continuity and rationale | durable decisions, supersession, drift evidence, rationale preservation | product-specific ownership | governed memory profile |
| Governance Context Projection | Vendor-neutral governance-facing view | derived precedent/context, material conditions, polarity, validity, derivation metadata | canonical memory truth, standing permission, consumer verdicts | deterministic projection first; estimator-mediated retrieval only as typed evidence |
| Conformance and Calibration Harness | System validation | fixtures, reports, trap classes, threshold calibration | product UX | measurement and falsification |
| Product and Agent Integrations | Adoption surfaces | implementations with explicit mapping evidence, consumer-specific adapters | redefining canonical terms locally | implementation-specific within doctrine |

## Component interaction pipeline

```text
Artifact or experience
  -> Identity Substrate
  -> Evidence and Provenance Substrate
  -> Reality Graph or Memory Unit
  -> probabilistic / heuristic interpretation
  -> Lifecycle and Saturation proposal
  -> Governance and Mutation Authority (PAMA)
  -> permitted action set
  -> Certification and Crystallization Gate when required
  -> committed state transition
  -> Runtime Memory Space
  -> recall-time governance
  -> Context Assembly Surface
```

Corrections and disputes can re-enter the pipeline at Evidence, Lifecycle, Governance, or Certification depending on severity.

The pipeline describes responsibility and authority flow, not necessarily one synchronous execution order.

The ADR-035 candidate architecture generalizes the same boundary into a cognitive loop:

```text
experience / observation
  -> stable cognitive identity + evidence
  -> Cognitive Mesh
  -> Cognitive Metabolism and/or Reality Graph processing
  -> candidate cognitive change
  -> PAMA authority evaluation
  -> governed durable commit or refusal
  -> governed recall
  -> Working Memory & Attention
  -> active cognition
```

A learned signal, graph score, prediction, or provider-native verdict remains a proposal unless existing authority doctrine says otherwise.

Governance Context Projection is an optional derived branch from canonical memory and governed recall, not a replacement stage in the canonical write/read path:

```text
canonical memory + evidence + scope + outcome
  -> governed retrieval / selection
  -> Governance Context Projection
  -> consumer-specific adapter
  -> external governance / approval / enforcement decision
```

The consumer may return approval or execution evidence through a separate interoperability/evidence seam. That returned evidence may become new Agent Memory input only through the normal identity, evidence, lifecycle, and authority boundaries.

## Uncertainty must survive handoff

When a component produces an estimate, the receiving component must be able to distinguish:

```text
value
semantic meaning
estimator or method
estimator version
calibration scope when relevant
uncertainty representation
source evidence
validity scope
```

For example, a CodeGenome relation with confidence `0.82` must not arrive at PAMA as a naked `0.82` with no indication that it is an inferred semantic edge.

Likewise, a sensitivity classifier that reports uncertainty must not be converted into `non_sensitive=true` merely because an API wanted a boolean.

A Cognitive Metabolism signal such as high reinforcement, low predicted utility, or crystallization candidacy must remain typed as a metabolic/lifecycle proposal. It must not arrive downstream disguised as truth, deletion authority, or permission to become canonical.

A Governance Context Projection selected through semantic similarity must likewise preserve the estimator and uncertainty that selected the precedent. The consumer may receive candidate relevance; it must not receive probabilistic similarity disguised as permission.

## Proposal, authority, selection, commit

Composition should preserve four different logical stages:

```text
PROPOSAL
what an estimator, model, rule, or planner suggests

AUTHORITY ENVELOPE
what PAMA policy permits, blocks, defers, or requires review for

SELECTION
which permitted action is chosen, deterministically or stochastically

COMMIT
what state actually changes and what receipt is emitted
```

A component may implement multiple stages, but it must not make them indistinguishable.

For external governance consumers, Governance Context Projection sits before their equivalent authority/selection/commit stages. It supplies remembered context, not a substitute authority envelope.

## Segmentation principle

A concept belongs in a separate component when it has a distinct failure mode.

Examples:

- cognitive-mesh failure means identity, type, or relationship semantics are corrupted across modules
- identity failure means the wrong object is addressed
- evidence failure means the object lacks support
- estimator failure means a confidence, relevance, sensitivity, persistence, or prediction estimate is miscalibrated or out of scope
- metabolic failure means the system reinforces, consolidates, retains, or forgets poorly
- reality-graph failure means domain state or relationships are wrong, stale, or insufficiently evidenced
- saturation failure means the system remembers or forgets poorly
- governance failure means the system changes memory or authority without permission
- certification failure means an unverified memory becomes durable
- runtime failure means the agent uses memory incorrectly
- durable-decision failure means rationale, supersession, or current decision state is lost or silently rewritten
- governance-projection failure means derived context loses provenance/scope, erases negative precedent, or becomes consumer authority
- composition failure means individually valid components combine into unsafe behavior
- conformance failure means the implementation cannot prove its behavior

If two concepts fail differently, segment them or expose the internal boundary clearly.

## Composition failure is first-class

Safe components do not automatically create a safe system.

Examples:

```text
safe retriever + missing tenant filter -> cross-tenant leakage
accurate sensitivity classifier + stale policy -> unsafe sharing
calibrated utility estimator + overbroad deletion authority -> irreversible loss
high reinforcement + bad evidence -> durable false belief candidate
accurate reality graph + stale currentness -> incorrect active cognition
useful prediction + authority collapse -> unauthorized action
valid individual memories + unsafe composition -> poisoned context
valid PAMA outcome + stale state snapshot -> incorrect commit
valid precedent + consumer-specific overgeneralization -> approval laundering
```

Therefore conformance must test handoffs and composition, not only isolated component behavior.

## Unification principle

A concept belongs under the same overall architecture when it participates in governed memory state transition, persistent cognition, or a governed projection of remembered state whose semantics must remain reconstructable.

Examples:

- UOR participates by providing stable identity
- CodeGenome participates as the initial Code Reality Graph implementation and provider of domain evidence and graph relations
- EvolveAI participates as the initial Cognitive Metabolism implementation and provider of lifecycle/decay/consolidation mechanisms
- PAMA participates as native doctrine controlling mutation and downstream authority
- COREFORGE Vault and Neurospace may participate by operationalizing memory
- FailSafe and Arbiter may participate as enforcement implementations
- durable decision memory participates through the repository's own decision-memory profile
- Governance Context Projection participates by exposing bounded, consumer-neutral context without owning the downstream governance decision

An adjacent product name is not itself an architectural role. Implementations should be named only when the mapping adds concrete evidence or responsibility.

## Boundary rules

1. Shared doctrine, segmented implementation.
2. A shared Cognitive Mesh, if ADR-035 is accepted, does not erase component or capability boundaries.
3. Components may depend on each other, but must not redefine each other.
4. Every durable memory transition must cross identity, evidence, authority, and certification boundaries; scoring may propose but not authorize.
5. Runtime memory may use uncertified memory only with scope and warning semantics.
6. Domain reality graphs may provide evidence, but do not own permanence.
7. Cognitive Metabolism may propose reinforcement, decay, consolidation, or restructuring, but does not own truth or consequence authority.
8. PAMA may authorize mutation, but does not determine factual truth.
9. Certification may confirm durability, but does not block later correction.
10. Probabilistic outputs must preserve semantic type, provenance, and uncertainty across handoffs.
11. A blocked action must remain blocked even when another component assigns it high confidence, utility, reinforcement, or predicted value.
12. Stochastic selection may occur only inside a policy-permitted action set.
13. Commit boundaries must bind to the state and policy snapshot under which authority was granted.
14. Composition-specific failure modes require composition-specific tests.
15. PAMA target class, lifecycle strength, requested operation, and downstream authority remain separate dimensions.
16. Module identity, component identity, and capability identity remain distinct.
17. External implementation names require an evidence-backed mapping role, not mere conceptual proximity.
18. Derived Governance Context Projection is reconstructable context, never an alternate canonical memory store or final policy authority.
19. Consumer-specific fields belong in consumer adapters unless they expose a genuinely general missing Agent Memory primitive.
20. Returned external approval or execution evidence re-enters Agent Memory through normal evidence/governance boundaries; an integration callback is not a privileged write path.

## Cross-component handoff contract

A consequential handoff should preserve, where applicable:

```text
memory_id
source_component
target_component
handoff_reason
state_snapshot
pama_target_class
lifecycle_strength
requested_operation
requested_downstream_authority
estimate_type
estimate_value
estimator_ref
estimator_version
calibration_ref
uncertainty_summary
evidence_refs
policy_refs
policy_version
authority_refs
permitted_action_set
certification_refs
ledger_ref
timestamp
```

For Cognitive Mesh participation, additional typed metadata may be required to preserve object class, relationship semantics, activation posture, canonical/derived posture, and currentness. ADR-035 acceptance requires that this be defined without forcing one implementation-specific universal ontology.

Not all fields apply to every handoff. Omitted authority-critical fields must not be guessed downstream.

Governance Context Projection has a separate minimized schema because it is a consumer-facing derived view rather than a canonical component mutation handoff. It must still preserve source-memory references, scope, derivation, validity, and uncertainty sufficient for reconstruction.

## Component maturity levels

| Level | Meaning |
|---|---|
| Conceptual | The component is defined in doctrine only |
| Documented | Interfaces and failure modes are documented |
| Handoff-documented | Input/output semantics and uncertainty/authority boundaries are documented |
| Fixture-tested | Component behavior appears in conformance fixtures |
| Composition-tested | Handoffs and multi-component failure modes are tested |
| Implemented | One repo implements the component |
| Enforced | The component blocks unsafe behavior at runtime |
| Cross-repo adopted | Multiple repos conform to the same boundary |

These architectural maturity descriptions do not replace ADR-033 capability maturity (`declared`, `implemented`, `runtime_wired`, `evidence_proven`, `reference_qualified`). Capability qualification remains independently version- and evidence-scoped.

## Architecture decision

This repo owns the overall architecture and native doctrine, including PAMA and the vendor-neutral Governance Context Projection profile.

If ADR-035 is accepted, Agent Memory will additionally own the canonical Cognitive Mesh contract and the module-level topology of the governed cognitive framework. That ownership will define interfaces and boundaries, not grant Agent Memory core a monopoly on implementation mechanisms.

Individual repos may own implementation slices after they demonstrate a meaningful mapping. Consumer-specific governance adapters should normally be owned with the consumer integration, not by changing Agent Memory core to mirror the consumer's policy model.

The shared architecture should stabilize concepts, boundaries, handoff semantics, and conformance expectations. It should not force every implementation into one repository or one runtime, and it should not grant doctrine ownership or capability maturity to whichever product happens to implement a feature first.
