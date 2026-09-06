# ADR-035: Agent Memory Is a Governed Cognitive Framework Built on a Shared Cognitive Mesh

## Status

Accepted

## Context

Agent Memory already defines bounded responsibilities for identity, evidence, lifecycle, decay, reality graphs, recall, correction, mutation authority, certification, scope, procedural memory, and conformance.

ADR-033 further establishes that component identity and capability identity are orthogonal:

```text
one component -> many capabilities
one capability -> many candidate implementations
```

That decision remains valid.

The missing architectural decision is the composition of those responsibilities into persistent cognition.

An agent's durable memory should participate in one cohesive cognitive substrate rather than exist as a collection of adjacent storage, retrieval, lifecycle, graph, and governance services. The current decomposition correctly identifies distinct failure modes, but it can make Agent Memory appear to be governance infrastructure around memory implementations rather than the persistent cognition layer itself.

First-party systems expose this gap clearly.

EvolveAI implements and experiments with adaptive memory metabolism, including lifecycle progression, salience, reinforcement, decay, temporal graph memory, consolidation, REM-style synthesis, crystallization proposals, negative/failure memory, and persistent continuity.

CodeGenome implements and experiments with structured reality representation, including content-addressed identity, graph-based code reality, structural and semantic relationships, provenance, independent observers, confidence fusion, freshness, and propagation/impact reasoning.

Agent Memory supplies the doctrine required to govern those mechanisms: identity and continuity, evidence and provenance, lifecycle, recall admission, correction and supersession, scope and isolation, procedural memory, PAMA mutation authority, certification, deletion, inheritance, conformance, and audit.

Treating these systems only as neighboring providers understates their architectural relationship. They are bounded subsystems participating in a common cognitive architecture.

The architecture therefore needs a shared **Cognitive Mesh** through which memory, learned structure, external reality, evidence, activation, uncertainty, lifecycle, scope, and authority can interoperate without collapsing their semantics.

## Decision

Agent Memory adopts the following architectural identity:

> **Agent Memory is a governed cognitive framework for persistent agents, built on a shared Cognitive Mesh and composed from bounded cognitive, reality, and authority modules.**

Agent Memory owns:

```text
canonical cognitive contracts
shared object and relationship semantics
cross-module boundaries
governance doctrine
authority constraints
conformance requirements
composition rules
```

Individual modules own mechanisms.

```text
Agent Memory defines the contract.
Modules implement the mechanism.
PAMA governs consequential change.
Conformance establishes what has actually been proven.
```

Agent Memory is therefore not merely:

```text
storage
+ retrieval
+ governance
```

It is:

```text
persistent cognitive state
+ adaptive cognitive structure
+ models of reality
+ memory metabolism
+ governed recall
+ bounded adaptation
+ consequence authority
+ durable continuity
```

## Three-plane architecture

The framework is organized into three primary logical planes.

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
|       +-- other domain graphs
|
+-- Authority Plane
    +-- PAMA
    +-- Governed Recall Admission
    +-- Certification & Durable Commit
    +-- Scope / Privacy / Isolation
    +-- Correction / Supersession
    +-- Deletion / Forgetting Authority
    +-- Inheritance / Multi-Agent Crossing

Cross-cutting substrates:
  Identity & Continuity
  Evidence & Provenance
  Conformance / Calibration / Evaluation
