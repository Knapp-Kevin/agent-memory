# Framework Lifecycle / Checkpoint Interoperability Profile

Status: V0.1 generic lifecycle seam, validated against two materially different reference hosts.

This profile defines the minimum Agent Memory-facing seam for stateful agent frameworks that expose runs, workflow/session state, checkpoints, retries, resumes, or related runtime events.

The first reference host is Microsoft Agent Framework (MAF) Python `1.13.0`, tag `python-1.13.0`, pinned source commit `e39a8a2e79c8c8987a0b9082d3ccb8665734b897`.

The second reference host is LangGraph `1.2.11`, tag `1.2.11`, pinned source commit `644815f9e5bc52ad8f7a5227a456227e9c3e639b`, with `langgraph-checkpoint==4.2.0` pinned for checkpoint behavior.

Both are reference hosts, not required Agent Memory runtimes or canonical storage layers.

## Core boundary

```text
framework persisted state
!= Agent Memory admitted durable memory

retry
!= new durable mutation authority

checkpoint rewind
!= permission to roll back current Agent Memory state

session / workflow / thread history
!= canonical memory by default
```

Framework runtime state may be useful as execution state, evidence, a memory candidate, or explicit non-memory. The classification must be explicit.

## Generic lifecycle seam

A V0.1 framework event may preserve:

```text
framework identity / version / pinned source
run / workflow / session reference
checkpoint and previous-checkpoint reference
event type
persistence classification
Agent Memory action / proposal identity
PAMA / decision receipt reference
composition / approval / execution reference when present
runtime trace-correlation reference when present
scope / tenant / project opaque references
Agent Memory state reference
idempotency key
evidence references
```

The generic contract does not copy framework conversation history, checkpoint blobs, prompts, tool payloads, or arbitrary framework metadata into canonical memory.

The same `framework-lifecycle-event.schema.json` contract is used by both MAF and LangGraph. The second host did not require LangGraph-specific core fields.

## Checkpoint ordering and memory-state freshness

The MAF `WorkflowCheckpoint` source at the pinned release carries both `previous_checkpoint_id` and `iteration_count`. MAF explicitly documents that `iteration_count` is not guaranteed unique, particularly around human-in-the-loop checkpoints, and that checkpoint ordering is defined by checkpoint lineage and timestamp rather than iteration count alone.

LangGraph exposes checkpoint identity and parent-config lineage through real `StateSnapshot` history. The second-host comparator reconstructs lineage from checkpoint IDs and parent checkpoint configuration rather than treating thread identity or state values as ordering authority.

Agent Memory therefore treats explicit lineage as the V0.1 **framework checkpoint relation** signal:

```text
resume checkpoint == latest checkpoint -> current
resume checkpoint is an ancestor of latest -> stale
known checkpoint on another lineage -> divergent
missing/incomplete lineage -> unknown
```

That relation is separate from whether the checkpoint is fresh relative to canonical Agent Memory state:

```text
framework checkpoint recency
!= Agent Memory state freshness
```

A framework may legitimately retain a checkpoint as its latest checkpoint even after an external governed memory mutation occurs. When the checkpoint is bound to an Agent Memory `memory_state_ref`, that binding must be compared with current Agent Memory state independently. A checkpoint bound to an older state is stale **for memory replay purposes** even if the framework still considers it valid execution history.

Neither a stale/divergent framework lineage nor a stale Agent Memory state binding gains rollback authority over newer canonical Agent Memory state.

## Retry and idempotency

A framework retry or resume may re-enter the same application code after Agent Memory already committed a durable mutation.

V0.1 binds the mutation attempt to a stable idempotency key and the original decision receipt:

```text
same idempotency key + same receipt -> replay / reuse receipt
same idempotency key + different receipt -> conflict
new key -> new governed proposal required
```

The framework runtime does not decide whether repeated execution is a new authorized memory mutation.

This rule survived both reference hosts:

- MAF stale-checkpoint replay re-entered the mutation step and reused the original receipt;
- LangGraph `RetryPolicy` re-entered a node after the Agent Memory commit had succeeded but before the node completed successfully, and the second attempt reused the recorded receipt rather than committing again.

