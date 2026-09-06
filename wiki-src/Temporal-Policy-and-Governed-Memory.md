# Temporal Policy and Governed Memory

Agent Memory can provide useful history and current context to external policy systems without turning those systems into memory stores or turning their decisions into memory authority.

The important boundary is not a particular product integration. It is the relationship between **evolving memory semantics**, **evidence about history**, and a policy consumer that expects an exact schema and context model.

For the complete relationship among temporal commitments, UOR, signer trust, external time/transparency evidence, Dogwood, Cedar/Cedarling, currentness, and PAMA, start with **[Temporal Memory Architecture](Temporal-Memory-Architecture)**.

<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-policy-semantic-mediation-light.svg">
  <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-policy-semantic-mediation.svg" alt="Flow from canonical Agent Memory through a governed semantic projection and compatibility gate into temporal or authorization consumers such as Dogwood, Cedar, and Cedarling, followed by monotonic policy composition and returned decision evidence. Schema or currentness changes loop back through compatibility evaluation instead of rewriting historical memory.">
</picture>

## What changed in the temporal model

Agent Memory now has a clearer separation between **historical evidence** and **policy-facing temporal context**.

A projected event can be backed by stronger evidence before it reaches a temporal policy consumer:

```text
canonical memory
  -> exact temporal commitment
  -> optional UOR content identity
  -> signer attestation / signer trust evidence
  -> optional external time / transparency evidence
  -> lifecycle currentness
  -> governed event/context projection
  -> compatibility gate
  -> temporal policy
```

Dogwood does not have to understand every layer. It can receive the bounded event/context representation needed for policy evaluation while Agent Memory preserves richer provenance, trust, correction, schema, and currentness semantics behind the projection.

That relationship is valuable in both directions. Dogwood can add temporal-policy interpretation to governed memory, and the resulting policy decision can return to Agent Memory as evidence for future reasoning without silently becoming memory authority.

## Why there is a compatibility gate

A deterministic policy engine can still evaluate **stale semantics**.

Suppose Agent Memory originally represented:

```text
Customer -> owns -> Contract
```

and later the governed domain model evolves into:

```text
Customer -> represents -> Organization
Organization -> holds -> Contract
Contract -> delegated signer / renewal authority
```

An old policy schema may still accept a request shaped like the old model. That does not mean the request still means what the current memory system means.

```text
valid JSON != semantic compatibility
schema similarity != schema compatibility
historical match != current authority
```

Accepted ADR-030 therefore requires a versioned compatibility/currentness boundary between a memory-derived projection and the exact target policy contract.

## What Agent Memory owns

Agent Memory remains authoritative for its own memory semantics:

- identity and provenance;
- event time, observed time, validity intervals, and currentness;
- temporal commitment and historical evidence references;
- correction, supersession, dispute, revocation, and deletion state;
- scope and isolation;
- domain-schema identity and governed evolution;
- derivation and currentness evidence;
- PAMA memory-specific consequence and downstream-authority boundaries.

External consumers receive a **derived projection**, not the canonical memory representation.

## What the projection does

A projection exports the smallest truthful and appropriately scoped representation needed by the consumer.

A projection can contain historical events, current context, or both.

Example:

```text
historical event:
  approval occurred at T1
  exact temporal commitment = E1
  signer evidence = S1

current context:
  approving authority was revoked at T2
  currentness(E1) = historically valid but no longer reusable authority
```

A temporal policy may need both facts. Replaying the T1 approval without the T2 currentness state would preserve history while producing the wrong current implication.

## The compatibility states

The reference contract uses four states:

| State | Meaning |
|---|---|
| `current` | Required evidence establishes compatibility for this exact projection and target contract. |
| `migration_required` | A known schema/semantic or policy-validation change must be governed and revalidated. |
| `incompatible` | A concrete contradiction prevents current use. |
| `unknown` | Required evidence is missing or insufficient. |

`unknown` is deliberately not treated as current.

Compatibility itself has no authority effect. It merely says whether the projection is eligible to be supplied as current input under the declared contract.

## Dogwood

Dogwood is a Cedar-derived temporal-policy language that can evaluate bounded history using expressions such as `formerly`, `previous`, and `since`. Its public model includes an action schema, an event schema, a stateful temporal history, information providers, and lowering into Cedar context.

That makes Dogwood an unusually useful peer for Agent Memory because it asks a question Cedar alone does not:

> **What may policy conclude from a bounded history of prior events?**

The architectural boundary is:

```text
Agent Memory canonical history
!=
Dogwood temporal trace
```

Agent Memory can project eligible historical events into a Dogwood trace. Those events may be backed by exact temporal commitments, signer/trust evidence, and currentness evidence without requiring Dogwood to become the source of those semantics.

Dogwood can then evaluate temporal policy over that trace. The resulting policy decision can return to Agent Memory as external decision evidence.

Dogwood's trace remains a consumer-specific derived representation. It does not become the canonical source for correction, currentness, deletion, signer trust, or memory authority.

### Why the interaction is useful

Agent Memory can tell Dogwood more than “this event occurred once.” It can mediate a governed temporal view that reflects:

- exact event identity;
- current/superseded/revoked status;
- scope and isolation;
- schema compatibility;
- bounded history horizon;
- external trust/time evidence where policy actually needs it.

