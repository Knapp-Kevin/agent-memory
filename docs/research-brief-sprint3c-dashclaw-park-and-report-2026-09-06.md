# Research Brief: Sprint 3c — the DashClaw correction seam after the fail-closed flip

**Date**: 2026-09-06
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 18.
**Implements**: the operator's 2026-09-06 acceptance of park-and-report for `run_dashclaw_external_verdict.py`, surfaced by PR #386's CI and held out of that PR
**Risk**: L2 — a CI-invoked governed caller's assertions, a workflow's invariant step, and a runtime-evidence document change; no policy, adapter or evaluator code changes

## 1. The defect, measured

`reference/run_dashclaw_external_verdict.py:334` asserts `report["correction"]["committed"] is True`, and `:335-338` assert the consequences (`state_version == 2`, `current_value == "release branch main"`, the old event invalidated, the new fact recalled). The runner is invoked by `.github/workflows/dashclaw-external-verdict.yml:83`, and the workflow's own "Verify workload invariants" step repeats the same assertions inline at lines 104-108. Both fail on `main` since #384 (ADR-037 step 4b-2, ledger Entry #24): the runner exits on the first failed assertion, so the JSON evidence file is never written.

Run with the assertions stripped, the correction block on `main` is:

```
committed: false          refusal: null             state_version: 1          current_value: "release branch release"
unapproved_refusal: approval_required
wrong_identity_refusal: approval_identity_mismatch
self_approval_refusal: self_approval_forbidden
old_value_event_invalid: false
```

The three refusals the runner tests first still hold. What changed is the fourth call, the one with a valid human approval bound to the exact `input_identity`: it now parks. The adapter's result for that call (captured by wrapping `DashClawGovernedCommitter.commit`) is `committed=False`, `refusal=None`, a `decision` with `outcome='require_review'`, `permitted_actions` `('enter_pending_verification', 'collect_more_evidence', 'defer')`, `prohibited_actions` `('correction',)`, and a receipt (`ref-0014`) whose `decision_outcome` is `require_review`. The park is recorded in the receipt; it is not surfaced as a refusal string, which is why the runner's report shows `refusal` only for the three DashClaw-half cases.

A consequence for the next case: `report["stale_replay"]` was `{"committed": false, "refusal": "stale_authorization"}` because the approved correction had advanced state to `v2` and the replay carried `state_snapshot="v1"`. With the correction parked, state stays at `v1`, the replay is not stale, and it parks the same way: `{"committed": false, "refusal": null}`. The runner can no longer demonstrate `stale_authorization` on this path, because a committed correction was its precondition. That is a coverage loss to record, not to paper over.

## 2. Why it parks: the seam's two halves

`dashclaw_external_verdict.commit_bound_mutation` (`:582-650` on `main`) has two halves.

**The DashClaw half** (`:609-635`) is intact and is not what the ADR flipped: a correction at medium risk resolves to `require_review`; the seam then requires an `approval_ref`, an `approval_actor_id` distinct from the agent, and an `approved_input_identity` equal to the mutation's. Those are the three refusals above, all still asserted, all still passing.

**The Agent Memory half** (`:636-641`) is the legacy asserted route: on a satisfied approval it sets `review_satisfied=True, approval_refs=(approval_ref,)` on the proposal and calls `memory.commit_proposal(proposal, fact_text)`. The adapter re-evaluates PAMA. Since 4b-2, `policy._apply_review` (`policy.py:284-292`) returns `review_requires_qualified_evidence` for that shape: "`review_satisfied=True` plus arbitrary `approval_refs` was the last route by which an unverifiable claim became an authority decision". The proposal parks at the adapter. Nothing in the seam forwards evidence, so the seam neither forwards nor reports why it parked; the runner then asserts a commit that did not happen.

## 3. What 4b-1 built for DashClaw, and what it did not

