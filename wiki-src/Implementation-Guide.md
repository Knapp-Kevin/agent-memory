# Implementation Guide

Agent Memory is implementation-neutral. A runtime does not need to copy one storage engine or framework. It needs to preserve the architectural boundaries that make retained state governable.

## Minimal runtime loop

A useful implementation should be able to show this chain explicitly:

```text
observation / request
  → evidence + provenance
  → estimate / proposal
  → PAMA governance decision
  → permitted action set
  → selected action
  → state transition
  → decision receipt
  → retained state
  → governed recall
```

If one opaque model call silently performs all of those jobs, the implementation may still work, but it is difficult to audit, test, constrain, or recover.

## Minimal component responsibilities

| Component | Responsibility |
|---|---|
| Identity | Stable object and reference identity |
| Evidence/provenance | Source, derivation, time, witnesses |
| Lifecycle | Explicit state and legal transitions |
| Estimators | Relevance, trust, contradiction, sensitivity, utility, risk, etc. |
| PAMA/governance | Authority envelope and permitted consequences |
| Commit layer | Explicit mutation + receipt |
| Storage/projections | Canonical and derived retained state |
| Recall planner | Candidate retrieval + governed admission + composition |
| Governance Context Projection | Vendor-neutral remembered context for external governance consumers |
| Observability | Transition and decision evidence |
| Recovery | Replay, rollback, compensation |

## Canonical versus derived state

A production implementation should declare which artifacts are authoritative and which are projections.

Possible projections include:

- vector indexes
- graph projections
- summaries
- caches
- compiled knowledge
- search indexes
- model-side derived state
- governance-context projections

Derived artifacts need dependency metadata if correction, deletion, or replay is expected to propagate reliably.

Governance Context Projection is explicitly derived state. It should be discardable and rebuildable from canonical memory plus declared derivation logic.

## Required version bindings

Runtime evidence should bind decisions to the versions that produced them:

```text
memory/state version
schema version
policy version
estimator/model version
calibration context
authority/delegation state
fixture/test version when evaluating conformance
```

Without those bindings, later replay can reproduce syntax while missing the actual decision context.

## Governed recall

Recall is not just nearest-neighbor retrieval.

A robust path is:

```text
candidate retrieval
  → identity/scope checks
  → sensitivity/privacy checks
  → freshness/conflict evaluation
  → policy admission
  → ranking among admitted candidates
  → context composition
```

Stochastic ranking can be perfectly acceptable **after** prohibited candidates are removed from the reachable set.

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/governed-recall-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/governed-recall-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/governed-recall-flow-light.svg" alt="Governed recall pipeline showing request and scope resolution, candidate generation and normalization, recall admission, ranking only among admitted candidates, composition risk checks, context budgeting, governed assembly, and recall explanation" width="100%">
  </picture>
</p>

The diagram preserves the canonical ordering rather than treating retrieval score as admission. Candidate generation may be probabilistic, but identity, tenancy, purpose, scope, sensitivity, destination, delegation, dispute/certification state, freshness, and policy constrain what may enter context. Ranking occurs only after admission. Composition risk and context budgeting remain separate governed stages, and a blocked candidate cannot re-enter merely because randomness or a stronger score prefers it.

## Building a governance consumer

Do not put a consumer's policy vocabulary directly into the canonical memory model.

Use the three-layer boundary:

```text
Agent Memory core
  → Governance Context Projection
  → consumer-specific adapter
  → policy / approval / enforcement runtime
```

Agent Memory core should expose generally useful primitives such as provenance, scope, validity, rationale, outcome, correction/supersession state, authority context, and uncertainty.

The Governance Context Projection may derive:

- relevant precedent references
- supportive / cautionary / contradictory polarity
- material conditions
- condition match / mismatch / unknown state
- freshness and validity
- negative precedent
- outcome and incident references
- derivation metadata

The projection must not emit a final permission or standing grant.

The consumer adapter owns:

- product-specific risk semantics
- policy vocabulary
- verdict mapping
- consumer API compatibility
- retries/timeouts specific to that consumer
- approval UX

For example, DashClaw- or AGT/ACS-specific fields belong in those consumer adapters, not in Agent Memory's canonical memory-unit schema.

See **[Governance Projection](Governance-Projection)**.

## Deterministic precedent first

Start with explicit material-condition comparison before semantic similarity.

```text
same protected-target status?
same force semantics?
same environment?
same policy version?
same scope?
same authority context?
```

Represent each condition as:

```text
match
mismatch
unknown
```

A semantic model may later retrieve candidate precedents, but the model must preserve estimator identity/version/uncertainty and cannot independently turn similarity into authorization.

## Decision receipts

A consequential memory mutation should be reconstructable. Useful receipt fields include:

- request
- state snapshot
- estimator versions/calibration
- uncertainty summary
- policy version
- authority references
- permitted/prohibited actions
- selected action
- selection mode/seed where relevant
- before/after state
- supporting evidence
- receipt hash or integrity reference
- recovery reference

An external governance decision or execution result can later become new Agent Memory evidence, but it must re-enter through normal provenance, lifecycle, scope, and authority boundaries. An integration callback is not a privileged memory write path.

## Start small

A minimal reference adapter should prove the boundaries before becoming a feature-rich memory product.

Recommended first milestone:

1. one canonical memory store
2. one probabilistic estimator
3. one explicit PAMA policy layer
4. one governed recall path
5. decision receipts
6. a handful of adversarial fixtures
7. repeated runs for stochastic behavior

For governance-consumer interoperability, add separately:

1. one deterministic governance-context projection builder
2. one matching-precedent fixture
3. one misleading near-match fixture
4. one negative-precedent case
5. proof that the projection carries no final consumer verdict
6. a fake consumer before a vendor-specific adapter

Then add richer graphs, consolidation, portability, semantic precedent retrieval, and real consumer adapters.

## Implementation evidence

When mapping a real system, pin the exact release or commit and document both positive and negative paths. Use the repository's **Implementation or conformance evidence** issue form.

## Canonical sources

- Component architecture: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/11-component-architecture.md
- Composition boundaries: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/13-system-composition-boundaries.md
- Recall planner: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/26-governed-recall-planner.md
- Schema registry: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/27-schema-registry-and-type-evolution.md
- Adapter contracts: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/34-adapter-contracts.md
- Governance Context Projection profile: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/profiles/governance-context-projection-profile.md
- Observability: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/30-memory-observability-and-audit-events.md
- Recovery/replay: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/31-recovery-rollback-and-replay.md

## Next

- **[Governance Projection](Governance-Projection)** for governance-consumer integration
- **[Conformance and Evidence](Conformance-and-Evidence)** for proving behavior
- **[Security and Privacy](Security-and-Privacy)** for negative paths
