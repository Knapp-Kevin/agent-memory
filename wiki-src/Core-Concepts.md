# Core Concepts

Agent Memory is easiest to understand as a set of boundaries. Most failures happen when two useful concepts are collapsed into one convenient but misleading field.

## Core definition

> **Agentic memory is retained state that can alter an agent's future interpretation, reasoning, planning, tool use, action, or adaptation across a meaningful persistence boundary.**

That includes facts, episodes, preferences, procedures, corrections, decisions, policies, evidence, and inherited state.

## Persistence horizons

A horizon answers **how far state survives**, not what kind of state it is.

`Immediate → Working → Session → Episodic → Long-term → Remote → Inherited`

A procedural memory can be session-local or inherited. A decision record can be short-lived or permanent evidence. “Long-term memory” is therefore a horizon, not one universal storage bucket.

## Memory content types

Common types include:

- observation
- episodic memory
- semantic memory
- procedural memory
- prospective memory
- preference
- relationship state
- policy
- failure
- correction
- decision
- evidence
- compact environment/model state
- inherited memory

## Signals are not interchangeable

| Signal | Means | Does **not** mean |
|---|---|---|
| Identity | Exact object/reference | Truth or usefulness |
| Confidence | Support for an estimate | Authority |
| Probability | Uncertainty with defined semantics | Generic score |
| Similarity | Representational closeness | Correctness |
| Source trust | Expected reliability in a scope | Permission |
| Relevance | Usefulness to the current task | Recall authorization |
| Saturation | Lifecycle persistence pressure | Truth |
| Sensitivity | Handling/privacy risk | Low utility |
| Scope | Where memory is valid/visible | Global truth |
| Authority | Permission for a consequence | Evidence quality |
| Certification | Required confirmation passed | Immutability |
| Contradiction | Retained states conflict | Automatic winner selection |

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/strength-stability-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/strength-stability-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/strength-stability-flow-light.svg" alt="Agent Memory strength and stability map showing distinct evidence confidence, source trust, saturation, contradiction pressure, certification, lifecycle stability, and PAMA authority signals" width="100%">
  </picture>
</p>

The diagram keeps those signals separate. Evidence quality, meaningful reuse, corroboration, and verification can strengthen the case for persistence. Contradiction, expiry, invalidation, uncertainty, and drift can increase decay, review, or demotion pressure. Neither direction grants authority to promote, share, execute, or delete. PAMA or equivalent governance determines permitted consequence, and any threshold or hysteresis value remains a calibrated operating choice rather than doctrine.

## High-value invariants

```text
identity != memory
retrieval != memory
confidence != authority
trust != authority
relevance != permission
saturation != truth
utility != deletion authority
proposal != commit
canonical != derived
raw delete != full delete
rebuild != maintenance
historical truth != current truth
chronology != causality
uncertain sensitivity != non-sensitive
adaptation != authority
memory != procedure
procedure != permission
permission != governance
```

## Historical truth versus current truth

A memory can remain historically valid while no longer describing the present.

```text
historically true != currently true
stale != false
stale != residual
superseded != corrected
```

Agent Memory keeps those distinctions because silently overwriting history destroys evidence.

The last two lines carry more weight than they look. *Stale* means a source has changed, so derived content may be wrong and recomputing it may help. *Residual* means a source was deleted, so derived content may be prohibited and recomputing it helps nobody — only the deletion authority can resolve that. Collapsing both into "invalid" is the most natural mistake in this area and the most expensive. See **[Canonical and Derived State](Canonical-and-Derived-State)**.

## Canonical sources

- Glossary: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/00-glossary.md
- Layer model: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/01-layer-model.md
- Scoring and decay: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/03-scoring-and-decay.md
- Governance and PAMA: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/04-governance-and-pama.md
- Source trust and reputation: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/16-source-trust-and-reputation.md
- Memory theory: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/22-agentic-memory-theory-and-development.md

## Next

- **[PAMA](PAMA)** for adaptive authority
- **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)** for persistence and deletion
- **[Governed Uncertainty](Governed-Uncertainty)** for probabilistic inference under bounded authority
