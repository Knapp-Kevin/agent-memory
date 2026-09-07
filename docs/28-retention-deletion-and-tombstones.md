# Retention, Deletion, and Tombstones

> Canonical requirement: [ADR-015](adr/ADR-015-retention-deletion-and-tombstones-are-required.md)

## Purpose

Forgetting is not one operation.

A governed memory system must distinguish reduced recall, archival, redaction, tombstoning, cryptographic deletion, and full deletion propagation through derived state.

Predicted low utility may nominate a memory for forgetting. It does not authorize irreversible deletion.

## Forgetting modes

| Mode | Active recall | Content retained | Recoverable | Typical use |
|---|---|---|---|---|
| deprioritize | yes, lower rank | yes | yes | low current relevance |
| suppress | no ordinary recall | yes | yes | temporary exclusion |
| archive | no ordinary recall | yes | yes | historical/audit retention |
| redact | limited representation | partial | depends | minimize sensitive content |
| tombstone | no content recall | marker/metadata | policy-dependent | preserve deletion/supersession fact |
| cryptographic delete | no | ciphertext may remain | no without key | strong local deletion |
| purge | no | intended no recoverable copies | no | required full deletion outcome |

Implementations may add modes but must define semantics.

## Retention inputs

Retention policy may consider:

- memory type
- legal/compliance hold
- user deletion request
- consent state
- sensitivity
- evidence/audit value
- dependencies
- currentness
- certification state
- dispute state
- historical value
- estimated future utility
- storage cost

Utility and staleness are advisory unless policy explicitly grants them bounded consequence.

## Consequence proportionality

```text
reversible deprioritization -> low authority may suffice
archival -> policy-defined authority
redaction -> sensitivity/privacy authority
irreversible deletion -> strongest applicable authority and verification
```

## Dependency graph

Deletion must traverse derivation relationships where required.

Potential dependents include:

- summaries
- semantic memories
- procedures
- embeddings/index records
- graph edges
- caches
- exported artifacts
- agent-generated reflections
- preference models
- successor-agent inherited memory

A deletion operation should identify which dependents are in scope and which cannot be controlled.

Those dependents are not one kind of thing. Summaries, semantic memories, and procedures are memory units with identity, lifecycle, and derivation links. Embeddings, index records, caches, and graph projections are not, so nothing obliges them to record what they were built from — which is where residue collects. Propagation semantics for both, including how staleness is expressed and what a purge must reach, are developed in [`programs/runtime-evidence/canonical-and-derived-state.md`](programs/runtime-evidence/canonical-and-derived-state.md). That is program design work; nothing in it is doctrine until an ADR adopts it.

## Tombstones

A tombstone records enough metadata to prevent accidental resurrection without preserving content that policy requires erased.

Possible fields:

```text
memory_id_or_irreversible_reference
deletion_mode
reason_class
policy_version
deleted_at
scope
superseded_by_if_applicable
```

Privacy policy may require minimizing even tombstone metadata.

## Deletion receipt

For consequential deletion:

```text
deletion_id
requester
actor_authority
memory_refs
requested_outcome
deletion_mode
policy_version
dependency_refs
completed_steps
failed_steps
residual_known_copies
verification_method
verification_result
timestamp
```

## Deletion verification

Verification should answer the user/policy outcome, not merely whether one database row disappeared.

Examples:

- hidden from ordinary recall
- inaccessible to specified actor
- removed from local durable store
- unrecoverable through cryptographic key destruction
- propagated through known derived memory
- external copies identified but not controllable

## Evidence retention tension

Audit evidence may conflict with deletion obligations.

Policy must define which requirement controls within the relevant legal and product context.

Do not silently keep deleted content under the label `audit` if the required outcome is erasure.

Possible alternatives:

- content-free tombstone
- hash/reference without content
- segregated legally required retention
- redacted audit event

## Supersession is not deletion

Historical truth should normally remain available when a newer state supersedes it.

```text
old value valid until T
new value valid from T
```

Use deletion only when policy requires removal, not merely because current truth changed.

## Correction is not deletion

Correction preserves the fact that an earlier claim was wrong or incomplete unless privacy/policy requires otherwise.

## Consolidation and deletion

Derived semantic/procedural memory should carry derivation links so deletion can determine whether a source contribution must be removed, recomputed, or marked unavailable.

This is difficult when model weights or lossy abstractions contain distributed influence. The system should not claim full deletion where it cannot demonstrate it.

## Unlearning

Machine unlearning or model-weight removal is distinct from deleting explicit memory records.

Do not use `deleted from vector store` as evidence that learned model state has been unlearned.

## Conformance cases

### Prune versus delete

Expected: pruned memory remains recoverable under policy; deleted memory follows stronger semantics.

### Derived summary residue

Expected: deletion verification detects or addresses a surviving summary.

### Low utility proposal

Expected: utility score alone cannot authorize purge.

### Legal/audit hold

Expected: policy resolves retention conflict explicitly.

### Superseded historical memory

Expected: ordinary current recall excludes it while historical retrieval may retain it.

### Unknown external copy

Expected: receipt reports residual uncontrollable copies rather than claiming universal deletion.

## Doctrine

Forgetting is a governed family of operations.

A system should be able to say exactly what "forgotten" means in each case, because humans have already overloaded that verb enough.
