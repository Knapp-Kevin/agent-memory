# ADR-004: PAMA Controls Mutation Authority

## Status

Accepted

## Context

Agentic memory systems need to adapt. Adaptation requires mutation of scores, links, summaries, states, procedures, capabilities, and sometimes durable memory records.

Without explicit authority, adaptive memory becomes silent self-modification.

**Proportional Adaptive Mutation Authority (PAMA) is native Agent Memory doctrine authored by Kevin R. Knapp.** Its systems-agnostic foundation is maintained in [`../pama/README.md`](../pama/README.md), with the memory-specific contract in [`../04-governance-and-pama.md`](../04-governance-and-pama.md).

PAMA is not an external dependency whose legitimacy depends on a standalone repository. Runtime systems implement its authority contract.

## Decision

PAMA controls mutation authority, or an implementation must provide an equivalent explicit authority model conforming to the same doctrine.

Any consequential transition that changes memory state, durable content, graph relations, promotion status, correction state, pruning/deletion state, sharing scope, capability authority, or certification status must pass through that authority boundary.

A PAMA decision considers separate dimensions including:

```text
M0-M5 mutation target class
lifecycle strength
requested operation
A0-A5 downstream authority
risk
scope
reversibility
actor / adaptive charter
evidence and uncertainty
policy state
```

Probabilistic or learned components may estimate confidence, trust, relevance, sensitivity, contradiction, utility, or risk. They may not grant themselves authority from those estimates.

A validated procedure or reusable capability does not automatically gain permission to execute externally. Reliability and authority remain separate.

## Consequences

### Positive

- makes memory mutation auditable
- scales autonomy by consequence, risk, authority, and reversibility
- permits low-risk adaptation without requiring human review for every observation
- prevents unauthorized rewriting of durable memory
- prevents validated capabilities from silently expanding their authority ceiling
- gives agents a clear boundary between inference, learning, procedure, permission, and governance

### Negative

- requires policy design
- requires mutation metadata and target/authority classification
- requires adaptive charter or equivalent actor-scope semantics
- may slow down high-impact memory changes

## Authority outcomes

Typical outcomes include:

```text
allow
allow_with_ledger
require_review
require_external_verification
block
```

Implementations may add bounded outcomes such as `abstain`, `quarantine`, or `collect_more_evidence` when their consequence semantics are explicit.

## Acceptance scope

Accepted establishes PAMA and explicit mutation authority as canonical Agent Memory doctrine.

Acceptance does **not** require one external PAMA codebase, standalone repository, or deployment topology. A conforming implementation may host the PAMA evaluator in a service, policy module, library, runtime, or other boundary, provided the semantics remain separately inspectable and auditable.

Accepted also does not claim runtime enforcement exists in every implementation. Runtime evidence remains required for implementation conformance and for the broader governed-uncertainty acceptance boundary in ADR-020.

## Doctrine

Adaptation is not authority.

Memory is not procedure.

Procedure is not permission.

Permission is not governance.

Capability is not authority.

Confidence is not authority.

The fact that an agent can change memory does not mean it is allowed to.
