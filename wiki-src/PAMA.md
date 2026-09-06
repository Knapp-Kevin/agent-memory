# PAMA

**Proportional Adaptive Mutation Authority (PAMA)** is native Agent Memory doctrine authored by Kevin R. Knapp.

PAMA solves a simple governance problem: agents need freedom to adapt, but not every learned change deserves the same authority to become durable, shared, or action-enabling.

> **Adaptation should be broadly available to authorized agents. Authority to make a mutation durable, influential, shared, or action-enabling should increase in proportion to the mutation's consequence.**

## Four dimensions

PAMA separates four dimensions that should not be reduced to one score:

| Dimension | Question |
|---|---|
| **M0–M5 target class** | What kind of state is being changed? |
| **Lifecycle strength** | How durable or reinforced is the state? |
| **Requested operation** | What mutation is being attempted? |
| **A0–A5 downstream authority** | What consequence can the resulting state create? |

The point is not to make every mutation wait for a person. Low-risk, reversible learning should be cheap. Durable or high-consequence changes should require stronger authorization and evidence.

## Core separations

```text
adaptation != authority
memory != procedure
procedure != permission
permission != governance
```

A validated procedure can become trusted without gaining permission to execute externally. A highly reinforced memory can remain barred from governance effects. A high-confidence estimate can still have zero mutation authority.

## PAMA in the governed-memory loop

```text
proposal
  ↓
identify target + operation + consequence
  ↓
resolve authority ceiling
  ↓
construct permitted action set
  ↓
select only inside that set
  ↓
commit + receipt
```

The required invariant is:

```text
selected_action ∈ permitted_action_set
```

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/pama-decision-flow.svg">
    <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/pama-decision-flow-light.svg">
    <img src="https://raw.githubusercontent.com/MythologIQ-Labs-LLC/agent-memory/main/assets/diagrams/pama-decision-flow-light.svg" alt="PAMA decision flow showing mutation proposal classification, authority floors, policy modifiers, authority outcomes, permitted action set construction, and commit or deferral with evidence" width="100%">
  </picture>
</p>

The diagram is an explanatory flow, not a replacement for the canonical PAMA taxonomy or decision table. PAMA first keeps target class, lifecycle strength, requested operation, and downstream authority distinct, then composes those dimensions with consequence, actor, evidence, uncertainty, and policy. Foundational class floors and the operation/risk table establish a minimum authority outcome; defined modifiers may escalate it or relax only explicitly relaxable cases. `block` remains absorbing, deferral does not grant authority, and confidence, saturation, repetition, or validated capability never create a broader authority ceiling.

## Why PAMA matters for memory

Without an authority model, memory systems tend to let confidence, repetition, relevance, or reinforcement quietly become permission. That creates several failure modes:

- hallucinations becoming durable because they were repeated
- summaries laundering authority from weaker sources
- learned procedures gaining execution rights without review
- useful memories being granted scope they never earned
- agents deleting or rewriting state because a utility model said it looked stale

PAMA keeps learning pressure separate from consequence authority.

## Human review is not the default gate

PAMA is explicitly compatible with autonomy. The governance result can be:

- permit automatically
- permit with constrained scope
- require stronger evidence
- require verification
- require review
- block

Human approval is one possible consequence class, not the universal answer to uncertainty.

## Canonical sources

- PAMA foundation: https://github.com/MythologIQ-Labs-LLC/agent-memory/tree/main/docs/pama
- Governance and PAMA: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/04-governance-and-pama.md
- Decision table: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/33-pama-decision-table.md
- ADR-004: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/adr/ADR-004-pama-controls-mutation-authority.md
- Machine-readable contract: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/schemas/pama-decision.schema.json

## Next

- **[Governed Uncertainty](Governed-Uncertainty)** for the estimator/governance boundary
- **[Implementation Guide](Implementation-Guide)** for runtime mapping
