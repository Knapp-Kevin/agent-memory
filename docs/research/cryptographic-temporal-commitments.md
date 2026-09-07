# Cryptographic temporal commitments

Status: research synthesis for #258

## Question

Can Agent Memory cryptographically commit to the **temporal meaning** of an event, rather than merely signing an event payload that happens to carry a timestamp?

The research answer is **yes, with an important decomposition**.

A useful architecture must not collapse four distinct claims:

1. **content identity** — what exact temporal object is being referenced;
2. **signer attestation** — which key endorsed that exact object;
3. **relative-order evidence** — what predecessor/stream relation the object commits to;
4. **external time/transparency evidence** — what an independent witness can prove about existence, inclusion, consistency, or freshness.

These claims compose. They are not interchangeable.

```text
valid content reference
!= valid signature
!= trusted wall-clock time
!= complete append-only history
!= current applicability
!= memory authority
```

## Primary-source findings

### RFC 8785: canonicalization before cryptography

RFC 8785 defines a deterministic JSON representation intended for hashing and signing. The cryptographic lesson is directly applicable: before a JSON temporal object is hashed or signed, all implementations must agree on the exact bytes being committed.

Agent Memory already has an optional UOR-Addr v0.2.0 profile whose JSON realization is:

```text
RFC 8259 + RFC 8785 JCS + UAX #15 NFC + SHA-256
```

and whose explicit authority effect is `none`.

That existing seam is a strong candidate for **temporal object identity** without making UOR a signing or authority system.

Primary source: https://www.rfc-editor.org/rfc/rfc8785.html

### RFC 3161: witnessed time is a separate assertion

RFC 3161 Time-Stamp Protocol accepts a message imprint and returns a signed time-stamp token from a Time Stamping Authority. Its purpose is to establish that data existed before/at a particular trusted time.

That is materially different from a signer placing `event_time = T` inside its own signed object.

```text
signer commits to event_time=T
-> signer made that temporal claim

trusted timestamp over commitment/signature
-> independent witness establishes existence by time T2
```

The latter does not prove that the event actually occurred at its claimed event time. It proves the witnessed object existed by the witness time.

Primary source: https://www.rfc-editor.org/rfc/rfc3161.html

### COSE / SCITT: signed statements and receipts are separate objects

RFC 9052 defines COSE signatures as data-origin and data-integrity evidence.

RFC 9943 SCITT defines signed statements separately from Transparency Service receipts. A statement issuer signs the statement; a transparency service can then register that signed statement in a verifiable data structure and return a receipt.

RFC 9942 defines COSE receipts that can prove properties including inclusion and consistency of verifiable data structures.

That decomposition maps well to Agent Memory:

```text
TemporalCommitment
  -> SignerAttestation
  -> optional Transparency/Time Receipt
```

The external receipt proves exactly its registered property. It does not reinterpret Agent Memory memory semantics.

Primary sources:

- https://www.rfc-editor.org/rfc/rfc9052.html
- https://www.rfc-editor.org/rfc/rfc9942.html
- https://www.rfc-editor.org/rfc/rfc9943.html

### Sigstore: signing-time evidence can be carried independently

Sigstore bundles can carry transparency-log signed entry timestamps and RFC 3161 timestamps. This is useful prior art for keeping signature verification material and trusted-time evidence together while still treating them as distinct evidence.

Primary source: https://docs.sigstore.dev/about/bundle/

## UOR finding

The current public UOR-Addr release remains v0.2.0. Agent Memory already proves its JSON labels across released Python and Rust implementations.

The useful UOR role in this design is:

> **identify the exact canonical temporal object that another cryptographic layer signs or witnesses.**

UOR is not required to provide:

- signer identity;
- public-key trust;
- signature verification policy;
- trusted wall-clock time;
- authorization;
- memory admission;
- PAMA consequence.

This preserves ADR-028's language-neutral / optional-profile boundary.

## Proposed object model

### 1. Temporal commitment

The immutable committed object contains the temporal claims whose mutation must change object identity.

```text
TemporalCommitment {
  profile_id
  profile_version

  event {
    event_type
    subject_ref
    payload_ref or payload_digest
  }

  temporal_claims {
    event_time?
    observed_at?
    valid_from?
    valid_to?
  }

  ordering {
    mode
    stream_ref?
    sequence?
    predecessor_refs[]
  }

  semantics {
    domain_schema_ref
    domain_schema_digest
    projection_profile?
    projection_version?
  }

  scope_ref
}
```

A field belongs inside the commitment when changing it should create a different historical temporal object.

### 2. Content reference

The commitment receives an exact content identity under a declared deterministic profile.

Initial optional evidence profile:

```text
agent-memory/uor-addr-json-content-reference
UOR-Addr v0.2.0
```

The content-reference profile is itself part of the signer transcript so a verifier cannot silently reinterpret the same label under another canonicalization/addressing profile.

### 3. Signer attestation

The signer signs a domain-separated transcript rather than an ambiguous raw string.

Conceptually:

```text
canonicalize({
  domain: "agent-memory/temporal-commitment-attestation",
  version: "1.0.0",
  content_reference_profile: ...,
  content_ref: ...
})
```

The first reference implementation may use Ed25519 because the existing `cryptography` dependency already supports it. Ed25519 is an implementation profile, not canonical doctrine.

Signer evidence should contain:

```text
signature_profile
algorithm
signer_key_ref
content_ref
signature
```

Historical content identity does not change merely because key trust, certificate status, or authorization changes later.

### 4. External time / transparency evidence

An optional witness object binds an independently verified statement to an exact subject.

```text
ExternalWitnessEvidence {
  witness_profile
  subject_kind
  subject_ref
  verification_status
  witnessed_at?
  proof_ref
}
```

