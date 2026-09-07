# Research Brief: Sprint 2b — recall authority record and unknown-scope admission

**Date**: 2026-09-04
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 3.
**Scope locked to**: GAP-SEC-02 (record leg) and GAP-ARCH-18.
**Owner decision applied**: the embedding host is the trust boundary and authenticates recall principals; the adapter's obligation is to **record**. The authentication leg therefore closes by contract; the decision record and unknown-scope admission need code.

## 1. Verified findings

### F1 — GAP-ARCH-18 confirmed: unknown scope is admitted as local

`adapter.py:404-406`:

```python
scope = self._fact_scope.get(fact.uuid)
if scope is None:
    return None          # None == admitted
```

A fact with no scope record passes after only the tenant, tombstone, supersession, and dispute checks. Probe:

```
ARCH-18 -- empty target domains, no principal:
   candidates: ['no-scope-1']
   admitted  : ['no-scope-1']
   refusals  : {}
```

Admitted with **empty** `target_domain_refs` and no principal. `docs/34:139` is explicit in the other direction: "candidates that arrive without scope metadata are rejected from admission — unknown scope is treated as out-of-scope, never as local."

### F2 — The JS runtime already does it correctly, and already has the vocabulary

`integrations/agent-memory-runtime/src/index.mjs:114`:

```js
if (!scopeValue) return { admitted: false, rejection: rejection(memoryId, 'unknown_scope') };
```

and `test/runtime-adapter.test.mjs:122` enumerates `['out_of_scope', 'unknown_scope']`. So this is a **Python-versus-JS divergence on a shared contract**, not an undecided design question. `unknown_scope` is the settled refusal string; Python simply lacks it.

### F3 — GAP-SEC-02 confirmed: the read path leaves no governance trace

`governed_recall` (`adapter.py:373-390`) never calls `policy.evaluate` and appends nothing to `self.events`. Probe:

```
   events emitted by governed_recall: 0
   AdmissionResult fields: ['admitted', 'candidates', 'refusals']
   carries policy_version: False
   carries a timestamp   : False

   cross-domain read by an unverified principal 'mallory':
   admitted: ['no-scope-1']  events: 0
```

A cross-domain read, by an unverified principal, against a domain the fact does not belong to, is admitted and leaves nothing behind. Even with the host authenticating perfectly, there is no record that the read happened, who made it, or under what policy.

### F4 — The decision record already exists, schema-backed, one layer up

This materially changes the fix. `schemas/contextual-recall-admission.schema.json` defines a complete governed-recall decision:

`decision_id`, `candidate_ref`, `policy` (`policy_ref`, `policy_version`, `status`, `selection_mode`), `context` (`target_domain_refs`, `principal_ref`, `project_ref`, `task_ref`, `purpose`, `destination_ref`), `outcome` (enum `admit`/`admit_with_warning`/`require_verification`/`require_review`/`quarantine`/`block`), `reason_code`, `evidence_refs`, `evaluated_at`, and an `interpretation` block whose `const` values pin the doctrinal invariants (`authority_effect: current_recall_only`, `prior_admission_authority: none`).

`ContextualRecallAdapter` (`contextual_recall_adapter.py:53-118`) already builds and validates these. But it **wraps** `GovernedMemoryAdapter` and only evaluates candidates that built-in admission already passed:

```python
for candidate_ref in base_result.admitted:
    decision = self._evaluate_current(candidate_ref, context)
    if decision is None:
        result.admitted.append(candidate_ref)   # no record
```

So **built-in admission decisions are recorded by neither layer**: the base adapter emits nothing, and the contextual layer only sees survivors and returns `None` (no record) when no policy is configured. Every built-in refusal reason — `out_of_scope`, `tombstoned`, `isolation_domain_mismatch`, `shared_space_non_member` — is computed and then discarded.

SEC-02's fix is therefore **wiring an existing, schema-validated record into the base path**, not inventing one. That is a much smaller and better-grounded change than the deep audit's framing implied.

### F5 — `event_type` is an open string, so no schema change is needed

`schemas/memory-audit-event.schema.json` requires `event_id`, `event_type`, `event_version`, `timestamp`, `component`, and constrains `event_type` only as `{"type": "string"}`. A `memory.recall` event is schema-legal today. No schema edit, no `SCHEMA_VERSION` bump, no fixture regeneration.

### F6 — Blast radius of ARCH-18 is exactly one emitter

Three modules call `substrate.write_fact` directly, producing scope-less facts:

| Site | Affected by `unknown_scope`? |
|---|---|
| `benchmark_security.py:49` | **No** — `group_id=OTHER_TENANT`, so `out_of_scope` fires first on the tenant check |
| `forbidden_hits.py:238` | **No** — the derived fact's source is tombstoned, so `derived_from_tombstoned_source` fires before the scope check |
| `systems_characterization.py:107` | **Yes** — seeds N same-tenant scope-less facts and then counts `admitted_count` via `governed_recall` |

This confirms the deep audit's blast-radius claim exactly. `systems_characterization` is run by `p9-systems-characterization.yml`; under a correct `unknown_scope` refusal its `admitted_count` drops to zero and the characterization becomes meaningless.

## 2. Design consequences

**ARCH-18** is a one-line refusal plus an emitter fix. The refusal string is dictated by F2 (`unknown_scope`), not chosen.

**The emitter fix looked like it had a trap; it does not.** *Correction, written after tracing the call graph.* `_seed_substrate` is consumed by exactly one function, `characterize_recall` (`:119`). `characterize_write_amplification` (`:78-101`) builds its own substrate and adapter and derives `serialized_evidence_bytes` from a single `commit_proposal`'s own `result.events`; `characterize_deletion_closure` (`:155`) uses `_projection_chain`, not the seed. So seeding through the governed path cannot move the published evidence-bytes numbers.

The earlier draft of this section said the plan had to choose between two options to avoid disturbing them. That caution was unfounded and is corrected here rather than deleted. Seeding through `commit_proposal` is simply the right fix: `characterize_recall` then measures recall over *governed* facts, which is what production looks like, and `candidate_count`/`admitted_count` stay at `size` because the fact text and query are unchanged.

**SEC-02** is: emit a `memory.recall` audit event per governed recall carrying the decision, and record a per-candidate built-in decision in the existing `contextual-recall-admission` shape. `AdmissionResult` can gain `policy_version` and `evaluated_at` as defaulted fields without touching the 70 `governed_recall(` call sites, which read only `.admitted`, `.candidates`, and `.refusals`.

**Deliberately out of scope**: re-shaping `AdmissionResult` into a schema-backed public type is GAP-ARCH-01, which Sprint 4 owns. This cycle adds defaulted fields and an event; it does not freeze a public contract.

## 3. What this cycle does *not* fix

Stated plainly because the gap is CRITICAL and partial closure must not read as closure:

- `RecallContext.principal_ref` remains caller-asserted. That is the owner's trust-boundary decision, not an oversight: the host authenticates, the adapter records. After this cycle a forged principal is recorded accurately as the principal the host asserted.
- `set_shared_domain_members` remains an unguarded setter (SEC-02's membership leg).
- Write-side crossing still never mutates `_fact_scope` (SEC-02's crossing leg).

Those stay open under GAP-SEC-02 and are named in the seal so the gap is not marked closed.

## 4. Risk grade

**L3.** Read-path authority semantics on a CRITICAL gap, and ARCH-18 changes admission from permissive to restrictive — a behaviour change that can hide data from a caller that previously saw it. The 884-test suite and the p9 emitter are the blast surface.

## 5. Next

`/qor-plan`.
