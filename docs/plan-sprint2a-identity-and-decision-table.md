# Plan: Sprint 2a — substrate identity collision and decision-table completion

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-04T1600-c8b357
**Research**: `docs/research-brief-sprint2a-identity-and-decision-table-2026-09-04.md`
**Iteration**: 2 (amended for audit attempt 1 grounds V1-V5)
**Gaps**: GAP-SEC-08, GAP-ARCH-09 (+ GAP-DOC new, see LD5)

## Objective

Stop two adapters over one substrate from minting colliding identifiers, and make the PAMA base decision table match doctrine for the three operations it omits.

## Boundaries

**In scope**: `reference/agentmem_ref/substrate.py`, `reference/agentmem_ref/adapter.py`, `reference/agentmem_ref/policy.py`, new tests, `docs/33-pama-decision-table.md`.

**Non-goals**: GAP-SEC-02, GAP-SEC-03, GAP-SEC-04, GAP-ARCH-04, GAP-ARCH-18 (Loops 3-5). Substrate-scoped id *semantics* and a declared `TemporalGraphPort` method stay Sprint 6 / Sprint 4.

**Exclusions**: no change to `TemporalGraphPort`'s Protocol declaration; no id-format change; no schema change; no fixture regeneration; no change to `graphiti_driver` or any external substrate implementation.

## Design decisions

**LD1 — Substrate-owned id counter, discovered by attribute.**
`InMemoryTemporalGraph` gains its own `DeterministicIds("ref")` and a `next_id()` method. `GovernedMemoryAdapter.__init__` binds `self._ids` to the substrate's counter when the substrate exposes `next_id`, and constructs a per-adapter `DeterministicIds("ref")` otherwise.

Discovery by `getattr` rather than by Protocol declaration is deliberate: `TemporalGraphPort` is a `Protocol` and adding a member would break `graphiti_driver` and any external implementation. Sprint 4 owns that declaration. This keeps the fix additive.

Single-adapter sequences are bit-identical: a substrate counter starting at zero with one consumer emits exactly what the per-adapter counter emits today. Two adapters now interleave instead of colliding, which is the defect.

**LD2 — Collision refusal in `write_fact`, as defence in depth.**
`InMemoryTemporalGraph.write_fact` raises `ValueError` when the uuid already exists and the incoming `Fact` differs from the stored one. An identical re-write is a no-op, so the method stays idempotent.

This is not redundant with LD1: a foreign substrate without `next_id` still falls back to per-adapter counters, and this guard turns the resulting silent data loss into a loud failure. Raising matches `docs/34`'s statement that rejection is the failure mode where this code raises `ValueError`.

Verified safe (research §7): `invalidate_fact` mutates `_facts` directly (`substrate.py:116`) and `restart_runtime.py:157` restores by assigning `substrate._facts` wholesale, so neither supersession nor restart passes through the guard. The two external direct callers use explicit non-`ref-` uuids.

Research §7 checked that *restore itself* bypasses `write_fact` — true — but not writes **after** a restore. LD6 closes that.

**LD6 — The counter's lifetime follows the substrate across a restart** (V1, V2).

`restart_runtime.py` owns counter state today: `:216` snapshots `adapter._ids._n`, and `:248-249` restores it by rebinding `adapter._ids` to a fresh private `DeterministicIds`. Under LD1 that rebinding **detaches the adapter from the substrate counter**, so the first restart silently reverts this entire fix. `restart_runtime.py` is therefore in scope.

The change is to stop rebinding and instead advance the substrate's counter:

```python
adapter = GovernedMemoryAdapter(substrate, tenant=tenant)   # bound to the substrate counter
adapter._ids._n = max(adapter._ids._n, int(raw.get("id_counter", 0)))
```

`max` rather than assignment because several adapters over one substrate each carry an `id_counter`; the shared counter must end at the highest observed position so no restored identifier can be re-minted.

This deliberately requires **no `SCHEMA_VERSION` bump and no snapshot-format change**. The `id_counter` field keeps its meaning — the counter position at snapshot time — and simply lands on the counter the adapter now draws from. Bumping the version would reject every existing operator-local snapshot for a field that did not need to move.

Residual, accepted and disclosed: a snapshot with no `id_counter` (defaulting to 0) alongside restored facts will make the next write collide, and LD2 will raise. That is correct behaviour — today the same write silently destroys a restored fact — and it is loud rather than silent. DoD 11 pins it.

**LD3 — Complete `_BASE_TABLE` from doctrine.**
Add the twelve cells for `score_adjustment`, `link_creation`, `link_deletion`, transcribed from `docs/33:80-93`. Research F3 establishes zero external blast radius: the constant is private, its three references are all in `policy.py`, and the operation strings appear in no Python file.

Two of the twelve close a real weakness — `score_adjustment/critical` (doctrine `block`, fallback `require_review`) and `link_deletion/critical` (doctrine `require_external_verification`, fallback `require_review`). Five make the reference *less* strict than the fallback, matching doctrine; that is a correctness fix, not a relaxation of a decision anyone relied on, because no caller passes these operations.

