# ADR-029: Governance Projection Is Derived Context, Not Authority

## Status

Proposed

## Context

Agent Memory can materially improve agent-governance decisions by preserving context that ordinary approval logs discard: prior rationale, material conditions, authority state, negative precedent, temporal validity, later outcomes, corrections, revocations, and incidents.

That opportunity creates an architectural risk. If the canonical memory model is reshaped around one governance consumer, Agent Memory stops being a general memory architecture and becomes an accidental extension of that consumer's policy API.

The repository already separates canonical memory semantics from product integrations in [`../11-component-architecture.md`](../11-component-architecture.md), defines typed seams in [`../34-adapter-contracts.md`](../34-adapter-contracts.md), and proposes an outbound portable evidence boundary in ADR-021. What is still missing is the complementary inbound/use-case boundary for governance systems that want memory-derived context when evaluating a current action.

ADR-028 separately proposes a language-neutral normative core with optional implementation profiles. ADR-029 complements that decision: the Governance Context Projection is itself vendor-neutral and must not make any governance consumer, implementation language, or external runtime normative merely because an adapter exists.

## Decision candidate

Adopt a three-layer ownership model:

```text
Agent Memory core
  canonical governed memory primitives
        |
        v
Governance Projection
  vendor-neutral derived context
        |
        v
Consumer-specific adapter
  DashClaw / AGT-ACS / other policy or enforcement runtime
```

### Agent Memory core owns

Core remains responsible for generally useful memory semantics, including where applicable:

- stable identity and target references
- provenance and derivation
- evidence and source class
- scope and isolation domain
- lifecycle state
- temporal validity
- correction, supersession, revocation, and dispute state
- actor and authority context when material to the remembered event
- rationale or explanation, preserving whether it was observed, inferred, or policy-generated
- outcome, consequence, incident, and rollback references
- confidence, uncertainty, and estimator provenance
- sensitivity and minimization constraints

These concepts belong in core only because they are generally meaningful to memory, not because a governance adapter wants them.

### Governance Projection owns

Governance Projection is a derived, reconstructable view that selects and minimally shapes canonical memory for governance consumers.

It MAY expose concepts such as:

- relevant precedent references
- precedent polarity such as supportive, cautionary, or contradictory
- material conditions that held in a prior episode
- material differences detected against current context
- validity and freshness state
- outcome/incident evidence
- authority context references
- uncertainty and derivation metadata

It MUST preserve provenance back to canonical memory/evidence and MUST remain reconstructable from canonical state plus declared derivation logic.

It MUST NOT become the sole authoritative copy of the underlying memory.

### Consumer-specific adapter owns

A consumer adapter owns translation from the vendor-neutral projection into the consumer's own domain, including:

- consumer API and version compatibility
- risk or policy-specific weighting
- verdict vocabulary mapping
- approval user experience
- retries, timeouts, and consumer-specific failure behavior
- any DashClaw-, AGT/ACS-, OPA-, Cedar-, or other product-specific fields

Consumer semantics do not become Agent Memory semantics merely because an adapter needs them.

## Core invariant

> **Adapter convenience must not redefine canonical memory semantics.**

For any field or concept requested by an integration, ask:

1. Is it a generally useful property of memory, evidence, scope, lifecycle, authority context, or outcome? If yes, it may justify the smallest reusable core primitive.
2. Is it useful mainly to one consumer or policy vocabulary? If yes, keep it in the projection or consumer adapter.
3. Does the integration reveal that core cannot express a genuinely general concept without distortion? If yes, add only that general primitive, not the consumer's full domain model.

## Governance projection does not decide

The projection is evidence and context for a governance decision. It is not itself permission, certification, a standing grant, or a final policy verdict.

Short form:

```text
precedent -> context / evidence
precedent != permission
projection -> decision input
projection != decision authority
```

A projection MAY report that six prior approvals shared conditions A/B/C and that the current action differs on C. It MUST NOT encode `therefore_allow=true` as a canonical Agent Memory consequence.

A downstream governance system remains responsible for deciding what that context is allowed to influence.

## Repetition does not manufacture authority

Repeated approvals may be remembered because the episodes have durable value. They may support a proposal for a narrow standing policy or grant.

They do not create that authority by repetition.

This ADR inherits ADR-002, ADR-003, ADR-009, ADR-020, and ADR-026:

- access/repetition is not truth;
- repetition is not certification;
- derived copies are not independent corroboration;
- uncertain discovery must cross deterministic governance before consequence;
- provenance does not confer evidentiary privilege.

A policy-generated allow MUST NOT recursively count as a new independent human approval unless its provenance truthfully establishes that independent adjudication occurred.