```

The planes describe responsibility, not physical deployment. A component may participate in more than one plane and expose multiple independently qualified capabilities under ADR-033.

## Cognitive Mesh

The Cognitive Mesh is the common representational substrate of Agent Memory.

It supports durable and transient cognitive objects with stable identity and typed relationships. Candidate object classes include:

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

The canonical vocabulary may evolve through normal schema and structural-governance processes.

A cognitive object should preserve, where applicable:

```text
identity
object type
temporal state
scope / isolation domain
provenance
evidence references
confidence / uncertainty
activation
lifecycle state
canonical / derived posture
currentness
authority ceiling
relationships
```

A shared mesh does not imply identical behavior or authority:

```text
common mesh != common behavior
relationship != truth
activation != authority
confidence != permission
persistence != correctness
```

Typed relationships may include:

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

Observed, inferred, learned, and synthesized relationships must preserve their epistemic character. An inferred relation does not become an observed fact merely because both occupy the same mesh.

## Cognitive Metabolism

Agent Memory defines **Cognitive Metabolism** as the module responsible for changes in persistence pressure, activation pressure, reinforcement, decay, interference, consolidation candidacy, and adaptive restructuring over time.

EvolveAI is the initial first-party reference and research implementation for this responsibility. This mapping does not promote all EvolveAI capabilities or make its internal ontology canonical.

Cognitive Metabolism may include:

```text
salience
reinforcement
decay
interference
persistence pressure
lifecycle proposals
memory tiering
consolidation candidacy
synthesis
crystallization candidacy
forgetting pressure
adaptive structural proposals
failure-pattern learning
```

The module may use deterministic, probabilistic, heuristic, learned, or hybrid mechanisms.

Its consequential outputs remain proposals or estimates until authorized:

```text
high reinforcement != truth
high salience != permanence
decay pressure != deletion authority
consolidation candidate != canonical memory
crystallization proposal != permission to crystallize
```

Cognitive Metabolism must not grant itself authority to perform irreversible, canonical, cross-scope, action-enabling, or governance-bearing mutations.

## Reality Graphs

Agent Memory defines **Reality Graphs** as domain-specific structured models of external or operational reality.

A Reality Graph answers:

> What entities and relationships does current evidence support within this domain?

Reality Graphs preserve, where applicable:

```text
stable identity
domain semantics
provenance
observer/source identity
observed vs inferred distinction
confidence / uncertainty
temporal validity
currentness / freshness
evidence relationships
```

Reality Graphs do not own memory permanence or downstream authority.

### Code Reality Graph

CodeGenome is the initial first-party implementation of the **Code Reality Graph**.

Its role includes representations such as:

```text
code artifacts
syntax
symbols
references
dependencies
control flow
data flow
runtime relationships
process relationships
change impact
structural provenance
freshness
```

CodeGenome's code-specific ontology does not become the universal ontology of the Cognitive Mesh. It implements the Reality Graph contract for the code domain.

### Additional Reality Graphs

The architecture permits additional domain graphs such as Environment, Task, Social, Organizational, System, or Product Reality Graphs where domain-specific identity, evidence, temporal, or relationship semantics justify specialization.

These are architectural roles, not required repositories.

## Working Memory and Attention

Working Memory and Attention owns active cognition: the portion of admissible cognitive state currently activated for reasoning, planning, perception, or action selection.

```text
persistent memory != active cognition
```

Activation may use relevance, goals, novelty, recency, association, learned salience, prediction error, or other signals. Activation never bypasses governed recall admission.

## Consolidation and Abstraction

Consolidation and Abstraction transforms lower-level experiences into candidate higher-level cognitive structures.

Examples include:

```text
episodes -> concepts
repeated observations -> semantic candidates
successful traces -> procedural candidates
multiple records -> summaries
recurring relations -> generalized structures
experiences -> learned associations
```

Consolidation remains distinct from persistence pressure and authority:

```text
frequent != true
similar != equivalent
repeated != canonical
generalized != authorized
```

Consequential consolidation crosses normal Agent Memory evidence, lifecycle, structural-mutation, and authority boundaries.

## Predictive and World Modeling

Predictive modeling is a first-class cognitive responsibility distinct from Reality Graphs.

Reality Graphs represent what current evidence supports. Predictive models represent what the system expects next given current state.

This boundary permits future implementations such as temporal prediction, causal models, latent world models, JEPA-like representations, probabilistic forecasts, and learned environment dynamics.

Prediction remains epistemic output. Prediction confidence does not create mutation or action authority.

## Procedural Memory and Skills

Procedural Memory owns retained knowledge of how to perform tasks. It may learn reusable sequences from successful behavior, demonstrations, validated workflows, or other evidence.

```text
experience
  -> repeated / successful structure
  -> procedure candidate
  -> validation
  -> governed retention
  -> recall
  -> planning influence
