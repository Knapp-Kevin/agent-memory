# Temporal Causality Layer

> Canonical requirement: [ADR-011](adr/ADR-011-temporal-causality-is-required-for-memory-evolution.md)

## Purpose

Memory is not only a collection of facts. It is a record of change.

A mature memory system must distinguish:

- what happened
- when it happened
- what was believed at the time
- what changed later
- what caused the change, when causality is actually supported

Chronology can often be observed directly. Causality usually cannot.

Therefore:

> Temporal order may be deterministic when timestamps and events are known. Causal attribution should preserve uncertainty unless independently established.

## Why temporal causality matters

Without temporal structure, memory systems confuse:

- stale facts with false facts
- superseded decisions with incorrect decisions
- sequence with causation
- current state with historical state
- future intentions with completed actions
- recurring patterns with causal laws

This causes bad retrieval and worse governance.

## Core temporal concepts

### Event time

When the underlying event occurred.

### Observation time

When the system observed or recorded the event.

### Valid time

When a claim was true or applicable.

### Transaction time

When the memory system committed the record.

### Decision time

When an authority approved a decision.

### Supersession time

When a newer state replaced an older current state.

### Expiry time

When a certification, policy, or memory should be re-evaluated.

These times may differ and should not be collapsed into one timestamp.

## Temporal memory record

Where relevant:

```text
memory_id
event_time
observation_time
valid_from
valid_until
recorded_at
superseded_at
source_refs
scope
causal_links
causal_confidence
estimator_ref
estimator_version
uncertainty
```

## Chronology versus causality

Observed sequence:

```text
A occurred
then B occurred
```

does not establish:

```text
A caused B
```

Causal links should identify their epistemic status:

```text
observed_dependency
explicit_human_rationale
verified_mechanism
statistical_association
model_inference
hypothesis
```

## Causal relation types

Useful relations include:

- caused
- contributed_to
- enabled
- blocked
- triggered
- motivated
- depended_on
- superseded_due_to
- correlated_with
- hypothesized_cause

Not every relation requires numerical probability. The system must distinguish observed/declared causal evidence from inferred causality.

## Deterministic temporal substrate

Where source data supports it, preserve exact:

- event identity
- timestamp
- sequence
- version
- commit hash
- policy version
- state transition
- supersession relationship

Do not ask a model to infer information the system already possesses deterministically.

## Probabilistic causal inference

Models may help infer:

- likely causes of failure
- relationships among historical events
- why a user preference appears to have changed
- whether one decision influenced another
- which prior memories explain a current state

These outputs should preserve:

```text
causal_hypothesis
supporting_evidence
alternative_hypotheses
confidence_or_probability
estimator_version
scope
```

Causal inference must not rewrite the historical event log.

## Stale versus false

A memory can be historically correct and currently stale.

Example:

```text
2026-01: service endpoint = A
2026-06: service endpoint changed to B
```

The first memory is not necessarily false.

Correct representation:

```text
A valid_until 2026-06
B valid_from 2026-06
current=B
```

## Supersession

Supersession should preserve:

```text
old_memory_ref
new_memory_ref
reason
supersession_authority
evidence_refs
effective_time
```

Do not delete historical state simply because it is no longer current.

## Correction

Correction differs from supersession.

```text
SUPERCESSION
old record was valid, new state applies later

CORRECTION
old record was wrong or materially incomplete within its claimed scope/time
```

The difference affects audit, retrieval, and trust.

## Temporal retrieval

A query should be able to express:

```text
current truth
truth at time T
state before event E
changes since T
why current state differs from prior state
what was believed when decision D was made
```

Retrieval ranking may be probabilistic, but valid-time filtering and scope rules should be explicit.

## Causally grounded retrieval

For consequential questions, the system may prefer memories that explain dependencies rather than merely resemble the query semantically.

Example:

```text
Why did deployment fail?
```

may require:

```text
recent configuration change
  -> changed dependency
  -> failed health check
  -> rollback decision
```

rather than the nearest vector match to the word "deployment."

## Temporal contradiction

Apparent contradictions should first test for time mismatch.

```text
claim A at T1
claim B at T2
```

may indicate supersession rather than factual conflict.

## Temporal causality and governance

Causal inference can influence priority and review, but should not create authority.

Wrong:

```text
model believes memory X caused failure -> permanently delete X
```

Correct:

```text
causal hypothesis -> evidence collection / review -> governed remediation
```

## Prospective memory

Temporal memory also points forward.

Prospective records may include:

```text
intention
trigger condition
due time
owner
completion state
cancellation state
policy scope
```

Remembering an obligation is distinct from executing it.

The execution system should verify current authority and conditions at action time.

## Procedural drift

A procedure that once succeeded can become stale as tools, APIs, environments, or policy change.

Track:

- procedure version
- environment version
- last successful use
- failure history
- dependency changes

A procedure's historical success is evidence, not eternal validity.

## Temporal decay

Time can decrease retrieval priority without implying falsity.

Decay policies should consider:

- memory type
- currentness requirements
- supersession links
- certification expiry
- evidence retention needs
- legal/privacy requirements

## Conformance cases

### Historically true, currently stale

Expected:

```text
historical query returns old fact
current query returns new fact
old fact is not labeled false solely because it is stale
```

### Out-of-order observation

An event occurred earlier but was observed later.

Expected:

```text
event_time and observation_time remain distinct
```

### Correlation mistaken for causation

Expected:

```text
causal claim remains hypothesis unless evidence supports stronger status
```

### Superseded policy

Expected:

```text
old decision remains auditable under old policy
new actions use current policy
```

### Prospective obligation after policy change

Expected:

```text
memory of obligation persists
execution re-checks current authority
```

### Procedure version drift

Expected:

```text
past success does not automatically certify current procedure
```

## Research signals

- [Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers](https://arxiv.org/abs/2603.07670) identifies causally grounded retrieval, contradiction handling, and long-horizon memory management as emerging agent-memory challenges.
- [Belief Memory: Agent Memory Under Partial Observability](https://arxiv.org/abs/2605.05583) supports retaining uncertainty instead of converting ambiguous observations into one deterministic historical conclusion.
- [From Agent Traces to Trust](https://arxiv.org/abs/2606.04990) emphasizes execution provenance, memory lineage, and process-level accountability, which are prerequisites for credible temporal explanation.

## Doctrine

Memory should preserve the difference between **what happened**, **what was believed**, **what became true later**, and **what the system merely infers caused it**.

Time can be exact while causality remains uncertain.
