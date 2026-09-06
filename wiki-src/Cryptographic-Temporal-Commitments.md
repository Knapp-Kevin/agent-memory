# Cryptographic Temporal Commitments

Agent Memory can make temporal claims tamper-evident without pretending cryptography makes them true, current, complete, or authorized.

This page focuses on the **historical commitment and evidence layers**. For the end-to-end relationship among canonical memory, UOR, trust, external time/transparency evidence, Dogwood, Cedar/Cedarling, currentness, and PAMA, see **[Temporal Memory Architecture](Temporal-Memory-Architecture)**.

<picture>
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/cryptographic-temporal-commitment-light.svg">
  <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/cryptographic-temporal-commitment.svg" alt="Flow showing an immutable temporal commitment receiving an exact content identity, separate signer attestation, relative ordering evidence, optional external witness evidence, and separate currentness and authority evaluation. The diagram emphasizes that a valid signature does not prove trusted time, a predecessor chain does not prove complete or unique history, and none of the cryptographic evidence independently grants authority.">
</picture>

## The idea

A timestamp beside a signed event is weaker than committing to the temporal claim itself.

```text
sign(payload) + timestamp metadata
```

allows the temporal metadata to live outside the signed identity.

Accepted ADR-031 instead establishes:

```text
TemporalCommitment {
  event / payload identity
  temporal claims
  scope
  schema/profile identity
  declared ordering relationship
}
        |
        v
exact content reference
```

Changing a material temporal claim changes the object identity.

That still does **not** make the temporal claim true.

## The evidence layers

### Exact content identity

The content-reference layer answers:

> What exact canonical temporal object are we talking about?

The first optional interoperability profile uses the existing UOR-Addr v0.2.0 JSON content-reference contract.

```text
UOR identity != authority
```

UOR does not become Agent Memory's signer, clock, policy engine, or canonical runtime dependency.

### Signer attestation

A signer attests to the exact content reference and the reference profile used to interpret it.

This proves data-origin/integrity under that signing profile.

It does not automatically prove:

- the event actually happened;
- the claimed clock value is accurate;
- the signer is currently trusted;
- the event is currently applicable;
- the event is authorized memory.

A useful state is therefore perfectly possible:

```text
cryptographic signature: valid
signer trust: revoked
currentness: superseded
authority effect: none
```

Historical integrity survives changes in present authority.

### Signer trust

The merged external-trust evidence layer makes signer trust a separate, explicit contract rather than a caller-supplied assumption.

Trust binds:

```text
logical key reference
+ exact public-key digest
+ trust source
+ verification status
+ validity window
+ evidence references
```

This matters because a stable logical label such as `key:service:production` must not transfer trust to different key material merely because the name is familiar.

```text
valid signature
!= trusted signer

matching key_ref
!= matching public key
```

### Relative-order evidence

The initial `linear_stream` profile commits to a stream, sequence, predecessor-reference profile, and predecessor reference.

The verifier recomputes predecessor identity and checks scope, stream, profile, and sequence.

That proves a local relation. It does not magically create a global ledger.

```text
valid predecessor chain
!= complete history
!= unique history
!= non-equivocation
```

A stronger claim needs additional evidence such as an authoritative head, coordinator receipt, consistency proof, or verifiable ordered-log receipt.

If two valid children reference the same predecessor, Agent Memory reports the fork. The fork detector does not decide which child is canonical.

### External witness and transparency evidence

A trusted-time or transparency service may provide additional evidence about an exact commitment or signer attestation.

The generic Agent Memory evidence model binds both the exact subject reference and its reference profile.

For example, RFC 3161 evidence may establish:

> this commitment existed by independently verified time T2

That does not mean:

> the event occurred at T2

or even that its own claimed `event_time` is correct.

```text
witnessed existence time != event occurrence time
```

The merged transparency contract also distinguishes two bounded history claims:

```text
verified inclusion
  -> exact subject included under a declared VDS profile

verified consistency
  -> append-only transition between two declared tree states
```

Those do not become universal claims:

