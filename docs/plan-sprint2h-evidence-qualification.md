# Plan: Sprint 2h — evidence qualification and dependence lineage

**change_class**: feature
**Risk Grade**: L2
**Session**: 2026-09-05T0045-37f432
**Research**: `docs/research-brief-sprint2h-evidence-qualification-2026-09-05.md`
**Iteration**: 4 (audit attempt 3: PASS with binding conditions C1, C2)
**Implements**: ADR-037 implementation order, **step 2 of 4**

## Objective

Make R2 and R3 computable: give an evidence item a checkability class, and collapse correlated items into dependence groups derived from lineage rather than from a label. Nothing consumes either result this cycle.

## Boundaries

**In scope**: a new `reference/agentmem_ref/evidence_qualification.py`, and its tests.

**Explicitly out of scope:**

| Step | Status here |
|---|---|
| 3. Governed resumption | **not built.** Nothing here discharges or resumes a parked proposal |
| 4. Fail-closed `require_review` | **not built.** `policy.py` unmodified, verified by empty diff |

The temptation this cycle is not resumption — it is wiring the qualifier into `policy.evaluate` to fix the M-EVID truthiness check, which looks like two lines. **Those two lines are step 4.** They convert all 51 sites at once with no resumption path built. `PendingVerificationRegistry` is likewise not imported: connecting qualification to parking is step 3's work.

## Design decisions

**LD1 — `qualification_class`, never `evidence_class`.**
`derivation_currentness.py:26` already owns `EVIDENCE_CLASSES` for polarity and role — ordinary, negative, adversarial, correction, incident — with two schema consumers. R3 ranks *checkability*, an orthogonal axis. Reusing the name would silently merge two axes that ADR-037's "four variables, kept distinct" section exists to keep apart.

**LD2 — A class is derived from which bindings are present, never accepted from the caller.**
This is the whole point of the cycle. The three R3 classes are distinguished by what an item binds:

| Class | Required bindings | Standing |
|---|---|---|
| `artifact_bound` | `artifact_ref` + `digest` + `verifier` | satisfies directly |
| `reproducible_procedure` | `inputs` + `method` + `method_version` + `result` + `verifier` | satisfies directly |
| `calibrated_estimator` | `estimator_id` + `estimator_version` + `calibration_ref` | contributes only |

An item is classified by what it actually carries. A caller cannot declare itself `artifact_bound`; it can only supply a digest and a verifier.

**That is not verification, and this plan will not claim it is (audit V1).** All three bindings are caller-supplied strings; `digest="deadbeef"` with `verifier="trust-me"` classifies `artifact_bound` with nothing checked. Presence of a binding raises the cost and names a verifier so the claim becomes checkable *by someone later* — it does not make the claim true.

So classification carries a **binding status** alongside the class, following the two precedents the repository already set for exactly this shape:

- Loop 6, `reusable_grants.py:434,441` — `ratification_evidence_verified` vs `ratification_evidence_asserted`
- Loop 7, `policy.py:320` — `review_discharge` records `asserted` or `verified`

| Status | Meaning |
|---|---|
| `asserted` | the bindings are present; **no verifier has been run** |
| `verified` | a verifier was executed against this item and **passed** |
| `refuted` | a verifier was executed and **failed** (audit V4) |

`refuted` is not optional bookkeeping. Without it the obvious implementation is `"verified" if passed else "asserted"`, which makes "nobody has checked this digest" and "somebody checked this digest and it did not match" the same state. The second is a **refutation** — the most valuable thing the system will ever learn about that item — and collapsing it lets a proposer whose artifact failed keep re-presenting it as merely unchecked. `refuted` must never collapse into `asserted`.

**The verifier registry is held by the evaluator, not the proposer**, on the `RatificationRegistry` precedent from Loop 6. A proposal *names* a verifier; it does not supply one. With no registry, everything is `asserted` — which is the honest reading of a system where nothing has been checked yet.

The class says what kind of claim this is. The status says whether anyone checked, and what happened when they did. **The honest claim for this cycle is that evidence stops being an opaque string and becomes a typed, ranked claim that names its own verifier** — real progress toward step 4, and not a closure of the caller-asserted pattern, which remains open until a verifier actually runs.

**LD3 — An item that binds nothing qualifying is `unqualified`, and that is a fourth state, not an error.**
The evidence in the wild today is bare strings (F1). Classification must have somewhere to put them that is neither a crash nor a free pass. `unqualified` names them so step 4 can later see how much of the corpus is opinion.