## Persistence classification

Every framework persistence event uses one of:

- `execution_state`: state retained only to continue/recover execution;
- `evidence`: runtime state retained as evidence about what happened;
- `memory_candidate`: state that may be proposed through normal Agent Memory admission;
- `explicit_non_memory`: state that must not be treated as Agent Memory.

None of these classifications establishes admission by itself, including `memory_candidate`.

Both real-host comparators classify framework checkpoint persistence as `execution_state` unless a separate governed process explicitly proposes it as evidence or a memory candidate.

## Scope binding

When a framework event is correlated to an Agent Memory action, expected action/input/scope/tenant/project references are compared deterministically. Missing or mismatched fields remain mismatch evidence rather than being repaired through timing, names, semantic similarity, checkpoint adjacency, or valid framework session/thread identity.

A valid MAF workflow or LangGraph thread/checkpoint is runtime identity, not tenant/project authority.

## Trace correlation

Runtime trace correlation from the #185 profile is optional evidence.

```text
trace available -> additional correlation evidence
trace unavailable -> governance/decision/checkpoint evidence remains valid
trace absent -> not proof that execution did not occur
```

Neither real-host comparator requires a trace backend to preserve the governance/checkpoint evidence under test.

## First-host behavioral proof: Microsoft Agent Framework

The pinned MAF comparator uses the real `agent-framework-core==1.13.0` package with `WorkflowBuilder`, `WorkflowCheckpoint`, and `InMemoryCheckpointStorage`. It does not require an LLM or cloud service.

The comparator executes a real checkpointed MAF workflow and proves a bounded lifecycle:

1. a governed Agent Memory seed is available for scoped recall;
2. MAF starts a workflow and emits a checkpoint after the first superstep;
3. execution is interrupted only after that checkpoint boundary;
4. a new MAF workflow instance resumes from the checkpoint;
5. the resumed framework step performs governed recall and commits one PAMA-authorized durable mutation;
6. the checkpoint's bound Agent Memory state becomes stale when the governed mutation advances canonical memory state, regardless of whether MAF emits a newer descendant checkpoint;
7. replaying that old checkpoint re-enters the framework step but reuses the original Agent Memory receipt and does not duplicate the durable mutation or roll state backward;
8. a separate real MAF run carries a PAMA-denied mutation through framework continuation without committing it;
9. cross-scope recall is not admitted;
10. missing trace correlation does not erase governance evidence.

A separate real-object checkpoint case creates two MAF checkpoints with the same `iteration_count` but different lineage, proving that the adapter does not use the iteration counter as ordering authority.

## Second-host behavioral proof: LangGraph

The pinned second-host comparator uses real `langgraph==1.2.11` and `langgraph-checkpoint==4.2.0` with `StateGraph`, `InMemorySaver`, checkpoint history, thread IDs, and `RetryPolicy`. It does not require an LLM, provider API, LangSmith, or external persistence service.

The comparator proves the same Agent Memory-facing lifecycle against materially different framework mechanics:

1. a real StateGraph thread performs governed recall inside a graph node;
2. a later graph node commits one PAMA-authorized durable Agent Memory mutation;
3. real LangGraph checkpoint history preserves a checkpoint before the mutation node and a later checkpoint after execution;
4. explicit checkpoint IDs and parent-config lineage feed the same generic checkpoint-relation classifier used by the framework profile;
5. the pre-mutation checkpoint's Agent Memory state binding becomes stale after canonical memory advances;
6. replaying from that old checkpoint re-enters the mutation node but reuses the original receipt and does not duplicate the durable write or roll Agent Memory state backward;
7. a separate LangGraph run deliberately commits a durable mutation and then raises before successful node completion;
8. real LangGraph `RetryPolicy` re-enters that node and reuses the recorded receipt, proving a post-commit framework failure does not create a second durable mutation;
9. another graph run carries a PAMA-denied mutation and produces zero durable writes;
10. a valid LangGraph thread runs with cross-scope recall context and receives no admitted memory;
11. framework checkpoint evidence uses the same generic lifecycle-event schema and is classified `execution_state`, not Agent Memory admission;
12. missing trace correlation remains an explicit evidence gap rather than non-execution proof.