```

ADR-034 remains controlling:

```text
procedure != permission
skill retention != execution authority
```

## Identity, Evidence, and Continuity

Identity and Continuity provides stable addressing across sessions, process restarts, representation changes, derived structures, module boundaries, agent versions, migrations, and successor agents.

Changing storage provider, graph representation, embedding model, or module implementation must not silently create a new logical identity for existing canonical memory.

Evidence and Provenance preserves the reconstructable basis for cognitive state and distinguishes observation, assertion, inference, synthesis, inheritance, external evidence, execution evidence, correction, and derived evidence.

No module may treat its own output as authoritative evidence merely because it generated that output.

## Governed Recall and Active Cognition

Governed Recall remains responsible for deciding which portions of the Cognitive Mesh may influence active cognition.

Candidate generation may use exact lookup, graph traversal, semantic retrieval, temporal retrieval, associative activation, procedural retrieval, prediction, reality-graph query, or learned routing.

Candidate discovery remains separate from admission:

```text
retrievable != admissible
relevant != permitted
```

Context Assembly operates only over admitted state and preserves material uncertainty, provenance, correction, scope, currentness, and policy information.

## Conflict, Correction, and Supersession

Agent Memory preserves disagreement and correction as explicit cognitive state. Conflicting memories or graph relations must not be silently merged merely because they share the same mesh.

The system must be able to distinguish:

```text
currently believed
historically believed
disputed
superseded
incorrect and corrected
unknown
```

Existing correction, dispute, and supersession doctrine remains controlling.

## PAMA Authority

PAMA remains the canonical Adaptive Mutation and Consequence Authority layer.

Every module may propose. No module may convert its own confidence, reinforcement, graph position, prediction, retrieval score, learned pattern, or native verdict into permission.

```text
Cognitive Metabolism
  -> may propose persistence or restructuring

Reality Graph
  -> may propose belief or relation updates

Consolidation
  -> may propose abstraction

Predictive Modeling
  -> may propose expected state

Procedural Memory
  -> may propose reusable behavior

PAMA
  -> determines permitted consequence
