# ADR-008: Memory Threat Model Is Required

## Status

Accepted

## Context

Trap classes such as access-spam and confidently-wrong memory are necessary but insufficient.

Persistent memory creates additional threats including poisoning, sleeper behavior, authority laundering, recursive self-citation, provenance stripping, scope leakage, stale authorization, deletion residue, unsafe composition, estimator manipulation, and policy bypass.

Without a threat model, conformance can appear strong while ignoring the seams where persistent state becomes a control channel.

## Decision

Agent Memory must include and maintain a formal memory threat model.

The threat model defines threat classes, trust boundaries, affected components, mitigations, required invariants, and adversarial conformance fixtures.

Canonical document:

- [`../15-memory-threat-model.md`](../15-memory-threat-model.md)

## Consequences

### Positive

- expands safety beyond simple trap classes
- gives PAMA, recall governance, privacy, and certification concrete adversarial cases
- improves conformance design
- makes memory-specific security boundaries explicit

### Negative

- increases documentation and fixture burden
- requires implementations to expose provenance, scope, authority, and audit data
- requires ongoing updates as attacks evolve

## Acceptance scope

Accepted means a formal memory threat model is canonical architecture doctrine and the foundational threat-model document now exists. It does not claim every required adversarial fixture or runtime mitigation is implemented.

## Doctrine

A memory system is not trustworthy unless it defines how persistent state can be attacked, laundered, leaked, corrupted, or incompletely forgotten.
