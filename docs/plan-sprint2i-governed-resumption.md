# Plan: Sprint 2i — governed resumption and re-evaluation

**change_class**: feature
**Risk Grade**: L3
**Session**: 2026-09-05T0140-688455
**Research**: `docs/research-brief-sprint2i-governed-resumption-2026-09-05.md`
**Iteration**: 4 (audit attempt 3: PASS with binding conditions C1, C2)
**Implements**: ADR-037 implementation order, **step 3 of 4**, plus **§4** (assigned here by step 2's LD9)

## Objective

Let a parked proposal be re-evaluated by the evaluator when qualifying evidence arrives, and tell an actor what would discharge it. After this cycle all three prerequisites for step 4 exist.

## The honest range of this cycle, measured (audit V4)

| Parked outcome | Resumable now? | Why |
|---|---|---|
| `require_external_verification` | **yes** | a bound, separated attestation discharges it through `evaluate_with_external_verification` — measured `-> allow_with_ledger` |
| `require_review` | **no** | evidence reaches the evaluator only as `proposal.evidence_refs`, and M-EVID is an emptiness check. Appending qualified, independently verified evidence to a proposal that already had one reference changes the outcome **not at all** — measured. Its only discharge today is `review_satisfied` + `approval_refs`, which is exactly the assertion path **step 4** converts |

This is not a shortfall; it is what the ordering means. Step 2's headline finding — that evidence is a truthiness check — applies to step 3's own mechanism, and step 4 is the cycle that fixes it.

It does change what the criteria report must say. For a parked `require_review`, the report states that **its discharge path is the assertion route step 4 replaces**, rather than listing an evidence criterion no evidence can currently satisfy. Telling an agent to collect evidence that cannot help is worse than telling it to wait.

## Boundaries

**In scope**: `reference/agentmem_ref/resumption.py` (new), a `resume` method on `PendingVerificationRegistry`, and tests.

**Explicitly out of scope:**

| Step | Status here |
|---|---|
| 4. Fail-closed `require_review` | **not built.** `policy.py` unmodified; the 51 assertion sites unconverted |

This is the last cycle before step 4 becomes permissible, which makes the temptation maximal: everything needed to flip the gate will exist when this lands. It is still a separate cycle with its own audit and 51 call sites.

## Design decisions

**LD1 — The independence bar is reported as `undefined`, never invented.**
ADR-037 §4 requires stating "what independence bar applies at this risk class". Research established that no such bar exists in accepted doctrine: the only count threshold is `reusable_grants`' `>= 2`, which R4 forbids generalizing; §2b argues against counting; and ADR-037:128 warns by name against inventing `independent_verified_approver_count >= 2`.

So `UnmetCriterion` carries an explicit `bar: "undefined"` for independence, with a pointer to the open question. **A message saying "this criterion has no defined bar" is more useful to an agent than a confidently invented number, and far more useful than silence.** An ADR amendment proposal is filed rather than the semantics being chosen here.

**LD2 — Resumption takes an attestation *and* evidence; they are different objects (audit V2).**

Iteration 1 conflated two things Loops 2 and 7 kept apart:

| | Question it answers | Type | Who supplies |
|---|---|---|---|
| **Evidence** | is this checkable, and how independent is it? | `EvidenceItem` (step 2) | the **actor** — R1 permits production |
| **Attestation** | did a separated authority verify *this proposal*? | `ExternalVerification` (Loop 7) | the **evaluator** |

`attestation_refusal(proposal, attestation)` requires an `ExternalVerification`; an `EvidenceItem` is not one, and iteration 1's signature had no parameter for it. Resumption needs both, so `resume` takes both.

Loop 7 already generalized binding, self-verification-by-identity, human-confirmation-at-high-risk, and risk ceiling into the shared evaluator, and re-deriving any of them here would be the eighth instance of the pattern this program exists to close.

**Resumption does not call `attestation_refusal` at all (audit C1).** Measured: `evaluate_with_external_verification` calls it *internally* and surfaces the result in `decision.reasons` — a mismatched binding returns `('M-IRREV: irreversible mutation', 'attestation_not_bound_to_proposal')`. A separate pre-check would be a second copy of a control already correctly placed in the shared evaluator, and two copies of one check are two things that can diverge. Nine cycles have gone into controls that lived in one place and were absent from another; adding a redundant copy is the same mistake with the polarity reversed.

So resumption calls the evaluator and **reads the refusal from the returned reasons**.

**LD3 — The actor supplies evidence; the evaluator supplies the registry and the state version.**
The signature is the enforcement: evidence is the actor's contribution (R1 permits it), while the attestation, the verifier registry, the current state version and the current policy version are the evaluator's and cannot be read off the parked record.

**The state version in particular must not come from the record.** The record was written *before* the delay that makes staleness a risk. Reading it from there would replay a decision made under earlier conditions — exactly what §5 forbids.

Full signature: `resume(proposal_id, *, evidence, attestation, verifiers, current_state_version, current_policy_version)`. Only `evidence` is the actor's.

**LD4 — `resume` returns a re-evaluation, never a permission.**
It returns the freshly computed `Decision` plus why resumption did or did not change anything. It does not commit, does not write to a substrate, and does not mark the parked record discharged on its own authority — the caller acts on a `Decision` exactly as it would on any other.

**LD11 — Re-evaluation routes through the function that can actually discharge (audit V4).**
With an attestation present, `policy.evaluate_with_external_verification(proposal, attestation)`; otherwise `policy.evaluate(proposal)`.

**This cycle depends on a Loop 7 invariant, and pins it (audit C2).** Probed: an otherwise-valid attestation offered for a parked `require_review` does **not** discharge it — `evaluate_with_external_verification` returns early unless the computed outcome is `REQUIRE_EXTERNAL_VERIFICATION`, so the result is `require_review`, identical to plain `evaluate`. That early return is the only thing stopping an attestation from becoming a general-purpose discharge for every parked proposal, which would do step 4's job without step 4's audit and would do it wrongly. A test asserts it, naming the dependency, because an undocumented reliance on another module's early return is how a later refactor removes a control nobody knew was load-bearing. Iteration 2 named `attestation_refusal` — the *guard* — and omitted the discharge function entirely, so it would have validated an attestation and then re-evaluated through a path that ignores it, returning the parked outcome unchanged. The one path that genuinely works would not have worked.

**LD12 — Admitted evidence amends `evidence_refs` and nothing else (audit V4).**
"Qualifying evidence is admitted" (§3) has to mean something, so admitted refs are appended to the re-evaluated proposal. Two constraints:

- **Amend-only, and only that field.** Every other field of the retained `Proposal` is carried through identically. This is load-bearing at L3: a resumption that may rewrite `risk_class` or `actor_id` is a proposal-rewriting primitive, and that is an authority bypass rather than a wrong shape.
- **It changes no outcome today, and the plan does not claim it does.** M-EVID is an emptiness check. The append exists because step 4 will read it.

**LD5 — Staleness refuses resumption outright, before policy is re-evaluated.**
Entry #14's guard "applies to resumption exactly as it applies to commit" (§5). If the world moved, the proposal's authority no longer binds, and re-evaluating would produce a decision against state the proposal was never assessed for. Refuse first, evaluate never.

**LD6 — Separation is checked on the attestation, where the principal actually lives (audit V1).**

Iteration 1 said "evidence whose verifier principal is the proposing actor". **`EvidenceItem` has no principal field** — measured: `ref, artifact_ref, digest, inputs, method, method_version, result, verifier, estimator_id, estimator_version, calibration_ref, derived_from, failure_domain`. Its `verifier` is a *name*, which step 2 deliberately made non-authoritative.

Leaving this unspecified invites adding `verifier_principal_id` to `EvidenceItem` — putting the separation control's input back in the hands of the party it constrains, for the eighth time.

The principal lives on `ExternalVerification.verifier_principal_id`, evaluator-supplied, and Loop 7 already derives self-verification from it (`attestation_self_verified`). **So R1's "may produce, may not certify" is enforced exactly where Loop 7 put it**, and LD2's `attestation_refusal` call is the whole mechanism:

- The actor may produce every evidence item. That is R1, and nothing here restricts it.
- The actor may not be the attesting principal. That is `attestation_self_verified`, already implemented.

No new separation logic is written this cycle. That is the point.

**LD10 — Policy drift is detected and reported, never silently absorbed (audit V3).**
§5 requires re-evaluation "against current policy and current state". Iteration 1 handled current state (LD5) and ignored current policy, though `ParkedProposal.policy_version` exists precisely to detect drift.

`current_policy_version` is compared to the record's. Drift does **not** refuse — re-evaluating under current policy is the correct behaviour — but it is reported, because a decision that changed for policy reasons rather than evidence reasons is a materially different fact to the actor receiving it. It is also the only way DoD 12's newly-yielded `block` can arise: `evaluate` is deterministic over a retained `Proposal`, so under unchanged policy the outcome reproduces exactly.

**LD7 — A resumption that still refuses re-parks nothing and mutates nothing.**
The parked record is unchanged by a failed resumption. Only the criteria report differs, because evidence may now be closer. An append-only registry that silently rewrote records on failure would destroy the evidence of the first refusal — Loop 8's LD2 reasoning.

**LD8 — `block` remains unreachable by resumption.**
Step 1 refuses to park `block` because its envelope prohibits `enter_pending_verification`. Nothing parked can therefore be a `block`, and re-evaluation that *newly* yields `block` must refuse rather than resume: an absorbing outcome has no route, and manufacturing one here would defeat step 1's guard from the other side.

## Affected files

| File | Change |
|---|---|
| `reference/agentmem_ref/resumption.py` | **new** — `UnmetCriterion`, `CriteriaReport`, `ResumptionResult`, `criteria_for`, `resume_parked` |
| `reference/agentmem_ref/evidence_qualification.py` | **unmodified** — no principal field added (audit V1, DoD 6b) |
| `reference/agentmem_ref/pending_verification.py` | **modified** — `resume` added (step 3's promised method) |
| `reference/tests/test_governed_resumption.py` | **new** |
| `reference/tests/test_pending_verification.py` | **modified** — the two LD6 absence tests invert now that step 3 exists |

## Feature Inventory Touches

| ID | Feature | Disposition |
|---|---|---|
| FX014 | A parked proposal is re-evaluated by the evaluator when qualifying evidence arrives, with staleness refused first, separation enforced through the shared evaluator, and policy drift reported | NEW |
| FX012 | Parked verification state | MODIFIED — gains `resume` |

## Definition of Done

1. Resuming a parked `require_external_verification` with a bound, separated attestation re-evaluates through `evaluate_with_external_verification` and returns `allow_with_ledger` (LD11). Asserted as the cycle's one working discharge path.
1b. **Resuming a parked `require_review` does not discharge it, and the report says why** (audit V4): the criteria report names the assertion route as step 4's, and does *not* list an evidence criterion that no evidence can currently satisfy. Asserted with qualified, verified, independent evidence attached, so the test proves the limit is structural rather than a weak fixture.
1c. **Admitted evidence amends only `evidence_refs`** (LD12): every other field of the re-evaluated proposal is identical to the retained one, asserted field by field.
2. **Re-evaluation uses the retained `Proposal`**, asserted by showing the decision equals `policy.evaluate(record.proposal)` under unchanged conditions — the property step 1's V1 correction exists to provide.
3. **A stale proposal is refused before policy is re-evaluated** (LD5): asserted by a refusal reason of `stale_authorization` *and* by the absence of any new decision, so refusing-then-evaluating cannot pass.
4. The current state version comes from the caller, not the record: resuming with a state version matching the record's snapshot succeeds where a differing one refuses, with the record byte-identical in both cases (LD3).
5. **An attestation whose principal is the proposing actor refuses resumption** (LD6, R1), with the evaluator's own `attestation_self_verified` reason — not a locally re-derived one. Asserted alongside the converse: the same actor *producing* every evidence item is fine, because R1 permits production.
6. **Separation refusals arrive in `decision.reasons` from the shared evaluator, not from a local pre-check** (LD2, audit C1): an attestation bound to a different proposal yields `attestation_not_bound_to_proposal`, an attestation whose principal is the actor yields `attestation_self_verified`, and a high-risk proposal with a non-human-confirmation attestation yields `human_confirmation_required` — each read from the returned decision.
6c. **An otherwise-valid attestation does not discharge a parked `require_review`** (audit C2), asserted with a comment naming the `evaluate_with_external_verification` early return this depends on.
6b. **`EvidenceItem` gains no principal field** (audit V1). Asserted over its dataclass fields, so the eighth instance of the caller-asserted pattern cannot be introduced quietly.
7. Unqualified evidence — bare strings — does not enable resumption, and the criteria report names the missing bindings (step 2's `missing_bindings`).
8. Estimator-only evidence does not enable resumption at any risk class (R3: never a sole basis).
9. **The criteria report states the independence bar as `undefined`** with the open-question pointer, and states no numeric threshold anywhere (LD1). Asserted by scanning the report for any integer bar.
10. The report names, per unmet criterion, what class would satisfy it — §4's actual requirement.
11. A failed resumption leaves the parked record byte-identical and emits no discharge event (LD7).
12. **Policy drift is detected and reported** (LD10): resuming with a `current_policy_version` differing from the record's succeeds, re-evaluates under current policy, and reports the drift. A re-evaluation that newly yields `block` — reachable only under drift, since `evaluate` is deterministic over the retained proposal — refuses rather than resuming (LD8).
13. `resume` is now present on `PendingVerificationRegistry`, and the two Loop 8 tests asserting its absence are inverted — declared amendments, not silent edits.
14. **All 999 prior tests pass** (minus the two inverted), and `policy.py` is unmodified — verified by empty diff, since step 4 is not in this cycle.
15. `validate_schemas.py` and `validate_fixtures.py fixtures` clean; no schema file modified.

## CI Commands

```
python -m unittest discover -s reference/tests -t reference
python scripts/validate_schemas.py
python scripts/validate_fixtures.py fixtures
```

## Rollback

Delete `resumption.py` and its tests; revert `resume` from `pending_verification.py` and re-invert the two Loop 8 tests.

## Next

`/qor-implement`. Audit attempt 3 returned PASS with binding conditions C1 (read separation refusals from the evaluator's returned reasons rather than pre-calling `attestation_refusal`, which it already calls internally) and C2 (pin the Loop 7 early return this cycle now depends on), both folded into LD2, LD11 and DoD 6/6c.

Attempts 1 and 2 vetoed on V1-V4: `EvidenceItem` has no principal so LD6 was unimplementable (V1); DoD 6 was unsatisfiable against the stated signature (V2); policy drift went undetected though the record carries the field (V3); and the mechanism was inert for `require_review` while the plan implied general discharge, with the discharge function itself omitted (V4). All four are discharged in this iteration.
