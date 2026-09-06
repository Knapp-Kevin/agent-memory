# Research Brief: Sprint 2l — migrating the evidence producers

**Date**: 2026-09-05
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 13.
**Implements**: ADR-037 **step 4b-1** — see §2, which argues 4b splits again

## 1. The classification that matters, and it is not the one expected

Step 4a's research split the affected sites by *kind of test*: those asserting the gate versus those using assertion as scaffolding. That distinction is real and still holds for the flip.

But it is not the axis that governs **conversion**. Measured across the seven production modules that set `review_satisfied=True`:

| Module | sets `review_satisfied=True` | digest / procedure material present |
|---|---|---|
| `procedural_memory` | 1 | **21** — carries `content_sha256` and `skill_version_ref` |
| `dashclaw_external_verdict` | 1 | **23** |
| `reusable_grants` | 1 | **9** — `grant_body_digest`, built in Loop 6 |
| `decision_overwrite` | 1 | 0 |
| `forbidden_hits` | 1 | 0 |
| `visibility_characterization` | 1 | 0 |
| `benchmark_security` | 1 | 0 |

**Only three of the seven can produce genuine artifact-bound evidence today.** `procedural_memory` already builds an approval object carrying `proposal_id`, `skill_version_ref`, `content_sha256` and `state_snapshot` — that is an `EvidenceItem` in all but name, and converting it is real rather than relabeling.

The other four hold a *name* and nothing checkable. For them, "conversion" would mean inventing an `artifact_ref` and a `digest` to satisfy the classifier — which is the caller-asserted defect this program has spent thirteen cycles closing, dressed as a migration.

**ADR-037 already ruled on what happens to them**, and it is not conversion:

> 51 call sites must present real evidence **or park**. That is the point, and it is why the path lands first.

So 4b contains two genuinely different operations: migrating sites that *have* evidence, and deciding what happens to sites that do not. Only the first is mechanical.

## 2. Why 4b splits

4a split step 4 because the discharge path did not exist. This split has a different and weaker justification, and it should be stated honestly rather than dressed in the same clothes.

There is **no doctrinal halt** here: converting the three evidence-carrying modules and flipping in one cycle would strand nobody who could not have been stranded anyway. The argument is risk and reviewability:

- The flip breaks **57 tests across 18 files**. Converting three modules inside that noise means a mistake in any one of them is masked by the other 54 failures.
- Four modules must be *decided about*, not converted, and that decision is the operator's, not an implementation detail.

So: **4b-1 (this cycle)** migrates the three modules that can produce real evidence, additively, with no flip. **4b-2** flips, amends the gate tests, and re-homes the scaffolding tests — by which point the conversion mechanism is proven and the remaining residue is small and understood.

This is a judgement call about blast radius, not a principle. It is recorded as such.

## 3. What "additive" means here, precisely

Each migrated module gains the ability to *produce* an `EvidenceItem` from material it already holds, and to route a discharge through `evaluate_with_qualified_evidence`. It does **not** stop setting `review_satisfied`, and `_apply_review` is not touched — so every existing caller keeps working and no test breaks.

The migration is therefore provable in isolation: a test can assert that the module's own evidence discharges through the ladder, *and* that its legacy path still works, in the same suite.

## 4. What the evidence actually is, per module

- **`procedural_memory`** — `content_sha256` of the skill payload is the digest; `skill_version_ref` is the artifact reference. The verifier re-hashes the payload and compares. That is `artifact_bound` with a genuine deterministic verifier, and it is `verified` rather than `asserted` whenever the payload is available to hash.
- **`reusable_grants`** — `grant_body_digest` (Loop 6) over `_GRANT_BODY_KEYS`. Loop 6 built it precisely so a grant could not be tampered with after ratification; it is a digest with a verifier already in the module.
- **`dashclaw_external_verdict`** — carries provider execution evidence and commit bindings. Richest of the three, and the one whose evidence is externally produced rather than self-produced, which makes it the useful adversarial case for R1: the provider produces, the module does not certify.

## 5. The honest strength of this migration

At low and medium risk, R5 accepts `asserted` binding — so a converted site that names a verifier nobody runs is only modestly stronger than the `approval_refs` it replaces. FX013 already records this residual and it is not re-litigated here.

What changes materially: the claim becomes **checkable**, the class becomes **derived** rather than claimed, and at high or critical risk the ladder demands `verified` plus human confirmation. `procedural_memory` can reach `verified` today, because it can re-hash. That is worth stating as the target rather than settling for `asserted` because low risk permits it.

## 6. Blast radius

Zero test breakage expected. Three modules gain a method and a path; nothing existing changes behaviour. `policy.py` untouched.

## 7. Risk grade

**L3.** The code is additive, but this cycle establishes the pattern the remaining conversions copy. A migration that produces evidence-shaped objects without checkable content would propagate the defect to every site that follows it.

## 8. Open question for the operator

Four modules — `decision_overwrite`, `forbidden_hits`, `visibility_characterization`, `benchmark_security` — hold no digest and no reproducible procedure. Under ADR-037 they park rather than convert. Whether that is acceptable, or whether they should acquire real evidence first, is a scope decision rather than an implementation one, and it is raised rather than assumed in 4b-2's favour.

## 9. Next

`/qor-plan`.