**LD4 — Keep the `REQUIRE_REVIEW` fallback.**
`_base_outcome` keeps its default for operations outside the table (`capability_promotion`, `authority_change`, `other` are in the schema enum but not in doctrine's base table). Removing the fallback would turn an unknown operation into a `KeyError` on the authority path. The fallback stays as the conservative floor for genuinely unknown operations; LD3 removes the cases where it was masking a *known* one.

**LD5 — Record the reverse drift in doctrine (F4).**
`domain_schema_mutation` has a `_BASE_TABLE` row, a schema enum entry, and an ADR-032 definition, but no row in the `docs/33` base table. Add the row, transcribed from the code's existing cells, with a note that ADR-032 introduced the operation after the table was written.

In scope because leaving it means this cycle asserts "the table matches doctrine" while a known mismatch remains in the other direction. It is a documentation edit with no runtime effect.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/substrate.py` | `InMemoryTemporalGraph`: own `DeterministicIds`, `next_id()`, collision guard in `write_fact` |
| `reference/agentmem_ref/adapter.py` | bind `self._ids` to the substrate counter when available |
| `reference/agentmem_ref/policy.py` | twelve new `_BASE_TABLE` cells |
| `reference/tests/test_substrate_identity.py` | **new** — collision regression + guard + fallback |
| `reference/tests/test_decision_table_doctrine.py` | **new** — every `docs/33` cell resolves as documented |
| `reference/agentmem_ref/restart_runtime.py` | stop rebinding `adapter._ids`; advance the substrate counter with `max` (LD6) |
| `reference/tests/test_substrate_identity_restart.py` | **new** — counter survives a restart and stays substrate-bound |
| `docs/33-pama-decision-table.md` | add the `domain_schema_mutation` row |

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX004 | Two adapters sharing a substrate mint disjoint identifiers across facts, receipts, and events | NEW |
| FX005 | PAMA base decision table resolves every `docs/33` operation/risk cell as documented | NEW |

## Definition of Done

1. The research probe becomes a passing regression test: two tenants, one substrate, **both facts survive**, and no identifier is shared between the two `CommitResult`s — fact uuid, `receipt_id`, `correlation_id`, and all four event ids pairwise disjoint.
2. A substrate without `next_id` still works, and a forced duplicate uuid through `write_fact` raises `ValueError` rather than replacing.
3. An identical re-write through `write_fact` is a no-op and does not raise.
4. Every one of the **52** `docs/33` operation/risk cells (**13** operations x 4 risk classes, including the `domain_schema_mutation` row LD5 adds) resolves to the documented outcome via `policy.evaluate`, asserted table-driven from the doctrine values.
5. `score_adjustment/critical` resolves `block` and `link_deletion/critical` resolves `require_external_verification` — the two previously-weaker cells, asserted by name so a regression is legible.
6. Single-adapter id sequences are unchanged, pinned by a **new** test that asserts the literal sequence a single adapter emits for a fixed proposal (`ref-0001` through `ref-0007` for one `commit_proposal`). No existing test or fixture asserts these values — `grep -rn "ref-000"` returns 0 hits in `reference/tests/` and 0 in `fixtures/` — so LD1's bit-identical claim has no existing coverage and this cycle must supply it.
7. `python -m unittest discover -s reference/tests -t reference` — **all prior 868 tests still pass**. A test that fails because it depended on the silent overwrite is a finding to report, not a test to amend.
8. `python scripts/validate_schemas.py` and `validate_fixtures.py fixtures` clean; no fixture regenerated.
9. `docs/33` base table carries a row for each of the **13 operations that have base cells**. The three remaining enum members — `capability_promotion`, `authority_change`, `other` — intentionally have no row and resolve through the LD4 fallback; `docs/33` states this explicitly so the omission reads as a decision rather than a gap.
10. After a snapshot/restore round trip, `adapter._ids is substrate._ids` — the adapter remains bound to the substrate counter — and a subsequent write mints an identifier greater than every restored one.
11. Restoring a snapshot whose `id_counter` is absent or 0 alongside existing facts raises `ValueError` on the next write rather than overwriting a restored fact, asserted explicitly.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
python scripts/validate_markdown_links.py docs/33-pama-decision-table.md
```

## CI Coverage Exemptions

Evidence workflows path-filtered on `adapter/policy/substrate` (`validate-doctrine-evidence`, `cognitive-mesh-evidence`, `restart-safe-runtime`, `runtime-composition`) are triggered by this change and are expected to pass unchanged, since single-adapter behaviour is bit-identical by LD1. They are covered by DoD 7, which runs the full suite those workflows invoke.

## Rollback

`git checkout -- reference/agentmem_ref/substrate.py reference/agentmem_ref/adapter.py reference/agentmem_ref/policy.py docs/33-pama-decision-table.md` and delete the two new test files. Nothing is committed by this cycle.

## Next

`/qor-audit`. L3 grade: adversarial mode with independent verification of the identity claim is mandatory.
