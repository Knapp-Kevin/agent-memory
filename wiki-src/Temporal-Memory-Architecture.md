# Temporal Memory Architecture

Agent Memory treats time as more than a timestamp attached to a record.

A useful memory system must distinguish **what happened or was claimed to happen**, **what exact historical object was committed**, **who signed it**, **whether that signer is trusted**, **what an independent witness can prove**, **what is currently applicable**, and **what an external policy may conclude**.

<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-memory-architecture-light.svg">
  <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/temporal-memory-architecture.svg" alt="Agent Memory temporal architecture showing canonical memory, deterministic temporal commitment, optional UOR exact identity, signer attestation and trust, external timestamp or transparency evidence, lifecycle currentness, governed projection compatibility, and Dogwood or Cedar-family policy consumers. The diagram emphasizes that identity, trust, time, currentness, policy compatibility, and authority remain separate claims.">
</picture>

## The architecture in one sentence

Agent Memory preserves rich temporal meaning internally and exposes the **smallest truthful, current, appropriately scoped, provenance-preserving representation each aligned consumer needs**.

```text
canonical memory
  -> temporal commitment and evidence
  -> lifecycle/currentness
  -> versioned governed projection
  -> compatibility gate
  -> Dogwood / Cedar / Cedarling / other consumer
  -> policy-decision evidence
  -> monotonic PAMA composition
```

No peer system has to understand the entire Agent Memory model, and no peer system silently becomes the canonical memory authority.

## The layers

### 1. Canonical memory semantics

Agent Memory owns memory-specific meaning:

- identity and provenance;
- claimed event time, observed time, and validity intervals;
- correction, supersession, dispute, revocation, and deletion;
- scope and isolation;
- domain-schema evolution;
- derivation and currentness;
- PAMA consequence and authority boundaries.

Historical truth and current applicability remain independently representable.

### 2. Deterministic temporal commitment

ADR-031 makes material temporal claims part of the deterministic object being committed.

```text
TemporalCommitment {
  payload / subject identity
  temporal claims
  scope
  schema/profile identity
  ordering relationship
}
```

Changing a material temporal field changes the exact object identity.

That creates tamper-evident history. It does not create truth or permission.

### 3. UOR as an optional exact-identity substrate

UOR-Addr can provide a portable content reference for the exact temporal object.

Its role is deliberately narrow and strong:

```text
UOR identity
!= truth
!= signer trust
!= currentness
!= permission
!= PAMA authority
```

This lets different runtimes agree on **which exact object** they are discussing without making UOR the Agent Memory runtime or authority ontology.

See **[Cryptographic Temporal Commitments](Cryptographic-Temporal-Commitments)** for the lower-level commitment model.

### 4. Signer attestation and signer trust

A cryptographic signature proves key possession for an exact commitment under the declared signing profile.

Signer trust is a separate claim.

The merged external-trust evidence layer binds trust to:

```text
logical key reference
+ exact public-key material
+ trust source
+ verification status
+ validity window
+ evidence references
```

This prevents a familiar logical key name from transferring trust to different key material merely because the label matches.

A historical signature can remain cryptographically valid after current signer trust is revoked or expires.

### 5. External time and transparency evidence

An external witness can strengthen temporal evidence without becoming the source of event truth.

The merged external comparator targets a bounded RFC 3161 claim using an exact OpenSSL 3.6.3 source checkout and source-tree fixture:

```text
this exact commitment existed by independently verified time T
```

That does **not** prove the represented event occurred at T.

Agent Memory also models provider-neutral inclusion and consistency evidence:

```text
verified inclusion
  -> exact subject included under a declared VDS profile

verified consistency
  -> bounded append-only transition between two tree states
```

Those claims remain bounded:

```text
inclusion != complete history
consistency != global non-equivocation
append-only integrity != current semantic truth
```

### 6. Lifecycle currentness

Currentness answers a different question:

> What does this historical object mean now?

A previously valid temporal commitment may later be:

```text
current
superseded
disputed
revoked
deleted
unknown
```

Changing currentness does not rewrite the signed historical object.

### 7. Governed projection and compatibility

ADR-030 governs the boundary between Agent Memory and temporal/authorization consumers.

A consumer receives a versioned derived projection, not the complete canonical memory system.

The compatibility gate binds the exact source/projection/consumer contract and evaluates states such as:

```text
current
migration_required
incompatible
unknown
```

This matters because a deterministic policy engine can make a perfectly deterministic decision against stale semantics.

```text
valid JSON != semantic compatibility
old policy still evaluates != old policy still means the right thing
```

## Dogwood: temporal policy over governed history

Dogwood is especially aligned because it asks a question Cedar alone does not:

> **What may policy conclude from a bounded history of prior events?**

The relationship is not database synchronization. It is semantic mediation.

