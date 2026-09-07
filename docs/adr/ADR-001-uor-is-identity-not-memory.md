# ADR-001: UOR Is Identity, Not Memory

## Status

Accepted

## Context

Work from the UOR Foundation materially informed Agent Memory's separation between **exact object identity** and **memory lifecycle/governance**.

A recurring architectural risk is treating content identity, addressability, retrieval relevance, lifecycle state, and mutation authority as if they were one property. They are not.

The useful distinction is:

- identity: what object is this?
- lifecycle: should this object persist, decay, route, consolidate, crystallize, or be forgotten?

The historical relationship to UOR is intellectual lineage and technical alignment. Agent Memory does **not** require the UOR Framework as a repository-wide runtime dependency.

## Decision

Agent Memory adopts the following architectural boundary:

> **Exact identity is a substrate concern. Memory lifecycle and governance are separate concerns.**

When UOR is used, it is a strong candidate identity substrate for deterministic object identity, content addressability, and exact object resolution.

A conforming Agent Memory implementation MAY use UOR or another exact identity mechanism, provided it preserves the same separation and does not allow probabilistic relevance, lifecycle scoring, confidence, saturation, or governance outcomes to mutate object identity implicitly.

UOR itself does not own Agent Memory lifecycle policy, saturation policy, mutation authority, recall governance, deletion semantics, or certification.

## Relationship boundary

This ADR records an architectural lesson informed by UOR Foundation work. It does not create:

- a mandatory UOR package or runtime dependency;
- joint ownership of Agent Memory doctrine;
- a claim that Agent Memory is a UOR implementation;
- a claim that the UOR Foundation endorses Agent Memory; or
- a transfer of either project's licensing or intellectual-property terms to the other.

See [`../40-aligned-projects-and-intellectual-lineage.md`](../40-aligned-projects-and-intellectual-lineage.md) for the repository-wide recognition convention.

## Consequences

### Positive

- preserves clean identity semantics;
- prevents lifecycle policy from corrupting identity;
- allows multiple memory runtimes and identity mechanisms to implement the architecture;
- preserves UOR as a meaningful aligned foundation without converting it into compulsory infrastructure;
- keeps crystallization as a governed transition rather than an address side effect; and
- makes licensing and implementation ownership easier to reason about.

### Negative

- implementations must explicitly select and document an identity mechanism;
- UOR-specific capabilities cannot be assumed in implementations that choose another mechanism; and
- interoperability profiles may need adapters between different exact-identity schemes.

## Acceptance scope

Accepted means the **identity-versus-memory boundary** is canonical doctrine.

It does not claim that every implementation uses UOR, that Agent Memory conforms to the UOR ontology, that any UOR integration is complete, or that a formal partnership exists.

## Doctrine

When UOR is present, **UOR answers what the object is**.

Agent Memory answers **what retained state is allowed to become and what consequences it is allowed to have**.
