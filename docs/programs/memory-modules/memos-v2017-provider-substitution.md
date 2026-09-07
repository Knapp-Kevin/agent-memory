# MemOS v2.0.17 resource-memory qualification and provider substitution

Issue: #354

## Purpose

This slice tests whether Agent Memory's Capability Contract v3 and Capability Qualification v1.2 can support real provider portability rather than provider-shaped abstractions.

The exact replacement candidate is:

- repository: `MemTensor/MemOS`
- release tag: `memos-local-plugin-v2.0.17`
- tag commit: `d3d1bcfaff65f31b621d58bc236ece6d1e0da5ab`
- package: `@memtensor/memos-local-plugin@2.0.17`
- bounded capability: `resource_artifact_memory@1.0`

The primary provider is the already-qualified Hindsight v0.9.0 resource-memory implementation merged in PR #353.

Provider qualification and substitution have `authority_effect: none`. They establish provider eligibility only. They do not grant recall admission, mutation, structural, policy, or action authority.

## Why the MemOS trace surface

The local plugin exposes a direct, agent-agnostic `MemoryCore` backed by SQLite. Its tagged source provides a bounded resource lifecycle without requiring OpenClaw, Hermes Agent, DeepSeek Harness, a hosted MemOS service, or a hosted LLM:

1. `importBundle()` accepts caller-supplied trace IDs.
2. A colliding trace ID is skipped instead of being assigned a fresh provider ID.
3. `getTrace()` provides direct readback.
4. `listTraces(q=...)` provides deterministic text-filtered candidate retrieval without invoking semantic embedding/ranking.
5. `updateTrace()` mutates user-facing content while retaining the same trace identity.
6. shutdown plus bootstrap against the same runtime home reconstructs SQLite state.
7. `deleteTrace()` hard-deletes the trace and removes its episode reference in a database transaction.

The qualification therefore tests a stable provider-native trace ID as the durable key. It does **not** claim that MemOS conversational `onTurnEnd()` writes are idempotent.

## Source-rights discrepancy

The exact tagged repository root contains an Apache-2.0 license grant, while `apps/memos-local-plugin/package.json` declares `license: MIT`. The plugin directory does not provide a separate MIT license text in the examined tagged source.

The qualification preserves both facts rather than choosing the more convenient label:

- source-rights license used for runtime eligibility: `Apache-2.0`, bound to the exact root `LICENSE` at the tag commit;
- package metadata recorded separately: `MIT`;
- the discrepancy is an explicit qualification check and limitation.

If the root Apache-2.0 grant cannot be verified at exact source, the provider cannot emit `runtime_allowed` qualification evidence.

## Bounded v3 contract

The MemOS candidate profile is deliberately narrower than the product:

### Behavior

- write: supported
- read: supported
- recall candidate: supported through deterministic `listTraces` filtering
- currentness: `provider_revalidated`
- invalidation: `explicit_signal`
- correction: `provider_revalidation`
- deletion: `provider_revalidation`
- residue: `scan_required`
- migration/rebuild: `requires_requalification`
- structural mutation: `none`

### Operational

- write atomicity: `none`
- concurrency control: `none`
- idempotency: `durable_keyed`
- restart recovery: `reconstructable`
- reconciliation: `deterministic_readback`

`handle.db.tx(...)` exists in MemOS tagged source, but this fixture does not inject transaction failures. Transactional atomicity is therefore not promoted into the qualification merely from source inspection.

## Executable lifecycle

The focused fixture uses a single stable trace/session/episode identity and two unique text markers. It proves:

1. initial stable-ID import yields one trace;
2. direct readback and deterministic candidate lookup see the initial content;
3. repeating the same import is skipped and the trace count remains one;
4. `updateTrace()` places replacement content on the same trace ID;
5. old text is no longer returned by the candidate lookup;
6. shutdown/bootstrap against the same SQLite home reconstructs the replacement state;
7. retrying the original import after restart is still skipped and does not overwrite replacement state;
8. hard delete removes direct readback and both old/new candidate residue.

A failed check produces an explicit ineligible result rather than a weaker silently accepted qualification.

## Durable Hindsight evidence

PR #353's passing Hindsight v0.9.0 Qualification v1.2 record is persisted under `reference/fixtures/component-qualification/` with:

- exact PR head `6274070fac248c38dc2b1a7c13fafab79881d681`;
- merge `24707456a9bc89f50a49cb2a889aaeb6998ada54`;
- workflow run `33341188586`;
- artifact digest;
- applicability digest.

The substitution path reconstructs the record and recomputes its applicability digest before use. A modified snapshot cannot become substitution evidence by retaining the old digest string.

## Common substitution requirement

Hindsight and MemOS are compared against one caller requirement rather than against each other.

Required:

- `resource_artifact_memory@1.0`;
- maturity at least `evidence_proven`;
- state posture `derived`;
- scope posture `external_scope_bridge`;
- write/read/recall-candidate support;
- provider-revalidated currentness, correction, and deletion;
- invalidation by either provider revalidation or explicit signal;
- residue scan required;
- requalification after migration/rebuild;
- no structural mutation requirement;
- `durable_keyed` idempotency;
- restart recovery `reconstructable` or stronger;
- reconciliation `deterministic_readback` or stronger;
- runtime-allowed source rights;
- provider authority posture unchanged and non-authoritative.

Atomicity and concurrency are intentionally unconstrained because neither bounded fixture earns stronger guarantees there.

The two provider contracts do not need to be identical. In particular, Hindsight uses provider revalidation for invalidation while the MemOS stable trace surface uses an explicit update/delete signal. Both are eligible only because the caller's requirement explicitly permits those behaviors.

## Negative proof

Focused tests refuse substitution when:

- a persisted qualification digest is tampered;
- a v1.1 qualification is supplied in place of v1.2 contract-bound evidence;
- current declarations drift from the qualified contract;
- durable idempotency degrades to process-local;
- restart recovery or reconciliation degrades to process-local;
- source rights become comparator-only;
- capability authority posture changes.

## Explicit non-goals

This slice does not qualify or import MemOS semantic ranking, learned L2 policies, L3 world models, skills, Hub behavior, disposition, epistemic state, predictive state, or agent integration semantics. It does not make MemOS architecture canonical. It tests whether a second implementation can satisfy one Agent Memory-owned capability boundary.
