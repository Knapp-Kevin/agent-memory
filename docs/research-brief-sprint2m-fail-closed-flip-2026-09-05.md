# Research Brief: Sprint 2m — the fail-closed flip

**Date**: 2026-09-05
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 14.
**Implements**: ADR-037 **step 4b-2** — the flip, under the operator ruling of 2026-09-05

## 1. The operator ruling, which supersedes the audit's working classification

Loop 13 classified modules by *"has a digest"*. The operator has ruled that this was **reconnaissance, not the governing rule**:

> A caller converts only if it already possesses **semantically relevant** material that can **truthfully** populate an existing R3 qualifying class. No new binding may be created merely because the migration requires one. Otherwise the proposal parks.

Two things change. R3 recognises **two** directly-satisfying classes — artifact-bound *and* reproducible procedure — so a digest was never the test. And more importantly, checkability is necessary but not sufficient: the material must establish **the proposition under review**.

> Evidence supports the proposition ≠ authority permits the consequence.

The operator's own reasoning on the tempting case is the clearest statement of it: `decision_overwrite`'s `AuthorityGrant` is unusually strong — bound to proposal, target, scope, actor, risk ceiling and lifetime, and `_grant_refusal` is deterministic. It would classify beautifully as a reproducible procedure. **And it answers the authority question, not the evidence question.** A perfectly valid grant can authorise review of a bad proposal, so it cannot also be proof that the proposal deserves discharge. Using it would collapse two of the four axes ADR-037 exists to keep apart.

**The live behavioural change is intentional.** The instruction is explicit: do not optimise for preserving the 1071-test baseline; preserve the invariants, not the historical outcomes, because those outcomes were partly obtained through an invalid discharge path.

## 2. The constraint that must not be misread — and it is the one an implementer will get wrong

**Semantic relevance is a conversion-time design judgement. It is not, and must not become, a runtime field.**

The obvious way to "implement" the ruling is a `relevance` or `establishes` attribute on `EvidenceItem`, asserted by the caller. That would be the caller-asserted defect for the eleventh time, and it would be worse than the ten before it because the assertion would be about *meaning*, which nothing can check.

The ruling is applied by **deciding which sites convert**, and recording why. The code gains no relevance concept. This is the same discipline as Loop 13's V3: the distinction is derived from lineage and design, never declared in a field.

## 3. Measured: what each of the four parking sites actually receives

Every site was evaluated under today's policy and under the flip:

| Site | Today | Flipped |
|---|---|---|
| `decision_overwrite` low | `allow_with_ledger` | **`require_review`** |
| `decision_overwrite` medium | `allow_with_ledger` | **`require_review`** |
| `decision_overwrite` high | `require_external_verification` | `require_external_verification` — **unchanged** |
| `forbidden_hits` correction (low) | `allow_with_ledger` | **`require_review`** |
| `visibility_characterization` correction (low) | `allow_with_ledger` | **`require_review`** |
| `benchmark_security` permanent deletion | `allow_with_ledger` | **`require_review`** |

The last row required care and nearly produced a false report. `benchmark_security`'s deletion is `irreversible`, which invites the assumption that it is already on the external-verification path — but its `_proposal` default is **`risk_class="low"`**, and M-IRREV escalates an irreversible low-risk mutation to `require_review`, not to `require_external_verification`. So it does go through the asserted route today, and it does park under the flip. **The operator's ruling holds for all four exactly as given**, and `decision_overwrite`'s high path is untouched, as the ruling requires.

## 4. Blast radius, measured against the current tree

```
Ran 1071 tests — FAILED (failures=44, errors=14)
```

**58 tests across 23 files.** Two of them are Loop 12's own (`test_qualified_discharge`) and one is Loop 13's — the tests that assert the asserted route still works. Those are the flip's most direct declared amendments and they are correct to break.

Per the operator's acceptance criterion, every changed test is classified as **expected semantic change** or **actual regression**, with no mass snapshot update. Three kinds:

| Kind | Treatment |
|---|---|
| Asserts the gate's own behaviour | declared amendment — the expectation inverts |
| Uses assertion as **scaffolding** to reach later behaviour | **split the concern**: one test proves the production call now parks without evidence; a separate scenario supplies genuine qualified fixture evidence *where the fixture actually establishes the proposition*. No test-only bypass |
| Uses assertion where **no honest qualifying fixture exists** | the later-stage scenario stays blocked and is redesigned, not grandfathered |

The third category is the one that will be tempting to smuggle through, and the operator has closed that door in advance.

## 5. What parking must produce

Criterion 7: *parking exposes the exact missing evidence class/status so the caller has a traversable remediation path.* Steps 1–3 already built this — `PendingVerificationRegistry.park`, `criteria_for`, and R5's ladder with per-axis refusal reasons (`insufficient_evidence_class`, `insufficient_binding_status`, `human_confirmation_required`). The flip does not need new remediation machinery; it needs the four sites to reach the machinery that exists.

## 6. What must not move

- `_apply_review`'s `require_external_verification` cap (Loop 7) — unchanged.
- `evaluate_with_external_verification` and its early return — unchanged. `decision_overwrite` high and every other external-verification path keeps its current semantics.
- `evaluate_with_qualified_evidence` (Loop 12) — the three producers continue through it.

## 7. Risk grade

**L3 — the top of the scale.** The grade ladder this toolchain defines is L1-L3; there is no L4. Recorded as L3, and noted as the most consequential L3 in the program. This is the first that changes live behaviour by design, across 23 test files and four production sites, and it removes a discharge path that has been load-bearing since the first policy implementation. A mistake is not a wrong shape or a silent weakening — it is a governance decision changing for the wrong reason, in production paths.

## 8. Next

`/qor-plan`.
