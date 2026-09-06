# Research Brief: Sprint 2j — the strength ladder (ADR-037 §4 independence bar)

**Date**: 2026-09-05
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 11.
**Implements**: the operator ruling on [#379](https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/379)

## 1. The ruling

> **"risk defines how strong"** — operator, 2026-09-05, selecting option 2 of #379.

Step 3 reported ADR-037 §4's independence bar as `undefined` because no such bar existed in accepted doctrine, and the ADR warns by name against inventing a count. The ruling resolves it, and it resolves it *away from counting*:

**The count is one at every risk class. Risk varies how strong that one must be.**

At least one qualifying independent dependence group is required — that is existence, not a count — and R2's lineage grouping already decides what "one group" means. What changes with risk is the **strength** that group's evidence must reach.

This is the reading the four-variables section implies: risk answers "how strong must all of the above be", not "how many".

## 2. Strength has three axes, and two are already implemented

The vocabulary built in Loops 9 and 10 gives strength three dimensions. Critically, **two of the three ladder rows are pre-existing implemented doctrine**, not new:

| Axis | Rule | Status |
|---|---|---|
| **Authority kind** | `human_confirmation` required at high/critical; `delegated_policy` valid only at low/medium | **already implemented** — `policy.attestation_refusal` (`_HIGH_RISK = ('high','critical')`) and `decision_overwrite._grant_refusal` (`delegation_not_permitted_for_risk`) |
| **Qualification class** | estimator "may contribute … **particularly at low or medium risk**", never sole basis, never authority | **already doctrine** — R3, verbatim at ADR-037:75 and :141 |
| **Binding status** | `verified` required at high/critical; `asserted` sufficient at low/medium | **NEW** — the one row derived from this ruling |

Only the third row is a new decision, and it must be labelled as such in the ADR. Presenting all three as equally novel would overstate the change; presenting the third as pre-existing would smuggle a ruling in as a restatement.

## 3. Why `verified` at high/critical is the right derivation

R3 says artifact-bound evidence "**with a deterministic verifier**" satisfies directly. Loop 9 then split what that phrase had conflated: `asserted` means a verifier is *named*, `verified` means one actually *ran and passed*, `refuted` means it ran and failed.

R3's phrase presumes the verifier works. At low and medium risk, accepting a named-but-unrun verifier is a reasonable cost trade — the claim is checkable, and someone can check it later. At high and critical, where `attestation_refusal` already refuses anything short of human confirmation, accepting evidence nobody has actually checked is inconsistent with the strictness the same risk classes already demand on the authority axis.

So the new row is not free-standing: it makes the **evidence** axis as strict as the **authority** axis already is, at the same risk classes, using the distinction Loop 9 built.

## 4. What must not happen

- **No count.** Not `>= 2`, not `>= 1` expressed as a threshold to be tuned later. The requirement is existence of a qualifying group, and it is the same at every risk class. ADR-037:128 is explicit about how this goes wrong.
- **No import of `reusable_grants`' `>= 2`.** R4 fences it off; it governs reusable authority from historical precedent, which is a different job.
- **No enforcement.** This cycle amends doctrine and makes the criteria *report* state the bar. Refusing on it is step 4.

## 5. Blast radius

`resumption.criteria_for` replaces `bar: undefined` with the ladder. ADR-037 gains R5 and §4 is amended. `policy.py` untouched; nothing enforces the ladder until step 4.

The test asserting "no numeric threshold appears anywhere in the report" (Loop 10) **must survive unchanged**. It was written to catch an invented count, and the ruling does not license one — it licenses a strength ladder. If that test needs weakening to accommodate this cycle, the implementation has drifted into counting.

## 6. Risk grade

**L3.** The report is advisory, but the ladder is what step 4 will enforce across 51 call sites, and it is doctrine the operator has just ruled on. A wrong ladder here is wrong everywhere, later.

## 7. Next

`/qor-plan`.
