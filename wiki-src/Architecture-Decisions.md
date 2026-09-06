# Architecture Decisions

Agent Memory uses Architecture Decision Records (ADRs) to preserve why important doctrine choices exist and when they should be reconsidered.

## Status semantics

ADR status describes **doctrine maturity**, not runtime implementation completeness.

| Status | Meaning |
|---|---|
| Proposed | The decision is under active evaluation and has not yet met its acceptance bar. |
| Accepted | The decision is canonical doctrine for this repository. |
| Superseded | A later decision replaces it while preserving history. |
| Rejected | The proposed direction was considered and intentionally not adopted. |

An Accepted ADR does **not** mean every mapped product implements it. That would be a convenient fiction, but still a fiction.

## Current state

- **ADR-001 through ADR-020:** Accepted
- **ADR-021:** Proposed, portable memory-governance evidence boundary
- **ADR-022:** Accepted, memory isolation domains and controlled boundary crossing
- **ADR-023:** Proposed, correction as supersession rather than deletion
- **ADR-024:** Accepted, pre-write coordination for shared-memory mutation
- **ADR-025:** Proposed, explicit authority for durable decision overwrite
- **ADR-026:** Proposed, origin is provenance rather than evidentiary authority
- **ADR-027:** Proposed, governed re-admission for rejected values
- **ADR-028:** Accepted, language-neutral core with optional implementation/interoperability profiles
- **ADR-029:** Proposed, Governance Context Projection as derived context rather than authority
- **ADR-030:** Accepted, versioned compatibility/currentness for temporal-policy projections
- **ADR-031:** Accepted, deterministic temporal commitments with separate evidence and authority layers
- **ADR-032:** Accepted, governed mutable memory structure with deterministic or explicit-human canonical structural authority
- **ADR-033:** Accepted, independent capability maturity and deterministic component/capability composition
- **ADR-034:** Accepted, procedural/skill memory as retained state rather than standing execution authority

Each Proposed ADR has its own acceptance evidence. A green implementation slice does not silently accept a doctrine decision whose ADR demands broader evidence.

## Important decision families

Rather than memorizing thirty-four filenames, think in decision families.

### Identity and provenance

Decisions about exact references, source evidence, derivation, durable traceability, and source-neutral evidence scrutiny.

### Lifecycle and persistence

Decisions about decay, consolidation, retention, correction, supersession, re-admission, forgetting, and inherited state.

### Governance and PAMA

Decisions about mutation authority, consequence classes, certification, and separating learned pressure from permission.

ADR-024 adds the shared-write coordination boundary:

```text
shared write intent
  -> pre-write claim / lease / equivalent coordination
  -> current-state and conflict validation
  -> PAMA authority evaluation
  -> durable mutation or refusal
```

A valid claim gives a writer the bounded opportunity to attempt a shared mutation. It does not grant permission to make that mutation durable.

### Composition and security

ADR-033 establishes the component/capability composition model:

```text
component identity != capability identity

required capability + maturity/posture
  -> deterministic compatibility resolution
  -> selected/composed implementation
```

A component may expose several independently matured capabilities, and several components may expose the same capability. Hidden registration order is not an acceptable routing policy. Ambiguous overlap must be resolved deterministically or fail explicitly, and fallback cannot silently lower maturity, isolation, currentness, deletion, failure, or authority guarantees.

Capability routing remains separate from PAMA mutation authority and governed recall admission.

### Governed uncertainty and mutable structure

ADR-020 establishes the general governed-consequence boundary around uncertain, learned, heuristic, or probabilistic discovery.

ADR-032 adds a stronger rule for canonical structural mutation:

```text
probabilistic / learned structural discovery
        -> proposal
        -> deterministic impact + authority classification
        -> bounded autonomous commit OR explicit human decision
```

Memory shape may adapt. A probabilistic system may discover and recommend a better shape, but it cannot be the authority that commits canonical structural semantics. Bounded rebuild-only and additive changes may be autonomous under versioned deterministic policy. Semantic migrations, destructive changes, scope/isolation widening, and authority-bearing structure require explicit authority unless a future Accepted ADR defines an exact narrower delegation.