```text
inclusion != complete history
consistency != global non-equivocation
append-only integrity != current semantic truth
```

## Claimed time, order, and witnessed time are different

A temporal event can carry several legitimate time concepts:

| Claim | What it means |
|---|---|
| **Event time** | When the event claims it occurred. |
| **Observed time** | When an observer/runtime claims it saw the event. |
| **Validity interval** | When the represented fact claims to apply. |
| **Relative order** | What predecessor/sequence relationship is cryptographically committed. |
| **Witnessed time** | When an independent service can establish the commitment/attestation existed or was registered. |

Collapsing these into one timestamp would be wonderfully convenient and wrong.

## Corrections do not rewrite history

A later correction, dispute, revocation, or supersession creates new currentness evidence.

```text
E1  signed historical commitment
 |
 +--> signature remains historically valid
 |
 C1  later currentness(E1) = superseded
 |
 +--> references correcting/superseding evidence
```

The currentness record explicitly preserves:

```text
historical_commitment_mutated = false
cryptographic_validity_changed = false
authority_effect = none
```

This is the same historical/current separation Agent Memory uses elsewhere.

## Multi-writer history

The first profile is intentionally narrow. A single predecessor is suitable for a serialized stream, not for pretending concurrent writers happened in a neat total order.

Shared/concurrent memory may use stronger profiles such as:

- multiple causal predecessors;
- shared-write coordination receipts;
- coordinator-issued positions;
- transparency or verifiable-data-structure receipts.

ADR-031 does not turn Agent Memory into a blockchain with better branding.

## Relationship to temporal policy

A consumer such as Dogwood may receive a derived event projection backed by this evidence.

```text
Agent Memory temporal commitment
  -> lifecycle/currentness
  -> governed compatible projection
  -> Dogwood temporal policy
```

The consumer does not need to become the canonical memory system, and a cryptographically valid historical event does not become current policy authority merely because it remains present in a temporal trace.

See **[Temporal Policy and Governed Memory](Temporal-Policy-and-Governed-Memory)** and **[Temporal Memory Architecture](Temporal-Memory-Architecture)** for the consumer-facing layers.

## What has been proved

The merged ADR-031 reference evidence exercises:

- temporal/payload/schema/profile mutation changing exact object identity;
- signature binding to exact reference/profile;
- cryptographically valid but untrusted signer states;
- false/future claimed event time remaining distinct from trusted-time evidence;
- exact predecessor and reference-profile validation;
- cross-scope predecessor rejection;
- explicit fork detection without branch selection;
- deliberate non-claims for complete history and non-equivocation;
- exact witness subject/profile binding;
- witnessed time remaining distinct from event occurrence time;
- supersession/currentness that does not rewrite historical evidence;
- exact UOR-Addr v0.2.0 temporal-object addressing, composed with the repository's independent Python/Rust UOR compatibility workflow.

ADR-031 is **Accepted**.

The completed #265 / PR #267 evidence slice adds exact signer-trust binding and provider-neutral inclusion/consistency evidence plus a real RFC 3161 comparator against exact OpenSSL 3.6.3 source. PR #267 passed the full repository matrix at exact final head `3d3483feb10647ce02ed67c9d09b7022406196a6`; those results remain bounded repository evidence rather than a production trust-service guarantee.

## Canonical references

- `docs/research/cryptographic-temporal-commitments.md`
- `docs/adr/ADR-031-temporal-claims-require-deterministic-content-commitments.md`
- `docs/profiles/temporal-commitment-evidence-profile.md`
- `reference/agentmem_ref/memory/temporal_commitment.py`
- `reference/agentmem_ref/memory/temporal_trust.py`
- `reference/agentmem_ref/memory/temporal_transparency.py`
- `schemas/temporal-commitment.schema.json`
- `schemas/temporal-signer-attestation.schema.json`
- `schemas/temporal-signer-trust.schema.json`
- `schemas/temporal-transparency-receipt.schema.json`
- `schemas/temporal-external-witness.schema.json`
- `schemas/temporal-currentness-evaluation.schema.json`
- #259 and #265