## Negative precedent is first-class

Projection must be able to preserve negative and cautionary context, including:

- prior denial
- revocation
- correction
- dispute
- incident
- rollback
- execution despite a block or review requirement, when such evidence exists

Positive frequency MUST NOT erase a materially relevant negative precedent merely because approvals are more numerous.

## Similarity boundary

Exact identity and deterministic condition comparison SHOULD be implemented first.

Semantic or contextual similarity MAY later retrieve candidate precedent, but a probabilistic matcher MUST NOT independently authorize a governance consequence.

```text
probabilistic similarity
  -> precedent candidate
  -> deterministic material-condition / policy evaluation
  -> governance consequence
```

## Privacy and minimization

Governance Projection SHOULD export references, structured characteristics, scoped fingerprints, and bounded rationale metadata rather than raw sensitive memory content whenever those are sufficient.

A consumer's desire for richer context does not override Agent Memory sensitivity, scope, retention, or minimization constraints.

## Relationship to ADR-021

ADR-021 concerns portable evidence flowing outward so another system can verify or correlate an Agent Memory governance/execution result.

ADR-029 concerns memory-derived context flowing toward a governance consumer so that consumer can make a better current decision.

They are complementary:

```text
memory context -> Governance Projection -> external decision/enforcement
external execution evidence -> portable evidence boundary -> Agent Memory audit
```

Neither direction grants the external system ownership of Agent Memory semantics.

## Relationship to ADR-028

ADR-028 keeps normative Agent Memory language-neutral and places external ecosystems behind optional implementation/interoperability profiles.

ADR-029 applies the same anti-capture principle specifically to governance consumers:

```text
language-neutral Agent Memory core
        |
        v
vendor-neutral Governance Context Projection
        |
        v
optional consumer-specific adapter
```

A DashClaw, AGT/ACS, OPA, Cedar, or future adapter may prove usefulness without becoming normative doctrine.

## Relationship to PAMA

PAMA remains Agent Memory's memory-specific mutation and downstream-authority boundary.

Governance Projection may carry PAMA-related context or authority references when relevant, but it does not reproduce PAMA as a general agent-policy engine.

An external governance system may further restrict an action. It must not use a projection to reinterpret a PAMA denial as permission for the underlying memory-specific consequence.

## Initial implementation

V0.1 should provide:

1. a versioned `governance-context-projection` JSON Schema;
2. deterministic fixtures for a materially matching prior case and a materially misleading near-match;
3. validation that projections preserve source references, scope/freshness, polarity, material conditions, and derivation mode;
4. a schema shape that deliberately omits consumer verdict, standing permission, and vendor-specific risk fields;
5. documentation and roadmap placement;
6. no DashClaw- or AGT-specific runtime dependency.

A later slice may add a deterministic reference projection builder. Consumer-specific adapters should follow only after the generic projection is stable enough to test without vendor dependencies.

## Acceptance evidence required

ADR-029 MUST remain Proposed until at least:

- the generic projection schema exists and validates;
- positive and negative/material-mismatch fixtures exist;
- projection validation demonstrates provenance and scope preservation;
- a reference builder can reconstruct projections from canonical Agent Memory primitives;
- derived projection state can be discarded and rebuilt without loss of canonical memory truth;
- at least one consumer adapter proves usefulness without requiring consumer-specific fields in the canonical memory-unit schema;
- a near-match adversarial case proves that superficial similarity does not become permission;
- policy-generated outcomes are distinguishable from independent human adjudication;
- privacy/minimization behavior is tested for at least one sensitive precedent case.

## Rejected alternatives

### Put DashClaw-specific precedent fields in the canonical memory-unit schema

Rejected. It optimizes one adapter by coupling the core to one consumer vocabulary.

### Make the consumer own all projection semantics

Rejected. Governance consumers have recurring, vendor-neutral needs for provenance-preserving precedent context. A shared projection profile prevents every adapter from inventing incompatible interpretations of the same memory primitives.

### Let Governance Projection emit the final allow/deny decision

Rejected. That would turn the projection into a policy engine and collapse the evidence/authority boundary.

### Treat repeated approval as implicit standing permission

Rejected. Human fatigue is real, but laundering repetition into authority creates a self-reinforcing permissiveness loop. Repetition may justify a policy proposal, not self-ratification.

## Related

- #152
- #153
- #154
- ADR-021
- ADR-026
- ADR-028
- [`../34-adapter-contracts.md`](../34-adapter-contracts.md)
- [`../profiles/durable-decision-memory-profile.md`](../profiles/durable-decision-memory-profile.md)
