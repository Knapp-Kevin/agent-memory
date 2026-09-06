# Plan: Sprint 2k — a qualified-evidence discharge path for `require_review`

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-05T0420-481bd9
**Research**: `docs/research-brief-sprint2k-qualified-discharge-2026-09-05.md`
**Iteration**: 4 (audit attempt 3: PASS with binding conditions C1, C2)
**Implements**: ADR-037 **step 4a** — the discharge path, not the flip

## Objective

Give `require_review` a way to discharge on qualified evidence, enforcing R5's ladder. Nothing flips; nothing converts.

## Why this is a separate cycle from the flip

Research established that **no entry point in `policy` discharges `require_review` on qualified evidence today.** `evaluate` and `evaluate_with_base_outcome` take no evidence; `evaluate_with_external_verification` early-returns unless the outcome is `REQUIRE_EXTERNAL_VERIFICATION`.

So flipping `_apply_review` now would leave 51 sites refused with no route — the halt ADR-037's own sequencing principle forbids:

> A control whose remediation path does not yet work is a halt, and the pressure it creates becomes a workaround that outlives it.

The principle applies recursively. Steps 1–3 built the path for *parking*; 4a builds the path for *discharging*; 4b flips.

## Boundaries

**In scope**: `policy.evaluate_with_qualified_evidence`, and its tests.

**Explicitly out of scope — 4b:**

| Not built | Consequence |
|---|---|
| The flip | `_apply_review` unmodified; asserted discharge still works |
| Site conversion | all 51 sites keep working unchanged |

Both paths coexist after this cycle, deliberately. That is what makes 4b a migration rather than a break.

## Design decisions

**LD1 — A dedicated entry point, mirroring the two precedents, with assertion excluded from its base (audit V1).**
`evaluate_with_qualified_evidence(proposal, analysis, *, attestation=None, base_outcome=None)`. Ordinary `evaluate` cannot reach it -- the idiom `evaluate_with_external_verification` documents and `reusable_grants.evaluate_pama_with_reusable_grant` established.

**The base decision is computed with `allow_review_discharge=False`.** Iteration 1 mirrored Loop 7's base computation, which defaults that flag to `True`. Measured, on a `require_review` proposal carrying `review_satisfied=True` and one approval ref:

    allow_review_discharge default (True):  allow_with_ledger  ("review discharged by ['approver-1']",)
    allow_review_discharge=False:           require_review     ()

So an asserting caller would have arrived **already discharged**, passed LD2's early return, and been returned unchanged with **zero evidence examined**. The ladder would never be consulted.

That is not merely a hole -- assertion works today regardless. It is that **4b's migration would become a no-op wearing the appearance of enforcement**: a site routed through this function while still setting `review_satisfied=True` would discharge exactly as before, behind a function name asserting qualified evidence was required. A control that reports success without checking is worse than no control.

Excluding assertion from the base makes the ladder **the only route through this function**, which is what the entry point's name has to mean.

**LD2 — Early-return on any outcome that is not `require_review`.**
Loop 7's invariant, which Loop 10 then depended on and pinned. This function must be equally narrow: it discharges `require_review` and nothing else. `require_external_verification` keeps its own path; `block` stays absorbing; `allow` is untouched. Without the early return, one function becomes a general-purpose discharge for every outcome.

**LD3 — One definition of the ladder, in the lower-level module.**
R5's ladder already exists as a function, derived from `policy._HIGH_RISK` at call time. Re-expressing it inside `policy` would be a second copy of doctrine that can diverge — the pattern this program has found nine times, most recently one cycle ago in this very ADR's own plan.

*Note the import direction*: `resumption` imports `policy` today. Reading `strength_for` from `policy` would be circular, so the ladder's **content** is derived in `policy` from `_HIGH_RISK` and `resumption.strength_for` is refactored to call it. One definition, in the lower-level module, with the reporting layer reading from it — not two.