Potential profiles include RFC 3161 timestamp tokens, SCITT/COSE receipts, Sigstore-style transparency evidence, or other deployment-specific witnesses.

The generic Agent Memory layer should consume **verified witness evidence**, not require one global timestamp/transparency provider.

## Three clocks / temporal claims

The model should explicitly distinguish:

### Claimed event time

What the event asserts about when it occurred.

A valid signature proves the signer committed to this claim. It does not make the clock trustworthy.

### Cryptographic / causal order

What predecessor or stream-order relation is committed.

This can be stronger than a free-form timestamp but is still only as complete as the ordering profile and available anchors.

### Externally witnessed time

When an independent service can prove that a commitment/signature was already present, registered, or included.

This provides an upper bound or witness-specific temporal statement, not necessarily the true event occurrence time.

## Ordering model

### Single-stream predecessor chains

For a strictly serialized stream, a commitment may bind:

```text
stream_ref
sequence
predecessor_ref
```

Because the predecessor is inside the content-addressed object, changing order changes the descendant content identity.

However:

```text
hash chain
!= proof of completeness by itself
```

An isolated chain fragment cannot prove that a verifier has seen the authoritative head, that the issuer did not fork the chain, or that no alternate history exists.

### Multi-writer / concurrent history

A single predecessor must not be imposed as a fake total order over concurrent writers.

Possible profiles include:

- explicit causal predecessor sets;
- an independently ordered shared-write receipt;
- a transparency/VDS receipt establishing inclusion/consistency;
- a coordinator-issued stream position.

The generic temporal commitment must describe what ordering it proves rather than claiming a universal total order.

This aligns with existing shared-memory pre-write coordination rather than replacing it.

## Relationship to Dogwood

Dogwood may consume temporal events derived from Agent Memory commitments, but it does not need to implement Agent Memory's entire cryptographic evidence model.

A projection might carry:

```text
event data
content_ref
verified signer/witness status needed by policy
currentness context
```

The adapter decides which verified claims become Dogwood event/provider fields.

The canonical relationships remain:

```text
Agent Memory temporal commitment
!= Dogwood trace entry

cryptographically valid historical event
!= current policy authority
```

Dogwood issue #7 also demonstrates that temporal semantics depend on trace shape: intervening request/response/error timepoints can change `since` continuity. Therefore event-kind selection and projection shape are semantic inputs to the compatibility gate, not harmless serialization details.

## Relationship to corrections and deletion

A signed historical event should remain historically immutable.

Later correction/revocation/supersession creates new governed state:

```text
E1 signed historical commitment
E2 correction/supersession references E1
currentness evaluation says E1 is no longer current
```

This does not require destroying E1's signature.

Deletion remains separate. A retained signature/content reference may itself constitute retained evidence or residue depending on policy. Cryptographic immutability is not an excuse to ignore deletion obligations.

## Relationship to authority

Every cryptographic layer in this design has a deliberately narrow meaning.

```text
UOR/content identity
  -> exact object identity

signature
  -> signer endorsed exact object

ordering link
  -> declared relative-order relationship

external witness
  -> witness-specific existence/inclusion/consistency claim
```

None independently establishes:

- truth of the event;
- trustworthiness of the signer;
- current applicability;
- memory admission;
- reusable authority;
- PAMA permission;
- execution/enforcement.

Trust and authority remain explicit higher-level evaluations.

## Adversarial requirements

The implementation evidence should include at least:

1. payload mutation changes content reference and invalidates attestation binding;
2. event-time mutation changes content reference;
3. predecessor mutation changes content reference;
4. schema/profile mutation changes content reference;
5. signer signature fails after content-ref mutation;
6. valid signature over an intentionally false/future event time remains only a signer claim;
7. unknown/untrusted signer remains cryptographically valid but is not promoted to authority;
8. missing predecessor is detectable for a profile requiring continuity;
9. forked descendants are represented as a fork, not silently flattened;
10. cross-scope predecessor reference fails the declared scope/order profile;
11. correction/supersession preserves the historical signature while changing currentness;
12. valid content address cannot satisfy PAMA;
13. external witness evidence with the wrong subject reference is rejected;
14. witness time cannot be relabeled as event occurrence time;
15. a chain without an anchored head/consistency receipt cannot claim complete history;
16. UOR unavailability disables only the optional UOR identity profile.

## Decision

This research justifies a **new ADR**, rather than extending ADR-021 or ADR-030.

- ADR-021 concerns portable memory-governance evidence and external trust/attestation boundaries.
- ADR-030 concerns whether a memory-derived projection is semantically compatible/current for a policy consumer.
- The new decision concerns the identity and evidence semantics of the temporal event itself before either portability or policy projection.

The proposed new invariant is:

> **Temporal claims that must remain historically tamper-evident belong inside a deterministic content commitment; signer and external witness evidence attest to that commitment without becoming memory authority or silently upgrading claimed time into trusted time.**

## Implementation recommendation

First slice:

1. language-neutral JSON Schema for `temporal-commitment` and signer/witness evidence;
2. Python-first reference implementation using existing RFC 8785 and `cryptography` dependencies;
3. optional injected UOR-Addr content-reference function, exact-pinned to v0.2.0 in focused CI;
4. Ed25519 signing profile for executable evidence only;
5. linear-stream predecessor profile plus explicit negative tests proving it is not global completeness/non-equivocation;
6. host-supplied verified witness evidence profile rather than building a TSA/transparency service;
7. adversarial fixtures and CI artifact;
8. wiki/visual only after the evidence survives review.

The first slice should **not** attempt a production RFC 3161 client, SCITT service, or Dogwood runtime integration. Those are optional adapter/profile follow-ups after the generic boundary is proven.
