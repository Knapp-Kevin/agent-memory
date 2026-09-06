# ADR-006: Neurospace Is Runtime Memory Space

## Status

Accepted

## Context

COREFORGE Vault and Neurospace provide a product/runtime model where agents assemble, traverse, retrieve, and use memory.

Runtime memory has different responsibilities from identity, scoring, governance, certification, and canonical doctrine.

## Decision

Neurospace is the canonical operational runtime-memory role in the current implementation map.

It consumes identity, evidence, lifecycle, governance, certification, sensitivity, and scope signals to support agent recall and action. It must not redefine those layers silently.

Candidate generation and ranking may be probabilistic. Recall admission must still enforce policy, tenant, sensitivity, dispute, and scope constraints.

## Consequences

### Positive

- keeps COREFORGE product behavior aligned with doctrine
- separates user-facing memory use from canonical permanence
- enables correction, dispute, and governance UI flows

### Negative

- requires Neurospace to expose state and authority metadata
- requires runtime memory to distinguish operational use from canonical use

## Runtime rule

```text
operationally_useful != canonical
highly_relevant != authorized_for_context
```

A memory may be useful in a context window without being crystallized, and a relevant memory may still be prohibited from recall.

## Acceptance scope

Accepted establishes the architectural role. It does not claim the current COREFORGE/Neurospace implementation satisfies every doctrine or conformance requirement.

## Doctrine

Neurospace is where memory is used.

It is not where memory becomes true or authorized by convenience.
