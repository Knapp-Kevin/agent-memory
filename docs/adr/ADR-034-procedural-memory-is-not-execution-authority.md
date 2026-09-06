# ADR-034: Procedural Memory Is Retained State, Not Execution Authority

## Status

Accepted

## Context

Agent Memory doctrine already states:

```text
memory is not procedure
procedure is not permission
permission is not governance
```

The external memory frontier makes this boundary operationally important. Agent systems increasingly retain reusable procedures, playbooks, tool-use routines, skills, scripts, resources, condensed experience, or learned strategies that can materially change later behavior. The representation is not the stable architectural question.

The stable question is whether storing or recalling a procedure silently grants authority to apply or execute it.

It must not.

A related frontier is **metamemory**: retained or learned procedures about how the memory system itself should extract, consolidate, route, retrieve, rank, prune, archive, or forget memory. Metamemory has a higher consequence surface because applying it changes future memory formation and recall.

Existing doctrine supplies the controlling boundaries:

- ADR-020 separates learned/probabilistic proposals from governed consequences;
- ADR-022 governs cross-scope memory movement;
- ADR-028 preserves representation and implementation portability;
- ADR-030 separates current compatible projections from historical/serializable state;
- ADR-032 governs structural adaptation and forbids probabilistic self-authorization;
- ADR-033 establishes capability-oriented composition and deterministic routing floors;
- PAMA separates target class, operation, downstream authority, risk, and review requirements.

## Decision

Agent Memory treats procedural/skill memory as **governed retained state with separate retrieval, admission/activation, action-authority, and execution boundaries**.

> **A remembered procedure may influence a plan after governed admission. It does not, by being remembered, grant permission to perform the procedure's actions.**

The architecture separates at least:

```text
skill retention
  store / version / scope / provenance the procedure
        |
        v
skill retrieval
  produce the procedure as a memory candidate
        |
        v
skill admission / activation
  permit the current procedure to influence plan/context
        |
        v
runtime action proposal
  identify an action the agent wants to perform
        |
        v
action governance where applicable
  permit / review / block the exact action
        |
        v
execution evidence
```

No earlier stage implies a later stage.

## Procedural-memory semantic boundary

A procedural-memory implementation MAY use Markdown, JSON, files, database records, code bundles, learned policies, or another representation.

At the Agent Memory boundary, a durable procedure MUST preserve or make reconstructable enough information to govern at least:

- logical procedure identity;
- version and currentness;
- scope and isolation domain;
- purpose/applicability;
- exact procedure content or integrity-bound reference;
- provenance/source evidence;
- validation evidence where available;
- constraints, hazards, or prerequisites where applicable;
- supersession/correction lineage;
- activation posture.

Exact field names and serialization are implementation/profile choices rather than canonical doctrine.

## Promotion

A procedure may originate from human instruction, documentation, episodic experience, consolidation/synthesis, external skill catalogs, another governed memory domain, or a learned skill-generation system.

Origin establishes provenance, not authority.

Promotion into durable procedural memory is a memory mutation and MUST pass the normal PAMA/currentness/scope path. Learned confidence or expected utility cannot authorize the durable consequence.

A proposal MUST NOT mutate durable procedural state merely because it exists.

## Exact payload and approval binding

Where a procedural mutation requires review or approval, the authorization MUST bind the exact payload or integrity-bound reference, proposal identity, and current-state snapshot sufficiently to prevent approval substitution.

```text
approval for skill X @ state N
        !=
approval for modified skill Y @ state N
        !=
approval for X after state N has changed
```

A generic `approved=true`, reused approval reference, stale cached approval, or approval for a predecessor version is not sufficient standing authority for a different payload or state.

## Retrieval and admission

Procedural retrieval produces a **candidate procedure**. Before the procedure may influence the active plan/context, governed admission must apply relevant currentness, supersession, scope/isolation, purpose/applicability, rejection/readmission, provenance, sensitivity, compatibility, and validation constraints.

