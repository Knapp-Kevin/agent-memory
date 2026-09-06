# ADR-035 Cognitive Mesh Reference Evidence

Status: **reference slice implemented; ADR-035 is Accepted**

This evidence slice proves a bounded composition path for the Cognitive Mesh proposed by ADR-035. It does not claim a complete cognitive substrate, production cognition, or universal ontology.

## Evidence boundary

The executable path is:

```text
experience / observation
  -> stable logical cognitive identity + evidence
  -> typed Cognitive Metabolism / Reality Graph / predictive signal
  -> Agent Memory proposal
  -> deterministic PAMA authority envelope
  -> governed durable commit or refusal
  -> substrate candidate retrieval
  -> governed recall admission
  -> active cognition
```

The reference implementation is:

- `reference/agentmem_ref/memory/cognitive_mesh.py`
- `reference/tests/test_cognitive_mesh.py`
- `reference/run_cognitive_mesh.py`
- `.github/workflows/cognitive-mesh-evidence.yml`

It composes existing Agent Memory primitives rather than creating a parallel memory runtime:

- `reference/agentmem_ref/runtime/adapter.py`
- `reference/agentmem_ref/core/policy.py`
- `reference/agentmem_ref/core/contextual_recall.py`
- `reference/agentmem_ref/state/substrate.py`

## Minimal Cognitive Mesh contract

The slice introduces three bounded reference types:

```text
CognitiveExperience
  source observation retained as evidence

MeshObject
  stable representation-neutral logical cognitive identity

CognitiveSignal
  typed non-authoritative provider output
```

`MeshObject.object_type` and `CognitiveSignal.module_role` are deliberately open strings. This slice does not establish a closed universal cognitive ontology.

Logical Agent Memory identity remains distinct from provider storage identity:

```text
MeshObject.object_ref
  !=
TemporalGraph Fact.uuid
```

Provider replacement therefore need not rewrite the logical object identity.

## Provider signals are proposals, not authority

A `CognitiveSignal` may preserve:

```text
module role
source component
signal type
estimator identity/version
confidence
evidence references
provider-native verdict
```

Those fields are evidence and proposal context only.

The signal does not choose the PAMA outcome and has no direct commit path.

The focused adversarial cases prove:

```text
reinforcement confidence 1.0
  != crystallization authority

graph confidence 1.0
  != durable-memory authority

prediction confidence 1.0 + provider PASS
  != external-action authority
```

For otherwise identical low-risk crystallization proposals, confidence `0.01` and `1.0` both resolve to `require_review` and neither commits.

## Happy path

The positive fixture uses an EvolveAI-labelled Cognitive Metabolism signal to propose low-risk promotion of a semantic candidate.

The expected sequence is:

```text
experience retained
  -> proposal carries evidence + estimator metadata
  -> PAMA returns allow_with_ledger
  -> governed adapter writes provider fact + receipt
  -> matching isolation-domain recall retrieves candidate
  -> current contextual policy admits candidate
  -> logical object enters active cognition
```

The EvolveAI label identifies the source component in the fixture. It does not assert additional EvolveAI capability qualification.

## CodeGenome boundary

The CodeGenome-labelled fixture contributes a `reality_graph` signal with graph confidence `1.0`.

The graph signal remains typed estimator evidence. A crystallization request still reaches PAMA and remains uncommitted when review is required.

This demonstrates the ADR-035 boundary:

```text
Reality Graph evidence
  -> may influence a candidate cognitive transition
  -> may not authorize the transition
```

It does not upgrade CodeGenome's existing capability maturity profile.

## Recall admission remains separate

One fixture first earns a durable low-risk promotion, then applies a contextual recall rule that blocks the same logical memory from entering active cognition.

Therefore:

```text
durable memory
  != currently admissible memory

substrate candidate
  != active cognition
```

The contextual decision reports `authority_effect = current_recall_only` and does not mutate the durable memory.

## Explicit module absence and replacement

The reference runtime requires the named source component to be configured before a signal may enter the proposal path.

If it is absent:

```text
CognitiveModuleUnavailable
  -> no episode write
  -> no proposal commit
  -> no implicit fallback
```

A replacement component may then be registered explicitly. The subsequent transition keeps the same `MeshObject.object_ref` while receiving a new provider fact UUID.

This is narrow evidence for ADR-035's module-replacement requirement. It does not yet prove restart persistence of the replacement registry or provider-state migration.

## What this slice proves

At the reference boundary, this slice establishes:

1. one logical cognitive object can flow through evidence, provider signal, PAMA, durable commit, governed recall, and active cognition;
2. Cognitive Metabolism, Reality Graph, and predictive signals remain non-authoritative;
3. confidence magnitude does not grant consequence authority;
4. a provider-native `PASS` verdict does not grant consequence authority;
5. durable commit and active recall are separate governed stages;
6. absent modules fail explicitly rather than silently degrading;
7. replacing a provider does not require changing canonical logical cognitive identity.

## What this slice does not prove

This evidence does not establish:

- a complete Cognitive Mesh ontology;
- cross-process persistence of mesh/provider mappings;
- production EvolveAI integration;
- production CodeGenome integration;
- cognitive quality or learning effectiveness;
- consolidation quality;
- prediction calibration;
- transitive deletion completeness across every future cognitive derivative;
- that ADR-035 has satisfied all doctrine acceptance gates.

ADR-035 is **Accepted**; the bounded evidence satisfying its acceptance requirements is recorded in `adr-035-acceptance-matrix.md`.