**LD4 — Dependence grouping is derived from lineage; a declared failure domain may only merge.**
Union-find over **three** relations (audit V2):

1. `derived_from` edges — an item derived from another shares its group.
2. Shared declared `failure_domain` — distinct roots that can fail together (the syndicated-report case).
3. **Identical `(method, method_version, inputs)`** — the same deterministic procedure run twice.

Relation 3 was missing in iteration 1, and without it LD6 and DoD 9 could not be satisfied: a repeated deterministic check has no `derived_from` edge to its own earlier run and need share no declared failure domain, so it would have reported as **two** independent groups — precisely the laundering R2 names. The fix is the algorithm, not a special case in the test.

A declaration can put two items in one group; it can never assert that two lineage-connected items are in different groups. The asymmetry is what makes accepting the declaration safe — the constrained party can only weaken its own independence claim, never strengthen it.

**LD5 — The result counts groups by class *and* status, and refuses to report a row count as corroboration.**
Carrying `autonomous_maintenance_harness`'s `row_count_is_not_corroboration` property into a form the evaluator could use. The returned type exposes independent **group** count; the item count is never presented as a strength.

**The breakdown is two-dimensional (audit V5).** A class-only breakdown cannot answer step 4's actual question — *how many independent groups carry directly-satisfying evidence that was actually verified?* — because a group holding one `asserted` `artifact_bound` item and one holding a `verified` one would be indistinguishable, collapsing the very distinction LD2 introduces. Step 4 would then have to reach past the result and re-derive the grouping, which is the reshaping cost that VETOed Loop 8 twice.

So `DependenceAnalysis` reports group counts by (class rank × binding status). **Counts, not verdicts** — LD7 still forbids the verdict; this supplies what a verdict would need.

**Counting discipline (audit C1).** Two edges both fail toward overstating evidence, so both are pinned:

- **A group's counted status is the weakest disposition it carries, not the strongest.** A group holding one `verified` and one `refuted` item is internally contradictory; counting it as verified would hide the refutation, reintroducing V4's harm one level up after V4 closed it at the item level. Groups containing any `refuted` item are reported separately. This module does not adjudicate the contradiction — it must simply not conceal it.
- **No single field mixes `unqualified` groups into a qualifying total.** Ten *distinct* bare strings legitimately form ten groups. A headline "10 independent groups" would then be true and misleading in precisely the way §2b names: *raising the count does not raise the class.* LD5 already refuses to present the item count as a strength; the same refusal extends to the group count.

**LD6 — Repetition of one deterministic procedure is one item, not two.**
R2 states this in as many words: "a second deterministic reproduction of the same test is validation of one evidence item, not a second evidence item." Two `reproducible_procedure` items with identical `method`, `method_version`, and `inputs` are the same check run twice, and LD4 relation 3 is the mechanism that collapses them — derived, not declared.

**LD7 — No method returns a decision, an outcome, or a permission.**
The same discipline as LD6 in Loop 8, and for the same reason. This module reports *what evidence is*; it never reports what may therefore happen. There is no `discharges`, no `sufficient_for`, no risk-class parameter — accepting a risk class would invite returning a verdict against it, and that verdict is step 4's.

**LD9 — ADR-037 §4 is recorded as step 3's, not silently dropped (audit V3).**
§4 requires `collect_more_evidence` to state which criteria are unmet, what class satisfies each, and what independence bar applies at this risk class. No step in the ADR's four-step order names an owner for it, which is how a requirement gets lost between four cycles that each correctly declare it out of scope.

It is **not** this cycle's: it needs a risk class, and LD7 refuses one on purpose. It lands in **step 3**, where resumption already re-evaluates against a risk class and already holds the parked record that would carry the message. Recorded here so the ADR can be amended to say so.

