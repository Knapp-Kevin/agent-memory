# P6 Mem0 adversarial comparator

P6 broadens the runtime-evidence program from the Agent Memory reference adapter to a mature production-oriented external memory layer: Mem0 OSS Python `2.0.18`.

The comparator has one job:

> Execute accumulation, scoped retrieval, correction, deletion, history, direct-ID operations, and scoped bulk deletion through Mem0's real memory layer, then classify what that layer provides without turning Mem0 into doctrine authority.

A missing Agent Memory guarantee is a classified gap. It is not automatically a Mem0 defect.

## Pinned subject

```text
repository       mem0ai/mem0
Python package   mem0ai==2.0.18
release          v2.0.18
license          Apache-2.0
```

The CI artifact records both the comparator package version and the exact Agent Memory commit that executed it.

## Execution boundary

The executed path uses:

- `mem0.memory.main.Memory` from the pinned package;
- Mem0's own `VectorStoreFactory` and local Qdrant implementation;
- Mem0's own SQLite history manager;
- Mem0's own add, get, get-all, search, update, delete, delete-all, and history methods.

Two construction seams are replaced solely to make CI deterministic and credential-free:

1. the embedder factory returns a deterministic eight-dimensional local embedder;
2. the LLM factory returns a construction-only double whose generation method raises if invoked.

Every add uses `infer=False`, which is a Mem0-supported path that stores raw memories without calling LLM extraction. The comparator therefore measures persistence, scope, mutation, deletion, and history behavior rather than model quality.

`MEM0_TELEMETRY=false` is set before Mem0 import. No hosted vector service, model endpoint, or product analytics endpoint is required.

The vector-store factory is **not** replaced. Neither `Memory`, Qdrant persistence, SQLite history, nor Mem0 CRUD/scoping logic is mocked.

## Classification vocabulary

P6 reuses the same five-value vocabulary as the Graphiti mapping:

```text
NATIVE               the comparator provides it directly with compatible semantics
CONFIGURABLE         available, but correctness depends on how the caller drives it
WRAPPER_REQUIRED     Agent Memory must supply the missing governance boundary
NOT_REPRESENTABLE    no compatible representation is exposed
UNKNOWN_NEEDS_TEST   execution has not yet resolved the behavior
```

A classification describes the external system. Each scenario separately records the **Agent Memory wrapper implication**. This prevents a useful native feature from being mistaken for delegated governance authority.

## Executed scenarios

### Scoped accumulation and retrieval

Two memories are added under distinct users. The comparator then executes both `get_all` and `search` with explicit user filters.

Pass condition:

```text
user A result set contains no user B memory
user B result set contains no user A memory
```

The observed path is classified `CONFIGURABLE`: Mem0 requires an entity filter for these query APIs and the local Qdrant path honors it, but the caller chooses the identity value. Agent Memory still has to bind that scope to authenticated principal, purpose, policy, and authority.

### Metadata identity laundering

A caller adds under explicit `user_id=A` while freeform metadata attempts to set `user_id=B`.

Pass condition:

```text
stored user_id == A
```

The tested identity-key stripping is `NATIVE`. That is useful hygiene, not an authorization system.

### Correction and update history

A memory is updated by ID while update metadata attempts to broaden its user identity.

Pass conditions:

- memory ID remains stable;
- text changes;
- original user scope remains unchanged;
- non-identity metadata may update;
- SQLite history contains the prior and new values under an `UPDATE` event.

The mechanics are `NATIVE`. Authority to correct and propagation into external derived state remain Agent Memory responsibilities.

### Deletion and history

A memory is deleted by ID.

Pass conditions:

- the live vector record is no longer returned;
- SQLite history records a `DELETE` event with `is_deleted=true` and the prior memory value.

For Agent Memory this is classified `WRAPPER_REQUIRED`, because:

```text
physical vector deletion + DELETE history != forgetting completeness
```

The comparator does not infer that every possible index, cache, summary, export, or other derived representation was removed merely because the primary record disappeared.

### Direct-ID boundary

The comparator executes `get(memory_id)`, `update(memory_id, ...)`, `history(memory_id)`, and `delete(memory_id)` without a scope parameter, because the tested Mem0 OSS APIs expose those operations by ID.

The observed seam is `WRAPPER_REQUIRED` for Agent Memory. Possession of an identifier cannot be treated as authorization. A wrapper must bind direct-ID actions to principal, scope, purpose, current policy, and authority state before invoking them.

This is **not** labeled a Mem0 vulnerability. The comparator does not claim Mem0 OSS promises an authorization layer at this API boundary.

### Scoped bulk deletion

The comparator first verifies that `delete_all()` with no user/agent/run identifier raises. It then executes a user-A bulk deletion and verifies a user-B memory remains.

The path is `CONFIGURABLE`: the API requires caller-supplied scope, and the tested Qdrant path honors it. Agent Memory still has to authorize that requested scope and independently measure deletion completeness.

## Machine-readable evidence

Run in the isolated environment used by CI:

```bash
python -m venv /tmp/agent-memory-p6-mem0
/tmp/agent-memory-p6-mem0/bin/python -m pip install \
  mem0ai==2.0.18 \
  jsonschema==4.26.0
MEM0_TELEMETRY=false PYTHONPATH=reference \
  /tmp/agent-memory-p6-mem0/bin/python reference/run_mem0_comparator.py \
  --agent-memory-commit <exact-40-hex-commit> \
  --output mem0-comparator.json
```

The report conforms to [`../../../schemas/mem0-comparator-report.schema.json`](../../../schemas/mem0-comparator-report.schema.json).

It contains no scalar quality score. `execution_success` means only that every specified experiment produced the expected observation. It does not mean Mem0 conforms to Agent Memory, nor does it average classifications into a grade.

## Limits

This slice does not test:

- hosted Mem0 platform authorization;
- Mem0 cloud tenancy guarantees;
- LLM extraction quality;
- long-horizon task success;
- poisoning or extraction red-team coverage beyond these scope/mutation probes;
- every supported vector-store backend;
- distributed concurrency;
- transitive forgetting across arbitrary external projections;
- latency or economic performance.

The deterministic embedder is a test driver, not a retrieval benchmark. Search is executed only to test whether scope filters survive the real memory-layer path.

## Non-adoption statement

P6 does not make Mem0 an Agent Memory dependency, implementation owner, reference implementation, or doctrine source.

Where Mem0 already provides useful mechanics, Agent Memory should recognize them rather than rebuild them out of ritual. Where authority, lifecycle semantics, receipt binding, or forgetting completeness remain outside the Mem0 OSS layer, a governed wrapper remains the correct boundary.
