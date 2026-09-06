# Layer Model

## Intent

The layer model prevents conceptual drift by assigning each system a clear responsibility.

The most important boundary is this:

UOR is identity. Saturation is lifecycle scoring. Certification is confirmation. PAMA is authority. Neurospace is runtime use.

A second boundary is equally important:

**Probabilistic or learned components may estimate what is likely, relevant, conflicting, stale, useful, or risky. They do not acquire authority from those estimates. Consequential memory transitions occur only through deterministic or formally bounded governance.**

## Relationship to the proposed Cognitive Mesh architecture

[ADR-035](adr/ADR-035-agent-memory-is-a-governed-cognitive-framework.md) proposes a system-level topology above this responsibility model. Until ADR-035 is accepted, the layers below remain current canonical doctrine and the three-plane topology remains a proposed composition of them.

The models answer different questions:

```text
layer model
  -> what semantic responsibility is being exercised?

ADR-035 planes
  -> where does that responsibility participate in persistent cognition?

component/capability model
  -> which implementation performs the responsibility at what proven maturity?
```

They must not be collapsed into one taxonomy.

The proposed mapping is:

```text
COGNITIVE PLANE
  Cognitive Mesh
  Saturation / lifecycle routing
  Lifecycle state machine
  Runtime memory / working cognition
  Consolidation / abstraction
  Procedural memory
  predictive / metacognitive signals

REALITY PLANE
  Domain Reality Graphs
  Code Reality Graph via CodeGenome where qualified
  future environment/task/social/organizational graphs

AUTHORITY PLANE
  PAMA governance
  certification / crystallization
  governed recall admission
  correction / dispute consequence
  scope / isolation / deletion / inheritance authority

CROSS-CUTTING
  Identity substrate
  Evidence and provenance
  Conformance and calibration
```

This mapping does not grant a plane or module exclusive ownership of a capability. ADR-033 remains controlling:

```text
module identity != component identity
component identity != capability identity
```

EvolveAI is the proposed initial Cognitive Metabolism implementation role because its evidenced capabilities include lifecycle/decay/orchestration/consolidation mechanisms. CodeGenome is the proposed initial Code Reality Graph implementation role because its evidenced capabilities are code-domain graph, structural, provenance, freshness, and traversal functions. Those architectural mappings do not promote any capability maturity and do not make either component's internal ontology canonical. Both components share Agent Memory's owner, so under [ADR-036](adr/ADR-036-same-owner-components-are-first-party-modules.md) they are first-party module candidates rather than attributed providers: work adopted from them is named for the Agent Memory contract it implements (Code Reality Graph, Cognitive Metabolism), not for its originating repository.

The proposed Cognitive Mesh is likewise not a ninth memory layer or a universal database schema. It is the shared identity-and-handoff substrate through which typed cognitive objects may participate in several bounded responsibilities while retaining provenance, uncertainty, scope, lifecycle posture, and authority semantics.

## Layer 1: Identity substrate

### Owner

UOR Framework, plus any implementation that uses deterministic content addressing.

### Responsibility

- assign stable identity to artifacts
- support deterministic resolution
- preserve addressability across tools
- enable exact lookup when a memory becomes crystallized

### Must not do

- decide truth
- decide lifecycle permanence
- replace evidence
- replace certification

## Layer 2: Evidence and provenance

### Owner

CodeGenome, EvolveAI traces, FailSafe ledgers, COREFORGE audit records, and source-specific observers.

### Responsibility

- record who observed what
- attach evidence to claims
- track creation and mutation history
- preserve witness material through summaries and transformations
- identify the method, model, rule set, or observer that produced probabilistic estimates used downstream

### Must not do

- promote memories by evidence volume alone
- treat model confidence as verification
- collapse provenance into a summary without retaining source links
- represent an estimated probability as if it were deterministic evidence

## Layer 3: Saturation and lifecycle routing

### Owner

PRISM-style bridge logic, EvolveAI lifecycle engine, UOR decay proposal consumers.

### Responsibility

- compute calibrated persistence pressure
- route memory between transient, graph, and durable tiers
- propose crystallization candidates
- adjust decay under contextual pressure
- identify stale, disputed, or prunable objects
- preserve uncertainty and calibration metadata when routing depends on probabilistic or learned estimators

### Control character

This layer may be probabilistic, heuristic, learned, or hybrid.

Its outputs are **proposals and estimates**, not authority grants.

### Must not do

- claim correctness
- grant permanence without certification
- crystallize access-spam
- treat repetition as durability
- convert a score, probability, ranking, or learned action directly into an irreversible transition

## Layer 4: Lifecycle state machine

### Owner

EvolveAI and any runtime memory engine.

### Responsibility

- manage memory states
- perform decay, reinforcement, dispute, correction, reconciliation, and pruning
- preserve audit trail for state transitions
- validate that requested transitions are legal from the current state
- separate transition proposal from transition commit

### Control character

The state-transition contract should be deterministic for a fixed current state, authorized transition, policy version, and committed inputs.

Probabilistic systems may propose a transition. They must not bypass transition validity or authority checks.

### Must not do

- skip governance gates during promotion
- mutate state without authority
- erase disputed history

## Layer 5: PAMA governance

### Owner

PAMA and enforcement surfaces such as Arbiter or FailSafe.

### Responsibility

- define mutation authority
- evaluate risk of change
- control promotion and demotion
- require approval when confidence, evidence, or authority is insufficient
- preserve adaptive constraints
- map uncertain evidence and estimator outputs into a finite policy-defined authority outcome

### Control character