```

PAMA evaluates consequences according to applicable target class, lifecycle strength, requested operation, downstream authority, scope, reversibility, evidence, risk, and policy.

## Certification and Durable Commit

Certification owns required verification before high-consequence state becomes canonical or equivalently durable.

Durable commit binds consequential changes to the evidence, authority, state, policy, and implementation context under which the change was permitted.

Successful provider execution is not sufficient evidence of justified durable mutation.

## Scope, Privacy, Isolation, and Inheritance

The Cognitive Mesh may be physically shared while remaining logically partitioned.

```text
same mesh != same authorized domain
```

Project, user, task, tenant, purpose, agent, and shared-memory boundaries remain governed isolation domains. Relationships and derived state must not silently widen scope.

Inheritance is a first-class cognitive operation, including crossings such as:

```text
agent -> successor agent
agent -> agent
agent -> team
agent -> organization
generation N -> generation N+1
```

Inherited state preserves provenance, scope, authority limitations, uncertainty, lifecycle status, and applicable policy. Receiving inherited memory does not imply accepting it as current canonical belief.

## Conformance, Calibration, and Evaluation

The framework evaluates module behavior and composed cognition separately.

```text
module conformance
+
cross-module composition conformance
```

Evaluation should cover, where applicable:

```text
identity continuity
retrieval quality
recall admission
memory interference
consolidation quality
decay behavior
correction propagation
prediction calibration
scope isolation
authority containment
deletion completeness
restart continuity
module replacement
cross-module provenance
unsafe cognitive composition
```

Claims such as improved learning, lower drift, better recall, useful consolidation, or successful prediction require empirical evidence rather than architectural assertion.

## Component identity, module identity, and capability identity

This ADR does not supersede ADR-033.

A module describes an architectural responsibility. A component is an implementation that may expose capabilities relevant to one or more modules.

```text
module identity != component identity
component identity != capability identity
```

EvolveAI may primarily implement Cognitive Metabolism while also exposing retrieval, graph, persistence, provenance, or other capabilities.

CodeGenome may primarily implement a Code Reality Graph while also exposing retrieval, structural reasoning, provenance, freshness, evaluation, or other capabilities.

Those capabilities continue to mature and qualify independently.

This ADR adds coherent system topology. It does not restore exclusive product categories.

## Initial first-party mapping

| Architectural responsibility | Initial implementation / source |
|---|---|
| Cognitive Mesh | Agent Memory core contract and reference substrate |
| Cognitive Metabolism | EvolveAI |
| Code Reality Graph | CodeGenome |
| Identity & Continuity | Agent Memory core plus qualified providers |
| Evidence & Provenance | Agent Memory core contract |
| Working Memory & Attention | Agent Memory reference implementation |
| Consolidation & Abstraction | Agent Memory contract with qualified provider mechanisms |
| Recall & Context Assembly | Agent Memory governed recall |
| Conflict / Correction / Supersession | Agent Memory |
| Predictive / World Modeling | Pluggable; no canonical implementation yet |
| Procedural Memory & Skills | Agent Memory procedural-memory profile |
| PAMA Authority | Agent Memory native doctrine |
| Certification & Durable Commit | Agent Memory |
| Scope / Privacy / Isolation | Agent Memory |
| Inheritance / Multi-Agent Memory | Agent Memory |
| Conformance / Calibration / Evaluation | Agent Memory |

This table identifies primary architectural responsibility only. It is not a claim of implementation completeness or capability qualification.

## Repository and packaging implications

This ADR defines architectural modules, not Git repository mechanics.

It does not require EvolveAI or CodeGenome to immediately become Git submodules, directories, packages, or vendored source inside the Agent Memory repository.

Physical composition may use workspace packages, versioned dependencies, Git submodules, service boundaries, adapters, embedded libraries, or other reproducible packaging.

Whatever packaging is selected must preserve:

```text
version identity
capability qualification
dependency boundaries
reproducibility
replaceability
licensing
failure isolation
authority boundaries
```

The long-term product surface should present these capabilities as one Agent Memory framework rather than requiring users to understand an accidental collection of research repositories.

## Framework ownership rule

Agent Memory owns interfaces and doctrine. Submodules own mechanisms.

```text
Agent Memory:
  defines Cognitive Metabolism requirements

EvolveAI:
  implements one Cognitive Metabolism strategy

Agent Memory:
  defines Reality Graph requirements

CodeGenome:
  implements the Code Reality Graph

Agent Memory:
  defines cognitive-object, evidence, lifecycle,
  recall, authority, and conformance semantics

implementations:
  satisfy those contracts at independently proven maturity
