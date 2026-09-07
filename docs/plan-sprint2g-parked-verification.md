# Plan: Sprint 2g — parked verification state

**change_class**: feature
**Risk Grade**: L2
**Session**: 2026-09-04T2347-39681d
**Research**: `docs/research-brief-sprint2g-parked-verification-2026-09-04.md`
**Iteration**: 4 (audit attempt 3: PASS with binding conditions C1, C2)
**Implements**: ADR-037 implementation order, **step 1 of 4**

## Objective

Make `enter_pending_verification` a real, recorded, evidence-emitting outcome, so a proposal that cannot discharge has somewhere to go instead of failing silently.

## Boundaries

**In scope**: a new `reference/agentmem_ref/pending_verification.py`, and its tests.

**Explicitly out of scope — the ordering is the decision, per ADR-037:**

| Step | Status here |
|---|---|
| 2. Evidence qualification and dependence lineage | **not built.** No dependence-group logic, no evidential-class ranking |
| 3. Governed resumption | **not built.** Nothing in this cycle discharges a parked proposal |
| 4. Fail-closed `require_review` | **not built.** `_apply_review` untouched; assertion still discharges after this cycle, by design |

The temptation is to add resumption while the lifecycle is in hand. A half-built resumption is worse than none, because it would let a proposal leave the parked state without the qualification machinery that decides whether it should.

## Design decisions

**LD1 — A new module, not the adapter.**
`PendingVerificationRegistry` lives in its own module, following the `DurableDecisionRegistry` precedent. Putting it on `GovernedMemoryAdapter` would widen a surface that #362 is going to re-shape, and would make every adapter consumer carry it before anything uses it.

**LD2 — Park refuses duplicates rather than overwriting.**
`park()` raises on a `proposal_id` already parked. Append-oriented, matching both `DurableDecisionRegistry.propose` and Loop 6's `RatificationRegistry`. A silent overwrite would let a second attempt erase the evidence of the first — the failure shape Loop 4's falsified tombstone had.

**LD3 — Parking emits a schema-valid audit event, using the schema's modeled fields (audit C1).**
`memory.pending_verification`, validated against `memory-audit-event.schema.json`. Legal because `event_type` is an open string.

The schema models `correlation_id`, `policy_version`, `state_snapshot`, `actor`, and `component` as **top-level properties**, so those go top-level. Only detail the schema does not model goes under `payload` (`proposal_id`, `outcome`, `reasons`, `permitted_actions`, `parked_at`) — the placement Loop 3 established for `memory.recall`.

Putting a modeled field in `payload` is schema-legal and wrong: it is invisible to any consumer joining on the modeled field, which defeats the reason DoD 1 records `correlation_id` at all.

**Retention (audit C2).** Parked records now hold full `Proposal` objects, which carry `tenant_ref`, `purpose`, `actor_id`, and `project_ref`. There is **no eviction path in this cycle**; retention and eviction belong to #363 (production state). This is a recorded deferral, not an oversight — the larger surface is the price of step 3 being able to re-evaluate at all.

**LD4 — The record retains the `Proposal` itself, not a summary of it (audit V1).**

Iteration 1 recorded identity fields only. That cannot support step 3. `policy.evaluate` takes a `Proposal`, and ADR-037 §5 requires resumption to re-evaluate policy from scratch — `target_class` and `downstream_authority` drive `_apply_floors`; `reversibility`, `evidence_refs`, and the isolation-domain fields drive `_apply_modifiers`. None is recoverable from an identity summary, so step 3 would have had to reshape this record, which is the cost this cycle exists to avoid.

The record therefore holds: the `Proposal`, the `Decision`, `correlation_id`, `parked_at`, and `policy_version`.

**This also anchors staleness (audit V3).** `state_snapshot` is a `Proposal` field, so retaining the proposal is what lets resumption apply the entry-#14 staleness guard and detect that the world moved while the proposal sat parked. That is the specific risk parking introduces, since parking is by definition a delay. Recorded here as a reason rather than acquired by luck.

It also records `permitted_actions` **copied from the decision, never restated** (audit V4). The route differs by outcome, and hardcoding one would reintroduce the caller-asserted-input defect this program has found four times.

**LD5 — No schema for the record itself.**
The parked record is an internal dataclass. Adding a schema is a public contract addition belonging to Sprint 4's boundary freeze (#362). The *evidence* is schema-valid; the *type* is not frozen. This mirrors Loop 3 adding defaulted fields to `AdmissionResult` rather than schema-backing it.

**LD6 — A parked proposal carries no authority, and the type must make that hard to misread.**
ADR-037 §5. The registry exposes no method that returns a permission, discharges a decision, or mutates the parked decision. `resume` does not exist in this cycle — not as a stub, not as `NotImplementedError`. A stub is an invitation; its absence is a statement.

