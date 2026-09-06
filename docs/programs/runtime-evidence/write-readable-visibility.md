# Write-to-readable visibility and runtime quiescence

Issue: #308
Related: #46 / P9, #282, #280

## Purpose

A successful Agent Memory mutation is not proof that every required read path is current.

This evidence slice makes the following boundaries explicit:

```text
request received
  -> policy decision complete
  -> canonical outcome durable or refused
  -> required derived refresh reaches a terminal state
  -> governed recall can observe the required current outcome
  -> active context can safely use that outcome
  -> runtime settles
  -> runtime is quiescent only when every correctness-required obligation is satisfied
```

The model is provider-neutral. It does not require a queue, index, database, vector store, graph store, or synchronous projection strategy.

## Why this is separate from P9

P9 already characterizes structural work and observational timing for governed writes, recall candidate/admission growth, and deletion derivation closure.

This slice does not replace those measurements. It answers a different question:

> after Agent Memory accepts or refuses a bounded mutation, when can the caller safely conclude that all read-path obligations required by the active profile are current?

Latency remains observational and environment-specific. It does not create authority, change maturity, or become a conformance threshold merely because CI measured it.

## Evidence boundary

The machine-readable contract is `schemas/write-readable-visibility.schema.json`.

The reference implementation lives in `reference/agentmem_ref/visibility.py` and emits exact-head evidence through `reference/run_write_readable_visibility.py`.

Every operation binds evidence to:

- logical memory identity and version;
- operation type;
- Agent Memory commit;
- runtime and profile versions;
- component and capability versions;
- required and optional projection identities;
- receipt and correlation references where available;
- requested visibility target;
- runtime/environment identity.

## Phases

The reference contract records equivalent observations for:

```text
request_received
policy_decision_complete
canonical_commit_complete
required_projection_refresh_started
required_projection_refresh_complete
governed_recall_current_visible
context_current_visible
settlement_reached
quiescence_reached
```

A phase that does not apply is recorded as `not_applicable`; it is not assigned a fabricated zero duration.

Phase order fails closed in the reference tracker. A projection cannot become complete before canonical commit, context cannot become current before governed recall currentness, and downstream visibility cannot be asserted before the canonical outcome exists.

## Obligations

Phases say what was observed. Obligations say what must be true.

Each obligation is explicitly:

```text
required: true | false
status: pending | satisfied | failed | quarantined | not_applicable
```

Typical required obligations include:

- canonical outcome;
- active-profile required projection currentness;
- governed recall currentness;
- context currentness;
- proof that a stale physical version is not admissible as current.

Optional projections may remain as disclosed residual work without blocking quiescence unless the active profile declares them correctness-required.

## Settled is not quiescent

A failed required background operation can reach a known terminal state without making the runtime fully current.

```text
pending required work
  -> settled = false
  -> quiescent = false
  -> posture = pending

explicit required failure or quarantine
  -> settled = true
  -> quiescent = false
  -> posture = degraded

all correctness-required obligations satisfied
  -> settled = true
  -> quiescent = true
  -> posture = quiescent
```

This distinction prevents a queue-empty or worker-returned signal from being mistaken for correctness.

An explicitly refused mutation can be settled and quiescent for that refused operation because no mutation/read-currentness obligations were created. The refusal does not become a successful write.

## Stale physical state

Physical presence and current admissibility are separate.

The reference deferred-projection scenario preserves a superseded canonical fact physically while governed recall rejects it as `superseded_not_current`. A required projection remains stale during that lag window, so the operation remains non-quiescent even though the new canonical value is already recallable.

This is deliberate:

```text
physically present != current
current canonical != all required projections current
recallable current value != profile quiescence
```

## Restart

`VisibilityTracker.snapshot_for_restart()` serializes the declared operation, observed phases, and pending/terminal obligations. `restore_after_restart()` creates a new timing segment and retains the correctness state.

Process-local monotonic clocks are not stitched together across restart. Any metric whose endpoints fall in different timing segments reports:

```text
reason = cross_restart_monotonic_segments
value_ns = null
```

This loses a timing number rather than inventing one. #282 remains responsible for the durable runtime mechanism that stores and reconstructs these obligations in a real restart-safe runtime.

## Deletion

Deletion is not quiescent merely because the canonical delete returns success.

If the active profile declares derived residue, rebuild, index, or absence-visibility obligations as required, those obligations must be satisfied before quiescence. A deletion can therefore be canonically durable and still remain pending.

## Comparator pressure

Two independently checked primary-source architectures informed this contract:

1. Claude-Mem demonstrates canonical persistence preceding a later derived/vector synchronization step that can lag or fail.
2. Nanobot at `HKUDS/nanobot@b99e0f937e828504e0f93dbe35dfd6b1540e20b2` persists producer and consumer progress separately and advances its Dream consumption cursor only after clean completion without tool errors.

Agent Memory does not import either implementation's completion marker as authority. They are failure-shape comparators that pressure the provider-neutral obligation model.

## Required reference scenarios

The characterization runner exercises:

1. synchronous canonical-only write;
2. deferred required projection refresh;
3. required refresh failure;
4. restart during a pending refresh obligation;
5. deletion with required residue work.

The structural gates are semantic. Timing summaries are p50/p95/p99 observations for the local runner where the relevant endpoints share a monotonic timing segment.

## Non-goals

This slice does not:

- create a universal latency SLO;
- require all projections to become synchronous;
- choose a queue/index/database implementation;
- make provider-native completion equal Agent Memory quiescence;
- make speed an authority or maturity signal;
- replace P9 structural cost characterization;
- complete #282's persistent runtime by itself.