```text
Agent Memory canonical history/currentness
        |
        v
versioned governed event/context projection
        |
        v
Dogwood temporal trace
        |
        v
temporal policy evaluation
        |
        v
policy-decision evidence returned to Agent Memory
```

Agent Memory can preserve the richer reason, provenance, correction, authority, schema, and currentness context while Dogwood receives the smaller temporal representation it needs for policy evaluation.

The return path matters too. A Dogwood decision can become useful remembered evidence, but only through normal Agent Memory provenance, lifecycle, scope, and PAMA boundaries.

```text
Dogwood temporal match
!= current memory truth
!= standing permission
!= human approval
!= execution evidence
```

See **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)** for the detailed projection/compatibility model.

## Cedar and Cedarling

Cedar provides deterministic authorization semantics. Cedarling provides a deployable embedded Cedar policy-decision surface with identity, policy-store, context, and logging capabilities.

Agent Memory can project current, compatible memory-derived context into those systems without turning them into the memory store.

| Component | Primary role here | What it does not own |
|---|---|---|
| **Agent Memory** | retained-state semantics, provenance, lifecycle, currentness, scope, PAMA | consumer policy language |
| **UOR-Addr** | optional exact portable content identity | truth, signer trust, currentness, authority |
| **Dogwood** | temporal policy over bounded governed history/context | canonical memory lifecycle/currentness |
| **Cedar** | deterministic authorization policy | memory lifecycle or memory authority |
| **Cedarling** | embedded Cedar PDP, identity/policy-store/runtime context | canonical Agent Memory semantics |
| **RFC 3161 / transparency evidence** | independent existence/order/history evidence | event truth, currentness, PAMA |

## Temporal correctness includes schema evolution

Time changes more than values. It can change the **meaning and shape of the domain itself**.

A projection that was valid yesterday can become semantically stale after a governed domain-schema mutation even if the old request still parses.

```text
T1: schema S1 -> projection P1 -> consumer contract C1

T2: governed schema mutation S1 -> S2

T3: compatibility(P1, S2, C1)
      -> current
      -> migration_required
      -> incompatible
      -> unknown
```

This same check applies to Dogwood event schemas, Cedar application schemas/entities, Cedarling policy stores, and future consumer-specific projections.

## The governing separations

```text
content identity != truth
signature validity != signer trust
signer trust != memory authority
claimed event time != witnessed existence time
local predecessor chain != complete history
transparency inclusion != global non-equivocation
historical truth != current truth
policy compatibility != permission
external ALLOW != PAMA authority
past approval != standing permission
```

These distinctions are what let historical memory remain useful without allowing old evidence to impersonate present authority.

## Why this matters for aligned technologies

Agent Memory is not trying to replace UOR, Dogwood, Cedar, Cedarling, transparency services, or governance runtimes.

The more useful relationship is compositional:

```text
aligned system contributes a strong primitive
        +
Agent Memory preserves memory-specific semantics
        +
versioned projections keep boundaries explicit
        +
returned evidence enriches future governed memory
```

That allows deeper interoperability while each project remains authoritative for the problem it actually solves.

## Current maturity

### Accepted doctrine

- **ADR-030**: temporal and authorization consumers require versioned compatible/current projections.
- **ADR-031**: material temporal claims belong inside deterministic content commitments while signer, trust, witness, currentness, and authority claims remain separate.

### Executable evidence already merged

The repository includes executable evidence for:

- exact temporal commitment identity;
- optional UOR-Addr addressing;
- signer attestation and key possession;
- predecessor continuity and explicit fork detection;
- external witness subject binding;
- historical/currentness separation;
- Dogwood-facing projection compatibility/currentness;
- Cedar/Cedarling policy boundaries.

### External temporal trust evidence

The completed #265 / PR #267 slice adds:

- signer trust bound to exact key material;
- revoked, expired, mismatched, and unverified trust negative paths;
- provider-neutral inclusion and consistency evidence;
- explicit non-claims for complete history and global non-equivocation;
- a real RFC 3161 comparator built from exact OpenSSL 3.6.3 source and exercised against the upstream source-tree fixture.

PR #267 passed the complete 28-workflow matrix at exact final head `3d3483feb10647ce02ed67c9d09b7022406196a6`. The external-evidence artifact is bound to that head with digest `sha256:82ea8c29cbc3637b6e4251d58ac224c0a77749e1b4db5bf544bc087d1df42357`. These are repository evidence claims, not production PKI or universal deployment guarantees.

## Related Wiki pages

- **[Cryptographic Temporal Commitments](Cryptographic-Temporal-Commitments)**
- **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)**
- **[Governance Projection](Governance-Projection)**
- **[Canonical and Derived State](Canonical-and-Derived-State)**
- **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)**
- **[PAMA](PAMA)**
- **[Quality Peers and Useful Projects](Quality-Peers-and-Useful-Projects)**
