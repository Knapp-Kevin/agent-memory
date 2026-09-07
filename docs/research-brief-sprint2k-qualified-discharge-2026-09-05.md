# Research Brief: Sprint 2k — a qualified-evidence discharge path for `require_review`

**Date**: 2026-09-05
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 12.
**Implements**: ADR-037 **step 4a** — see §2, which argues step 4 must split

## 1. The finding that reshapes the step

ADR-037 step 4 is written as one action: "convert the 51 caller sites" so `require_review` fails closed. Measured, **step 4 as written would flip the gate before the discharge path exists** — which is the one thing this ADR's sequencing principle forbids:

> Do not flip the gate before 1–3 exist. **A control whose remediation path does not yet work is a halt**, and the pressure it creates becomes a workaround that outlives it.

Every public entry point in `policy` was enumerated:

| Entry point | Discharges `require_review` on qualified evidence? |
|---|---|
| `evaluate(proposal)` | no — no evidence parameter exists |
| `evaluate_with_base_outcome(proposal, *, base_outcome, allow_review_discharge)` | no |
| `evaluate_with_external_verification(proposal, attestation, *, base_outcome)` | **no** — early-returns unless the outcome is `REQUIRE_EXTERNAL_VERIFICATION` (confirmed in source) |

None mentions `evidence_qualification` or `DependenceAnalysis`. **There is no path today by which a `require_review` proposal discharges on qualified evidence.** The only route is the asserted one step 4 exists to remove.

So flipping `_apply_review` now would leave all 51 sites with a refusal and no route — the precise halt the ADR names. The split is not a convenience:

- **4a (this cycle)** — build `evaluate_with_qualified_evidence`, the discharge path. **Purely additive**: `_apply_review` untouched, assertion still works, nothing breaks, no site converts. Both paths coexist.
- **4b (next cycle)** — flip `_apply_review` and convert the sites.

This is the same shape as every prior step in this ADR, and the same shape Loop 7 used for external verification: the dedicated entry point and the cap. It also matches the repository's existing idiom, which `evaluate_with_external_verification` documents in its own docstring — *"Mirrors `reusable_grants.evaluate_pama_with_reusable_grant`, which is already this repository's pattern for evidence-gated discharge through a dedicated entry point. Ordinary `evaluate` cannot reach this path."*

## 2. The blast radius is larger than "51 sites", and differently shaped

The ADR's 51 is accurate for its own metric — sites setting `review_satisfied=True`: **7 in `agentmem_ref/`, 6 in `run_*.py`, 38 in `tests/` = 51.**

But a hard flip was probed by patching `_apply_review` to refuse, and running the suite:

```
Ran 1026 tests — FAILED (failures=41, errors=14)
```

**55 tests across ~30 files.** More importantly they are not one kind of work:

| Kind | Example | Correct treatment |
|---|---|---|
| Tests asserting the gate's own behaviour | `test_derived_authority`, `test_verified_discharge`, `test_asserted_discharge_is_recorded` | declared amendments |
| Tests using assertion as **scaffolding** to reach unrelated behaviour | semantic readmission, interchange propagation, epistemic/predictive memory, deletion completeness, boundary crossing | **must be given real qualified evidence**, not amended |

The second group is the majority and the reason 4b is a separate cycle. Amending them would quietly weaken coverage of features that have nothing to do with review discharge — a test that stops reaching the behaviour it was written for is not a passing test, it is a deleted one wearing a passing test's name.

They can only be given real evidence once the path exists. Which is 4a.

## 3. What the discharge path must enforce

R5's ladder, and only R5's ladder — it was ruled on two cycles ago and is now doctrine.

| Risk | What discharges `require_review` |
|---|---|
| low / medium | one qualifying independent group: directly-satisfying class, `asserted` binding sufficient; `delegated_policy` authority acceptable |
| high / critical | one qualifying independent group at **`verified`** binding, **and** `human_confirmation` — evidence alone is not enough |

Note the consequence at high and critical, which is not obvious and should be stated in the plan rather than discovered: **the ladder's authority row means qualified evidence alone cannot discharge a high-risk `require_review`.** It requires an attestation carrying `human_confirmation` as well. That is R5 read faithfully — the authority axis does not relax because the evidence axis was satisfied — and it is why the discharge path needs an optional attestation parameter rather than evidence alone.

## 4. Existing controls that must be reached, not re-derived

- **Self-approval** — already derived from identity in `_apply_modifiers` (entry #15). The new path runs after it and inherits it.
- **`block` stays absorbing** — `_apply_review` already returns early for anything that is not `require_review` / `require_external_verification`.
- **Separation on the attestation** — `attestation_refusal`, called *inside* `evaluate_with_external_verification`. Loop 10's audit condition C1 applies with equal force here: do not pre-call it, and do not write a second copy.
- **The estimator bar** — `evidence_qualification` already separates `qualifying_group_count` from `contributing_group_count`. Reaching for the first and ignoring the second is the whole enforcement.

## 5. Blast radius of 4a itself

Near zero, deliberately. A new entry point that nothing calls. `_apply_review` unmodified; the 51 sites keep working unchanged; both paths coexist until 4b.

## 6. Risk grade

**L3.** Additive, but this is the function that will *grant*. Steps 1–3 described and transitioned; this one discharges. A ladder misread here becomes an authority bypass the moment 4b routes callers through it.

## 7. Next

`/qor-plan`.
