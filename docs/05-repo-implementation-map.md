# Repo Implementation Map

## Purpose

This map assigns related repositories or systems to implementation roles in the Agent Memory architecture while keeping **native doctrine**, **aligned foundations**, and external/product-specific implementations separate.

The goal is to prevent repo-specific terminology from fragmenting the doctrine and to prevent implementations from collapsing probabilistic estimation, governance, and committed state mutation into one opaque subsystem.

**Agent Memory owns the doctrine. PAMA is part of that doctrine.** PAMA is not listed as an external repository dependency simply because implementations must consume its authority contract.

Named implementation systems appear only when they add specific architecture or conformance value.

An external project may materially inform Agent Memory without owning an implementation role. See [`40-aligned-projects-and-intellectual-lineage.md`](40-aligned-projects-and-intellectual-lineage.md).

## Native doctrine components

### PAMA

**Proportional Adaptive Mutation Authority (PAMA)** is native Agent Memory governance doctrine authored by Kevin R. Knapp.

Canonical doctrine:

- [`pama/README.md`](pama/README.md)
- [`04-governance-and-pama.md`](04-governance-and-pama.md)
- [`33-pama-decision-table.md`](33-pama-decision-table.md)
- [`adr/ADR-004-pama-controls-mutation-authority.md`](adr/ADR-004-pama-controls-mutation-authority.md)

PAMA owns the **authority semantics**, not a particular repository or deployment location. A runtime may implement PAMA as a dedicated service, policy module, library, or enforcement boundary, provided the separation remains explicit and auditable.

### PAMA implementation contract

A PAMA implementation must preserve:

- M0-M5 mutation target classes;
- lifecycle strength as separate from authority;
- A0-A5 downstream authority ceilings;
- explicit operation classification;
- consequence-proportional handling;
- no self-approved privilege expansion;
- evidence and charter binding;
- deterministic or formally bounded authority envelopes for committed inputs;
- receipts reconstructing permitted, prohibited, selected, and committed consequences.

## Aligned foundations

### UOR Foundation / UOR Framework

**Relationship:** intellectual lineage / conceptually aligned foundation / optional exact-identity mechanism.

