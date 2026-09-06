# Governance Projection

Agent Memory can make external governance systems more intelligent without becoming a governance product itself.

The boundary is:

```text
Agent Memory core
  remembers generally valuable state
        |
        v
Governance Context Projection
  vendor-neutral derived context
        |
        v
consumer-specific adapter
        |
        v
policy / approval / enforcement runtime
```

The projection exists because approval history by itself is dangerously shallow.

A useful memory is not merely:

```text
"git push was approved before"
```

It may preserve:

```text
what was approved or denied
why
under what conditions
which scope and policy applied
who had authority
what exceptions mattered
whether the decision was later corrected or revoked
what happened after execution
whether an incident or rollback followed
```

That context can help a governance system distinguish a genuinely repetitive approval from a superficially similar but materially different action.

## Why this matters

Human approval is not infinitely reliable. Repeated prompts create approval fatigue, and eventually a person stops evaluating each prompt carefully.

The unsafe shortcut is:

```text
approved before
approved again
approved again
        ↓
probably safe forever
```

Agent Memory instead enables a richer question:

> **Why was the earlier action acceptable, and do those material conditions still hold?**

For example:

```text
Prior approval:
  feature branch
  no force push
  current CI
  expected remote

Current action:
  main branch
  force push
  stale CI
```

The action family may look similar. The precedent is not materially equivalent.

The projection should preserve that mismatch rather than converting prior approval frequency into permission.

## What core Agent Memory owns

Core remains consumer-neutral.

It owns generally useful memory semantics such as:

- identity
- provenance and derivation
- evidence
- scope and isolation domain
- lifecycle state
- temporal validity
- correction, supersession, revocation, and dispute
- actor and authority context where relevant
- rationale and explanation with provenance
- outcome, incident, rollback, and consequence references
- uncertainty and estimator provenance
- sensitivity and minimization constraints

A field does not belong in core merely because one governance product would find it convenient.

## What Governance Context Projection owns

The projection is a rebuildable view over canonical memory.

It may expose:

- relevant precedent references
- supportive, cautionary, contradictory, or neutral polarity
- material conditions
- condition matches, mismatches, and unknowns
- validity and freshness
- negative precedent
- outcome and incident references
- authority-context references
- derivation mode and uncertainty

The projection remains evidence/context.

It is **not**:

- a standing permission
- a final allow/deny verdict
- a risk score
- a consumer policy object
- a second canonical memory store

## What consumer adapters own

Specific governance systems own the last-mile translation.

A DashClaw adapter may map the projection into DashClaw's own guard, approval, and risk vocabulary.

An Agent Governance Toolkit / ACS-style adapter may map the same projection into that policy runtime's inputs.

Another policy engine may interpret it differently.

None of those consumer-specific vocabularies need to reshape Agent Memory core.

## The ownership rule

> **Core owns memory semantics. Governance Projection owns vendor-neutral remembered context. Consumer adapters own consumer-specific interpretation.**

When an adapter needs a missing field, ask:

1. Is this generally meaningful to memory, evidence, scope, lifecycle, authority context, or outcome?
2. Or is it merely convenient for this consumer?
3. If there is a genuine general gap, what is the smallest reusable primitive that closes it?

That keeps Agent Memory extensible without turning the canonical schema into a museum of every API it has ever met.

## Precedent is not authority

Repeated approvals can be remembered. They can support a proposal for a narrow standing policy or grant.

They cannot create that authority by repetition alone.

```text
repeated materially equivalent decisions
        ↓
evidence of a stable pattern
        ↓
policy / grant proposal
        ↓
explicit authority transition
        ↓
future review requirements may change
```

The authority transition is separate from the memory that motivated it.

This prevents a permissive feedback loop where policy-generated approvals recursively become evidence that the policy should become even more permissive.

## Negative precedent matters

Denials, incidents, revocations, corrections, rollbacks, and execution despite a governance gate are first-class context.

Ten harmless approvals do not erase one materially relevant denial merely because ten is a larger number.

