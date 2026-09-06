# Native EvolveAI Cognitive Mesh Evidence

Status: **implementation/evidence slice under validation; ADR-035 is Accepted**

This slice closes the provider-native seam identified by the ADR-035 acceptance review. It reuses the existing pinned EvolveAI public-facade workload rather than recreating EvolveAI behavior inside Agent Memory.

## Exact provider boundary

The evidence workflow checks out:

```text
MythologIQ-Labs-LLC/EvolveAI
@21161ce7b88dbffeb7ed59757b4d02d24a9c2acd
```

The existing qualification driver runs EvolveAI's public `MemoryProcessor` with its `MockEngine`, encodes three memories, calls provider-native `detach()`, and emits:

```text
observations.lifecycle_synthesis = true
native_evidence.detach_traces_processed >= 3
```

The driver output is retained as the raw provider artifact.

This slice does not claim the real embedding path is exercised. The provider's raw runtime field must preserve that boundary explicitly.

## Adapter boundary

`reference/agentmem_ref/evolveai_cognitive_mesh.py` introduces a versioned normalization adapter:

```text
EvolveAI native observation
  -> exact provider/version validation
  -> lifecycle_synthesis validation
  -> native trace-count validation
  -> typed CognitiveSignal
```

The normalized signal is:

```text
module_role = cognitive_metabolism
source_component = evolveai
signal_type = rem_synthesis_consolidation_candidate
capability = rem_synthesis_consolidation
authority_effect = proposal_only
```

The adapter preserves:

- exact EvolveAI commit;
- raw provider evidence reference/digest;
- native runtime identity;
- native trace count;
- Agent Memory qualification evidence reference;
- exact adapter identity/version;
- estimator/source identity.

It does **not** invent a confidence value. The native workload does not emit a meaningful confidence for the synthesis event, so the Cognitive Mesh signal carries `confidence=None`.

It does **not** convert provider behavior into authority.

## End-to-end path

The evidence runner exercises:

```text
three native EvolveAI inputs
  -> EvolveAI MemoryProcessor
  -> native detach / REM-style synthesis
  -> raw native observation artifact
  -> EvolveAI Cognitive Metabolism adapter
  -> CognitiveSignal
  -> CognitiveExperience + stable MeshObject identity
  -> CognitiveMeshRuntime
  -> existing Agent Memory PAMA
  -> governed durable commit
  -> governed recall
  -> active cognition
```

The logical Agent Memory object identity remains independent of the provider fact UUID.

## Authority containment

The same native provider-derived signal is also submitted as a crystallization request.

Expected result:

```text
native lifecycle synthesis = true
  != crystallization authority

PAMA outcome = require_review
committed = false
```

This proves that real provider execution does not gain consequence authority merely by crossing the Cognitive Mesh adapter.

## Fail-closed normalization

Focused tests require the adapter to reject:

- wrong provider identity;
- wrong EvolveAI commit;
- missing/false native `lifecycle_synthesis` evidence;
- native synthesis below the configured three-trace threshold;
- absent runtime identity;
- malformed explicit embedding-path posture.

## Relationship to EvolveAI qualification

This evidence reuses an already evidence-proven EvolveAI capability:

```text
rem_synthesis_consolidation -> evidence_proven
```

That capability remains `proposal_only` under Agent Memory's existing component profile.

This slice does not:

- promote `rem_synthesis_consolidation` to `reference_qualified`;
- promote any unrelated EvolveAI capability;
- claim real GG-CORE embedding quality;
- claim EvolveAI's internal ontology is canonical Agent Memory ontology;
- make native Shadow Genome verdicts Agent Memory PASS/BLOCK authority;
- prove transitive forgetting across all derived cognitive state.

## ADR-035 effect

If this exact-head evidence passes and lands on `main`, it supplies the missing native-provider portion of ADR-035 acceptance requirement 6:

```text
provider-native Cognitive Metabolism processing
  -> typed Cognitive Mesh signal
  -> candidate cognitive change
  -> PAMA
  -> governed consequence
  -> governed recall
  -> active cognition
```

ADR-035 status must still be changed only through a separate explicit promotion review after the evidence is on `main` and the acceptance matrix is updated. Evidence completion does not silently promote doctrine.
