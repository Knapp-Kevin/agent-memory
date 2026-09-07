# Capability Qualification v1.2 and Provider Portability

Status: **bounded implementation for issue #350**

Qualification v1.2 extends the reusable component qualification harness from #300 so Capability Contract v3 behavior and operational guarantees are part of the evidence applicability boundary.

## Why v1.2 exists

Qualification v1.1 already binds:

```text
component / implementation
capability
adapter
qualification profile
runtime / configuration / fixture
source rights
evidence
maturity
```

Capability Contract v3 added a separate operational contract for:

```text
write atomicity
concurrency control
idempotency
restart recovery
reconciliation
```

A qualification earned before those properties were part of its applicability key must not silently certify them later. Likewise, a provider whose declared behavior or operational posture changes must not retain an old qualification merely because its component/version strings were left unchanged.

The v1.2 boundary is therefore:

```text
v1.1 applicability
+ component profile version
+ state posture
+ scope posture
+ failure posture
+ capability authority effect
+ behavior contract
+ operational contract
= v1.2 applicability
```

These fields are evidence/eligibility metadata. They do not create memory authority.

## Backward compatibility

Historical v1.1 records remain valid historical qualification evidence.

```text
v1.1 qualification
!= v1.2 contract-bound qualification
```

A v1.1 record cannot be supplied as proof that a provider satisfies a v3 operational requirement. Requalification or explicit compatibility evidence is required.

## Contract-bound applicability

A v1.2 `QualifiedCapabilityContract` records the exact capability posture that was exercised:

- component capability profile version;
- state posture;
- scope posture;
- failure posture;
- authority effect;
- lifecycle/behavior contract;
- operational contract when the component profile is v3.

The serialized contract participates in the qualification applicability digest. Changing correction behavior, restart recovery, reconciliation, or another bound field therefore changes applicability even if the surrounding component identity remains unchanged.

Runtime use additionally compares the qualification with the **current** component declaration. A stale declaration/qualification pair fails closed.

## Provider substitution proof

Provider substitution is evaluated against one explicit `CapabilityRequirement`.

Each provider must independently satisfy:

```text
capability identity / version
minimum earned maturity
current qualification applicability
runtime-allowed source rights
state posture
scope posture
behavior requirement
operational requirement
authority posture preservation
```

The two providers do **not** need identical internal operational implementations.

For example, one provider may satisfy a durable requirement with:

```text
single_record_atomic
optimistic_revision
durable_keyed
reconstructable
deterministic_readback
```

while another satisfies the same request with:

```text
transactional_multi_record
serializable
durable_keyed
checkpoint_replay
authoritative_rebuild
```

If both are explicitly allowed by the caller's requirement, the providers may be substitutable. Provider equality is neither required nor claimed.

By contrast, a process-local provider is ineligible for a requirement that demands durable restart reconstruction and independent reconciliation even when its retained-content semantics look identical.

## Source-rights gate

Executable runtime substitution requires `runtime_allowed` source rights.

A `comparator_only` qualification remains useful evidence but cannot be turned into a runtime dependency merely because it passed behavioral tests. Legal posture is therefore preserved as part of runtime eligibility rather than buried in a README footnote after somebody notices the license.

## Authority boundary

Qualification and substitution remain non-authoritative:

```text
qualified provider != authorized memory consequence
better operational guarantees != PAMA authority
provider substitution != recall admission
provider substitution != mutation permission
provider-native confidence/verdict != action authority
```

The substitution evidence itself always reports `authority_effect: none`. It also requires the two provider capability declarations to preserve the same capability authority posture so a swap cannot silently change `none` into `proposal_only` or vice versa.

## First proof boundary

Issue #350 intentionally uses synthetic external-provider declarations and qualification evidence.

The proof includes:

- two materially different durable providers satisfying one `epistemic_belief_memory` requirement;
- a process-local provider rejected by durable restart/reconciliation requirements;
- behavior/operational contract drift invalidating prior qualification;
- historical v1.1 evidence rejected as v3 operational proof;
- comparator-only source rights rejected for runtime substitution;
- authority-posture drift rejected.

Synthetic profiles prove the admission/substitution contract. They do **not** qualify Neo4j, Kuzu, MemOS, Supermemory, Cloudflare, or another external implementation.

## Next external-provider slice

A real provider qualification must now supply primary-source and executable evidence for the exact contract it claims:

```text
exact provider source/release/package
+ exact adapter
+ exact qualification profile
+ exact fixture/runtime/configuration
+ raw provider evidence
+ behavior checks
+ operational checks
+ source-rights posture
-> v1.2 contract-bound qualification
```

Only after that qualification exists may the provider participate in substitution against another independently qualified provider. Product popularity, architecture resemblance, or a vendor feature page is not a qualification record.
