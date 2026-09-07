# Research Brief: Sprint 2e — the ratification trust anchor

**Date**: 2026-09-04
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 6.
**Gap**: GAP-SEC-04, implementing the operator's decision of 2026-09-04.
**Operator decision being implemented**: option **C as the code path** (bind evaluation to independently-held ratification evidence), **option D retained as a declarable deployment profile**. Binding requirement: *at least one term in the verification must come from a store the presenter cannot write.*

## 1. The same defect, a third time

`reusable_grants.evaluate_reusable_grant:309,339`:

```python
ratification_evidence_present: bool,
...
if status == "current" and ratification_evidence_present is not True:
    status = "invalid"
    reasons.append("ratification_evidence_missing")
```

The check for ratification evidence is a **caller-asserted boolean**. The caller declares whether the evidence exists.

This is now the third instance of one pattern, and it is worth naming as the unifying diagnosis of GAP-ARCH-04 and GAP-SEC-04:

| Control | Location | Input |
|---|---|---|
| self-approval | `_apply_modifiers` | `approves_own_authority` — caller-asserted (fixed Loop 5) |
| review discharge | `_apply_review` | `review_satisfied` — caller-asserted (open) |
| ratification evidence | `evaluate_reusable_grant` | `ratification_evidence_present` — caller-asserted |

**The controls are present and correct. Their inputs are supplied by the party they constrain.** That is the whole of both gaps, stated once.

## 2. The store pattern already exists

`decision_overwrite.DurableDecisionRegistry:99-118` is an append-oriented registry whose docstring says exactly what is needed here:

> Decision objects are never mutated after registration. Current/superseded status is derived from the append-only supersession journal. This registry demonstrates the authority boundary, not a production decision database.

That is the shape of "a store the presenter cannot write". Loop 6 generalizes it to ratification evidence, as Loops 2, 3, and 5 each generalized an existing in-repo pattern rather than inventing one.

## 3. Why a digest check alone still fails, restated with the fix in view

Loop 4's probe: tamper `expires_at` to 2030, recompute `grant_id` from the tampered body, and evaluation returns `current` against a perfectly self-consistent artifact. A digest is a function of the thing being checked, so it can never satisfy the operator's binding requirement.

A registry does, but **only if the comparison uses the held record's values**. Resolving `grant_id` in a store and stopping there would still pass the recompute attack, because the tampered grant carries a *different* id and simply would not resolve — which looks like a fix until an attacker registers a benign grant and then presents a tampered one under a recomputed id. The verification must compare the presented grant's authority-bearing fields against the **held** record's, field by field.

That distinction is the difference between a control that works and one that appears to.

## 4. The external-verification refusal is already correct where grants are concerned

`evaluate_pama_with_reusable_grant:388-410`:

```python
if baseline.outcome != policy.REQUIRE_REVIEW:
    return baseline
```

with the docstring "External verification and blocks remain absorbing for this profile."

So a reusable grant **cannot** discharge `require_external_verification` — the bridge already refuses. Loop 5's finding that four sites discharge external verification by assertion therefore does **not** implicate the grant path at all. Two of those four are `decision_overwrite`, which builds its `Proposal` directly (`decision_overwrite.py:171-173`) and **bypasses this bridge**.

That relocates GAP-ARCH-04's external-verification leg precisely: it is not a missing control, it is one module constructing a proposal around an existing one. Loop 7, not Loop 6.

## 5. Schema constraint on provenance

`reusable-grant-evaluation.schema.json` sets `additionalProperties: False`, and `evaluate_pama_with_reusable_grant` validates against it. An `evidence_source` field cannot be added without changing a public schema, which belongs to Sprint 4's boundary freeze (GAP-ARCH-01).

`reasons` is an existing `list[str]` already carrying machine-readable tokens (`policy_version_drift`, `grant_expired`, `scope_mismatch`, `ratification_evidence_missing`). Provenance fits that vocabulary without a contract change.

**Verified safe**: no test or harness asserts `reasons == []` on a successful evaluation. The only `reasons` assertion in the tree is a membership check (`reusable_grant_harness.py:214`). So adding a token on the success path breaks nothing.

## 6. Blast radius

`evaluate_reusable_grant` has exactly two callers: `reusable_grant_harness.py:174` and `test_reusable_grants.py:146`. `ratification_evidence_present` appears at four sites total. Adding an optional `registry` parameter changes no existing call.

## 7. Risk grade

**L3.** The trust anchor for reusable authority, implementing a decision the operator took specifically because the obvious fix was insufficient.

## 8. Next

`/qor-plan`.