**LD4 — At high and critical risk, qualified evidence alone does not discharge.**
R5's authority row says `human_confirmation` only at those classes. The authority axis does not relax because the evidence axis was satisfied. So at high/critical the function requires **both** `verified` qualifying evidence **and** an attestation carrying `human_confirmation`.

This is R5 read faithfully rather than conveniently, and it is the decision most likely to be argued with later, so it is stated here rather than discovered.

**LD9 — At low and medium risk, the evidence-based discharge *is* the delegated policy (audit V3).**

R5's authority row is not vacuous below high risk, and iteration 2 left it unenforced and unexplained -- which admitted two incompatible readings: that authority is simply unchecked below high risk, or that an attestation is required there too. They differ on whether an autonomous caller can discharge anything without a separated principal, so leaving the choice to the implementation is not acceptable on the function that grants.

Neither reading is adopted. **`DELEGATED_POLICY` is this repository's name for non-human authority valid at low and medium risk** (`decision_overwrite._grant_refusal`, `delegation_not_permitted_for_risk` above medium). A policy engine discharging on qualified, independently grouped, class-checked evidence is precisely that authority being exercised. So the low/medium row is satisfied **by construction**, and the decision **records `delegated_policy` as the authority kind it exercised**.

**Where it is recorded (audit C1):** a new **defaulted** field `discharge_authority: str = ""` on `Decision`, on the precedent Loop 7 set with `review_discharge` and Loop 3 set with `AdmissionResult`. Additive, no schema change, existing constructions unaffected.

It does **not** overload `review_discharge`, which records how *strong* a discharge was (`asserted` / `verified`) rather than *whose authority* produced it. Collapsing them would merge two of the four variables ADR-037's model exists to keep apart, inside the module that defines them.

Recording it is what makes the row non-vacuous. It also matters for 4b: a converted site must be able to answer "under what authority did this discharge?", and an empty string is not an answer.

This names the authority; it does **not** generalize the `DELEGATED_POLICY` constant into `policy`. That remains the seventh-instance item recorded in Loop 10's research, and generalizing an authority kind is a doctrine change rather than a step-4a implementation detail.

**LD5 — Separation is reached, never re-derived.**
Where an attestation is supplied, its cross-checks come from `attestation_refusal`. Loop 10's condition C1 applies with equal force: it is already called inside `evaluate_with_external_verification`, and a second copy of a control correctly placed in the shared evaluator is two things that can diverge. Self-approval is already derived in `_apply_modifiers` and inherited by running after it.

**LD6 — The estimator bar is enforced by which count is consulted.**
`DependenceAnalysis.qualifying_group_count` covers only directly-satisfying classes; `contributing_group_count` covers estimators. Reading the first and never the second *is* R3's "never a sole basis". No separate estimator check is written, because writing one would imply the counts do not already mean what they mean.

**LD7 — One qualifying group. Not a threshold.**
R5: the count is one at every risk class. The comparison is `>= 1` in the sense of existence, expressed as a truthiness check on the count rather than a constant to be tuned. No named constant holds a number, and Loop 10's no-numeric-threshold test remains the standing guard.