### Generic finding from the second host

LangGraph did **not** require a new canonical lifecycle concept.

Its thread identity maps to generic run/session identity; checkpoint IDs and parent configs map to checkpoint lineage; `RetryPolicy` maps to retry evidence; persisted graph state maps to explicit persistence classification.

That result strengthens the generic seam:

```text
MAF workflow/checkpoint mechanics
and
LangGraph thread/checkpoint mechanics
-> same Agent Memory-facing lifecycle contract
```

The frameworks are materially different, but the memory/governance boundary remains stable.

## Checkpoint or node failure after memory commit

Framework persistence or successful node completion can fail after Agent Memory has already committed a durable mutation.

The default consequence remains:

```text
Agent Memory commit succeeded
+ framework checkpoint/node completion failed
-> canonical memory commit remains current
-> framework recovery is required
-> retry must consult the prior receipt/idempotency key
-> no silent rollback
-> no automatic second durable mutation
```

MAF exercises checkpoint/replay recovery. LangGraph exercises a concrete post-commit node failure followed by real framework retry. Both preserve the same rule.

A framework failure does not itself authorize compensation or rollback. Any compensating memory mutation must cross normal Agent Memory governance.

## Privacy and minimization

Default to stable identifiers, opaque scope refs, digests, receipt refs, checkpoint refs, thread/run refs, and classifications.

Do not persist raw framework messages, prompts, hidden reasoning, complete checkpoint state, provider credentials, or full tool payloads merely to establish lifecycle correlation.

The LangGraph comparator records checkpoint IDs/history counts and bounded state references rather than copying checkpoint payloads into Agent Memory evidence.

## V0.1 non-claims

V0.1 does not claim:

- MAF or LangGraph checkpoints are Agent Memory;
- checkpoint persistence proves lifecycle satisfaction;
- either framework's latest checkpoint proves Agent Memory state freshness;
- a framework thread/session ID is an authority boundary;
- framework retry creates new authority;
- framework HITL history is reusable approval authority;
- trace success proves semantic authorization;
- two hosts prove the seam is universal across every framework;
- MAF or LangGraph is a required dependency for Agent Memory core/reference use;
- LangGraph Store or framework-native long-term memory is automatically Agent Memory.

## Failure behavior

- Agent Memory unavailability at a durable-mutation boundary cannot silently widen authority; the framework must fail according to configured policy rather than infer permission;
- stale/unknown checkpoint lineage does not silently restore older memory state;
- a checkpoint whose bound Agent Memory state is stale cannot silently restore older memory state even when the framework still considers the checkpoint valid/current execution history;
- retry after a known committed mutation reuses the bound receipt rather than committing again;
- framework failure after a successful memory commit preserves the memory receipt and requires framework recovery rather than silent rollback;
- a denied mutation remains denied even if framework execution continues;
- cross-scope context does not inherit memory merely because the framework run/thread/checkpoint is valid;
- framework persistence remains explicitly classified and does not become durable memory by persistence alone;
- trace backend unavailability preserves explicit evidence gaps without widening authority.

## Rollback / removal

Framework comparators and adapters are optional. Removing MAF or LangGraph support leaves canonical Agent Memory state, receipts, and lifecycle semantics interpretable because framework-specific runtime objects remain in adapter/evidence layers and the canonical lifecycle event carries vendor-neutral references only.

## Follow-on gate

The same generic lifecycle contract has now survived the two intentionally different first reference hosts required by #169: MAF and LangGraph.

A third framework may now be considered breadth work rather than a prerequisite for the generic seam. The #169 research order recommends Google ADK as a useful later versioning/migration stress case, followed by OpenAI Agents SDK and other runtimes.

Before adding a third host:

```text
new framework maps cleanly to the existing lifecycle seam
or
real semantic incompatibility returns to #169 research
```

Do not accumulate framework-specific core exceptions merely to increase adapter count.
