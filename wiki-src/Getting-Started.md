# Getting Started

Agent Memory is a reference architecture, not a single memory library. The fastest way to understand it is to follow the decisions a memory system must make from experience to durable state and back into active context.

## Ten-minute tour

### 1. Start with the definition

A memory is not merely something retrievable.

> **Agentic memory is retained state that can alter future agent behavior across a meaningful persistence boundary.**

That includes facts, episodes, preferences, procedures, corrections, decisions, policies, evidence, and inherited state.

### 2. Follow the memory lifecycle

Think in seven functions:

`ENCODE → RETAIN → CONSOLIDATE → RETRIEVE → REVISE → FORGET → INHERIT`

Each function has its own evidence and authority requirements. A system can be excellent at retrieval while still being unsafe at retention, correction, or deletion.

Read: **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)**.

### 3. Separate estimates from permission

A model may estimate that a memory is relevant, trustworthy, contradictory, sensitive, stale, or valuable. None of those estimates automatically creates authority.

`estimate / proposal → governance envelope → permitted actions → selection → committed consequence`

Read: **[Governed Uncertainty](Governed-Uncertainty)**.

### 4. Learn PAMA

**Proportional Adaptive Mutation Authority** controls how much authority is required for a mutation based on what is being changed and what downstream consequence that change can create.

Low-risk reversible adaptation should not require a human approval ceremony. Durable, shared, security-sensitive, or action-enabling changes require stronger authority.

Read: **[PAMA](PAMA)**.

### 5. Treat forgetting as architecture

Forgetting can mean decay, suppression, pruning, archival, compression, supersession, redaction, tombstoning, cryptographic deletion, or model unlearning. Those are not interchangeable operations.

Read: **[Lifecycle and Forgetting](Lifecycle-and-Forgetting)**.

### 6. Demand evidence for runtime claims

Agent Memory distinguishes doctrine, structural evidence, implementation mapping, observed behavior, and runtime proof.

A valid fixture is not a deployed guarantee. A passing benchmark is not universal conformance. A product README is not evidence that negative paths work.

Read: **[Conformance and Evidence](Conformance-and-Evidence)**.

## Repository map

| Area | Canonical location |
|---|---|
| Architecture spine | `docs/00` through `docs/10` |
| Composition, trust, security, time, privacy | `docs/11` through `docs/19` |
| Theory, research, governed uncertainty | `docs/20` through `docs/25` |
| Operational contracts | `docs/26` onward |
| Native PAMA doctrine | `docs/pama/` |
| Architecture decisions | `docs/adr/` |
| Machine-readable contracts | `schemas/` |
| Conformance scenarios | `fixtures/` |
| External source-rights records | `sources/` |

Full index: https://github.com/MythologIQ-Labs-LLC/agent-memory/blob/main/docs/README.md

## Three rules worth memorizing

1. **Retrieval is not memory.**
2. **Confidence is not authority.**
3. **Proposal is not commit.**

Those three distinctions prevent a surprising amount of architectural nonsense.

## Next

- New to the vocabulary: **[Core Concepts](Core-Concepts)**
- Building a runtime: **[Implementation Guide](Implementation-Guide)**
- Reviewing governance: **[PAMA](PAMA)**
- Evaluating claims: **[Conformance and Evidence](Conformance-and-Evidence)**
