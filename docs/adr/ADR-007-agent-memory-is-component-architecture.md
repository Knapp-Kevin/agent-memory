# ADR-007: Agent Memory Is a Component Architecture

## Status

Accepted

## Context

The Agent Memory doctrine combines native architecture with evidence and implementation lessons from systems such as UOR, EvolveAI, CodeGenome, COREFORGE Vault / Neurospace, FailSafe, Arbiter, and future conforming implementations.

**PAMA is native Agent Memory doctrine authored by Kevin R. Knapp**, not an external system being consolidated into the architecture.

These concepts and implementations are tightly related, but they do not all belong in the same implementation layer.

If everything is treated as one concept, the architecture becomes vague. If everything is split into unrelated projects, the doctrine fragments. If every adjacent product is named as a doctrine source, implementation history starts masquerading as architecture.

## Decision

Agent Memory is one overall architecture composed of bounded components.

The doctrine repo owns the shared architecture, vocabulary, contracts, native doctrine such as PAMA, segmentation rules, and conformance expectations.

Individual repos may own implementation slices after they provide a meaningful mapping to those contracts.

Components may contain deterministic, probabilistic, learned, or hybrid internals, but cross-component handoffs must preserve signal semantics, provenance, scope, uncertainty, and authority boundaries.

External implementation names are non-canonical examples. Their presence in an implementation map does not grant them ownership of the underlying doctrine concept.

## Component boundaries

The canonical components include:

1. Identity Substrate
2. Evidence and Provenance Substrate
3. Reality Graphs
4. Lifecycle Engine
5. Saturation and Decay Engine
6. Governance and Mutation Authority (PAMA)
7. Certification and Crystallization Gate
8. Runtime Memory Space
9. Context Assembly Surface
10. Correction and Dispute Surface
11. Durable Decision Memory
12. Conformance and Calibration Harness
13. Product and Agent Integrations

Additional components may be added when they have distinct cross-system interfaces and failure modes.

PAMA's native foundation is maintained in [`../pama/README.md`](../pama/README.md).

## Consequences

### Positive

- preserves one coherent architecture
- avoids monolithic implementation pressure
- gives every concept a home
- separates doctrine ownership from implementation ownership
- makes cross-repo adoption easier
- allows conformance to test boundaries rather than repo names
- supports product runtimes without letting them redefine doctrine locally
- prevents adjacent products from becoming accidental provenance requirements

### Negative

- requires adapter contracts between components
- requires careful documentation discipline
- requires cross-repo backlinks and implementation maps when external implementations are material
- creates composition-specific failure modes that must be tested
- requires explicit distinction between native doctrine and imported evidence or implementation patterns

## Rejected alternatives

### One monolithic memory system

Rejected because identity, inference, scoring, certification, governance, runtime use, privacy, correction, and durable decision memory have distinct failure modes.

### Completely separate concepts

Rejected because the concepts participate in governed memory transition/admission and need shared doctrine.

### Product-first definition

Rejected because products should conform to doctrine rather than redefine memory terms locally.

### Repository-name architecture

Rejected because an architecture should not require an adjacent product to remain named after the product stops adding unique implementation evidence.

## Acceptance scope

Accepted establishes component architecture as canonical doctrine. It does not freeze the component list forever, require one repository per component, or require external repositories for native Agent Memory doctrine.

## Doctrine

Agent Memory is unified by contracts, not repository location.

PAMA is native doctrine, not a repository dependency.

The system is one architecture, segmented into bounded components, composed through governed handoffs.
