# Common Cross-Architecture Analysis Contract

Status: exploratory research contract for #67 / #224.

Every architecture-family study must answer the same questions before it can be compared with another family. Product-specific features may extend this contract but must not replace it.

## Evidence record for every conclusion

Each material conclusion should record:

```text
claim_id
architecture_family
claim
boundary_conditions
evidence_status
supporting_evidence_refs
challenging_evidence_refs
reproduction_status
counterexamples
promotion_state
```

Allowed evidence status:

```text
architectural_deduction
primary_research_supported
implementation_observed
benchmark_or_conformance_evidence
cross_architecture_reproduced
open_hypothesis
contradicted
not_yet_evaluated
```

`architectural_deduction` means the conclusion follows from the explicitly modeled architecture, not that it has been empirically proven in every implementation.

## 1. Identity and retained-state unit

Answer:

- What is the smallest independently governed retained-state unit?
- How is exact identity represented?
- Does identity survive movement, serialization, indexing, embedding, summarization, graph extraction, compaction, or replay?
- Which identity changes are versions versus new objects?
- Can the retained state be addressed without revealing sensitive content?

## 2. Canonical, derived, and projection state

Classify every important state surface as one of:

```text
canonical candidate
derived state
materialized projection
cache / ephemeral acceleration state
external evidence
unknown / disputed ownership
```

If multiple surfaces claim canonical status, describe conflict resolution explicitly.

## 3. Mutation path and durable write authority

Map:

```text
observation / retrieval / inference
-> proposal
-> target memory consequence
-> PAMA classification
-> permitted action set
-> committed mutation
-> receipt
```

Identify every automatic writer and estimator-mediated mutation path.

Test:

```text
probabilistic recommendation
!= durable write authority
```

## 4. Recall discovery versus governed admission

Separate:

```text
candidate discovery
ranking / relevance estimation
governed admission
context representation / assembly
model influence
```

Describe where tenant, scope, sensitivity, lifecycle, dispute, revocation, and authorization checks can be enforced.

## 5. Provenance and transformation chain

For every derived state ask:

- Can it point to its source basis?
- Is the transformation/version reconstructable?
- Can source changes invalidate it deterministically?
- Can a derived object combine sources with different scopes or authority states?
- Can provenance be stripped or laundered during export/rebuild?

## 6. Correction, contradiction, and supersession

Characterize:

- proposition-level correction availability;
- overwrite versus supersession;
- historical versus current truth;
- contradictory active state;
- derived invalidation;
- correction propagation latency;
- rebuild requirements.

Correction must not be treated as “write new value” unless the architecture actually preserves the necessary history and dependency semantics.

## 7. Forgetting, deletion, and residue

Map:

```text
canonical delete / suppress / tombstone
-> declared dependency closure
-> derived purge / invalidation
-> independent residue detection
-> lifecycle result
```

Record whether the architecture supports physical deletion, logical deletion, tombstoning, key destruction, access revocation, rebuild suppression, or some combination.

Test:

```text
successful delete operation
!= forgetting proof
```

## 8. PAMA insertion and authority laundering risk

Identify where PAMA can classify:

- target memory class M0-M5;
- requested operation;
- downstream authority A0-A5;
- scope/domain crossing;
- review/approval requirements.

Locate paths where maintenance, summarization, inference, synchronization, or retrieval could accidentally create a stronger durable consequence than the initiating authority allowed.

## 9. Isolation and boundary crossing

Apply #68's completed isolation doctrine:

```text
same agent != same scope
shared store != shared authority
boundary crossing = governed consequence
```

Evaluate tenant/project/task/compartment crossing, shared membership, derived-state scope propagation, and revocation propagation.

## 10. Observability and evidence

Identify distinct observable events for:

```text
write
derive
retrieve
admit
assemble
revise
invalidate
rebuild
compact
synchronize
delete
purge
residue sweep
```

Specify what can be correlated without placing raw memory content into telemetry.

## 11. Security and privacy

Evaluate at minimum:

- direct poisoning;
- sleeper poisoning;
- provenance stripping;
- ranking/retrieval manipulation;
- stale derived state;
- graph-edge/link poisoning;
- embedding contamination;
- cross-domain leakage;
- unauthorized traversal;
- automatic rebuild after revocation/deletion;
- summary laundering;
- shared-memory privilege escalation;
- latent-state leakage where applicable.

## 12. Deterministic versus probabilistic behavior

Classify each material step:

```text
deterministic
probabilistic
hybrid
external / unknown
```

Then record which probabilistic outputs are constrained by deterministic governance consequences.

A useful default hypothesis to test is:

> Probabilistic discovery and inference may propose consequences; durable authority boundaries should remain deterministically enforceable and reconstructable.

## 13. Failure, recovery, and rebuild

Characterize:

- crash consistency;
- retry/replay identity;
- duplicate mutation risk;
- stale checkpoint/state recovery;
- index/graph/embedding rebuild;
- recovery from partial propagation;
- whether recovery can resurrect revoked or deleted state.

## 14. Economics and operational amplification

Measure or estimate only when evidence supports it:

- storage amplification;
- write amplification;
- indexing/extraction cost;
- retrieval latency;
- synchronization cost;
- correction propagation cost;
- deletion/purge cost;
- rebuild cost;
- freshness lag;
- local/offline feasibility.

Cost is an optimization input, never authority.

## 15. Human inspectability and intervention

Describe what a human can directly inspect, understand, correct, export, or audit.

Do not equate inspectability with governance quality. Human-readable files may hide unsafe derived indexes; opaque stores may still provide strong reconstructable receipts.

## Required conclusion form

Every family study must end with:

```text
current doctrine survived:
  [list]

current doctrine needs clarification:
  [list]

candidate doctrine gap backed by counterexample:
  [list]

implementation-specific issue only:
  [list]

unresolved hypotheses:
  [list]
```

A doctrine change is not a required output. “No change after adversarial comparison” is a valid research result.
