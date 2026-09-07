# ADR-003: Crystallization Requires Certification

## Status

Accepted

## Context

Crystallization moves memory into a durable or exact-address retrievable state. That transition can create long-lived agent behavior, so it cannot be granted by repetition, retrieval frequency, saturation, relevance, or model confidence alone.

## Decision

Crystallization requires certification or an explicitly scoped policy exception whose authority is equivalent and auditable.

Certification may include human approval, test evidence, cryptographic verification, corroboration, policy approval, or a ledgered gate specific to the memory type.

## Consequences

### Positive

- prevents accidental permanence
- creates an audit point for durable memory
- preserves correction and dispute pathways
- aligns memory permanence with governance

### Negative

- adds friction to promotion
- requires implementation-specific certification mechanisms

## Required gate

A simplified gate is:

```text
can_crystallize =
  identity_resolved
  and provenance_present
  and lifecycle_candidate == true
  and pama_authority == allow
  and certification_gate == pass
  and dispute_status == clear
```

`lifecycle_candidate` may depend on calibrated probabilistic or heuristic signals. Those signals do not themselves certify the transition.

## Acceptance scope

Accepted establishes certification as a canonical durable-transition boundary. The precise certificate mechanism remains implementation- and memory-class-specific.

## Doctrine

Crystallization is a governed transition.

It is not a reward for being repeated often enough.