```

First-party ownership does not confer conformance. A first-party module may be experimental, incomplete, replaceable, or rejected without changing the canonical Agent Memory contract.

## Consequences

### Positive

- gives Agent Memory an explicit cognitive substrate rather than implying one through scattered components;
- makes EvolveAI and CodeGenome coherent parts of one architecture;
- preserves modularity without presenting the system as disconnected projects;
- creates a shared substrate for episodic, semantic, procedural, predictive, and reality-linked cognition;
- creates explicit homes for attention, consolidation, prediction, and metacognitive signals;
- preserves PAMA as the consequence boundary across the cognitive system;
- keeps external cognitive technologies replaceable implementations rather than architectural definitions;
- allows future reality domains beyond code;
- gives Agent Memory a clearer identity as persistent governed cognition rather than advanced RAG infrastructure.

### Negative

- expands Agent Memory's declared scope from governed memory architecture toward governed cognition;
- requires careful vocabulary work to keep the Cognitive Mesh from becoming an unbounded universal ontology;
- increases cross-module conformance requirements;
- creates implementation pressure for currently conceptual responsibilities such as predictive modeling;
- requires documentation and diagram updates across the repository;
- may eventually require repository/package restructuring after architectural boundaries stabilize.

These costs are preferable to leaving the already-existing cognitive composition implicit.

## Alternatives considered

### Continue treating EvolveAI and CodeGenome only as adjacent providers

Rejected. This preserves implementation flexibility but fails to express that memory metabolism, structured reality, recall, continuity, and governance participate in one cognitive system.

### Adopt EvolveAI as the complete cognitive substrate

Rejected. EvolveAI provides useful first-party mechanisms but remains replaceable and independently qualified. Implementation identity must not become canonical architecture.

### Adopt CodeGenome's graph as the universal Cognitive Mesh

Rejected. CodeGenome models code reality. Its ontology and evidence structure are useful, but a code-domain reality graph is not a universal cognitive ontology.

### Adopt an external cognitive substrate wholesale

Rejected as the architectural default. External research implementations may provide useful mechanisms and evidence, but Agent Memory's foundational cognitive contract must not inherit unproven topology, learning, authority, or representation assumptions from one implementation.

### Build one monolithic cognitive engine

Rejected. A cohesive cognitive framework does not require a monolithic implementation. Identity, evidence, metabolism, reality representation, prediction, recall, authority, and certification have distinct failure modes and must retain explicit boundaries.

### Remain representation-neutral and avoid a shared mesh

Rejected. Representation neutrality should prevent provider/storage lock-in, not prevent Agent Memory from defining the common semantic contracts required for persistent cognition.

## Relationship to existing doctrine

This ADR extends rather than supersedes:

- ADR-020, probabilistic discovery and governed consequence;
- ADR-022, memory isolation domains;
- ADR-028, language-neutral core and implementation profiles;
- ADR-032, governed mutable memory structure;
- ADR-033, capability-oriented composition;
- ADR-034, procedural memory is not execution authority.

The shared Cognitive Mesh does not weaken any authority, isolation, deletion, correction, currentness, or capability-maturity boundary established by those decisions.

## Acceptance requirements

ADR-035 may move from Proposed to Accepted when:

1. the Cognitive Mesh boundary is documented without creating a universal implementation-specific ontology;
2. the three-plane architecture is integrated consistently into canonical documentation;
3. EvolveAI is mapped to Cognitive Metabolism without falsely promoting unqualified capabilities;
4. CodeGenome is mapped to Code Reality Graph without promoting its domain ontology to universal memory semantics;
5. module identity, component identity, and capability identity remain distinct and consistent with ADR-033;
6. at least one end-to-end reference path demonstrates:

```text
experience / observation
  -> Cognitive Mesh identity
  -> Evidence / Provenance
  -> Cognitive Metabolism or Reality Graph processing
  -> candidate cognitive change
  -> PAMA authority evaluation
  -> governed durable commit or refusal
  -> governed recall
  -> active cognition
```

7. an adversarial path proves that learned reinforcement, graph confidence, prediction confidence, or a provider-native verdict cannot independently grant durable or action authority;
8. module replacement or absence fails explicitly without corrupting canonical cognitive identity;
9. conformance documentation distinguishes architectural acceptance from implementation maturity.

The bounded evidence satisfying these requirements is recorded in [`../programs/runtime-evidence/adr-035-acceptance-matrix.md`](../programs/runtime-evidence/adr-035-acceptance-matrix.md). Acceptance does not promote unrelated provider capability maturity or claim universal production conformance.

## Decision summary

Agent Memory is the canonical framework for persistent governed agent cognition.

Its shared substrate is the Cognitive Mesh.

EvolveAI becomes the initial first-party Cognitive Metabolism implementation.

CodeGenome becomes the initial first-party Code Reality Graph implementation.

Additional bounded modules provide working cognition, consolidation, prediction, procedural memory, evidence, correction, scope, inheritance, recall, certification, and conformance.

All modules may adapt, infer, retrieve, associate, predict, or propose according to their contracts.

None may convert those signals into consequential authority on its own.

```text
shared cognition
      +
bounded modules
      +
explicit evidence
      +
governed adaptation
      +
PAMA authority
      =
Agent Memory
```
