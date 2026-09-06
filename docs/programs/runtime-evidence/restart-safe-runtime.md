# Restart-safe reference runtime

Status: implementation evidence for #282

This slice establishes the first executable process-restart boundary for Agent Memory. It is intentionally a bounded reference durability profile, not a storage recommendation.

## Earned claim

`reference_file_checkpoint_v1` proves that a governed reference runtime can stop, reconstruct durable substrate state plus governance-critical interpretation state, and continue enforcing currentness, supersession, scope, rejected-value history, stale-state protection, exact component interpretation, and pending write-to-readable obligations.

It does **not** prove production HA, distributed consensus, transactional database semantics, or live DashClaw HTTPS restart behavior.

## Durable boundary

The store writes three records:

1. `substrate.json` contains retained episodes/facts and physical temporal state.
2. `governance.json` contains the governance envelope required to interpret that state safely.
3. `runtime-manifest.json` is replaced last and binds both payloads plus the runtime/profile/component interpretation by SHA-256 digest and generation.

The separation is deliberate:

```text
substrate persisted
  != governance recovered
  != component interpretation recovered
  != required read paths current
  != quiescent
```

A missing payload, malformed payload, digest mismatch, unsupported schema, changed profile, unavailable required capability, or changed component interpretation causes recovery to fail closed.

## Governance state reconstructed

The first profile preserves or reconstructs:

- tenant identity;
- logical memory state version;
- current fact by logical memory identity;
- superseded physical fact state in the temporal substrate;
- fact isolation-domain/project/task bindings;
- shared-domain membership state used by the reference admission gate;
- disputed state;
- tombstones and deletion obligations already represented by the adapter;
- rejected-value fingerprints and lifecycle history;
- deterministic clock/identifier progress needed to prevent object identity reuse;
- audit/containment records retained by the reference adapter;
- exact runtime/profile/component/capability interpretation;
- #308 visibility snapshots, including pending required projection/currentness obligations.

The implementation currently supports deterministic selector recovery only. An unsupported selector fails rather than silently changing selection semantics.

## Component interpretation

The persisted runtime profile contains exact capability bindings:

- component id/version;
- capability id/version;
- maturity;
- evidence reference;
- source-rights posture.

Recovery currently requires the same exact interpretation. A component upgrade is not assumed compatible. Future #280/#300 compatibility evidence may permit an explicitly proven migration, but version movement alone cannot silently reinterpret durable memory.

## Acceptance scenario

`reference/tests/test_restart_safe_runtime.py` exercises the release-branch scenario through multiple independent runtime objects:

1. Session A retains `release_branch = release`.
2. Session B reconstructs state and recalls it.
3. an externally reviewed correction supersedes it with `release_branch = main`;
4. replay of the stale `v1` correction fails;
5. Session C/D reconstruct the current `main`, preserve historical `release` as superseded, and preserve rejected-value history;
6. project-scope mismatch remains blocked;
7. a pending required projection obligation from #308 remains pending after restart and is not relabeled quiescent;
8. missing provider interpretation fails closed;
9. corrupt governance state fails closed.

The exact-head runner emits machine-readable evidence:

```bash
python reference/run_restart_safe_runtime.py \
  --agent-memory-commit <exact-40-hex-commit> \
  --output restart-safe-runtime.json
```

CI also runs the complete reference regression suite before preserving that artifact.

## Remaining #282 work

This PR should not close #282. The next slices still need to prove, among other things:

- explicit crash injection at finer transaction boundaries, including durable substrate change without a matching governance checkpoint;
- deterministic ambiguous-provider failure after restart;
- capability maturity downgrade and compatibility-migration evidence integrated with the common #280/#300 registry rather than the bounded exact-binding profile;
- deletion/rebuild recovery beyond the currently persisted obligation representation;
- live DashClaw external-verdict restart composition where required by #279;
- a service/CLI boundary suitable for the eventual attach-to-existing-stack installation flow.

The important product consequence is that future `agent-memory doctor` behavior can distinguish persistence, successful reconstruction, degraded currentness, and true quiescence instead of reporting a single cheerful but useless `healthy=true`.