Current PAMA 1.2 remains conservatively review-first for `domain_schema_mutation` until narrower implementation evidence is earned.

See **[Governed Uncertainty](Governed-Uncertainty)** and **[Mutable Memory Fabric](Mutable-Memory-Fabric)**.

### Procedural memory and skills

ADR-034 establishes:

```text
skill retained
  != skill retrieved
  != skill admitted / activated
  != action authorized
  != execution evidence
```

A remembered procedure may shape a plan after governed recall admission. It does not become standing permission to execute shell commands, repository changes, external calls, deployments, payments, or other consequential actions.

The accepted #295 reference slice proves proposal without mutation, governed promotion, cross-session plan influence, separate action-governance/execution evidence, correction/supersession, exact-content approval binding, stale replay refusal, cross-project refusal, revocation/residue honesty, and metamemory refusal.

The approval path binds the exact proposal, procedure version, content SHA-256, and state snapshot. Approval for one procedure cannot be reused to commit a substituted payload.

ADR-034 also distinguishes ordinary task skills from **metamemory**. A remembered routine for changing how Agent Memory extracts, consolidates, routes, retrieves, ranks, prunes, archives, or forgets memory is a memory-management/profile-change proposal. It remains subject to PAMA and ADR-032 rather than applying itself because it was recalled.

The evidence remains bounded to the reference runtime. It does not claim process-restart durability, a universal skill format, or universal production conformance.

See the canonical runtime evidence at `docs/programs/runtime-evidence/procedural-memory.md` in the repository.

### Implementation portability

ADR-028 separates normative doctrine from implementation language and optional ecosystem profiles:

```text
normative doctrine / schemas / fixtures
        !=
reference implementation language
        !=
optional implementation or interoperability profile
```

Python, Rust, UOR, AGT, MCP, and future ecosystems may participate without becoming the definition of Agent Memory.

### Interoperability and governance projection

ADR-021 and ADR-029 preserve two different directions across an external-governance boundary:

```text
ADR-029
memory-derived context
  -> external governance decision

ADR-021
Agent Memory decision / execution evidence
  -> external verifier / attestation system
```

ADR-029 keeps Governance Context Projection vendor-neutral and non-authoritative. ADR-021 keeps external evidence verification distinct from memory-semantic authority.

See **[Governance Projection](Governance-Projection)**.

### Temporal policy and temporal commitments

ADR-030 requires versioned compatibility/currentness before memory-derived context is treated as current input for a temporal or authorization consumer.

ADR-031 establishes deterministic temporal commitments while keeping historical identity, evidence, lifecycle currentness, and PAMA authority distinct.

See **[Temporal Commitments](Cryptographic-Temporal-Commitments)**.

## When an ADR should change

An accepted decision should be revisited when there is:

- contradictory research with material architectural consequences;
- a reproducible implementation failure;
- a security or privacy failure mode the decision does not contain;
- a semantic incompatibility discovered in schemas or composition;
- evidence that a simpler architecture satisfies the same constraints;
- new interoperability requirements that invalidate the original boundary.

Preference alone is not enough. Neither is “the new framework has a nicer README.”

## Proposing a decision change

A strong proposal states:

1. current decision;
2. new evidence or failure mode;
3. proposed replacement or clarification;
4. affected docs, schemas, fixtures, and implementations;
5. compatibility impact;
6. falsification/rejection criteria.

Use the **Doctrine or architecture proposal** issue form for new ADR work.

## Canonical source

ADR index: https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/docs/adr

The canonical ADR files, not this Wiki summary, determine current decision text and status.

## Next

- **[Governed Uncertainty](Governed-Uncertainty)** for governed consequences around probabilistic discovery
- **[Mutable Memory Fabric](Mutable-Memory-Fabric)** for ADR-032/ADR-033, configurable components/capabilities, and structural adaptation
- **[Governance Projection](Governance-Projection)** for ADR-029 and governance-consumer interoperability
- **[Temporal Commitments](Cryptographic-Temporal-Commitments)** for ADR-031
- **[Aligned Projects & Intellectual Lineage](Aligned-Projects-and-Intellectual-Lineage)** for current external governance comparators
- **[Contributing](Contributing)** for the change process