Sprint 2l (ledger Entry #22-#23; `docs/plan-sprint2l-evidence-producers.md` LD3, LD4, DoD 4-5) gave the module `evidence_for(bound)` (`dashclaw_external_verdict.py:234-272`): two `artifact_bound` items in two dependence groups — the mutation's `content_sha256` under `CONTENT_VERIFIER`, and the resolved `authority_evidence_ref` under `PROVIDER_VERIFIER`. `test_evidence_producers.py:230-247` proves the pair discharges `require_review` at **high** risk under `evaluate_with_qualified_evidence` when the content verifier is registered and a `human_confirmation` attestation is present.

LD3 was explicit that the module "produces; the caller decides whether to route through `evaluate_with_qualified_evidence`". No caller does. `grep -n 'evidence_for' reference/agentmem_ref/dashclaw_*.py` finds the definition only; `commit_bound_mutation` never calls it and `commit_proposal` is never given `evidence=`. The 4b-2 seal (Entry #24) lists `dashclaw_external_verdict` among the three modules that "present real evidence" and cross; that statement is true of the producer and was tested at the producer. It was never true of the correction seam, which is the path the CI runner exercises.

## 4. Whether forwarding that evidence would be honest

This is the question the operator's ruling turned on, and the research answer is sharper than the recommendation the operator accepted.

If `commit_bound_mutation` forwarded `evidence_for(mutation)` to `commit_proposal(evidence=...)`, then at **medium** risk — the runner's correction — the ladder in `evaluate_with_qualified_evidence` (`policy.py:447-500`) needs "one qualifying group, `asserted` binding sufficient", and both items are `artifact_bound`. The correction would discharge as `delegated_policy` with no attestation consulted. That is not a park; it is a commit on two digests. What those digests establish: that the fact text is the text that was approved (binding), and that a grant covering the requested scope resolved (authority). Neither is an adjudication that "release branch release" should become "release branch main". The operator's 4b-2 ruling names this exactly: *evidence supports the proposition; authority permits the consequence; they are not interchangeable*, and a record binding "A became B under authority X" was rejected as circular because "that establishes binding and integrity, never that A *should* become B". The DashClaw provider's own verdict on the correction is `escalate` (`report["correction"]["provider_decision"]`), which is the provider declining to adjudicate it.

So the recommendation stands, with its second clause corrected: **forwarding `evidence_for` as the seam's evidence would discharge the medium correction on digests and must not be done.** DoD 20 ("forward qualified evidence/attestation or demonstrably park") is met by the seam parking with the adapter's stated reason, made visible in the runner's report. A route that later un-parks it is a `TransitionRuleCorpus` (`verification.py:145-200`) the evaluator holds for DashClaw-originated corrections — an adjudication that pre-exists the proposal, classified `reproducible_procedure`, re-run by the evaluator's verifier — which is R6's "parked modules earn routes", DashClaw-side work, and not this cycle.

## 5. The minimal correction

Three surfaces, each currently asserting a commit that the doctrine forbids:

1. `reference/run_dashclaw_external_verdict.py` — the correction block records the parked outcome: `committed: False`, `refusal: None`, the decision outcome `require_review` and its reasons (which carry `review_requires_qualified_evidence`, `policy.py:442`), the receipt's `decision_outcome`, `state_version: 1`, `current_value` unchanged, recall still admitting the v1 fact; the assertions at `:334-338` and `:341` change to assert exactly that. The three DashClaw-half refusals, the stale-replay case, the scope attack, the unauthorized project and the cross-target cases are untouched. The `stale_replay` block asserts what the replay now returns (`committed: false`, `refusal: null`, decision outcome `require_review`) and the report names the lost demonstration: `stale_authorization` is still asserted at unit level by five non-DashClaw tests (`test_governed_paths.py`, `test_restart_safe_runtime.py`, `test_procedural_memory.py`, `test_concurrency_evidence.py`, `test_benchmark_security.py`), but no DashClaw test or runner reaches it any more.
2. `.github/workflows/dashclaw-external-verdict.yml:104-108` — the inline invariant step mirrors the runner's new assertions, so the workflow and the runner cannot disagree.
3. `docs/programs/runtime-evidence/dashclaw-external-verdict.md` — the section describing the approved correction's commit (`:297-300` and the flow at `:44-58`) states the park and the reason, and names the transition-rule route as the way it would later un-park.

No change to `commit_bound_mutation`, `policy`, `adapter`, or `evidence_for`.

## 6. Blueprint alignment

| Claim | Source | Actual | Status |
|---|---|---|---|
| "`dashclaw_external_verdict` present[s] real evidence" and crosses | ledger Entry #24 | True at the producer (`evidence_for`, tested at high risk with attestation); false at the correction seam, which never forwards it and parks on the legacy route | **DRIFT** — a seam-level claim was made on producer-level evidence |
| The runner's approved correction commits | `run_dashclaw_external_verdict.py:334`, workflow `:108`, doc `:297` | Parks with `review_requires_qualified_evidence` since Entry #24 | **DRIFT** — pre-existing on `main`, surfaced by #386 CI |
| DoD 20: every path forwards or demonstrably parks | Entry #24 | The seam parks but reports nothing; the runner asserts the opposite | **DRIFT** — "demonstrably" not met |
| Forwarding the module's evidence would still park | the recommendation the operator accepted on 2026-09-06 | It would discharge at medium on `asserted` `artifact_bound` digests | **DRIFT** in the recommendation itself; corrected in §4 |

## 7. Recommendations

1. **(this cycle)** Park-and-report across the three surfaces in §5. The runner must write its evidence JSON on the parked path, since a failed assertion currently means no evidence file at all.
2. **(this cycle, negative test)** A test that forwarding `evidence_for` to `commit_proposal` at medium risk would commit — asserted so the laundering path is named and refused by construction, not by omission.
3. **(later, DashClaw-side, R6)** An evaluator-held `TransitionRuleCorpus` for DashClaw corrections. Not this cycle.

## 8. Updated knowledge

Shadow Genome: a conversion recorded as complete at the producer layer while the seam that CI exercises stayed on the legacy route, found only when that workflow's paths were next touched.
