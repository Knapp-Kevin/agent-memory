# Governed Uncertainty

Agent Memory does not require deterministic cognition. It requires uncertain inference to remain separate from permission to create consequences.

> **Probabilistic epistemics. Governed consequences.**  
> **Uncertainty may propose. Authority constrains.**

For canonical structural mutation, Agent Memory adopts an additional safeguard from ADR-032:

> **Memory shape may adapt. Authority over canonical structural mutation may not be probabilistic.**

## The control pipeline

```text
experience / request
      ↓
estimate / proposal
      ↓
governance envelope
      ↓
permitted action set
      ↓
selection
      ↓
committed consequence
      ↓
receipt + state transition
```

A selector may be deterministic or stochastic. The invariant is that it cannot choose outside the permitted set.

```text
selected_action ∈ permitted_action_set
```

## Where determinism belongs

Deterministic or formally bounded controls are especially valuable for:

- exact identity and references
- schema validity
- tenant and scope binding
- capability/authorization checks
- provenance requirements
- lifecycle transition legality
- policy-version binding
- state/version matching
- cryptographic verification

These are the substrate constraints that should not depend on a model “feeling confident.”

Canonical structural mutation has a deliberately stronger rule. Learned or probabilistic systems may discover and propose structural changes, but the authority determination that commits a canonical shape change must be either:

- a versioned deterministic rule proving the change is inside an explicitly authorized bounded envelope; or
- an explicit authorized human decision.

This does not make all governance computationally deterministic. It prevents uncertain structural discovery from becoming structural authority.

## Where probability belongs

Probabilistic, learned, or heuristic components are useful for:

- relevance
- confidence
- contradiction detection
- source trust
- sensitivity inference
- staleness
- utility
- clustering
- summarization
- causal hypotheses
- poisoning likelihood
- structural novelty and candidate schema discovery

The estimates can influence the decision. They do not define their own authority.

## Governance envelope

The governance layer maps uncertain evidence plus hard constraints into a finite set of allowed consequences.

Examples:

- permit ephemeral use but prohibit durable mutation
- permit recall but redact sensitive fields
- permit a reversible correction but prohibit destructive deletion
- allow stochastic ranking only among tenant-authorized candidates
- require verification before promotion
- block an action when delegation has expired
- autonomously rebuild a derived index under deterministic maintenance policy
- allow a bounded additive schema extension only when deterministic impact rules prove it is local, reversible, non-destructive, and non-authority-bearing
- require explicit human authority for semantic migrations, destructive schema retirement, scope widening, isolation changes, or authority-bearing structure

## Consequence classes

A useful mental model is to increase governance strength with permanence and blast radius:

| Class | Typical consequence |
|---|---|
| 0 | observation or ephemeral analysis |
| 1 | reversible runtime influence |
| 2 | durable mutation |
| 3 | shared, canonical, or sensitive effects |
| 4 | irreversible, security, or privilege-critical effects |

Structural changes additionally use ADR-032's S0-S3 classification so rebuild-only, bounded additive, semantic/migration-bearing, and destructive/authority-bearing changes do not collapse into one generic schema operation.

## Determinism is not automatically safety

A deterministic rule can be reproducibly wrong. A threshold can be exact while encoding bad assumptions. A formally bounded action set can still be unsafe if the policy is wrong.

The architecture therefore requires challenge tests for:

- brittle policies
- estimator-policy coupling
- state races
- hidden stochasticity
- false formalism
- over-conservative blocking
- human-review laundering
- stale structural impact analysis
- structural dependency and migration residue

## ADR status

**ADR-020 is Accepted.** Its stronger doctrine-maturity gate was satisfied by executable end-to-end evidence and adversarial negative paths showing uncertain proposals remain inside governed consequence boundaries.

**ADR-032 is Accepted.** It narrows the structural-mutation authority rule without claiming the implementation already supports autonomous low-risk schema adaptation. Current PAMA 1.2 remains conservatively review-first for `domain_schema_mutation`; issue #281 owns the evidence required before a narrower S0/S1 autonomous path is introduced.

Doctrine maturity and implementation maturity remain separate claims.

## Canonical sources

- Governed uncertainty: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/24-determinism-probability-and-governed-uncertainty.md
- ADR-020: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-020-probabilistic-discovery-deterministic-governance.md
- ADR-032: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-032-governed-mutable-memory-structure.md
- Mutable memory fabric: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/42-governed-mutable-memory-fabric.md
- Decision receipt schema: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/schemas/decision-receipt.schema.json

## Next

- **[PAMA](PAMA)** for proportional mutation authority
- **[Mutable Memory Fabric](Mutable-Memory-Fabric)** for configurable modules and structural adaptation
- **[Conformance and Evidence](Conformance-and-Evidence)** for the runtime proof bar
