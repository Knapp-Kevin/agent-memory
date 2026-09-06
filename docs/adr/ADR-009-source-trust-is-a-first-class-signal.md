# ADR-009: Source Trust Is a First-Class Signal

## Status

Accepted

## Context

Evidence and provenance tell the system where memory came from and what supports it. They do not fully answer whether a source remains reliable over time or within the current domain.

A low-quality source can produce high volume. A stale source can remain cited. An agent can recursively cite its own prior claims. A single-source assertion can become over-weighted if the system treats provenance as equivalent to trust.

## Decision

Source trust and reputation are first-class evidence signals.

Trust may be probabilistic, multidimensional, scoped, and time-varying. The system should preserve source class, reliability evidence, contradiction history, independence, freshness, domain scope, estimator provenance, and uncertainty where material.

Trust is not mutation authority, certification, or factual truth.

Canonical document:

- [`../16-source-trust-and-reputation.md`](../16-source-trust-and-reputation.md)

## Consequences

### Positive

- prevents high-volume low-quality sources from dominating memory
- improves evidence weighting
- supports conflict resolution
- helps detect recursive self-citation and manufactured corroboration
- makes source reliability visible to governance and certification

### Negative

- requires source metadata beyond simple provenance
- requires policy for demotion, rehabilitation, and scope
- may require calibration of trust estimators

## Required invariant

```text
source_trust -> evidence weighting
source_trust != authority
source_trust != certification
```

## Acceptance scope

Accepted establishes source trust as canonical doctrine. Specific reputation algorithms and thresholds remain implementation-specific and require calibration.

## Doctrine

Provenance says where memory came from.

Source trust estimates how much evidentiary weight that source deserves within a defined scope.
