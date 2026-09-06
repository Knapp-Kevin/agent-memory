# EvolveAI multi-capability qualification profile

Status: **executable qualification evidence for #292**

Exact provider revision:

`MythologIQ-Labs-LLC/EvolveAI@21161ce7b88dbffeb7ed59757b4d02d24a9c2acd`

That revision contains EvolveAI PR #21, which repairs #19 by recording L3 deletion in the hash-chain ledger and reconciling live vault state against replayed store/update/delete history.

## Qualification posture

EvolveAI is treated as one multi-capability component, not as one monolithic maturity label.

The component profile is:

`reference/fixtures/component-capabilities/evolveai.example.json`

It uses `component-capability-v2` and declares fifteen independently graded capability surfaces. Every surface uses `external_scope_bridge`; EvolveAI provider scope is not silently equated with Agent Memory actor/tenant/project scope.

The executable profile is:

`evolveai-public-facade-behavior@1.0.0`

Adapter:

`evolveai-public-facade-adapter@1.0.0`

The common #298 qualification record/schema remains the authority for evidence shape. EvolveAI does not get a private certification vocabulary.

## Public-facade workload

The qualification driver compiles against the exact checked-out EvolveAI `evolve-core` crate and exercises public `MemoryProcessor` behavior.

It proves a bounded sequence:

1. ordinary 384-dimensional mock-engine inputs route to L2;
2. session co-capture creates temporal graph associations;
3. the supported query path performs vector candidate scan;
4. lifecycle traces reach `detach()` and execute the current REM-synthesis path;
5. a public Shadow Genome failure record can produce EvolveAI's native `Block` verdict;
6. a sensitive input routes to L3;
7. content-addressed L3 exact retrieval returns the live unit;
8. explicit save/load preserves the current L3 value and chain health;
9. explicit forget removes the live L3 unit and appends the repaired `delete:<address>:<last-content-hash>` ledger event;
10. the deleted value is not current after deletion;
11. save/load after deletion preserves the delete history and continued absence.

The raw provider observation is preserved before normalization.

## Independent maturity result

The profile intentionally does not promote every row equally.

`reference_qualified` is bounded to:

- `content_addressed_exact_retrieval`;
- `persistent_snapshot_restart`;
- `audited_deletion`;
- `l3_provenance_audit`.

`evidence_proven` is bounded to:

- mock-backed `vector_representation`;
- mock-backed `vector_candidate_retrieval`;
- `temporal_graph`;
- direct-neighbor `graph_traversal`;
- `tier_routing`;
- `lifecycle_orchestration`;
- current `rem_synthesis_consolidation` behavior;
- `negative_failure_memory`.

`lifecycle_decay` remains `runtime_wired`: the workload proves the supported invocation path through synthesis but does not claim exhaustive threshold/decay behavior.

`transient_cache_storage` remains `implemented` in this profile because the 1.0.0 workload does not independently exercise the ephemeral L1 boundary.

`graph_augmented_context_assembly` remains `declared` and disabled. Temporal graph state plus vector retrieval is not an end-to-end GraphRAG/context-assembly qualification.

## Mock versus real representation

The exact supported CLI and qualification workload use EvolveAI `MockEngine` at 384 dimensions.

EvolveAI also contains a GG-CORE-backed ONNX `GgCoreEngine` behind its `ggcore` feature. That implementation existence is preserved as source evidence, but this profile does not execute it and does not transfer mock-path evidence to real embedding quality.

Therefore:

```text
mock vector runtime behavior proven
!= real embedding quality proven
!= production semantic retrieval quality proven
```

## Shadow Genome authority boundary

The provider-native workload deliberately produces an EvolveAI `Verdict::Block` from a matching negative/failure memory.

Agent Memory normalizes that result as:

`risk_candidate_only`

It does not become Agent Memory PASS/BLOCK, mutation authority, recall-admission authority, or action authority.

Trigger count, similarity, severity, and repeated encounters remain provider evidence. Repetition is not independent corroboration.

## Deletion and residue boundary

The repaired EvolveAI revision now earns the narrower native claim that was previously blocked:

```text
live L3 state
-> explicit forget
-> delete record bound to prior content hash
-> live state absent
-> chain verifies
-> delete history survives explicit restart
```

It does **not** earn:

```text
native L3 delete
!= Agent Memory transitive forgetting completeness
!= proof every external/derived representation is absent
!= authority to perform a governed deletion
```

The profile therefore records provider-managed residue and preserves `external_derived_residue_absence_proven = false`.

## Scope and applicability

Qualification applicability binds:

- exact EvolveAI commit;
- exact component profile digest;
- adapter identity/version;
- qualification profile identity/version;
- runtime configuration;
- fixture digest;
- Agent Memory scope binding;
- provider scope binding;
- dependency/runtime refs.

Foreign Agent Memory scope, stale EvolveAI version, or stale component-profile digest fails closed. A changed version does not inherit qualification by resemblance.

## Failure posture

The component declares `explicit_unavailable`.

CI additionally builds the exact qualification adapter, removes its executable from the configured path, and uses the common provider-unavailable probe to preserve the real `FileNotFoundError` evidence. The normalized result is `provider_unavailable`, `currentness = unavailable`, and `authority_effect = none`.

An ordinary provider error or timeout is not silently relabeled as unavailable.

## Evidence outputs

Focused CI:

`.github/workflows/evolveai-multicapability-qualification.yml`

The workflow preserves:

- raw EvolveAI public-facade observation;
- raw and normalized unavailable-provider evidence;
- provider-neutral normalized evidence;
- one schema-valid #298 qualification record per advanced capability;
- exact applicability digests;
- exact-head profile report and summary;
- SHA-256 evidence digests.

The workflow also reruns EvolveAI's native delete regression suite and the full Agent Memory reference suite.

## Claim boundary

This qualification makes EvolveAI a stronger first-party component candidate. It does not make EvolveAI the Agent Memory architecture, import EvolveAI tier names as doctrine, or grant its learned signals governance authority.

Component identity remains provenance. Capability behavior remains evidence. Consequence remains governed by Agent Memory's existing authority boundaries.
