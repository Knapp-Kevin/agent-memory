# Plan: Sprint 2c — deletion authority

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-04T1635-bb5378
**Research**: `docs/research-brief-sprint2c-deletion-authority-2026-09-04.md`
**Iteration**: 2 (amended for audit attempt 1 grounds V1-V3)
**Gaps**: GAP-SEC-03 (closed)

## Objective

Make `governed_delete` enforce the authority the write path already enforces: staleness, target binding, tenant ownership, and existence — and stop it writing tombstones that misattribute a fact.

## Boundaries

**In scope**: `reference/agentmem_ref/adapter.py` `governed_delete`, new tests.

**Non-goals**: GAP-SEC-04 — research §4 establishes that the available fix (digest recomputation) closes nothing against a body-editing attacker, and real closure needs an owner decision on the trust anchor. It does not enter an implementation cycle until that is answered. GAP-ARCH-04 is Loop 5.

## Design decisions

**LD1 — Honour staleness on the delete path (D1).**
`governed_delete` passes `blocked_by_stale=self._is_stale(proposal)` instead of the hardcoded `False`. The write path already computes this at `adapter.py:183`; deletion is the more destructive operation and had the weaker guard.

`_is_stale` returns `False` for an empty `state_snapshot`, so the guard is opt-in. Making the snapshot mandatory is a caller-contract change belonging to Sprint 4's boundary freeze (GAP-ARCH-01), not to this cycle.

**The 17 call sites were examined, not assumed (audit V3).** Sixteen pass the default. One does not: `procedural_memory.py:485` passes `state_snapshot=f"v{current_version}"`, and it is safe — `current_version = self.adapter.state_version(memory_ref)` with `target_reference=memory_ref` (`:470-476`), so the snapshot is exactly what `_is_stale` compares against, matches, and the delete still commits. `forbidden_hits.py:324,333,351` pass snapshots to `commit_proposal`, not `governed_delete`. DoD 6 pins this site by name.

**LD2 — Refuse a delete whose fact does not belong to the claimed target (D2, D3).**
Before committing, resolve the fact and require that its memory binding matches `proposal.target_reference`. A mismatch refuses rather than deletes.

This closes D2 (authorization bypass) and D3 (falsified tombstone) together, because the falsified tombstone is the *product* of the unchecked binding. D3 is the weightier half: a tombstone is the record that survives deletion, and one asserting a fact belonged to a memory it never belonged to actively misleads a later reader.

**Binding source (audit V1).** `_fact_scope` does **not** carry a memory reference — it holds `domain_refs`, `required_domain_refs`, `project_ref`, `task_ref`, and `purpose` only, so it cannot answer this question. `_current_fact_by_memory` maps a memory to its *current* fact only, so using it would refuse deletion of any superseded fact, which `pruning` legitimately performs.

The binding is therefore recorded explicitly: `_write` populates a new `_fact_memory: dict[str, str]` mapping `fact_uuid -> proposal.target_reference`, and `governed_delete` requires `self._fact_memory.get(fact_uuid) == proposal.target_reference`.

For a fact with no binding record the delete is refused `target_binding_unknown` — consistent with Loop 3's LD1, where a fact with no scope record became `unknown_scope` on the read path rather than being treated as local. Unknown provenance is not permission.

**LD2b — the binding must survive a restart (audit V2).**
`_fact_memory` is new adapter state, and `restart_runtime._snapshot_governance:219` explicitly snapshots `fact_scope`, `state_version`, `tombstones`, and `current_fact_by_memory`. A map that is not added there restores empty, and every delete after a restart would then refuse `target_binding_unknown` — the guard becomes an outage.

`restart_runtime.py` is therefore in scope: `_snapshot_governance` gains `fact_memory` and `_restore_adapter` restores it. This is the same defect class the Loop 2 audit caught, where `restart_runtime` silently reverted the identity fix; the lesson is that a change to adapter state is a change to restart state.