A high similarity score, graph reachability, trigger match, learned router choice, or component-selection result cannot bypass admission.

Superseded or tombstoned procedures may remain retrievable for reconstruction while being refused as current guidance.

## Execution remains outside memory authority

Once admitted, procedural memory may shape planning and produce candidate runtime actions. Actual tool/action authority remains with Agent Runtime and/or Agent Governance as applicable.

A stored skill containing a shell command, HTTP request, repository mutation, deployment step, payment action, or destructive operation does not inherit execution authority from its retention, prior validation, prior successful use, or prior approval in another state.

The identities for memory proposal, PAMA decision, memory commit receipt, recall/admission, action proposal, action-governance decision, and execution evidence SHOULD remain distinguishable and correlatable rather than being collapsed into one reusable "approved skill" token.

## Correction and supersession

Procedural memories are versioned retained state.

```text
old current procedure
  -> correction/successor proposal
  -> current-state + authority evaluation
  -> exact approval when required
  -> new current procedure
  -> old procedure retained as superseded history where required
```

A superseded procedure MUST NOT regain current influence merely because retrieval ranks it highly. Stale proposals and approvals MUST fail after the governed state advances.

## Cross-scope transfer

A useful procedure in one project, tenant, environment, or toolchain does not automatically transfer to another. Cross-scope procedural reuse is governed by ADR-022 and may require rescoping, compatibility validation, renewed authority, or new evidence.

The same text in two domains does not imply the same applicability or authority.

## Procedure plus executable artifacts

A skill may reference scripts or resources. Retention and integrity do not imply trust or execution permission:

```text
artifact retained
  != artifact trusted
  != artifact executable
  != execution authorized
```

Supply-chain validation, sandboxing, external governance, and execution evidence remain separate concerns.

## Metamemory is a stricter profile

A procedure for performing a user task is ordinary procedural memory.

A procedure that changes how Agent Memory forms, consolidates, routes, retrieves, ranks, prunes, archives, or forgets memory is a metamemory/profile-change proposal.

The safe path is:

```text
learned metamemory insight
  -> retained/proposed management change
  -> deterministic compatibility / impact / regression evidence
  -> PAMA / ADR-032 classification
  -> bounded authorized commit OR explicit review
```

A recalled metamemory artifact MUST NOT silently modify the active memory profile. This ADR creates no parallel metamemory authority system.

## Learned and self-evolving skills

Learned systems MAY propose new procedures, refinements, applicability triggers, retirement candidates, or metamemory changes. They MAY provide utility estimates or validation evidence.

They do not self-authorize durable promotion, semantic correction, cross-scope transfer, retirement/deletion, active profile mutation, or action execution.

## Capability composition

Procedural memory is a capability under ADR-033 rather than a required dedicated product or repository.

A component may declare `procedural_skill_memory` alongside other capabilities. Multiple implementations may satisfy the capability. Selection/composition is deterministic and maturity-aware, and provider choice does not become mutation authority or recall permission.

The first reference profile intentionally uses a simple inspectable artifact and the existing governed adapter instead of creating a specialized skill database.

## Acceptance evidence

ADR-034 was promoted only after the #295 reference vertical slice exercised the decision end to end and the repository-wide doctrine validator passed at the implementation head.

The executable evidence surfaces are:

- `reference/agentmem_ref/contracts/capabilities.py` — independent capability maturity and deterministic provider resolution;
- `schemas/component-capability-profile.schema.json` — machine-readable capability declaration profile;
- `reference/agentmem_ref/memory/procedural_memory.py` — procedural retention, exact approval binding, activation, action separation, revocation, and metamemory boundary;
- `reference/tests/test_component_capabilities.py` — maturity, ambiguity, preference, and no-downgrade tests;
- `reference/tests/test_procedural_memory.py` — positive and adversarial procedural-memory paths;
- `reference/run_procedural_memory.py` — deterministic reconstructable evidence harness;
- `.github/workflows/procedural-memory-evidence.yml` — exact-head focused evidence workflow;
- `docs/programs/runtime-evidence/procedural-memory.md` — evidence map and claim boundary.