Dogwood, in turn, contributes temporal-policy semantics that Agent Memory does not need to reinvent in its core.

This is the kind of aligned composition Agent Memory is designed for:

```text
peer contributes specialized semantics
+
Agent Memory contributes governed memory context
+
neither peer absorbs the other's authority model
```

### Temporal horizon

If a policy question requires more history than the target Dogwood configuration can evaluate, the correct result is a capability mismatch.

```text
required history > available temporal window
-> incompatible
```

It is not evidence that a historical event never happened.

### Isolation and pins

Dogwood's event schema supports `pin` correlation. The public contract is important here: a **universal symmetric** pin can provide key-local semantics and a partition guarantee, while partial/asymmetric use may retain global-trace semantics.

Therefore:

```text
pin exists != partition guarantee
```

An Agent Memory adapter that claims isolation must validate the actual target event schema or rely on an independently sufficient host partition.

### Trace shape affects temporal semantics

Dogwood's own public issue history demonstrates another important boundary: temporal operators can depend on the exact sequence of timepoints present in the trace.

That means Agent Memory cannot treat event projection as a cosmetic serialization step. Which events are included, omitted, or classified as decision versus history-only events may change the temporal semantics evaluated by the consumer.

The projection profile therefore belongs inside compatibility evidence.

## Cedar

Cedar provides a typed authorization model around principal, action, resource, context, policies, and an application schema.

A Cedar schema is part of the authorization contract. When the application/domain model changes, previously valid policies may require revalidation.

Agent Memory therefore cannot assume that an old Cedar policy remains semantically current merely because a request can still be constructed.

## Cedarling

Cedarling adds a deployable embedded Cedar policy-decision surface with policy-store identity/version, identity handling, logs, and dynamic context data.

Its dynamic context surface is useful for memory-derived **current facts**, but pushed values still have to satisfy the Cedar schema.

Cedarling also has context precedence:

```text
inline request context
>
pushed context data
>
default context
```

So a decision receipt must bind what was actually evaluated. Proving that Agent Memory pushed a value is insufficient if a higher-precedence inline request shadowed it.

## UOR's role before policy

UOR-Addr can optionally give a projected temporal event an exact portable content identity before it reaches a consumer.

That makes the handoff easier to correlate across runtimes without turning UOR into the authorization layer.

```text
UOR exact identity
-> useful binding primitive

UOR exact identity
!= currentness
!= Dogwood policy result
!= Cedar authorization
!= PAMA authority
```

This gives UOR a meaningful temporal role while preserving the language-neutral and provider-neutral Agent Memory core established by ADR-028.

## Returned policy decisions

The compatibility gate enables external evaluation. It does not loosen Agent Memory governance.

```text
PAMA deny + external allow -> deny
PAMA review + external allow -> review
PAMA allow + external deny -> deny
```

An external ALLOW/DENY or temporal match is **policy-decision evidence**.

It is not automatically:

- human approval;
- reusable authority;
- memory admission;
- execution evidence;
- enforcement evidence;
- memory truth.

That evidence can still become useful future memory through normal provenance, scope, lifecycle, currentness, and PAMA boundaries.

## Schema and currentness evolution

Historical projections are not rewritten to make current compatibility look cleaner.

```text
T1: projection P1 + compatibility E1 = current

T2: source or target schema changes
    P1 remains historical evidence
    E2 = migration_required / incompatible / unknown

T3: governed migration/rebuild
    new projection P2
    new evaluation E3 may become current
```

This preserves the distinction between **what happened** and **what is currently applicable**.

## Current Dogwood research maturity

The current comparator is pinned to public source commit `c6237c88099b3f492ecc5fcee42df06a19224b97` in `dogwood-policy/dogwood`.

The public repository is Apache-2.0 and provides a reference interpreter, but it explicitly describes its published tree as a sanitized synchronization from an internal source without the internal git history, and there is currently no public GitHub release artifact. Agent Memory therefore treats published public behavior as evidence and unpublished/internal behavior as unknown.

This is a maturity boundary, not a criticism. It prevents an adapter from depending on capabilities that have not actually been published.

## Evidence and canonical references

- [Temporal Memory Architecture](Temporal-Memory-Architecture)
- [Cryptographic Temporal Commitments](Cryptographic-Temporal-Commitments)
- [Governance Projection](Governance-Projection)
- [Canonical and Derived State](Canonical-and-Derived-State)
- [Decision Flows and Memory Lifecycle](Decision-Flows-and-Memory-Lifecycle)
- [Quality Peers and Useful Projects](Quality-Peers-and-Useful-Projects)
- `docs/adr/ADR-030-temporal-policy-consumers-require-versioned-compatible-projections.md`
- `docs/adr/ADR-031-temporal-claims-require-deterministic-content-commitments.md`
- `docs/profiles/policy-projection-compatibility-profile.md`
- `docs/profiles/temporal-commitment-evidence-profile.md`
- `docs/research/temporal-policy-semantic-mediation.md`
- `schemas/policy-projection-compatibility.schema.json`
- `reference/tests/test_policy_projection_compatibility.py`

The diagrams summarize these boundaries. They do not create doctrine beyond the linked evidence and ADR status.