For a fixed policy snapshot and reconstructable input record, the authority envelope must be deterministic or formally bounded.

A probabilistic estimate may influence the decision, but it must not define its own permission to mutate memory.

### Must not do

- allow high-confidence autonomous mutation in high-risk domains without explicit authority
- allow agents to rewrite durable memory without ledgered correction
- use stochastic choice to escape a blocked or review-required authority outcome

## Layer 6: Certification and crystallization

### Owner

Certification gate, approval system, policy engine, or ledger-backed governance layer.

### Responsibility

- confirm that a memory may become durable
- verify identity, provenance, evidence, and authority
- attach certificate or approval records
- move objects to exact-address durable lookup when permitted
- bind certification to the relevant memory state, evidence set, policy version, scope, and estimator context when probabilistic evidence materially affected promotion

### Control character

Certification is a governed consequence. Its acceptance criteria must be explicit and reproducible or formally specified within a bounded approval protocol.

### Must not do

- certify without scoped evidence
- treat a certificate as eternal truth
- block correction pathways

## Layer 7: Runtime memory space

### Owner

COREFORGE Vault / Neurospace and related product runtimes.

### Responsibility

- assemble context windows
- serve agent recall
- perform graph traversal
- enforce local privacy and encryption boundaries
- expose memory through governed product workflows
- apply recall-time policy after probabilistic candidate generation or ranking

### Control character

Candidate retrieval and ranking may be probabilistic.

Scope, tenancy, sensitivity, certification-state, and policy exclusions must still be enforced before retrieved memory enters active context.

A runtime may choose stochastically among multiple already-permitted candidates or strategies, but only inside the permitted action set.

### Must not do

- treat operational utility as canonical truth
- hide agent memory mutation from users or ledgers
- inject a highly relevant memory that violates scope or authority constraints

## Layer 8: Domain reality graphs

### Owner

CodeGenome for code artifacts. Future domain graphs may cover decisions, tasks, documents, organizations, or user workflows.

### Responsibility

- represent domain-specific reality as graph structure
- fuse observations from multiple sources
- retain confidence and provenance
- expose query and traversal primitives
- distinguish exact graph facts from inferred edges, ranked hypotheses, or probabilistic relations

### Control character

Graph identity, schema, and committed relations should remain reproducible. Relation discovery, confidence fusion, entity resolution, and ranking may be probabilistic when their provenance and uncertainty are preserved.

### Must not do

- allow one observer to become canonical without fusion and evidence
- hide confidence conflicts

## Control-character map

| Responsibility | Typical control character | Why |
|---|---|---|
| identity and exact reference | deterministic | ambiguity here corrupts every later decision |
| schema and transition validity | deterministic | invalid states must not become policy-dependent guesses |
| evidence interpretation | probabilistic or hybrid | evidence can be incomplete, noisy, or contradictory |
| confidence, trust, relevance, saturation | probabilistic, learned, heuristic, or hybrid | these are estimates, not authority |
| authority envelope | deterministic or formally bounded | permissions and prohibitions must be reconstructable |
| certification consequence | deterministic or explicitly governed approval | durable promotion requires accountable consequence |
| retrieval candidate generation | probabilistic or hybrid | semantic and contextual relevance are uncertain |
| recall-time scope enforcement | deterministic or formally bounded | high relevance does not override access policy |
| choice among already-permitted actions | optionally stochastic | uncertainty may remain useful inside the safe action set |
| ledger and state-transition receipt | deterministic | accountability requires replayable evidence |

## Governed uncertainty boundary

The canonical flow is:

```text
observation / query
        |
        v
probabilistic or learned interpretation
(confidence, relevance, trust, contradiction, risk, candidate ranking)
        |
        v
explicit governance envelope
(scope, authority, transition validity, policy, sensitivity, reversibility)
        |
        v
permitted action set
        |
        +--> zero actions: block / abstain / escalate
        |
        +--> one action: commit defined consequence
        |
        +--> multiple actions: deterministic or stochastic selection may occur inside set
        |
        v
state transition + audit receipt
```

Required properties:

1. Estimator output must identify what it measures and how it was produced when it materially affects a consequential transition.
2. Estimator confidence must not be reused as mutation authority.
3. A blocked action must remain blocked regardless of how confidently a probabilistic component proposes it.
4. Policy outcome and estimator output must remain separately inspectable.
5. Consequential commits must bind to the policy version and state snapshot under which they were authorized.
6. If required authority inputs cannot be reconstructed for a high-consequence action, the system should abstain, block, or escalate rather than infer permission.

## Boundary table

| Question | Correct layer |
|---|---|
| What is this object? | Identity substrate |
| Why do we believe this claim? | Evidence and provenance |
| How likely, relevant, stale, or persistent does it appear? | Saturation / epistemic routing |
| Is the proposed transition legal from this state? | Lifecycle state machine |
| Can the memory change? | PAMA governance |
| Can this become durable? | Certification and crystallization |
| How does the agent use it now? | Runtime memory space |
| What is true or hypothesized about a codebase? | Domain reality graph |

## Anti-collapse rules

1. Do not collapse identity into memory.
2. Do not collapse saturation into truth.
3. Do not collapse confidence into certification.
4. Do not collapse runtime utility into permanence.
5. Do not collapse mutation capability into mutation authority.
6. Do not collapse probabilistic inference into permission.
7. Do not collapse deterministic execution into correctness.
8. Do not collapse policy outcome and estimator output into one opaque score.
9. Do not collapse the Cognitive Mesh into a universal truth store or implementation-specific ontology.
10. Do not collapse module identity, component identity, and capability identity.
