# ADR-013: Governed Recall Planner Is Required

## Status

Accepted

## Context

Retrieval is not memory.

A governed memory system needs recall planning that respects current state, certification, dispute status, sensitivity, source trust, tenancy, authority, and context boundaries.

Candidate generation may legitimately be probabilistic. Recall admission is a governed decision.

## Decision

Agent Memory includes a governed recall planner or equivalent recall-admission component contract.

The planner composes exact lookup, graph traversal, evidence search, semantic retrieval, temporal retrieval, procedural recall, and policy constraints without treating relevance as permission.

## Required invariant

```text
candidate_generation may be probabilistic
relevance != permission
prohibited_memory never enters admitted context
```

## Consequences

### Positive

- prevents disputed or wrong-scope memory from entering context as canonical
- distinguishes exact lookup from similarity retrieval
- supports recall explanations and composition checks
- makes context assembly policy-aware

### Negative

- adds a governance step before context assembly
- requires recall metadata and destination context
- may reduce convenient but unsafe recall

## Acceptance evidence

Canonical contract:

- [`../26-governed-recall-planner.md`](../26-governed-recall-planner.md)

Repository conformance fixtures include:

- `cross-tenant-relevance-trap.json`
- `stochastic-retrieval-policy-envelope.json`
- `unsafe-multi-memory-composition.json`
- `uncertain-sensitivity-before-export.json`

These fixture definitions and schemas are validated by the repository's `Validate Doctrine Evidence` workflow.

## Acceptance scope

Accepted establishes governed recall as canonical doctrine. It does not claim any particular runtime implementation has passed the behavioral cases end to end.

## Doctrine

Retrieval finds candidates.

Governed recall decides what may enter context.