The projection therefore preserves **what kind of precedent it is** and **why it applies** rather than turning history into a vote count.

## Determinism first

The first implementation uses deterministic condition comparison.

```text
match
mismatch
unknown
```

Semantic similarity can later retrieve candidate precedent, but it cannot independently authorize a consequence.

```text
probabilistic retrieval
  -> candidate precedent
  -> material-condition / policy evaluation
  -> governance consequence
```

The estimator must preserve its identity, version, scope, and uncertainty when it enters the path.

## Privacy and minimization

Governance consumers should receive only the context required for their decision.

Prefer:

- stable references
- structured conditions
- categorical outcome summaries
- scoped fingerprints
- bounded rationale summaries

when those are sufficient instead of copying raw sensitive memories into another system.

A governance integration is not permission to create an accidental secondary memory store.

## Relationship to external governance systems

Two current aligned projects make this boundary concrete:

- **[DashClaw](Aligned-Projects-and-Intellectual-Lineage#dashclaw)** is an enforcement/approval runtime and a useful target for a consumer adapter.
- **[Microsoft Agent Governance Toolkit](Aligned-Projects-and-Intellectual-Lineage#microsoft-agent-governance-toolkit)** is a broader governance-policy/runtime comparator and another potential adapter target.

They remain independent projects. Agent Memory does not require either system.

## Temporal policy and evolving schemas

Dogwood, Cedar, and Cedarling expose a second question beyond ADR-029's anti-authority boundary:

> **Is this versioned memory-derived projection still semantically current for the exact policy consumer evaluating it?**

A projection can remain syntactically valid while its source/domain schema, currentness, target policy schema, temporal horizon, isolation model, or actually evaluated context has changed.

Accepted ADR-030 and the merged #256 implementation add a compatibility/currentness gate:

```text
canonical memory
  -> governed projection
  -> compatibility/currentness evidence
  -> consumer-specific temporal/policy view
```

The target trace or context cache remains derived state. External policy may tighten the Agent Memory boundary but cannot silently widen PAMA.

See **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)** for the Dogwood/Cedar/Cedarling relationship, schema-evolution failure modes, and visual flow.

## Current maturity

The base governance-projection architecture remains tracked by **Proposed ADR-029** pending its own stronger maturity review. Its merged schema, fixtures, reference builder, precedent handling, and consumer-facing evidence do not silently make it canonical doctrine.

The temporal/schema compatibility extension is **Accepted ADR-030**. Its research and implementation evidence, including #255 and #256, established versioned compatibility/currentness checks and adversarial consumer behavior before acceptance. ADR-030 acceptance does not promote ADR-029.

**ADR-028 is Accepted** and separately preserves the language-neutral normative core and optional implementation-profile boundary. Together, ADR-028 and ADR-030 keep implementation language and temporal-policy consumers from capturing core Agent Memory semantics while ADR-029 remains independently maturity-gated.

## Canonical sources

- Architecture decision: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-029-governance-projection-is-derived-context-not-authority.md
- Temporal compatibility decision candidate: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-030-temporal-policy-consumers-require-versioned-compatible-projections.md
- Projection profile: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/profiles/governance-context-projection-profile.md
- Policy projection compatibility profile: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/profiles/policy-projection-compatibility-profile.md
- Schema: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/schemas/governance-context-projection.schema.json
- Compatibility schema: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/schemas/policy-projection-compatibility.schema.json
- Adapter contracts: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/34-adapter-contracts.md
- Roadmap: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/07-integration-roadmap.md

## Next

- **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)** for versioned projection compatibility across Dogwood, Cedar, and Cedarling
- **[Aligned Projects & Intellectual Lineage](Aligned-Projects-and-Intellectual-Lineage)** for the DashClaw and AGT relationship boundaries
- **[Architecture Decisions](Architecture-Decisions)** for ADR maturity
- **[Implementation Guide](Implementation-Guide)** for building against Agent Memory contracts