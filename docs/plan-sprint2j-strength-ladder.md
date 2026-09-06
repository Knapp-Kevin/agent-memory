# Plan: Sprint 2j — the strength ladder

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-05T0310-7132cd
**Research**: `docs/research-brief-sprint2j-strength-ladder-2026-09-05.md`
**Iteration**: 4 (audit attempt 3: PASS with binding conditions C1, C2)
**Implements**: the operator ruling on [#379](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/379) — *"risk defines how strong"*

## Objective

Record the ruling as doctrine, and make the §4 criteria report state the bar it resolved. Nothing enforces the ladder this cycle.

## Boundaries

**In scope**: ADR-037 gains R5 and an amended §4; `resumption.criteria_for` replaces `bar: undefined` with the ladder; tests.

**Explicitly out of scope**: **enforcement.** Refusing a resumption because evidence falls short of the ladder is step 4's work, and `policy.py` stays unmodified. The report describes; step 4 decides.

## Design decisions

**LD1 — The count is one at every risk class, and that is not a threshold.**
The requirement is *existence* of a qualifying independent dependence group — R2's lineage grouping already defines what one group is. It does not vary by risk and is not a number to be tuned. Risk varies the strength that one group must reach.

No constant holds a count. No comparison is made against an integer. ADR-037:128 describes precisely how the other choice decays.

**LD2 — The ladder has three axes, and the ADR labels which row is new.**

| Risk | Authority kind | Qualification class | Binding status |
|---|---|---|---|
| low | `delegated_policy` or `human_confirmation` | directly-satisfying; estimator may contribute | `asserted` sufficient |
| medium | `delegated_policy` or `human_confirmation` | directly-satisfying; estimator may contribute | `asserted` sufficient |
| high | `human_confirmation` only | directly-satisfying only | **`verified`** |
| critical | `human_confirmation` only | directly-satisfying only | **`verified`** |

**Not all of this is in force today (audit V2).** Measured: `require_review` occupies **nine `_BASE_TABLE` cells at high or critical risk**, and the authority row comes from `attestation_refusal` and `_grant_refusal`, **both of which sit on the external-verification path**. `_apply_review` still discharges on `review_satisfied` plus `approval_refs` at any risk, with no authority-kind check at all.

So the report must distinguish what bites now from what step 4 will enforce:

| Row | `require_external_verification` | `require_review` |
|---|---|---|
| Authority kind | **in force** — `attestation_refusal` enforces it | **pending step 4** |
| Qualification class | pending step 4 | pending step 4 |
| Binding status | pending step 4 | pending step 4 |

Reporting the ladder as currently binding for a parked high-risk `require_review` would state a bar the system does not enforce — the same class of defect Loop 10's V4 corrected, where the report told an actor something the implementation did not honour. Loop 10 already built `CRITERION_GATE` for exactly this, so the distinction is cheap.

Rows one and two are **pre-existing implemented doctrine** — `policy.attestation_refusal` and `decision_overwrite._grant_refusal` for authority kind, R3 verbatim for the estimator. Row three is **the new ruling**. The ADR says which is which, because presenting all three as novel overstates the change and presenting the third as pre-existing smuggles a ruling in as a restatement.

**LD3 — The ladder is a function, not a table, so it derives at call time (audit V1).**
`_HIGH_RISK` already exists in `policy` and already means "the classes that demand human confirmation". Measured: a dict built at import reads it **once and holds a copy** — re-listing the constant with extra steps, which is what this decision exists to forbid. Under a monkeypatched `_HIGH_RISK` an import-time table does not move; a call-time function does.

So `strength_for(risk_class)` computes from `policy._HIGH_RISK` on every call. There is no `STRENGTH_LADDER` constant. Re-listing `("high", "critical")` locally would be the eighth instance of the pattern this program has spent eleven cycles on.

**LD4 — `criteria_for` derives the risk class from the record, and still returns criteria rather than a verdict (audit V3).**

The ladder appears as the `bar` on each unmet criterion — what *would* satisfy it. `criteria_for` gains no `satisfies()`, no boolean, no comparison of supplied evidence against the ladder. That comparison is step 4.

**It takes no risk-class parameter.** Iteration 2 said it "gains a risk class"; it needs one and already has it — `record.proposal.risk_class`. A parameter would let a caller pass `low` for a proposal recorded as `critical`, **understating every row at once**: permitting `delegated_policy` where human confirmation is required, admitting an estimator where it is excluded, and accepting `asserted` where `verified` is required. All three rows key off the same value, so one wrong argument weakens every axis simultaneously.

That is the caller-asserted-input defect in a governance control — the ninth instance, after `approves_own_authority`, `review_satisfied`, `ratification_evidence_present`, the duplicated version literals, and the `verifier_principal_id` near-miss Loop 10 caught on this very module. Deriving the risk *boundary* from `_HIGH_RISK` (LD3) while accepting the risk *class* from the caller would close the smaller hole and leave the larger one open.

**LD5 — Loop 10's no-numeric-threshold test survives unchanged.**
It was written to catch an invented count. The ruling licenses a ladder, not a count, so the test must still pass with no weakening. **If it needs relaxing, the implementation has drifted into counting** and the cycle has failed regardless of what else is green.

**LD6 — `UNDEFINED_BAR` is removed, not left dangling.**
It existed because doctrine was silent. Doctrine now speaks. Leaving the constant would let a later reader think the question is still open, and leaving `INDEPENDENCE_OPEN_QUESTION` in place would be actively false — it points at an issue the operator has ruled on.

## Affected files

| File | Change |
|---|---|
| `docs/adr/ADR-037-fail-closed-review-requires-a-remediation-path.md` | **modified** — R5 added, §4 amended, implementation order note |
| `reference/agentmem_ref/resumption.py` | **modified** — `strength_for` (a function, not a table — audit V1); `UNDEFINED_BAR` removed |
| `reference/tests/test_governed_resumption.py` | **modified** — undefined-bar tests become ladder tests; the no-numeric-threshold test is untouched |

`policy.py` unmodified. `evidence_qualification.py` unmodified.

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX014 | Governed resumption and §4 criteria reporting | MODIFIED — the independence bar is now the strength ladder |

## Definition of Done

1. `strength_for("low")` and `strength_for("medium")` permit `delegated_policy`, allow an estimator to contribute, and accept `asserted` binding status.
2. `strength_for("high")` and `strength_for("critical")` require `human_confirmation`, exclude the estimator, and require `verified`.
3. **No count appears anywhere.** Asserted by scanning the ladder and every criteria report for an integer or a comparison operator, extending Loop 10's test rather than replacing it (LD1, LD5).
4. **Loop 10's `test_no_numeric_threshold_appears_anywhere_in_the_report` passes unmodified**, verified by diff of that test body.
5. The high/critical rows are **derived from `policy._HIGH_RISK` at call time** — asserted by monkeypatching `_HIGH_RISK` to include `medium` and observing `strength_for("medium")` change with it. An import-time table fails this, measurably (LD3, audit V1).
5b. **No `STRENGTH_LADDER` constant exists** — asserted over the module's public names, so the table form cannot return quietly.
6. `criteria_for` reports the ladder as the `bar` for the independence criterion at each risk class, replacing `undefined`.
6b. **Each ladder row is marked in force or pending step 4, per outcome** (audit V2): for `require_external_verification` the authority row reports in force; for `require_review` every row reports pending, because `_apply_review` enforces none of them. Asserted at high risk on both paths, since that is where the two diverge.
7. `UNDEFINED_BAR` and `INDEPENDENCE_OPEN_QUESTION` no longer exist; nothing imports them (LD6).
8. **`criteria_for` gains no verdict surface** — no method compares supplied evidence to the ladder, asserted over the module's public names (LD4).
8b. **`criteria_for` accepts no risk-class parameter** (audit V3): asserted over its signature, and asserted behaviourally by showing the ladder reported for a `critical` record is the critical row with no way for a caller to obtain the `low` row for it.
9. ADR-037 R5 records the ruling, states the count is one at every risk class, and **labels which ladder rows are pre-existing and which is new**.
9b. **The ADR's implementation-order section records that step 4's last blocker is cleared** (audit C2), so "now permissible" and the resolved bar cannot be read as contradicting each other.
9c. **#379 is closed with the ruling quoted and ADR-037 R5 linked** (audit C1) — removing the in-code pointer while leaving the issue open would just invert the inconsistency.
10. All 1020 prior tests pass; `policy.py` unmodified by diff.
11. Validators clean; no schema modified.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## Rollback

Revert the three files. #379 reopens.

## Next

`/qor-implement`. Audit attempt 3 returned PASS with binding conditions C1 (close #379 with the ruling recorded and R5 linked) and C2 (the ADR's implementation-order section records that step 4's last blocker is cleared), folded into DoD 9b and 9c.

Attempts 1 and 2 vetoed on V1-V3: an import-time table could not satisfy DoD 5 (V1); the ladder is not in force for `require_review` and the report would have said it was (V2); and `criteria_for` would have taken a caller-asserted risk class, understating every ladder row at once — the ninth instance of the pattern this plan invokes by name one decision earlier (V3). All three are discharged.