**LD3 — Refuse a cross-tenant delete (D4), and a delete of a fact that is not there (D5).**
One `self._substrate.get_fact(fact_uuid)` lookup yields both: `None` gives D5's existence refusal, and a `group_id` that is not `self._tenant` gives D4's ownership refusal. Both precede any tombstone or physical delete. Research confirmed tenant B currently performs `permanent_deletion` of tenant A's fact on a shared substrate, and that Loop 2 did **not** address this: Loop 2 fixed identifier minting, while `governed_delete` accepts a `fact_uuid` directly.

**LD4 — Order the guards so the refusal names the real problem.**
Existence (D5) → tenant ownership (D4) → target binding (D2/D3) → staleness (D1). A nonexistent fact must not report `cross_tenant_delete`, and a foreign fact must not report `target_binding_unknown`. Deleting `"does-not-exist"` currently commits and writes a tombstone, manufacturing a governance record for an event that did not occur.

**LD5 — Refusals are refusals, not exceptions.**
All four checks produce a non-committed `CommitResult` carrying a refusal reason, matching how `commit_proposal` already reports a stale or readmission-blocked proposal. Raising would change the failure mode for 17 call sites; returning a refusal keeps the seam and is what the existing contract does.

Refusal vocabulary, matching the existing admission strings: `fact_not_found`, `cross_tenant_delete`, `target_binding_mismatch`, `target_binding_unknown`, `stale_decision`.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/adapter.py` | four guards in `governed_delete` (LD1-LD4), refusal reporting (LD5) |
| `reference/agentmem_ref/restart_runtime.py` | snapshot and restore `fact_memory` (LD2b) |
| `reference/tests/test_deletion_authority.py` | **new** — one test per defect, guard ordering, restart survival, positive path |

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX008 | Governed deletion enforces staleness, target binding, tenant ownership, and existence | NEW |

## Definition of Done

1. Delete with a stale `state_snapshot` is refused `stale_decision`; the fact survives. Previously committed.
2. Delete whose `fact_uuid` does not belong to `proposal.target_reference` is refused `target_binding_mismatch`; **no tombstone is written**. Previously committed and wrote a tombstone attributing the fact to the wrong memory.
3. Cross-tenant delete is refused `cross_tenant_delete` and the victim fact **remains in the substrate**. Previously the fact was physically removed.
4. Delete of a nonexistent uuid is refused `fact_not_found`; no tombstone.
5. The positive path is unchanged: a same-tenant, correctly-targeted, non-stale `pruning` and `permanent_deletion` both still commit, tombstone, and (for permanent) physically delete.
6. An empty `state_snapshot` still permits deletion. The one call site that passes a non-empty snapshot, `procedural_memory.py:485`, still commits — asserted by exercising `ProceduralMemory` revocation end to end, not by inspection.
6b. Guard ordering is asserted: a nonexistent uuid reports `fact_not_found` (not a tenant or binding error), and a foreign-tenant fact reports `cross_tenant_delete` (not a binding error).
6c. After a snapshot/restore round trip, a correctly-targeted delete still commits — `fact_memory` survived. Without LD2b this test fails with `target_binding_unknown`.
7. **All 901 prior tests pass.** A test failing because it depended on an unguarded delete is a finding to report, not a test to amend.
8. `validate_schemas.py` and `validate_fixtures.py fixtures` clean; no fixture regenerated.
9. The seal records GAP-SEC-04 as **investigated and deliberately not implemented**, carrying the §4 decision to the operator.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## CI Coverage Exemptions

Adapter-path evidence workflows (`validate-doctrine-evidence`, `cognitive-mesh-evidence`, `restart-safe-runtime`, `runtime-composition`, `structural-mutation-governance`) are triggered. DoD 7 covers them: the full suite those workflows invoke must pass.

## Rollback

`git checkout -- reference/agentmem_ref/adapter.py` and delete the new test file.

## Next

`/qor-audit`. L3: adversarial mode, independent verification that DoD 6's opt-in claim holds across all 17 call sites.
