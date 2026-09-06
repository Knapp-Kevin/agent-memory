# Research Brief: Sprint 2h — evidence qualification and dependence lineage

**Date**: 2026-09-05
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 9.
**Implements**: ADR-037 implementation order **step 2 of 4**, and only step 2.

## 1. Scope, stated first because the order is part of the decision

Step 1 landed in entry #18: a refusal now parks with its decision and its route. It cannot yet be resumed, because resumption requires knowing whether arriving evidence *qualifies* — which is this step.

**This cycle builds step 2 only**: R2 and R3 made computable.

| Step | Status here |
|---|---|
| 1. Parked proposal state | **done**, entry #18 |
| 2. Evidence qualification and dependence lineage | **this cycle** |
| 3. Governed resumption | **not built.** Nothing here discharges or resumes a parked proposal |
| 4. Fail-closed `require_review` | **not built.** `_apply_review` untouched; `policy.py` unmodified |

The temptation this time is different from last cycle's. It is not to build resumption — it is to *wire the qualifier into `policy.evaluate`* while the vocabulary is in hand, because M-EVID is visibly weak (F1) and the fix looks like a two-line change. That two-line change **is step 4**. It converts every one of the 51 sites at once, with no resumption path built. The gate does not flip before step 3 exists.

## 2. The gap, measured

`policy._apply_modifiers:252` is the shared evaluator's **entire** treatment of evidence:

```python
if not proposal.evidence_refs:
    outcome = _strictest(outcome, REQUIRE_REVIEW)
    reasons.append("M-EVID: no evidence references supplied")
```

Measured on `semantic/write/low/reversible`:

| `evidence_refs` | Outcome | Reasons |
|---|---|---|
| `()` | `require_review` | `M-EVID: no evidence references supplied` |
| `("i-said-so",)` | `require_review` | `()` |
| `(" ",)` | `require_review` | `()` |
| `("same",) * 10` | `require_review` | `()` |
| `("receipt://sha256:deadbeef",)` | `require_review` | `()` |

A single space clears the evidence modifier exactly as a content-addressed receipt does, and ten copies of one reference are "evidence supplied". **Evidence is currently a truthiness check on a tuple.** R3's ranking exists as doctrine and has no computable form anywhere in the evaluator.

This is the **sixth** control this program has found implemented in one module and absent from the shared evaluator, after derived self-approval, verified/unverified provenance, the ratification registry, version derivation, and the `DurableDecisionRegistry` lifecycle.

## 3. The estimator leg is half-enforced

`estimator_refs`, `estimator_versions`, and `confidence` are recorded on `Proposal` and **never read** by the evaluator. Measured: confidence `0.99` and `0.01` produce identical decisions, identical reasons, identical envelopes.

That is correct for the half of R3 that says an estimator must never *become* authority — `policy.py:8` and the `authority_laundering_harness` checks `confidence_does_not_change_outcome` / `confidence_has_no_authority` hold it.

It leaves the other half unenforced. R3 also says a calibrated estimator "must **never** be the sole basis for discharging `require_review`". Since evidence is an opaque string tuple, **an estimate placed in `evidence_refs` is indistinguishable from an artifact-bound receipt** — measured, the two proposals compare equal. The prohibition is unenforceable while evidence has no class.

## 4. Dependence grouping exists, and is caller-asserted

`autonomous_maintenance_harness._group_probabilities:33-56` collapses a dependence group before cross-group fusion, asserting `row_count_is_not_corroboration`. It is the right idea and the only implementation.

It groups by `signal["dependence_group"]` — **a caller-supplied string**. The harness's own docstring is candid that the reducer is a fixture convenience. Nothing verifies that two signals in *different* groups are actually independent.

**Building step 2 on an asserted group label would reproduce the exact defect this program has now found six times**: a control whose input is asserted by the party it constrains. It is the same shape as `approves_own_authority`, `review_satisfied`, and `ratification_evidence_present`.

**The lineage needed to derive grouping is already in the fixtures.** `autonomous-maintenance-scenarios.json` carries `root_ref` and `derived_from` alongside the label, and two distinct grouping mechanisms appear in the data:

- **Derivation lineage** — `derived:summary-a` with `derived_from: ["root:a"]` shares a group with `root:a`. Computable from the refs.
- **Shared failure domain** — `root:news-a` and `root:news-b` are distinct roots that share `syndicated-report`. *Not* computable from derivation; it must be declared.

So grouping must be **derived from lineage, with declared failure domains as an additional merge input** — and where a caller's grouping disagrees with what lineage shows, lineage must win. A declaration may only ever *merge* groups (assert more dependence), never *split* them (assert more independence). That asymmetry is what makes the input safe to accept: the party being constrained can only make its own claim weaker.

## 5. Name collision, found before it was spent

`derivation_currentness.py:26` already defines:

```python
EVIDENCE_CLASSES = {"ordinary", "negative", "adversarial", "correction", "incident"}
```

That is **polarity and role** — what the evidence says. R3's ranking is **checkability** — how strongly it can be verified. Two orthogonal axes, and `evidence_class` is already taken for the first, in a schema (`derivation-currentness-evaluation.schema.json:45`) and a second consumer (`precedent-candidate-retrieval.schema.json:58`).

Step 2 must not reuse the name. `qualification` / `qualification_class` keeps the axes distinct and leaves the existing vocabulary alone.

## 6. What must not be generalized

`reusable_grants` establishes independence by `source_ref` identity plus a caller-asserted `independent_adjudication` boolean, and requires `minimum_independent_human_evidence >= 2`.

R4 rules that this has a **different job** — creating reusable authority from historical precedent, followed by a separate ratification transition — and "must not be generalized into a two-approver requirement for ordinary review". `_eligible_human_precedents` does dedupe correctly by `source_ref` (`by_source.setdefault`), so there is no defect to fix. **Do not touch it, and do not import its threshold.**

Noted for the record: its independence test is by source identity, which R2 says is not sufficient on its own. That is a live tension inside a module R4 has fenced off, so it is recorded here rather than acted on.

## 7. Blast radius

Near zero, deliberately, and for the same reason as step 1: a new module that nothing calls. `policy.py` is not modified — verified by empty diff at the end of the cycle, as in Loop 8. The 51 assertion sites keep working unchanged.

## 8. Risk grade

**L2.** New isolated module, no existing caller, no schema change, no policy path modified. Not L1 because the qualification vocabulary and the grouping algorithm are what steps 3 and 4 build on, and a wrong shape here is expensive later — the same reasoning that graded step 1, and step 1's audit proved it right twice.

## 9. Next

`/qor-plan`.
