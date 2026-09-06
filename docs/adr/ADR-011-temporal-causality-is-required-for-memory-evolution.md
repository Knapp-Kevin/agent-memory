# ADR-011: Temporal Causality Is Required for Memory Evolution

## Status

Accepted

## Context

Memory changes over time. A memory may become stale, superseded, corrected, disputed, or historically relevant.

Time-based decay alone does not explain why memory changed.

However, exact chronology and causal interpretation are not the same epistemic problem. Event order may be known deterministically while causality remains uncertain.

## Decision

Agent Memory must include explicit temporal and causal representation sufficient to distinguish history, current state, supersession, correction, and causal hypotheses.

The architecture must preserve exact event/observation/valid times where known and label inferred causal relations with provenance and uncertainty.

Canonical document:

- [`../18-temporal-causality-layer.md`](../18-temporal-causality-layer.md)

## Consequences

### Positive

- distinguishes stale from superseded and false
- supports temporal and causal recall
- preserves decision and correction history
- avoids treating sequence as proof of causation
- supports prospective and procedural drift handling

### Negative

- requires multiple temporal fields and causal-link modeling
- increases complexity of historical queries and lifecycle transitions

## Required distinctions

The architecture must distinguish:

- event time from observation/record time
- stale from false
- superseded from corrected
- historical from current truth
- observed dependency from inferred causality
- prospective obligation from action execution

## Acceptance scope

Accepted establishes temporal evolution and uncertainty-aware causal representation as canonical doctrine. It does not claim a universal causal-inference algorithm.

## Doctrine

Time can be exact while causality remains uncertain.

Memory evolves through events, evidence, correction, supersession, and sometimes causal relationships whose strength must remain explicit.
