# Federated Resource Exchange

Status: **bounded implementation for issue #358**

This slice implements the first executable `federated_memory_exchange` path over two independently qualified external `resource_artifact_memory@1.0` providers:

- Hindsight v0.9.0;
- `@memtensor/memos-local-plugin@2.0.17`.

It follows #276's `no_new_algebra` conclusion. Agent Memory does not create a new universal state algebra or consolidate the providers into one physical store.

## Architecture boundary

The capability vocabulary defines federated memory exchange as exchange across independent stores without requiring one physical store.

The bounded path is therefore:

```text
current Capability Qualification v1.2 evidence
        |
        v
common resource_artifact_memory requirement
        |
        v
logical resource snapshot
  Agent Memory logical ID
  exact content + digest
  representation kind
  source domain refs
  provenance refs
        |
        v
provider-native copy
        |
        v
direct target readback
        |
        v
invariant-bound exchange receipt
```

Provider-native object IDs are mappings only. They do not become Agent Memory logical IDs.

## Relationship to provider substitution

PR #357 proved that Hindsight and MemOS independently satisfy the same durable resource-memory requirement.

Exchange reuses that gate. It does not infer compatibility from similar APIs, SQLite/PostgreSQL durability, or provider marketing language.

Every exchange receipt binds:

- source qualification applicability digest;
- target qualification applicability digest;
- common requirement digest;
- exact provider identities and versions.

A changed provider declaration or stale qualification therefore cannot silently inherit old exchange evidence.

## Resource snapshot

`LogicalResourceSnapshot` is intentionally narrow:

```text
logical_resource_id
representation_kind
content
content_digest
source_domain_refs
provenance_refs
```

The snapshot is not a new lifecycle object. It is the exact provider-neutral payload needed to prove a copy while preserving existing Agent Memory identity, scope, and provenance semantics.

## Exchange receipt

`ResourceExchangeReceipt` records:

```text
snapshot_digest
logical_resource_id
content_digest
source / target provider binding
source / target qualification digests
common requirement digest
target direct-readback digest
source / destination domain refs
provenance refs
source_retained = true
destructive_cutover = false
crossing_receipt_ref, when applicable
outcome = copied_verified
authority_effect = none
```

The receipt proves a bounded copy and direct-readback equality. It does not grant recall admission, action authority, durable mutation authority, source deletion, or destructive cutover.

## Isolation-domain crossing

ADR-022 and `docs/41-memory-isolation-domains-and-governed-crossing.md` remain controlling.

For a same-domain provider copy, the exchange receipt records the unchanged domain and no separate boundary-crossing receipt is required.

For a domain-changing transfer, the exchange layer requires an already-committed canonical `boundary-crossing-receipt` whose:

- operation is compatible with copy/export/import;
- source and destination domains exactly match;
- logical resource reference matches;
- representation kind and content digest match;
- PAMA disposition allows the consequence.

The exchange module does not mint that authority itself.

## Exact runtime proof

The dedicated workflow exercises both directions in one isolated job.

### Hindsight -> MemOS

1. create one exact Hindsight chunk-backed document under a provider-native document ID;
2. direct-read the source;
3. write those bytes to a distinct MemOS stable trace ID;
4. direct-read the MemOS target;
5. direct-read the Hindsight source again;
6. require source-before, target, and source-after bytes to match exactly.

### MemOS -> Hindsight

1. create one MemOS trace under a provider-native stable trace ID;
2. direct-read the source;
3. write those bytes to a distinct Hindsight document ID;
4. direct-read the Hindsight target;
5. reopen the same MemOS SQLite home and direct-read the source again;
6. require source-before, target, and source-after bytes to match exactly.

Bidirectionality prevents either provider representation from becoming an implicit canonical format.

## Deliberate non-goals

This slice does not implement:

- destructive migration or cutover;
- source deletion;
- replication or synchronization daemons;
- conflict resolution between concurrently changing replicas;
- third-provider federation;
- semantic-memory conversion;
- L2/L3/skill/graph transfer;
- automatic scope promotion;
- a new logical-state algebra.

Those are separate consequences and require separate evidence.

## Failure is meaningful

The exchange fails closed for content mismatch, provider/logical identity collapse, missing provenance, qualification drift, source-rights downgrade, provider-version drift, destructive-cutover claims, or an invalid/missing cross-domain boundary receipt.

A failed provider copy is not repaired by weakening the common qualification requirement or by treating serialization success as semantic compatibility.
