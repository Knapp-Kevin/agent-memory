# Hindsight v0.9.0 Qualification

Status: **candidate external-provider qualification for issue #352**

Provider boundary:

```text
repository: vectorize-io/hindsight
release: v0.9.0
source commit: b12646f49ec512136b9f709e608524ffed969668
published: 2026-08-07
license: MIT
runtime package: hindsight-embed==0.9.0
```

## Qualification target

This slice does not qualify Hindsight as a product. It qualifies one exact provider/version/runtime path against one Agent Memory capability contract:

```text
Hindsight v0.9.0
+ embedded pg0 runtime
+ LLM provider disabled
+ retain extraction mode = chunks
+ stable document identity
-> resource_artifact_memory@1.0 candidate qualification
```

No richer Hindsight capability is inherited merely because the provider also contains fact extraction, entities, observations, graph relationships, causal links, reflect, mental models, or other features.

The bounded profile therefore declares only:

```text
resource_artifact_memory@1.0
```

It does not earn `semantic_fact_memory`, `epistemic_belief_memory`, `predictive_counterfactual_memory`, `graph_state`, `causal_model_memory`, or `policy_memory` from this run.

## Exact source and rights boundary

The qualification workflow fetches tag `v0.9.0` and requires the checked-out commit to equal:

```text
b12646f49ec512136b9f709e608524ffed969668
```

It also verifies the exact source license contains the MIT license text and verifies `hindsight-embed` reports version `0.9.0` before any behavioral evidence is accepted.

That exact MIT evidence supports `runtime_allowed` source-rights posture for this pinned runtime. A future Hindsight release must be evaluated independently.

## Documentation/source discrepancy

The versioned v0.9 retain prose documents extraction modes `concise`, `verbose`, and `custom`, but the exact v0.9.0 source defines:

```python
RETAIN_EXTRACTION_MODES = (
    "concise",
    "verbose",
    "custom",
    "verbatim",
    "chunks",
)
```

The same pinned source defines `HINDSIGHT_API_RETAIN_EXTRACTION_MODE` and explicitly discusses a `chunk-extraction bank` in recall configuration comments.

The executable fixture therefore uses `chunks`, but its provenance is the exact source revision rather than the stale versioned prose page. The discrepancy is preserved as a qualification limitation instead of silently rewriting the historical documentation.

## LLM-free fixture

The fixture disables the provider LLM and the Hindsight features that would otherwise introduce unrelated inference behavior:

```text
HINDSIGHT_API_LLM_PROVIDER=none
HINDSIGHT_API_SKIP_LLM_VERIFICATION=true
HINDSIGHT_API_RETAIN_EXTRACTION_MODE=chunks
HINDSIGHT_API_ENABLE_OBSERVATIONS=false
HINDSIGHT_API_ENABLE_AUTO_CONSOLIDATION=false
HINDSIGHT_API_ENABLE_RERANKING=false
HINDSIGHT_API_ENABLE_GRAPH_RETRIEVAL=false
HINDSIGHT_API_ENABLE_TEMPORAL_RETRIEVAL=false
HINDSIGHT_API_MCP_ENABLED=false
```

No external model API key is permitted in the qualification environment.

This does not prove Hindsight's richer LLM-backed memory behavior. It isolates provider storage/currentness/retrieval mechanics so the evidence is repeatable and attributable.

## Lifecycle fixture

One isolated bank and one stable provider-native document ID are exercised through:

```text
initial retain
-> exact document readback
-> recall visibility

same-key repeat
-> one current document

same-key replacement
-> replacement document current
-> replacement recall visible
-> initial marker no longer recallable

daemon stop/start
-> document reconstructs
-> replacement remains recallable

same-key retry after restart
-> one current document

document delete
-> direct get fails
-> document list is empty
-> initial marker absent from recall
-> replacement marker absent from recall
```

Every provider command, return code, stdout, and stderr is retained in the raw evidence artifact before Agent Memory normalizes any conclusion.

## Candidate behavior contract

The profile uses provider revalidation rather than pretending Hindsight implements Agent Memory-native lifecycle semantics:

```text
currentness_model: provider_revalidated
invalidation_model: provider_revalidation
correction_model: provider_revalidation
deletion_model: provider_revalidation
residue_model: scan_required
migration_rebuild_model: requires_requalification
```

Stable Hindsight document identity is provider-native identity. It never becomes Agent Memory logical memory identity or authority.

## Candidate operational contract

Only properties directly exercised by the fixture may survive qualification:

```text
write_atomicity: none
concurrency_control: none
idempotency: durable_keyed
restart_recovery: reconstructable
reconciliation: deterministic_readback
```

`none` for atomicity and concurrency is deliberate. PostgreSQL underneath Hindsight is not evidence that the Hindsight operation exposed to Agent Memory has a particular atomic or concurrency guarantee.

The stronger three claims have executable gates:

- `durable_keyed` requires the same document ID to remain singular across repeat, replacement, restart, and retry;
- `reconstructable` requires an actual daemon stop/start followed by successful state/recall recovery;
- `deterministic_readback` requires exact document readback and lifecycle comparison rather than inference from a successful write command.

If the exact runtime fails one of these checks, the candidate qualification is rejected. Agent Memory does not weaken the test to make the provider appear compatible.

## Deletion and residue

Hindsight documentation says deleting a document removes the document and associated memories. Agent Memory treats that as a claim to test, not as proof.

The qualification requires all of the following after deletion:

```text
delete reports success
direct document read fails
document list contains no current document
old marker is not recallable
replacement marker is not recallable
```

A stale recall result is therefore sufficient to fail the candidate contract even when Hindsight's direct document endpoint reports deletion success.

This remains provider-local deletion evidence. It is not a claim of transitive forgetting completeness across external systems or arbitrary derived artifacts.

## Maturity and authority

The profile may land at `evidence_proven` only when the exact-head provider workflow proves every required check and the resulting Qualification v1.2 record validates against the current component declaration.

```text
provider success != Agent Memory authority
provider recall score != recall admission
provider document ID != Agent Memory logical identity
provider qualification != PAMA permission
```

The qualification record and normalized result always carry:

```text
authority_effect: none
```

## Failure is a valid result

The qualification harness is intentionally capable of producing an explicit ineligible result. Examples include:

- the pinned source/package identity does not match;
- an external LLM credential is required;
- replacement leaves the old document recallable;
- restart loses current state;
- stable document identity duplicates across retries;
- deletion leaves direct or recall residue.

Such a result is evidence about the exact provider version, not a reason to modify Agent Memory's canonical semantics.

## Stop condition

Issue #352 stops after Hindsight v0.9.0 has one exact, bounded qualification result for chunk-backed `resource_artifact_memory`. It does not integrate a second external provider and does not begin cross-substrate consolidation.
