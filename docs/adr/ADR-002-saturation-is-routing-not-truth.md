# ADR-002: Saturation Is Routing, Not Truth

## Status

Accepted

## Context

Saturation is useful for deciding whether memory should persist, decay, route, or become a crystallization candidate. However, high saturation can be produced by flawed signals such as access-spam, repeated incorrect claims, narrow fiber definitions, or estimator drift.

A fully pinned object can still be wrong.

## Decision

Saturation is a calibrated lifecycle routing score.

It must not be treated as correctness, integrity, identity, certification, or mutation authority.

## Consequences

### Positive

- prevents hallucination permanence
- allows saturation to support routing without overclaiming truth
- makes trap-class testing mandatory
- preserves the role of certification, provenance, and PAMA

### Negative

- requires more than one signal to promote memory
- requires calibration before thresholds can be trusted

## Required rule

```text
high_saturation != true
high_saturation != certified
high_saturation != authorized
high_saturation == candidate_for_routing_or_review
```

## Acceptance scope

Accepted means this separation is canonical doctrine. Specific saturation formulas, estimators, thresholds, and calibration scopes remain implementation concerns and must be validated independently.

## Doctrine

Saturation can propose.

Governance and certification determine consequence.
