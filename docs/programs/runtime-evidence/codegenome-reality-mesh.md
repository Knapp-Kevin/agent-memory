# CodeGenome Reality Graph -> Cognitive Mesh Evidence

Status: implementation evidence slice; no capability maturity promotion.

This slice implements the first native Code Reality Graph seam under Accepted ADR-035.

## Provider boundary

The provider remains pinned to:

```text
MythologIQ-Labs-LLC/CodeGenome@43a6b7147ec78ec5c616723fa1dd30f342174860
```

That is the same revision already qualified by the `code-graph-traversal-currentness@1.1.0` profile. At this boundary `code_graph_traversal` remains `evidence_proven`; CodeGenome has no `reference_qualified` capability.

This integration does not change those maturity claims.

## Why relation/traversal is the first Reality Graph seam

CodeGenome exposes richer native graph values than its convenience MCP surfaces:

```text
Node
  UOR identity
  kind
  confidence
  provenance
  content hash
  source span

Edge
  source UOR
  target UOR
  typed relation
  confidence
  provenance
  evidence UORs
```

The first Agent Memory seam therefore consumes a provider-native relation produced from CodeGenome's fused graph and native traversal APIs.

It deliberately does not use:

- MCP `context` as the canonical seam because that surface reduces graph relations to a count;
- impact propagation as the first seam because propagated impact is a derived scoring/inference surface rather than a basic Reality Graph observation;
- CodeGenome governance/experiment verdicts as Agent Memory authority.

## Native evidence path

```text
pinned CodeGenome source
  -> native codegenome index of the existing v2 qualification fixture
  -> fused on-disk overlay
  -> native symbol resolution
  -> LocalQueryContext
  -> graph::traversal::execute
  -> direct provider-native Calls edge
       source UOR
       target UOR
       relation
       confidence
       provenance
       evidence refs
  -> raw JSON evidence artifact
  -> codegenome-code-reality-mesh-adapter@1.0.0
  -> CognitiveSignal(module_role=reality_graph)
  -> CognitiveMeshRuntime
  -> PAMA
  -> governed durable commit or refusal
  -> governed recall
  -> active cognition
```

The checked-in Rust driver is not a replacement graph engine. It loads CodeGenome's own fused store and executes CodeGenome's own graph types, `LocalQueryContext`, and traversal function at the exact provider pin.

## Identity boundary

CodeGenome UOR identity is provider/domain identity evidence.

It does not silently become Agent Memory's logical Cognitive Mesh identity.

```text
CodeGenome source UOR
CodeGenome target UOR
        !=
Agent Memory MeshObject.object_ref
```

The provider UORs are retained as evidence references while Agent Memory owns the logical object reference used for governed durable state and recall.

## Confidence and authority

Native edge confidence is preserved exactly as a provider confidence signal.

```text
provider confidence
  -> Proposal.confidence evidence
  != PAMA outcome
```

The focused adversarial path sends the same native Reality Graph signal through a crystallization request. Even if CodeGenome reports confidence `1.0`, the provider cannot self-authorize the consequence. PAMA remains controlling and the mutation is refused/review-gated according to Agent Memory policy.

## Provenance and evidence

The adapter preserves:

- exact CodeGenome commit;
- raw provider artifact digest/reference;
- source and target UORs;
- relation kind;
- native relation confidence;
- provider provenance source;
- provider provenance actor;
- provider provenance timestamp;
- provider evidence UORs;
- existing Agent Memory qualification evidence reference.

Normalization does not convert provider provenance into independent corroboration or authority.

## Maturity boundary

This slice proves interoperability of an already-evidenced capability. It does not change CodeGenome's capability profile.

Expected posture remains:

```text
code_graph_traversal: evidence_proven
reference_qualified CodeGenome capabilities: 0
authority effect from this integration: none
```

Separate evidence would be required to promote any capability maturity.

## Non-claims

This slice does not claim:

- CodeGenome is the universal Cognitive Mesh ontology;
- all CodeGenome graph overlays are qualified;
- impact propagation is qualified as predictive cognition;
- provider confidence is truth or permission;
- provider UOR is Agent Memory canonical identity;
- CodeGenome deletion/rebuild residue is fully qualified;
- MCP GraphRAG/context assembly is qualified;
- physical repository/package consolidation has been decided;
- universal production conformance.

## Focused evidence

`.github/workflows/codegenome-reality-mesh-evidence.yml` must prove at the exact PR head:

1. exact provider checkout and MIT source boundary;
2. existing adapter/profile/qualification regression tests remain green;
3. native CodeGenome CLI indexes the existing evidence fixture;
4. the native driver loads the fused overlay and emits a real `Calls` relation;
5. the raw relation preserves UOR, confidence, provenance, and evidence fields;
6. the versioned adapter normalizes it into a Reality Plane `CognitiveSignal`;
7. the signal traverses Cognitive Mesh, PAMA, commit/refusal, recall, and active cognition;
8. logical mesh identity remains independent of CodeGenome UOR identity;
9. provider confidence cannot self-authorize crystallization;
10. CodeGenome capability maturity remains unchanged.