**LD8 — A refusal names the axis that failed.**
`insufficient_evidence_class`, `insufficient_binding_status`, `human_confirmation_required` — distinct reasons, so a caller (and 4b's migration) can tell *which* ladder row it missed. A single `review_not_discharged` would make 4b's conversion guesswork.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/policy.py` | **modified** — `evaluate_with_qualified_evidence`, `strength_ladder_for`; `_apply_review` **untouched** |
| `reference/agentmem_ref/resumption.py` | **modified** — `strength_for` delegates to `policy.strength_ladder_for` (LD3) |
| `reference/tests/test_qualified_discharge.py` | **new** |

`evidence_qualification.py` unmodified.

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX015 | `require_review` can be discharged by qualified independent evidence meeting R5's ladder, through a dedicated entry point | NEW |

## Definition of Done

1. At low and medium risk, one qualifying independent group at `asserted` discharges `require_review` to `allow_with_ledger`.
1b. **That discharge records `delegated_policy` as the authority it exercised** (LD9, audit V3), so an auditor can later see which authority discharged the decision and 4b's converted sites can answer the question. Asserted at both low and medium.
1c. A high or critical discharge records `human_confirmation`, from the attestation.
1d. **The two paths are distinguishable after the fact** (audit C2): a low-risk evidence discharge and a high-risk attested discharge produce `Decision` objects differing in `discharge_authority`, asserted directly. Cheap now and unrecoverable later -- once 4b converts 51 sites, a decision with no authority recorded is indistinguishable from one that never went through the ladder.
1e. `review_discharge` keeps its existing meaning and is not overloaded (audit C1).
2. At high and critical risk, the same evidence **does not** discharge — `human_confirmation_required` (LD4).
3. At high and critical, `verified` qualifying evidence **plus** a bound `human_confirmation` attestation discharges.
4. At high and critical, a `human_confirmation` attestation with only `asserted` evidence refuses with `insufficient_binding_status` — both axes are required, asserted independently.
5. Estimator-only evidence never discharges, at any risk class (LD6). Asserted at low risk, where it is otherwise most permissive.
6. Zero qualifying groups never discharges, however many unqualified groups exist — ten distinct bare strings do not discharge at low risk (R5, §2b).
7. **Any outcome that is not `require_review` under the no-assertion base passes through unchanged** (LD2, audit V2): `allow`, `allow_with_ledger`, `require_external_verification` and `block` are byte-identical to `evaluate_with_base_outcome(proposal, base_outcome=_base_outcome(proposal), allow_review_discharge=False)`. Stated against the no-assertion base deliberately -- comparing to plain `evaluate` would fail for an asserting `require_review` proposal, and the tempting way to make that comparison pass is to revert V1.
7b. **An asserting caller gets no free pass** (audit V1): a `require_review` proposal with `review_satisfied=True`, valid `approval_refs` and **no evidence** does not discharge through this function. Asserted directly, because this is the single defect the cycle exists to prevent.
8. **`block` is not dischargeable** by any combination of evidence and attestation.
9. Self-approval still refuses — an actor in its own `approval_refs` cannot discharge with perfect evidence (entry #15, inherited not re-derived).
10. Attestation cross-checks arrive from `attestation_refusal` via the shared evaluator, not a local copy (LD5): a mismatched binding refuses with `attestation_not_bound_to_proposal`.
11. **`_apply_review` is unmodified**, verified by diff, and all 51 asserted-discharge sites still work — asserted by a test exercising the asserted path unchanged.
12. **`resumption.strength_for` returns exactly what it did before** the LD3 refactor, asserted across all four risk classes, and still tracks a monkeypatched `_HIGH_RISK`.
13. No named constant holds a count; Loop 10's `test_no_numeric_threshold_appears_anywhere_in_the_report` passes unmodified (LD7).
14. All 1026 prior tests pass.
15. Validators clean; no schema modified.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## Rollback

Revert `policy.py` and `resumption.py`; delete the new test file. Nothing else changes, because nothing else calls it.

## Next

`/qor-implement`. Audit attempt 3 returned PASS with binding conditions C1 (record the authority on a new defaulted `Decision.discharge_authority`, never by overloading `review_discharge`) and C2 (assert the two discharge paths are distinguishable after the fact), folded into LD9 and DoD 1d/1e.

Attempts 1 and 2 vetoed on V1-V3: the path was satisfiable by assertion, which would have made 4b's migration a no-op wearing the appearance of enforcement (V1); DoD 7 contradicted that fix and would have tempted its reversion (V2); and R5's low/medium authority row was left unenforced and unexplained, admitting two incompatible readings that differ on whether an autonomous caller can discharge without a separated principal (V3). All three are discharged.
