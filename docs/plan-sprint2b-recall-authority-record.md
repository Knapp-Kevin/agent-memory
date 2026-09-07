# Plan: Sprint 2b — recall authority record and unknown-scope admission

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-04T1623-fc1836
**Research**: `docs/research-brief-sprint2b-recall-authority-record-2026-09-04.md`
**Iteration**: 2 (amended for audit attempt 1 grounds V1-V3)
**Gaps**: GAP-ARCH-18 (closed), GAP-SEC-02 (record leg only — **not** closed)

## Objective

Refuse candidates that arrive without scope metadata, and make every governed recall leave a governance record.

## Boundaries

**In scope**: `reference/agentmem_ref/adapter.py`, `reference/agentmem_ref/systems_characterization.py`, new tests.

**Non-goals**: GAP-SEC-03, GAP-SEC-04 (Loop 4); GAP-ARCH-04 (Loop 5); re-shaping `AdmissionResult` into a schema-backed public type (GAP-ARCH-01, Sprint 4).

**Explicitly not fixed by this cycle** — GAP-SEC-02 stays open:
- `RecallContext.principal_ref` remains caller-asserted. This is the owner's trust-boundary decision (host authenticates, adapter records), not an oversight.
- `set_shared_domain_members` remains an unguarded setter.
- Write-side crossing still never mutates `_fact_scope`.

## Design decisions

**LD1 — Refuse unknown scope as `unknown_scope`.**
`_admission_refusal` returns `"unknown_scope"` where it currently returns `None` for a missing `_fact_scope` entry.

The string is dictated, not chosen: `integrations/agent-memory-runtime/src/index.mjs:114` already returns exactly this, and `test/runtime-adapter.test.mjs:122` enumerates the vocabulary. This closes a Python/JS divergence on a shared contract and satisfies `docs/34:139`.

**LD2 — Seed the p9 emitter through the governed path.**
`systems_characterization._seed_substrate` currently writes N facts straight to the substrate, so every one is scope-less and would now be refused, dropping `admitted_count` to zero and voiding the characterization. Replace the direct `substrate.write_fact` loop with `adapter.commit_proposal`, one proposal per fact, preserving fact text so the query still matches.

Verified safe (research §2, corrected): `_seed_substrate` feeds only `characterize_recall`, which reports `retained_facts`, `candidate_count`, `admitted_count`, and timing. The module's `serialized_evidence_bytes` figures come from `characterize_write_amplification`, which builds its own adapter. No published evidence-byte number moves.

**LD3 — Emit one `memory.recall` audit event per governed recall, in the shape the schema and `docs/34` specify.**

`memory-audit-event.schema.json` sets `additionalProperties: False` (audit V1), so field placement is dictated, not free. The event uses the structure `docs/34:136` names (audit V2):

| Field | Value |
|---|---|
| `event_type` | `"memory.recall"` — legal because the schema constrains `event_type` only as `{"type": "string"}` (research F5) |
| `signal.signal_type` | `"recall_admission"` — the literal `docs/34:136` requires |
| `signal.signal_semantics` | the admission outcome summary, which `docs/34` requires to live here |
| `principal` | `context.principal_ref` — a top-level string in the schema |
| `policy_version` | `policy.POLICY_VERSION` |
| `timestamp`, `event_id`, `event_version`, `component` | schema-required |
| `payload` | the remaining context (`target_domain_refs`, `project_ref`, `task_ref`, `purpose`), counts, and the per-candidate outcome map. `payload` is `additionalProperties: true`, so this is its legitimate home |

Nothing goes at top level that the schema does not name. The event is validated against the schema on construction so a malformed record fails loudly.

**LD4 — Record a per-candidate built-in decision in the existing shape.**
For each candidate, build a `contextual-recall-admission` document — the schema already exists and `ContextualRecallAdapter` already validates against it — with `outcome` `admit` or `block`, `reason_code` the refusal string (or `admitted`), and the `interpretation` block's doctrinal consts.

This is the substance of SEC-02's record leg: today every built-in refusal reason is computed and discarded, and `ContextualRecallAdapter` only ever sees candidates that already passed. Reusing the existing schema rather than inventing a record keeps the two recall layers speaking one vocabulary.

**LD5 — Extend `AdmissionResult` additively.**
Add `decisions: dict[str, dict]`, `policy_version: str`, and `evaluated_at: str`, all defaulted. The 70 `governed_recall(` call sites read only `.admitted`, `.candidates`, and `.refusals` and are unaffected.

