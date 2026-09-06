# ADR-035 Acceptance Evidence Matrix

Status: **all nine acceptance requirements satisfied at the bounded evidence boundary; explicit doctrine promotion in review**

ADR-035 remains canonical only after the separate promotion PR carrying this matrix and the ADR status change merges.

This matrix evaluates the acceptance requirements in [`../../adr/ADR-035-agent-memory-is-a-governed-cognitive-framework.md`](../../adr/ADR-035-agent-memory-is-a-governed-cognitive-framework.md) against repository-main evidence after the native EvolveAI Cognitive Metabolism integration landed in PR #340.

## Decision rule

```text
documented architecture
  != implemented mechanism
  != provider-native integration
  != capability qualification
  != doctrine acceptance
```

A `satisfied` requirement means the boundary named by ADR-035 has evidence. It does not promote unrelated provider capabilities or claim universal production conformance.

## Matrix

| # | ADR-035 acceptance requirement | Status | Evidence boundary |
|---|---|---|---|
| 1 | Cognitive Mesh boundary documented without creating a universal implementation-specific ontology | **satisfied** | ADR-035 defines the mesh contract; `reference/agentmem_ref/memory/cognitive_mesh.py` keeps `object_type` and `module_role` open; `docs/01-layer-model.md` states the mesh is not a ninth memory layer or universal database schema. |
| 2 | Three-plane architecture integrated consistently into canonical documentation | **satisfied** | PR #339 landed `docs/11-component-architecture.md`, `docs/01-layer-model.md`, and `docs/13-system-composition-boundaries.md` with the Cognitive, Reality, and Authority topology while preserving layer/component/capability distinctions. |
| 3 | EvolveAI mapped to Cognitive Metabolism without falsely promoting unqualified capabilities | **satisfied** | The mapping is architectural only. Existing EvolveAI qualification remains capability/version scoped and preserves its known limitations. PR #340 retains `proposal_only` posture for native REM/consolidation output. |
| 4 | CodeGenome mapped to Code Reality Graph without promoting its ontology to universal memory semantics | **satisfied** | ADR-035 and composition doctrine constrain CodeGenome to the code-domain Reality Graph role. Its ontology does not become the universal Cognitive Mesh ontology, and its capability maturity remains independently qualified. |
| 5 | Module identity, component identity, and capability identity remain distinct and consistent with ADR-033 | **satisfied** | ADR-033 remains Accepted and controlling. ADR-035 preserves `module identity != component identity != capability identity`. |
| 6 | At least one end-to-end path demonstrates Cognitive Mesh identity -> Evidence/Provenance -> Cognitive Metabolism or Reality Graph processing -> candidate cognitive change -> PAMA -> commit/refusal -> governed recall -> active cognition | **satisfied** | PR #340, merged at `5ef4f6936cbe0af4846135bee0562c4d4c23a3ab`, checks out pinned `EvolveAI@21161ce7b88dbffeb7ed59757b4d02d24a9c2acd`, executes native `MemoryProcessor` encode/detach behavior, retains raw provider evidence, normalizes the native synthesis observation through the versioned Cognitive Metabolism adapter into `CognitiveSignal`, then carries it through `CognitiveMeshRuntime`, PAMA, governed durable commit/refusal, governed recall, and active cognition. The exact-head `EvolveAI Cognitive Mesh Evidence` workflow passed all steps. |
| 7 | Adversarial path proves learned reinforcement, graph confidence, prediction confidence, or provider-native verdict cannot independently grant durable/action authority | **satisfied** | PR #338 proves estimator confidence and provider verdict cannot grant authority. PR #340 additionally proves native EvolveAI synthesis cannot self-authorize crystallization and is refused when it requests authority it has not earned. |
| 8 | Module replacement or absence fails explicitly without corrupting canonical cognitive identity | **satisfied at reference boundary** | PR #338 proves unavailable providers produce explicit failure with zero writes and that replacement preserves logical `MeshObject.object_ref` independently of physical provider fact identity. Stronger universal restart-persistent provider mapping is not claimed. |
| 9 | Conformance documentation distinguishes architectural acceptance from implementation maturity | **satisfied** | ADR status semantics, ADR-033 capability maturity, `docs/programs/runtime-evidence/cognitive-mesh.md`, this matrix, and PR #340's non-claims separate doctrine acceptance, reference evidence, native integration, and provider capability qualification. |

## Acceptance result

```text
requirements satisfied: 9 / 9
material acceptance gaps: 0
provider capability promotions implied: 0
universal production conformance claimed: false
```

## Native provider evidence now on main

The accepted evidence boundary is intentionally narrow:

```text
EvolveAI@21161ce7b88dbffeb7ed59757b4d02d24a9c2acd
  -> native MemoryProcessor encode x3
  -> native detach() / lifecycle synthesis
  -> retained raw provider artifact
  -> versioned EvolveAI Cognitive Metabolism adapter
  -> CognitiveSignal
  -> CognitiveMeshRuntime
  -> PAMA
  -> governed durable commit or refusal
  -> governed recall
  -> active cognition
```

The adapter proves:

1. provider identity and revision are pinned and reconstructable;
2. the source observation is produced by native EvolveAI behavior rather than recreated as an Agent Memory fixture;
3. normalized signal semantics are explicit;
4. no confidence is invented where the provider emits none;
5. provider output cannot bypass PAMA;
6. logical Cognitive Mesh identity remains independent of provider storage identity;
7. raw provider evidence and its digest survive normalization;
8. the integration does not promote unrelated EvolveAI capabilities.

CodeGenome does not need an equivalent native seam to accept ADR-035 because the ADR requires at least one native end-to-end module path. A Code Reality Graph seam remains a separate future implementation scope and must preserve the same evidence/authority boundaries.

## Promotion decision boundary

With PR #340 on `main`, the evidence prerequisites named by ADR-035 are satisfied. The remaining act is deliberately doctrinal rather than evidentiary:

```text
all nine requirements satisfied
+
explicit ADR promotion diff
+
exact-head doctrine / architecture validation
=
eligible to merge ADR-035 as Accepted
```

The promotion PR must not alter EvolveAI or CodeGenome capability maturity, packaging, repository ownership, or PAMA authority semantics. Those remain separate decisions and evidence programs.
