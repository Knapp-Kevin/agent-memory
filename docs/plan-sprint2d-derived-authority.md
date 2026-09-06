# Plan: Sprint 2d — derived authority in the review discharge

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-04T1652-5eb9f9
**Research**: `docs/research-brief-sprint2d-derived-authority-2026-09-04.md`
**Iteration**: 2 (amended for audit attempt 1 grounds V1-V3)
**Gap**: GAP-ARCH-04 — **self-approval leg only; the gap remains OPEN**

## Objective

Make `_apply_review` enforce the invariant its own docstring states — review is satisfied by an approver, never by the proposer — by deriving self-approval from identity instead of trusting an asserted boolean, and make every discharge record what it rested on.

## Boundaries

**In scope**: `reference/agentmem_ref/policy.py`, new tests.

**Non-goals**: requiring verified evidence for a discharge (Loop 6, under the operator's option-C decision); the `actor_authority_resolved` default; GAP-SEC-04.

**Declared reach beyond the edited file (audit V2).** `crossing.py:107` calls `policy.evaluate` directly, so LD1 reaches boundary crossings automatically. This is intended — closing the self-approval leg wherever proposals are evaluated is the point — and it is a **behaviour change**: the deep audit's R3 probe recorded "a `share` crossing committed on the same asserted approval", and that crossing now blocks. DoD 2b covers it.

What remains a non-goal for `crossing.py` and `scope_governance.py` is the *discharge-by-assertion* leg: they still inherit a `review_satisfied` discharge backed by nothing. Only the self-approval leg closes there.

## Design decisions

**LD1 — Derive `approves_own_authority` from identity, in `_apply_modifiers`.**
A proposal is self-approving when `proposal.actor_id` appears in `proposal.approval_refs`, regardless of the asserted boolean. The check goes in **`_apply_modifiers`** (`policy.py:186-187`), beside the flag it generalizes.

**Placement is load-bearing (audit V1).** `_apply_modifiers` runs on every evaluation and blocks unconditionally. `_apply_review` runs only when the outcome is already `require_review` or `require_external_verification` and `review_satisfied` is set. Deriving in `_apply_review` would leave a self-approving proposal at `allow_with_ledger` — `runtime_assembly/low`, `pruning/low`, `score_adjustment/low` — permitted when derived but blocked when asserted, making the derived path *weaker* than the flag it generalizes. The invariant is not conditional on a review requirement and neither is its enforcement.

This generalizes `decision_overwrite.py:171`, which already does exactly this (`grant.principal_id == proposal.proposing_actor`). The control is not new; it is applied in one module and absent from the shared evaluator every other module routes through.

The asserted boolean is **retained and honoured**: a caller that sets `approves_own_authority=True` still blocks. Derivation only adds a way to reach the check — it never weakens it. Formally: `effective = asserted or derived`.

Measured blast radius: **zero**. Instrumenting `_apply_review` across 912 tests found no proposal presenting its `actor_id` inside its own `approval_refs`.

**LD2 — Comparison is exact-match on the whole ref, not substring.**
`actor_id in approval_refs` as a set membership test over string-normalised refs. Not `any(actor_id in ref for ref in refs)`, which would make `actor_id="a"` self-approve against `approval_refs=("grant:human",)`. Refs are compared after `str()` and surrounding-whitespace strip, and nothing else — no case folding, no prefix matching. An identity scheme where `agent:x` and `AGENT:X` are the same principal is a real question and belongs to Sprint 4's boundary work, not to a silent normalisation choice here.

**LD3 — Record what the discharge rested on.**
`Decision` gains `review_discharge: str = ""`, set to `"asserted"` when a discharge is granted on `review_satisfied` alone.

**Plumbing (audit V3).** `_apply_review` returns `(outcome, reasons)` and `Decision` is built once in `evaluate_with_base_outcome` (`policy.py:262-267`); nothing carries a third value. `_apply_review`'s signature is **not** changed — its symmetry with `_apply_floors` and `_apply_modifiers` is deliberate. Instead the discharge is detected at the construction site from what `_apply_review` already returns: the outcome changed to `ALLOW_WITH_LEDGER` and the reason list is non-empty. That is a property of the returned values, not a re-derivation of the condition, so the logic stays in one place. When `allow_review_discharge=False` the helper is skipped and the field stays empty. Every discharge in the tree today is `asserted`; `"verified"` is reserved for Loop 6 and is not produced by this cycle.

This generalizes `enforcement_evidence._approval_status:61-80`, which already distinguishes `unverified` from verified for approval evidence. `policy` currently has no such notion, so a receipt reading `review discharged by ['i-said-so']` is indistinguishable from one backed by a validated grant.

Additive with a default, so nothing constructing or reading `Decision` changes.

**LD4 — Do not tighten `require_external_verification` in this cycle.**
Only four sites discharge it by assertion, which makes tightening look cheap. Two are `decision_overwrite` presenting a **validated grant** through the asserted channel; they would have to re-express real authority through a verified carrier that does not exist until Loop 6.

Tightening first would force legitimate callers to fake the channel, which is how a control acquires a workaround that outlives it. Loop 5 makes provenance visible; Loop 6 makes it required.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/policy.py` | derived self-approval in `_apply_review` (LD1, LD2); `Decision.review_discharge` (LD3) |
| `reference/tests/test_derived_authority.py` | **new** — derivation, precedence, non-weakening, exact-match, provenance |

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX009 | Review discharge derives self-approval from identity and records what it rested on | NEW |

## Definition of Done

1. `actor_id="agent:x"` with `approval_refs=("agent:x",)` and `review_satisfied=True` resolves **`block`** for `policy_mutation/critical`. It previously resolved `allow_with_ledger`.
2. The same holds when the actor is one of several refs — `approval_refs=("approver:1", "agent:x")`.
2b. **Reach**: a self-approving proposal at a base outcome of `allow_with_ledger` (`runtime_assembly/low`) also blocks — the V1 case that placement in `_apply_review` would have missed. Asserted explicitly, because an implementation placed in the wrong function passes DoD 1 and 2 and fails only this.
2c. **Crossing**: a `share` crossing evaluated through `crossing.py` with a self-approved proposal blocks. Previously it committed.
3. A genuine third-party discharge still works: `actor_id="agent:x"`, `approval_refs=("approver:1",)` → `allow_with_ledger`.
4. Non-weakening: `approves_own_authority=True` still blocks even when the actor is absent from the refs.
5. Exact-match: `actor_id="a"` with `approval_refs=("grant:human",)` **discharges** — substring matching would have blocked it. Asserted by name, because a substring implementation passes DoD 1 and 2 while silently blocking legitimate discharges.
6. `Decision.review_discharge == "asserted"` on every discharge this cycle can produce; `"verified"` appears nowhere in the codebase.
7. **All 912 prior tests pass.** F3 predicts zero breakage; a failure is a finding that F3's measurement was wrong, not a test to amend.
8. `validate_schemas.py` and `validate_fixtures.py fixtures` clean.
9. The seal records GAP-ARCH-04 as **partially addressed and still open**, naming the four legs left open.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## CI Coverage Exemptions

Every adapter- and policy-path evidence workflow is triggered by a change to `policy.py`. DoD 7 covers them: the full suite those workflows invoke must pass unchanged.

## Rollback

`git checkout -- reference/agentmem_ref/policy.py` and delete the new test file.

## Next

`/qor-audit`. L3: adversarial mode, independent verification that the derivation cannot weaken the existing check and that F3's zero-blast-radius measurement holds.
