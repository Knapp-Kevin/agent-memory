# Research Brief: Sprint 2f — verified discharge of external verification

**Date**: 2026-09-04
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 7.
**Gap**: GAP-ARCH-04, remaining legs.

## 1. The finding that reframes this leg

Loops 5 and 6 left GAP-ARCH-04 with two open legs: the `review_satisfied` discharge (74 sites), and `decision_overwrite` discharging `require_external_verification` by assertion while `evaluate_pama_with_reusable_grant` refuses to.

The natural reading was that `decision_overwrite` bypasses a control. **It does not.** `DurableDecisionRegistry._grant_refusal:329-367` is the most rigorous authority check in the repository:

```python
if grant.revoked:                                          return "authority_grant_revoked"
if grant.proposal_id != proposal.proposal_id:              return "authority_proposal_mismatch"
if grant.target_decision_id != proposal.target_decision_id: return "authority_target_mismatch"
if grant.scope != proposal.scope:                          return "authority_scope_mismatch"
if grant.mutation_class != "decision_overwrite":           return "authority_mutation_mismatch"
if proposal.proposing_actor not in grant.authorized_actor_ids: return "actor_not_delegated"
if grant.principal_id == proposal.proposing_actor:         return "self_approval_prohibited"
if grant.grant_id not in proposal.replacement.approval_refs: return "authority_not_recorded_on_replacement"
if _RISK_ORDER[proposal.risk_class] > _RISK_ORDER[grant.max_risk_class]:
                                                           return "authority_risk_ceiling_exceeded"
human_required = target.human_confirmed or proposal.risk_class in ("high", "critical")
if human_required and grant.authority_kind != HUMAN_CONFIRMATION:
                                                           return "human_confirmation_required"
if grant.authority_kind == DELEGATED_POLICY and proposal.risk_class not in ("low", "medium"):
                                                           return "delegation_not_permitted_for_risk"
```

It derives self-approval from identity, binds the grant to this specific proposal and target, enforces a risk ceiling, and **requires human confirmation for high or critical risk**. Human confirmation is what `require_external_verification` means doctrinally.

**So `decision_overwrite`'s discharge is legitimate.** It has earned external verification and is expressing it through `review_satisfied=True` because that is the only channel `policy` offers.

## 2. The actual defect, restated

`policy._apply_review` cannot tell `decision_overwrite`'s human-confirmed, proposal-bound, risk-ceilinged grant from the literal string `"i-said-so"`. Both arrive as `review_satisfied=True` plus a non-empty `approval_refs`, and both discharge `require_external_verification` to `allow_with_ledger`.

The defect is not a bypass. It is that **the policy layer has no channel for verified authority**, so legitimate authority and pure assertion are indistinguishable at the point of decision.

This also explains the apparent inconsistency with `evaluate_pama_with_reusable_grant:397`, which refuses to discharge anything but `REQUIRE_REVIEW`. Both stances are correct for their evidence class: a reusable grant is a *review* precedent and should never satisfy external verification; an `AuthorityGrant` carrying `HUMAN_CONFIRMATION` should. They differ because the evidence differs — and neither can say so in the `Proposal`.

## 3. What Loop 5 and Loop 6 already built toward this

- Loop 5 added `Decision.review_discharge`, recording `asserted` on every discharge. Provenance is visible on the *output*.
- Loop 6 built the verified-evidence machinery for grants, and established the pattern: verification compares against a term the presenter does not write.

The missing piece is on the *input* side: a way for a caller with genuine verified authority to say so in a form `policy` can check, rather than assert.

## 4. The trap this cycle must avoid

The obvious move is a `Proposal` field such as `review_evidence_verified: bool`. **That would be a fourth caller-asserted boolean**, which is the exact pattern this program has now removed three times. It would let `"i-said-so"` become `"i-said-so", verified=True`.

Whatever carries verified authority into `policy` must not be a boolean the proposer sets.

## 5. Design space (for the plan, not decided here)

- **(a) Refuse external-verification discharge in `evaluate`, and add an explicit entry point** taking a verification artifact — mirroring `evaluate_pama_with_reusable_grant`, which already has exactly this shape for the review case. `decision_overwrite` calls the new entry point with its validated grant. Ordinary `evaluate` can then never discharge external verification, so `"i-said-so"` is capped at `require_review`.
- **(b) Carry a verification callable/artifact on the `Proposal`** that `policy` invokes. More flexible, but puts an executable in a data object and widens the public type — Sprint 4's territory.
- **(c) Leave external verification dischargeable and rely on `Decision.review_discharge` for detection.** Rejected as a candidate: it is detection where prevention is available, and Loop 5 already shipped the detection half.

(a) is the shape most consistent with what the repository already does.

## 6. Blast radius, measured

Four sites discharge `require_external_verification` by assertion (Loop 5 instrumentation, re-derived):

| Site | Disposition under (a) |
|---|---|
| `test_decision_overwrite.py:145` | routes through the new entry point once `decision_overwrite` does |
| `test_decision_overwrite_fixtures.py:121` | same |
| `test_deletion_authority.py:79` | **this program's own Loop 4 fixture** — asserts `permanent_deletion/critical`; would need to express verified authority or drop to a review-requiring risk class |
| `test_deletion_authority.py:106` | same |

The 74 `require_review` discharges are **unaffected** by (a): capping external verification does not touch them. That leg stays open and is not this cycle's scope.

**Honest note on the last two rows.** This program has held "no prior test amended" as a discipline across six loops. Those two tests are its own, written in Loop 4, and they use assertion to reach a `permanent_deletion/critical` delete. Under (a) they must change. That is a legitimate amendment — the behaviour they depended on is being deliberately removed — but it must be declared in the plan and in the seal rather than done quietly, because "no prior test amended" has been used as evidence in five seals and its first exception should be visible.

## 7. Risk grade

**L3.** Removes an existing discharge path on the authority evaluator.

## 8. Next

`/qor-plan`.