**LD8 — `calibrated_estimator` is marked as never-sole, structurally.**
R3: an estimator "must never be the sole basis for discharging `require_review`". The result therefore reports the qualifying (direct-satisfying) groups separately from the contributing ones, so a caller cannot reach "one estimator is enough" without deliberately reading past the distinction.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/evidence_qualification.py` | **new** — `EvidenceItem`, `Qualification`, `DependenceAnalysis`, `qualify`, `group_by_dependence` |
| `reference/tests/test_evidence_qualification.py` | **new** |

No existing file is modified. Nothing calls this yet, by design.

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX013 | Evidence carries a derived checkability class and binding status, and correlated items collapse into lineage-derived dependence groups | NEW |

**FX013's index note must carry the narrowed claim (audit C2).** The feature index is where a claim outlives the cycle that made it, and FX011 sets the precedent by recording its own residual. The note states that classification is derived from bindings present, that `asserted` is the default because no verifier has run, and that **this cycle does not close the caller-asserted pattern**. Six prior instances make an unqualified claim here actively harmful to the next reader.

## Definition of Done

1. `artifact_bound` is derived only when `artifact_ref`, `digest`, and `verifier` are all present; missing any one drops the item to `unqualified`, asserted per-binding.
2. `reproducible_procedure` requires all of `inputs`, `method`, `method_version`, `result`, `verifier` — asserted per-binding (LD2).
3. `calibrated_estimator` requires `estimator_id`, `estimator_version`, `calibration_ref`.
4. **A caller cannot declare its own class.** An item carrying `qualification_class="artifact_bound"` as an input field and no digest classifies `unqualified`.
4b. **Binding status is `asserted` unless a verifier actually ran** (audit V1). Bindings present with no registry classify with the correct class and status `asserted`; a passing verifier yields `verified`.
4c. **A failing verifier yields `refuted`, never `asserted`** (audit V4). Asserted as a distinct third state, and asserted that `refuted` is not equal to `asserted`, because `"verified" if passed else "asserted"` is the implementation this DoD exists to fail.
4d. The registry is supplied by the evaluator, not carried on the item: an item naming a verifier absent from the registry stays `asserted`, and cannot reach `verified` by naming it.
5. A bare string reference (`"i-said-so"`, `" "`) classifies `unqualified` without raising (LD3).
6. Two items linked by `derived_from` land in one dependence group, whatever their declarations say.
7. Two items with distinct roots and a shared declared `failure_domain` land in one group (the syndicated-report case).
8. **A declaration cannot split a lineage-connected pair.** Two items joined by `derived_from` and given different `failure_domain` values remain in one group — merge-only asymmetry (LD4).
9. Two `reproducible_procedure` items with identical `method`, `method_version`, and `inputs` land in one group **with no `derived_from` edge and no shared declared `failure_domain` between them** (LD4 relation 3, LD6, R2's "second deterministic reproduction"). Stated this way so the test cannot pass by accident through relation 1 or 2.
10. The result reports independent group count, and breaks groups down by **class rank and binding status together** (LD5, LD8, audit V5). Asserted by answering step 4's question directly from the result: the count of independent groups carrying `verified` directly-satisfying evidence, with no reach into the raw items and no re-derivation of the grouping.
11. Ten copies of one reference yield **one** group, and the result exposes no field that presents the row count as corroboration.
12. **The module exposes no method returning a decision, outcome, permission, or sufficiency verdict**, asserted over the public surface (LD7).
13. **All 971 prior tests pass**, and `policy.py` is unmodified — verified by empty diff, since step 4 is explicitly not in this cycle.
14. `validate_schemas.py` and `validate_fixtures.py fixtures` clean; no schema file modified.
15. **A group's counted status is its weakest** (audit C1): a group holding a `verified` and a `refuted` item is not counted as verified, and is reported among the refuted-carrying groups.
16. **No reported total mixes `unqualified` groups with qualifying ones** (audit C1). Ten distinct bare strings produce ten groups and zero qualifying groups, asserted together.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## CI Coverage Exemptions

No workflow path filter covers a new unreferenced module. DoD 13 runs the full suite, which is the coverage that matters for a module nothing calls yet — the same disposition as Loop 8.

## Rollback

Delete both new files. Nothing else changes.

## Next

`/qor-implement`. Audit attempt 3 returned PASS with binding conditions C1 (counting discipline: a group counts at its weakest status; no total mixes `unqualified` groups with qualifying ones) and C2 (FX013 carries LD2's narrowed claim, not the ambitious one), both folded into LD5, the Feature Inventory section, and DoD 15-16.

Attempts 1 and 2 vetoed on V1-V5: presence of a binding is not verification (V1); the stated algorithm could not satisfy DoD 9 (V2); ADR-037 §4 was unassigned across all four steps (V3); a failing verifier had no state and would have collapsed into `asserted` (V4); the result could not answer step 4's question without reshaping (V5). All five are discharged in this iteration.