**LD7 — Park only outcomes that have a remediation route: refuse both `allow` and `block` (audit V2).**

`park()` raises for `allow`, `allow_with_ledger`, **and `block`**.

Refusing `allow` is straightforward: parking a permitted proposal manufactures a governance record for an event that did not occur — the defect class of Loop 4's D5, where deleting a nonexistent fact still wrote a tombstone.

Refusing `block` is the correction. `_envelope` (`policy.py:290`) returns empty permitted actions for `block` **and explicitly prohibits `enter_pending_verification`**. The policy states a blocked proposal may not enter pending verification, so parking one contradicts the very envelope the record would be preserving. It would also create a record that can never leave the parked state — no evidence discharges an absorbing `block` — producing permanent residue charged against retention (#363) for a proposal policy said may not park.

**The envelope has three states, not two (audit V4).** Measured across all five outcomes:

| Outcome | `permitted_actions` | `enter_pending_verification` | Parks? |
|---|---|---|---|
| `allow` / `allow_with_ledger` | `(operation, 'collect_more_evidence', 'defer')` | unlisted | **no** — nothing was refused |
| `require_review` | `('enter_pending_verification', 'collect_more_evidence', 'defer')` | **permitted** | **yes** — the envelope authorizes parking by name |
| `require_external_verification` | `('request_external_verification', 'collect_more_evidence', 'defer')` | unlisted | **yes** — refused with a route, but the route is `request_external_verification` |
| `block` | `()` | **prohibited** | **no** — the envelope forbids it by name |

Parking is for refusals **with** a route, and the record carries whichever route the decision actually granted. `block` is the only outcome whose envelope names `enter_pending_verification` as prohibited, which is what makes refusing it a contradiction rather than a preference.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/pending_verification.py` | **new** — `ParkedProposal`, `PendingVerificationRegistry` |
| `reference/tests/test_pending_verification.py` | **new** |

No existing file is modified. Nothing calls this yet, by design.

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX012 | A refused proposal can be parked with its decision, unmet criteria, and remediation routes, emitting schema-valid evidence | NEW |

## Definition of Done

1. Parking a `require_review` decision records the **`Proposal` itself**, the decision, `correlation_id`, `parked_at`, and `policy_version`, and returns the parked record.
1b. **The retained proposal is sufficient to re-evaluate**: `policy.evaluate(record.proposal)` reproduces the recorded decision exactly. Asserted directly, because this is what step 3 depends on and an identity-summary record would fail it (audit V1).
1c. The retained proposal carries `state_snapshot`, so resumption can apply the staleness guard (audit V3).
2. **The record's `permitted_actions` equals the decision's, per outcome** — asserted by equality against `decision.permitted_actions`, never against a literal (audit V4):
   - `require_review` → `('enter_pending_verification', 'collect_more_evidence', 'defer')`
   - `require_external_verification` → `('request_external_verification', 'collect_more_evidence', 'defer')`
   Asserting a fixed tuple for both is the failure this DoD exists to prevent.
3. Parking emits exactly one event per park; it validates against `memory-audit-event.schema.json`; `event_type` is `memory.pending_verification`. **`correlation_id`, `policy_version`, and `state_snapshot` are top-level; unmodeled detail is under `payload`** (audit C1). Asserted by reading the top-level keys, so a regression into `payload` fails.
4. Parking the same `proposal_id` twice raises, and the first record is unchanged.
5. Parking an `allow_with_ledger` or `allow` decision raises — a permitted proposal cannot be parked (LD7).
6. `require_external_verification` parks as well as `require_review`; both are refusals with routes, and the parked record shows the *different* route each was granted (DoD 2).
7. **Parking a `block` decision raises.** `_envelope` prohibits `enter_pending_verification` for `block`, so parking one would contradict the recorded envelope and create a record that can never resume (audit V2). Asserted with the prohibition quoted, so the reason survives the test.
8. **The registry exposes no method that discharges, resumes, or returns a permission.** Asserted over the public surface, so step 3 cannot arrive by accident (LD6).
9. `resume` is absent from the public surface — not present-and-raising (LD6).
10. **All 951 prior tests pass**, and `_apply_review` is unmodified — verified by diff, since step 4 is explicitly not in this cycle.
11. `validate_schemas.py` and `validate_fixtures.py fixtures` clean; no schema file modified.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## CI Coverage Exemptions

No workflow path filter covers a new unreferenced module, so no evidence lane is triggered by it specifically. DoD 10 runs the full suite, which is the coverage that matters for a module nothing calls yet.

## Rollback

Delete both new files. Nothing else changes.

## Next

`/qor-implement`. Audit attempt 3 returned PASS with binding conditions C1 (modeled event fields top-level) and C2 (retention deferral recorded), both folded into LD3 above and DoD 3. Attempts 1 and 2 vetoed on V1-V4; all four are discharged in this iteration.