Work from the [UOR Foundation](https://github.com/UOR-Foundation/UOR-Framework) materially informed Agent Memory's separation between deterministic object identity and memory lifecycle/governance.

Agent Memory adopts the architectural boundary, not a compulsory implementation dependency:

```text
exact identity
    !=
lifecycle state
    !=
relevance
    !=
authority
```

When UOR is used, it is a strong candidate for deterministic addressability, exact object resolution, and content identity. A conforming implementation may use another exact identity mechanism if it preserves the same boundary.

UOR does **not** become the owner of Agent Memory lifecycle policy, saturation policy, mutation authority, recall governance, deletion semantics, or certification by virtue of that influence.

See [`ADR-001`](adr/ADR-001-uor-is-identity-not-memory.md) and [`40-aligned-projects-and-intellectual-lineage.md`](40-aligned-projects-and-intellectual-lineage.md).

## Related implementation map

| System | Canonical implementation role | Primary responsibility | Governed-uncertainty posture |
|---|---|---|---|
| EvolveAI | Memory metabolism prototype | lifecycle orchestration, decay, tier routing, crystallization prototype | probabilistic/heuristic proposals allowed; lifecycle commit remains governed |
| CodeGenome | Code reality graph | code artifact graph, overlays, confidence fusion, provenance, impact traversal | inferred relations preserve confidence, estimator provenance, and disagreement |
| COREFORGE Vault | Runtime memory container | encrypted local memory, graph recall, context windows, governed storage | probabilistic retrieval may generate candidates; scope and mutation boundaries remain enforced |
| Neurospace | Operational memory space | agent-facing memory traversal and use within COREFORGE | learned ranking may operate only inside recall-time policy |
| GG-CORE | Local inference compute substrate — **not a memory role** | contained offline model execution, consumed by COREFORGE behind a feature gate | performs model compute only; holds no memory, policy, or authority responsibility |
| FailSafe | Governance enforcement implementation candidate | evidence capture, approval gates, policy checks, release/session audit | can enforce policy version, estimator context, action set, and consequence receipt |
| Arbiter | Product policy enforcement candidate | authorization, rate limits, audit logging, action boundaries | can enforce prohibited and permitted actions independently of model confidence |
| Shadow Genome | Negative memory substrate | failure patterns, blocked behaviors, prior harm avoidance | failure inference may be probabilistic; guardrail promotion preserves evidence and authority |

This table is an implementation map, not a source-of-doctrine or acknowledgement table. Absence from the table does not mean a project is unimportant; it means it has not earned a distinct implementation role in this architecture map.

## Identity mechanism contract

Agent Memory requires exact identity semantics where identity is consequential. It does not require one repository to supply them.

An identity mechanism should provide stable references that probabilistic layers can reason about without changing the identity of the underlying object. Exact reference resolution is a deterministic substrate concern, not a confidence-weighted guess.

If UOR is selected, UOR-specific adapters may expose its addressability and resolution semantics. If another mechanism is selected, the implementation must preserve the same doctrine boundary.

## EvolveAI

### Canonical owner of

- autopoietic memory theory prototype
- memory metabolism
- L1 / L2 / L3 tier model
- REM synthesis
- CMHL decay engine
- lifecycle orchestration

### Should import from this doctrine

- PAMA authority for promotion and mutation
- calibration protocol for saturation thresholds
- trap-class conformance tests
- certification gate before durable crystallization
- transition proposal must remain separate from transition commit
- estimator uncertainty, version, and calibration scope must remain inspectable
- threshold jitter and estimator disagreement require explicit handling

### Governed-uncertainty contract

EvolveAI may use learned or heuristic signals to propose decay, retention, consolidation, or promotion. Those signals must not self-authorize irreversible or canonical state changes.

## CodeGenome

### Canonical owner of

- code artifact graph
- BLAKE3 node identity for code objects
- observer separation
- confidence fusion
- provenance and evidence bundles
- governed code reality queries

### Should import from this doctrine

- confidence is evidence support, not lifecycle permanence
- code graph nodes can become memory units when consumed by agents
- memory lifecycle state should preserve graph provenance
- inferred edges should identify estimator/method version when material to downstream decisions
- confidence fusion should preserve material estimator disagreement rather than averaging it into invisibility

### Governed-uncertainty contract

Exact syntax or content-addressed facts may be deterministic while semantic overlays, entity resolution, impact estimates, and relation confidence remain probabilistic. Consumers must be able to tell which is which.

## COREFORGE Vault / Neurospace

### Canonical owner of

- local-first memory storage
- encrypted Vault memory
- runtime graph recall
- RAG and context windows
- product-level memory UX

### Should import from this doctrine

- memory write boundary must enforce PAMA
- crystallization should be ledgered
- runtime usefulness must not imply permanence
- user-visible correction and dispute flows are required for durable memory
- retrieval ranking occurs before recall-time scope, tenancy, sensitivity, and certification filters
- stochastic strategy selection may occur only among policy-permitted recall or write actions

### Governed-uncertainty contract

High semantic relevance must not override privacy, tenancy, scope, dispute state, or policy. Candidate generation may be probabilistic; admission into active context remains governed.

### Inspection evidence

Direct inspection of the private COREFORGE repository on 2026-08-11 (default branch, commit `48ee0ca`) confirmed this role is implemented as code, not only claimed: a `vault/` module carrying a lifecycle store, a mutation contract and mutation gate producing an approved/pending-review/vetoed envelope, Neurospace assembler/inspector/mutator, context broker/engine/packet, a knowledge graph, UOR-style references with memory domains, lineage records, and a RAG engine. The Vault also consumes EvolveAI and CodeGenome through in-tree memory-provider seams, which makes the proposer-versus-committer split described in [`39-implementation-ownership-map.md`](39-implementation-ownership-map.md) a live integration rather than a diagram.

Two boundaries from the same inspection. No Agent Memory doctrine backlink exists in COREFORGE — occurrences of `agent_memory` there are local identifier names, not references to this architecture. And GG-CORE is COREFORGE's *compute* dependency, not its memory successor: GG-CORE's own architecture documents list `vault/` among forbidden modules, and its runtime promise is model execution only. The role above stays with COREFORGE Vault.

This inspection verifies **existence**, not conformance. Status remains governed by the resolution path in `39-implementation-ownership-map.md`.

## PAMA enforcement boundary

PAMA is not another external system in this map. It is the native authority contract every mutating implementation must satisfy.

A compliant runtime should expose where:

1. a mutation target is classified M0-M5;
2. lifecycle strength is read or proposed;
3. the requested operation is classified;
4. requested downstream authority A0-A5 is declared;
5. evidence, actor charter, scope, and reversibility are bound;
6. policy produces the permitted/prohibited/review-required envelope;
7. optional deterministic or stochastic selection occurs only inside the permitted set; and
8. the committed consequence is receipted.

A runtime may host the PAMA implementation. It may not absorb the semantic boundary so thoroughly that authority becomes indistinguishable from its estimator or storage layer.

## FailSafe / Arbiter

### Candidate implementation value

- policy enforcement
- evidence capture
- human approval gates
- audit trails
- action governance

### Should import from this doctrine

- memory mutation must be treated as a governed action
- durable memory changes require evidence and rollback paths
- approval workflows should bind to lifecycle transitions
- receipts should bind estimator versions, policy version, permitted action set, selected action, and before/after state when relevant
- high-consequence actions should fail closed or escalate when required governance state cannot be reconstructed

FailSafe or Arbiter may be useful implementation mappings for parts of PAMA. They are not the origin or owner of PAMA doctrine.

## Shadow Genome

### Canonical owner of

- negative memory and failure patterns
- recurrence avoidance
- blocked behaviors and learned caution

### Should import from this doctrine

- failure inference must preserve causal evidence and applicability scope
- a high-confidence negative pattern must not become a global prohibition without governed promotion
- guardrails derived from failure memory should retain provenance to the failures that justified them

## Durable decision memory

Decision continuity, drift, rationale preservation, supersession, and durable decision recall are defined as **Agent Memory capabilities** rather than attributed to an adjacent product.

See [`profiles/durable-decision-memory-profile.md`](profiles/durable-decision-memory-profile.md).

A product or implementation should be named here only if it provides specific implementation evidence against that profile.

## Cross-repo control contract

Implementations should identify which responsibilities they own using these control classes:

```text
DETERMINISTIC_SUBSTRATE
exact identity, schema, authorization primitives, state validity, committed receipts

PROBABILISTIC_EPISTEMICS
confidence, relevance, trust, contradiction, semantic similarity, staleness, risk estimates

GOVERNANCE_ENVELOPE
policy-defined permitted / prohibited / review-required outcomes

BOUNDED_ACTION_SELECTION
optional deterministic or stochastic choice among already-permitted actions

COMMITTED_CONSEQUENCE
state mutation, ledger record, scope change, certification, deletion, or other durable effect
```

A repo may own more than one implementation class, but it must expose the boundary between them.

## Required implementation evidence

A repo claiming governed-uncertainty alignment should be able to point to:

1. where probabilistic or learned estimates are produced;
2. how those estimates identify their method/version and calibration scope;
3. where PAMA policy converts estimates into authority outcomes;
4. where prohibited actions are enforced;
5. where the permitted action set is represented, if more than one action can follow;
6. where committed state changes are ledgered;
7. how estimator drift differs from policy change;
8. how the implementation behaves when required authority inputs are missing; and
9. how M0-M5 target class and A0-A5 authority ceilings are represented or equivalently enforced.

## Source of truth policy

This repo owns the doctrine, including PAMA.

Other repos may own implementations, experiments, and product behavior, but should reference this doctrine for shared terms and boundaries.

No external repository is required to make Agent Memory doctrine legitimate or canonical.

## Implementation labels

Suggested labels for cross-repo issues:

```text
agent-memory
memory-doctrine
pama
governed-memory
governed-uncertainty
crystallization
saturation-calibration
neurospace
uor-identity
code-reality-graph
conformance
```

## Required cross-repo backlinks

Each implementation repo should eventually include a short doctrine pointer:

```text
This implementation follows the Agent Memory doctrine in MythologIQ-Labs-LLC/agent-memory.
```

And should link to the specific docs it conforms to.
