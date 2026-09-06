# System Composition Boundaries

## Purpose

This document defines how the larger Agent Memory architecture composes from separate systems without collapsing their responsibilities.

The goal is to make the architecture feel like one coherent system while preserving the boundaries that make it implementable, governable, and testable.

Composition is also where uncertainty can become dangerous: an estimate produced safely by one component can become an unauthorized consequence if another component consumes it without preserving meaning, scope, uncertainty, or policy state.

## Composition model

Agent Memory is a composed system.

Current accepted responsibilities remain:

```text
Agent Memory
  = Identity
  + Evidence
  + Reality Graphs
  + Lifecycle
  + Saturation and Decay
  + Governance
  + Certification
  + Runtime Memory
  + Context Assembly
  + Correction and Dispute
  + Conformance
```

[ADR-035](adr/ADR-035-agent-memory-is-a-governed-cognitive-framework.md) proposes composing those bounded responsibilities into an explicit persistent-cognition topology:

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
|       +-- other domain reality graphs
|
+-- Authority Plane
|   +-- PAMA
|   +-- Governed Recall Admission
|   +-- Certification & Durable Commit
|   +-- Scope / Isolation
|   +-- Correction / Supersession
|   +-- Deletion / Inheritance Authority
|
+`-- Cross-cutting
+    +-- Identity & Continuity
+    +-- Evidence & Provenance
+    `-- Conformance / Calibration / Evaluation
```

Until ADR-035 is accepted, this is a proposed composition model rather than a replacement for accepted component doctrine.

The planes are responsibility groupings. They are not repositories, exclusive component categories, deployment zones, or capability-maturity claims.

```text
module identity != component identity
component identity != capability identity
```

ADR-033 remains controlling for implementation selection and maturity.

This is one concept at the architecture level and many components at the implementation level.

## Cognitive Mesh composition contract

Under ADR-035, the Cognitive Mesh is the proposed shared representational and handoff substrate for persistent cognition.

It is not a universal truth store, a replacement for the identity/evidence/lifecycle contracts below, or a mandate that every implementation share one physical graph.

A mesh handoff may carry, where applicable:

```text
logical_object_ref
object_type
relationship_type
canonical_or_derived_posture
activation_posture
currentness
scope / isolation domains
provenance / evidence refs
signal semantics
estimator identity/version
confidence / uncertainty
lifecycle posture
authority ceiling
provider/component identity
```

The receiving module must preserve material semantics rather than flattening them into an opaque object.

The core anti-collapse rules are:

```text
common mesh != common behavior
relationship != truth
activation != authority
confidence != permission
persistence != correctness
provider verdict != Agent Memory authority
```

A Cognitive Metabolism implementation may propose reinforcement, decay, consolidation, or restructuring. A Reality Graph may propose or evidence a relation. A predictive model may produce an expectation. None of those outputs owns the consequential mutation, recall, or action decision.

The executable bounded reference evidence for this seam is documented in [`programs/runtime-evidence/cognitive-mesh.md`](programs/runtime-evidence/cognitive-mesh.md).

## Initial first-party architectural mapping

ADR-035 proposes the following primary responsibility mapping while ADR-033 preserves multi-capability composition:

| First-party component | Primary proposed module role | Boundary |
|---|---|---|
| EvolveAI | Cognitive Metabolism | lifecycle/decay/consolidation signals remain proposals; native verdicts do not become PAMA authority |
| CodeGenome | Code Reality Graph | code-domain graph/evidence does not become universal Cognitive Mesh ontology or memory authority |
| Agent Memory core | Cognitive Mesh contracts, authority boundaries, governed recall, conformance | core owns doctrine/interfaces rather than monopolizing provider mechanisms |

This mapping does not upgrade provider capability maturity. Qualification remains capability-, version-, adapter-, and evidence-scoped.

## System boundary

The system boundary includes any component that participates in governed memory state transition, persistent cognitive influence, or governed memory admission.

A component is inside Agent Memory if it answers at least one of these questions:

1. What is this memory or cognitive object?
2. Why is this object or relation supported?
3. What does the system estimate about this object?
4. How should this memory be scored, activated, consolidated, or routed?
5. What state is this memory in?
6. What does a domain reality model currently support?
7. Who may mutate, share, prune, delete, inherit, or expose this memory?
8. Can this memory become durable?
9. May this memory enter the current agent context?
10. How is this memory corrected, disputed, or pruned?
11. How is memory and composed cognition behavior tested?

## Outside the system boundary

A tool is outside the core Agent Memory system when it only consumes outputs without influencing memory state or admission.

Examples:

- a UI that only displays certified memory
- an analytics dashboard that reads conformance reports
- a documentation site that mirrors doctrine files
- an LLM prompt template that consumes an already-governed context package and cannot mutate state

These can be integrations, but not core components.

## Canonical component contracts

### Identity contract

Input:

```text
artifact
```

Output:

```text
stable identity or address
```

Guarantees:

- deterministic resolution where required
- no lifecycle decision
- no truth claim
- no confidence-weighted identity substitution

### Evidence contract

Input:

```text
identity, observation, source reference
```

Output:

```text
evidence record, provenance, confidence or uncertainty signal
```

Guarantees:

- source traceability
- witness record
- estimator/method provenance when evidence is inferred
- no permanence decision by evidence alone

### Reality graph contract

Input:

```text
evidence records, domain artifacts
```

Output:

```text
graph nodes, graph edges, relation confidence, provenance
```

Guarantees:

- domain structure
- deterministic and inferred relations remain distinguishable
- confidence and source separation
- material disagreement remains visible
- no mutation authority by graph confidence alone
- domain ontology does not silently become the universal Cognitive Mesh ontology

### Cognitive Metabolism contract

Input:

```text
memory/cognitive object, interactions, lifecycle state, evidence, learned or heuristic signals
```

Output:

```text
reinforcement, decay, retention, consolidation, synthesis, or restructuring proposal
```

Guarantees:

- proposal semantics and estimator provenance remain explicit
- learned/heuristic signals may recommend but do not authorize consequence
- repetition and salience do not establish truth
- decay or forgetting pressure does not establish deletion authority
- provider-native PASS/BLOCK or equivalent verdict does not become PAMA authority

### Lifecycle contract

Input:

```text
memory unit, event, score, policy signal, transition proposal
```

Output:

```text
validated transition proposal or committed state-transition record
```

Guarantees:

- proposal and commit remain distinct
- state machine alignment
- transition metadata
- no unauthorized mutation
- policy and state snapshot can be reconstructed for consequential commits

### Saturation and decay contract

Input:

```text
memory unit, fibers, interaction history, pressure
```

Output:

```text
sigma, decay profile, candidate routing signal, uncertainty metadata
```

Guarantees:

- calibrated scoring where used for consequential routing
- score semantics are declared
- calibration scope and version are preserved
- trap-class resistance
- no truth or permission claim

### Governance contract

Input:

```text
requested mutation, memory state, risk, evidence, actor, reversibility, estimator outputs, uncertainty
```

Output:

```text
PAMA outcome and permitted action set
```

Guarantees:

- finite authority decision
- deterministic or formally bounded outcome for committed inputs and policy snapshot
- audit requirement
- no factual confirmation by authority alone
- missing authority-critical inputs are not guessed

### Action-selection contract

Input:

```text
permitted action set, planner state, runtime objective
```

Output:

```text
selected permitted action
```

Guarantees:

- deterministic or stochastic selection is allowed only inside the permitted set
- blocked actions are not selectable
- selection mode can be recorded when consequential

### Certification contract

Input:

```text
candidate memory, evidence, authority outcome, verification material
```

Output:

```text
certification status, scope, certificate reference
```

Guarantees:

- durable transition confirmation
- scoped certification
- certificate binds to relevant policy/evidence context
- correction remains possible

### Runtime memory / working cognition contract

Input:

```text
memory units, graph relations, context request, policy constraints
```

Output:

```text
retrieval candidates, admitted memory, assembled context, active cognitive view
```

Guarantees:

- candidate generation may be probabilistic
- scope, tenancy, sensitivity, dispute, and policy constraints apply before admission
- persistent memory remains distinct from currently active cognition
- user or agent usable memory
- no hidden durable mutation

### Correction and dispute contract

Input:

```text
contradiction, user correction, failed verification, expired source
```

Output:

```text
dispute proposal, correction proposal, demotion, reconciliation, or pruning action
```

Guarantees:

- conflict interpretation may remain probabilistic
- consequence is governed
- old state is preserved
- correction is ledgered
- disputed memory is blocked from canonical use

### Conformance contract

Input:

```text
fixtures, implementation behavior, report data
```

Output:

```text
conformance result, calibration metrics, failure report
```

Guarantees:

- trap-class checks
- uncertainty and calibration transparency
- component, module, and composition boundaries are testable
- stochastic systems are judged against invariants, not identical sampled outputs
- architecture acceptance is kept distinct from provider capability maturity

## Cross-component handoff record

When one component passes consequential memory information to another, the handoff should preserve where applicable:

```text
memory_id
logical_object_ref
object_type
source_component
target_component
module_role
handoff_reason
state_snapshot
signal_type
signal_semantics
signal_value
estimator_ref
estimator_version
calibration_ref
uncertainty_summary
evidence_refs
scope_refs
canonical_or_derived_posture
activation_posture
currentness
policy_refs
policy_version
authority_refs
permitted_action_set
certification_refs
ledger_ref
timestamp
```

Not every handoff requires every field. A receiving component must not infer omitted authority, scope, or certainty.

## Handoff invariants

Across adapters and service boundaries:

1. identity must not become probabilistic accidentally
2. confidence must not become certification
3. relevance must not become access permission
4. utility must not become deletion authority
5. saturation must not become factual truth
6. activation must not become authority
7. a provider-native verdict must not become Agent Memory authority
8. disagreement must not vanish through undocumented averaging
9. estimator version must not be confused with policy version
10. a blocked action must remain blocked downstream
11. stochastic action selection must remain within the permitted action set
12. committed consequences must remain auditable after the handoff chain completes
13. module identity, component identity, and capability identity must remain distinguishable

## Composition-specific failure modes

### Semantic type erasure

```text
confidence=0.92 -> receiving service treats 0.92 as approval probability
```

Mitigation: preserve score semantics and estimator provenance.

### Cognitive type erasure

```text
learned association -> receiving service treats relation as observed fact
```

Mitigation: preserve object/relation type, provenance, and canonical/derived posture through the Cognitive Mesh handoff.

### Boolean coercion of uncertainty

```text
sensitivity classifier: uncertain -> API field: sensitive=false
```

Mitigation: support abstention/unknown or enforce a conservative policy state.

### Authority leakage

```text
retriever recommends delete -> storage service interprets recommendation as authorization
```

Mitigation: require explicit governance outcome and permitted action set.

### Cognitive-metabolism authority leakage

```text
reinforcement=1.0 or provider verdict=PASS -> runtime commits crystallization/action
```

Mitigation: convert provider output into typed proposal/evidence and pass the consequential operation through PAMA.

### Scope laundering

```text
cross-tenant memory -> summary service removes tenant metadata -> context assembler treats summary as local
```

Mitigation: scope and provenance must survive synthesis.

### Stale authorization

```text
PAMA allow at state S1 -> state changes to S2 -> old allow reused for commit
```

Mitigation: bind authority to state snapshot, policy version, and requested action.

### Unsafe composition

```text
memory A safe alone
memory B safe alone
A + B creates prohibited instruction or inference
```

Mitigation: apply read-time/composition governance and test multi-memory fixtures.

### Deterministic wrapper fallacy

```text
probabilistic score -> deterministic threshold -> therefore safe
```

Mitigation: preserve uncertainty and calibrate the consequential decision boundary.

## Composition anti-patterns

### Monolith collapse

Wrong:

```text
Cognitive Mesh owns identity, truth, scoring, certification, recall, and correction.
```

Correct:

```text
Cognitive Mesh preserves shared identity/handoff semantics while bounded modules retain distinct responsibilities and authority boundaries.
```

### Graph absolutism

Wrong:

```text
The graph says it, therefore memory is canonical.
```

Correct:

```text
The graph provides evidence and relations. Certification decides durable state.
```

### Score absolutism

Wrong:

```text
Sigma is high, therefore crystallize.
```

Correct:

```text
Sigma is high, therefore propose candidacy and evaluate authority plus certification.
```

### Relevance absolutism

Wrong:

```text
This memory is the best semantic match, therefore inject it.
```

Correct:

```text
This memory is a retrieval candidate. Recall-time governance still applies scope, sensitivity, dispute, and policy filters.
```

### Provider-verdict absolutism

Wrong:

```text
EvolveAI/another provider says PASS, therefore the requested mutation or action is allowed.
```

Correct:

```text
Provider verdict is typed evidence or a risk candidate. PAMA remains the Agent Memory consequence-authority boundary.
```

### Product-local doctrine

Wrong:

```text
COREFORGE defines memory differently from EvolveAI and CodeGenome.
```

Correct:

```text
Each repo implements its slice while referencing shared doctrine boundaries.
```

## Integration posture

Use typed adapters between components and modules.

Do not use implicit shared assumptions.

Recommended adapters:

- cognitive-mesh object/handoff adapter
- identity adapter
- evidence adapter
- graph adapter
- cognitive-metabolism proposal adapter
- lifecycle proposal adapter
- scoring / estimator adapter
- PAMA adapter
- action-set adapter
- certification adapter
- runtime memory adapter
- recall-admission adapter
- conformance adapter

Adapters that carry consequential estimates should document both data schema and semantic contract.

A provider adapter is not qualified merely because an architectural module mapping exists. Native/provider evidence, adapter semantics, exact version binding, and capability maturity remain separately evaluated under ADR-033.

## Composition conformance

At least these end-to-end paths should be tested:

```text
experience -> Cognitive Mesh identity -> typed provider signal -> PAMA -> commit/refusal -> governed recall -> active cognition
semantic retrieval -> scope filter -> context admission
confidence estimator -> PAMA -> transition commit
saturation estimator -> candidate proposal -> certification
reality graph relation -> typed evidence -> governed cognitive consequence
provider PASS/BLOCK -> typed candidate signal -> PAMA authority remains controlling
sensitivity classifier -> sharing policy -> export
utility estimator -> retention policy -> prune/delete decision
conflict detector -> dispute policy -> correction/reconciliation
multi-memory retrieval -> composition policy -> context assembly
module unavailable -> explicit failure / deterministic replacement -> logical identity preserved
```

Tests should inject uncertainty and disagreement at the seams, not only inside individual components.

The current Cognitive Mesh reference evidence proves the architectural seam with provider-labelled signals and existing Agent Memory governance. It does not yet claim that native EvolveAI or CodeGenome outputs are directly wired into that mesh path. Native first-party provider integration remains a separate evidence boundary.

## System rule

Agent Memory is unified by contracts, not by repository location.

The concepts should be segmented by responsibility, then recomposed through governed, typed handoffs.

A cohesive Cognitive Mesh does not mean a monolith. The mesh is useful precisely because identity and relationships can be shared while evidence, reality modeling, metabolism, recall, and authority continue to fail differently and therefore remain bounded.

A safe component is necessary. A safe composition is the actual requirement.