Additive fields, not a re-shaped public type: GAP-ARCH-01 owns schema-backing this class and belongs to Sprint 4. This cycle must not freeze a contract Sprint 4 is going to change.

**LD6 — `policy.status` is `unavailable`, and that is a deliberate choice among what exists.**

The recall path does not call `policy.evaluate`. Built-in admission is not a PAMA proposal evaluation, and recording `evaluated` would fabricate a decision the reference never made.

`contextual-recall-admission.schema.json` constrains `policy.status` to `['evaluated', 'unavailable', 'error', 'invalid']` (audit V3). There is no value meaning "built-in admission, no contextual policy". Of the four, **`unavailable`** is the honest one: no contextual policy was available to evaluate, which is precisely the state. `policy_ref` records `contextual-recall-policy:none` and `policy_version` records `policy.POLICY_VERSION`, so a reader can tell the built-in decision from an evaluated one without the status field carrying that weight alone.

The missing vocabulary is a real gap and is **not** papered over: this cycle records it for Sprint 4, which owns the recall-decision contract under GAP-ARCH-01. A status value meaning "built-in admission" belongs to that boundary freeze, not to a cycle that must not change a public schema.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/adapter.py` | `unknown_scope` refusal (LD1); recall event (LD3); per-candidate decision (LD4); `AdmissionResult` fields (LD5) |
| `reference/agentmem_ref/systems_characterization.py` | seed through `commit_proposal` (LD2) |
| `reference/tests/test_recall_unknown_scope.py` | **new** — refusal, JS parity, and the three shielded call sites |
| `reference/tests/test_recall_authority_record.py` | **new** — event emitted, decision per candidate, schema-valid, fields populated |

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX006 | Recall refuses candidates with no scope metadata as `unknown_scope`, matching the JS runtime | NEW |
| FX007 | Every governed recall emits an audit event and a per-candidate admission decision | NEW |

## Definition of Done

1. A same-tenant fact with no `_fact_scope` entry is refused `unknown_scope`, including when `target_domain_refs` is empty. The probe that previously showed it admitted now shows it refused.
2. The refusal string matches the JS runtime's exactly — asserted against the literal `unknown_scope`, with the parity source cited in the test.
3. Refusal ordering is unchanged: `benchmark_security`'s foreign fact still refuses `out_of_scope`, and `forbidden_hits`' derived fact still refuses `derived_from_tombstoned_source`. Both asserted, because F6's blast-radius claim depends on that ordering.
4. `governed_recall` appends exactly one event per call and it **validates against `memory-audit-event.schema.json`** — the discriminating check, since `additionalProperties: False` fails any stray top-level field. It carries `signal.signal_type == "recall_admission"`, the admission outcome in `signal.signal_semantics`, `principal`, `policy_version`, and the context and counts under `payload`.
5. Every candidate — admitted and refused — has an entry in `result.decisions`, each validating against `contextual-recall-admission.schema.json`, with `policy.status == "unavailable"` and `policy_ref == "contextual-recall-policy:none"` asserted by name so a later change to `evaluated` is legible as a regression.
6. `result.policy_version` and `result.evaluated_at` are populated.
7. `characterize_recall` still reports `admitted_count == size` for sizes 10, 100, 500.
8. **All 884 prior tests pass.** A test failing because it depended on unknown-scope admission is a finding to report, not a test to amend.
9. `validate_schemas.py` and `validate_fixtures.py fixtures` clean; no fixture regenerated.
10. The seal records GAP-SEC-02 as **partially** addressed, naming the three legs left open.
11. The seal records the `policy.status` vocabulary gap (no value means "built-in admission") as a Sprint 4 / GAP-ARCH-01 item, so LD6's compromise is visible rather than buried in a field value.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## CI Coverage Exemptions

Evidence workflows path-filtered on the adapter (`validate-doctrine-evidence`, `cognitive-mesh-evidence`, `restart-safe-runtime`, `runtime-composition`, `p9-systems-characterization`) are triggered by this change. DoD 7 and DoD 8 cover them: the full suite those workflows invoke must pass, and the p9 emitter's own output is asserted.

## Rollback

`git checkout -- reference/agentmem_ref/adapter.py reference/agentmem_ref/systems_characterization.py` and delete the two new test files.

## Next

`/qor-audit`. L3: adversarial mode, independent verification of the refusal-ordering claim and of the "no prior test depended on this" assertion.