The evidence demonstrates:

1. procedure proposal does not mutate durable state;
2. governed promotion creates a versioned, scoped, integrity-bound procedure;
3. later-session governed recall admits the current procedure and changes the plan;
4. admission does not execute actions;
5. an action requires a separately bound governance decision before execution evidence can be recorded;
6. correction requires review under the current PAMA profile and supersedes rather than erases the prior version;
7. approval is bound to the exact procedure payload, proposal, version, and state, and a substituted payload is refused;
8. an unbound review flag/reference cannot manufacture approval;
9. stale proposal replay fails after state advances;
10. a high-relevance foreign-project candidate is not admitted;
11. revocation/tombstoning removes active influence while retained recovery content/residue is reported honestly;
12. retained metamemory cannot apply itself through ordinary skill activation and instead yields a separate M5/A5 `policy_mutation` proposal;
13. memory, approval, action-governance, and execution identities remain distinct;
14. capability routing remains non-authoritative.

## Evidence boundary

Acceptance is a doctrine-maturity decision, not a universal production-conformance claim.

The reference proof is deliberately bounded:

- it proves cross-session reuse inside one governed reference runtime;
- it does **not** prove process-restart durability, which remains separate work;
- it uses a reference in-memory procedural representation rather than selecting a universal skill store;
- it models a separate action-governance/execution boundary without claiming a specific external governance product or real external tool execution;
- it does not make Markdown, the reference serialization, EvolveAI, CodeGenome, or any external skill format canonical;
- it does not grant `reference_qualified` maturity to first-party components merely because example declarations exist.

## Consequences

### Positive

- reusable competence can persist across sessions without becoming standing authority;
- procedural state gains scope, currentness, correction, supersession, provenance, and revocation semantics;
- exact approval binding prevents "approved X, committed Y" substitution;
- human-readable, external, learned, or first-party skill stores can fit behind one semantic boundary;
- metamemory evolution has a governed path under existing PAMA/ADR-032 rules;
- the capability provides a concrete workload for ADR-033 composition.

### Negative

- a skill requires more lifecycle/evidence than a convenient prompt snippet;
- runtime integrations must preserve an explicit activation/action-authority boundary;
- external skill stores may need adapters for Agent Memory scope/currentness/provenance;
- self-evolving memory systems cannot directly apply every learned optimization.

## Alternatives considered

### Treat skills as ordinary facts

Rejected. Procedures have applicability, activation, validation, and downstream action consequences that ordinary facts do not.

### Treat a recalled skill as authorized execution

Rejected. This collapses memory, procedure, permission, and governance into a replayable standing-authority artifact.

### Make one skill format canonical

Rejected. Representation remains a capability/profile concern.

### Put procedural memory entirely in Agent Runtime

Rejected. Durable cross-session identity, provenance, scope, correction, supersession, deletion/revocation, and recall are memory responsibilities even though execution is not.

### Create a proprietary skill-memory repository immediately

Rejected. The semantics are proven without another subsystem. A dedicated implementation should be created only if later conformance evidence establishes a capability/substrate gap that existing first-party components, ordinary stores, or external adapters cannot satisfy cleanly.

## Relationship to other ADRs

- ADR-020 governs learned/probabilistic skill discovery and proposal.
- ADR-022 governs skill scope and cross-domain transfer.
- ADR-023, if accepted, further generalizes correction-as-supersession doctrine.
- ADR-025, if accepted, applies when procedural state carries durable decision-like overwrite consequences.
- ADR-027, if accepted, applies to rejected/unsafe procedures attempting re-entry.
- ADR-028 preserves representation/language portability.
- ADR-030 governs compatible/current projections consumed by temporal or authorization systems.
- ADR-032 governs metamemory and structural/profile mutation.
- ADR-033 governs capability declaration, maturity, and deterministic composition.

This ADR adds no exception to PAMA or existing authority rules.
