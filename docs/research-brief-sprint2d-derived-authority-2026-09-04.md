# Research Brief: Sprint 2d — derived authority in the review discharge

**Date**: 2026-09-04
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 5.
**Gap**: GAP-ARCH-04.

## 1. The defect, precisely

`policy._apply_review` (`policy.py:212-226`):

```python
if not proposal.review_satisfied:
    return outcome, []
if not proposal.approval_refs or proposal.approves_own_authority:
    return outcome, ["review claimed without an external approval record"]
return ALLOW_WITH_LEDGER, [f"review discharged by {list(proposal.approval_refs)}"]
```

Probe:

```
Baseline, no asserted review:
   scope_expansion/high        -> require_external_verification
   permanent_deletion/critical -> require_external_verification
   policy_mutation/critical    -> require_external_verification

With review_satisfied=True and approval_refs=('i-said-so',):
   all three -> allow_with_ledger
```

The strictest non-blocking outcome collapses to `allow_with_ledger` on the string `"i-said-so"`. `require_review` and `require_external_verification` become the same thing under assertion, which erases the distinction the decision table exists to draw.

**The invariant is checked, but only against a boolean the proposer sets.** With `actor_id="agent:x"` and `approval_refs=("agent:x",)` — the actor approving itself, in plain sight — the outcome is `allow_with_ledger`. Setting `approves_own_authority=True` correctly yields `block`, so the check works; nothing derives it, so nothing reaches it.

The function's own docstring states the invariant the code does not enforce:

> Review is satisfied by an approver, never by the proposer.

`actor_authority_resolved` defaults `True`, so the M-AUTH block is skipped unless a caller volunteers otherwise; `approves_own_authority` defaults `False`.

## 2. The fix already exists in this repository, twice

This is the finding that makes the cycle small, and it matches the deep audit's own remediation note ("generalize verified-grant pattern; derive self-approval from identity").

**Identity-derived self-approval — `decision_overwrite.py:171`:**

```python
approves_own_authority=grant.principal_id == proposal.proposing_actor,
approval_refs=(grant.grant_id,),
```

It **derives** the flag from identity rather than accepting an assertion, and the approval ref is a validated grant's id rather than a free string. Exactly the control `_apply_review` needs, already written.

**Verified-versus-unverified provenance — `enforcement_evidence._approval_status:61-80`:**

```python
if approval_verification is None:
    return approval_evidence_ref, "unverified" if approval_evidence_ref else "absent"
...
if approval_verification["input_identity"] != composition["input_identity"]:
    raise ValueError(...)
```

It distinguishes an approval *reference* from a *verified* approval, and cross-checks identity relationally. `policy` has no equivalent notion: a discharge is a discharge, and the receipt cannot say what it rested on.

So ARCH-04 is generalizing two in-repo patterns into `_apply_review`, not inventing a control.

## 3. Blast radius, measured rather than estimated

96 `Proposal(` construction sites across 73 files; 24 files assert `review_satisfied=True`. The deep audit's counts (82/65/37) have shifted with the tree.

More useful: `_apply_review` was instrumented across a full 912-test run.

| Observation | Count |
|---|---|
| `require_review` discharged on a caller-asserted boolean | 74 |
| `require_external_verification` discharged on a caller-asserted boolean | **4** |
| **Self-approvals reaching a discharge** | **0** |

**Deriving self-approval from identity therefore has zero blast radius — measured, not argued.** Nothing in 912 tests presents an actor id inside its own approval refs.

The four external-verification discharges, identified individually:

| Site | Proposal | Refs |
|---|---|---|
| `test_decision_overwrite.py:145` | `decision_overwrite/high` | `('grant:human',)` |
| `test_decision_overwrite_fixtures.py:121` | `decision_overwrite/high` | `('grant:fixture-human',)` |
| `test_deletion_authority.py:79` | `permanent_deletion/critical` | `('approver:1',)` |
| `test_deletion_authority.py:106` | `permanent_deletion/critical` | `('approver:1',)` |

Two are `decision_overwrite`, which routes a **validated grant** through the asserted boolean — legitimate authority expressed through an untrustworthy channel. Two are this program's own Loop 4 test scaffolding.

## 4. What this cycle should and should not do

**Should: derive self-approval (§2 pattern one).** Zero blast radius, closes the hole the docstring already claims is closed, generalizes `decision_overwrite.py:171`.

**Should: record discharge provenance (§2 pattern two).** Today a receipt says `review discharged by ['i-said-so']` and cannot distinguish that from a discharge backed by a verified grant. Adding an `asserted` / `verified` distinction to the decision makes all 74 assertion-only discharges visible in the evidence surface without breaking any of them.

**Should not: require verified evidence yet.** Tightening `require_external_verification` to reject assertion-only discharge touches only four sites, which is tempting. But two of them are `decision_overwrite` presenting a *validated* grant — they would have to re-express that authority through a carrier that does not exist yet. That carrier is exactly the Loop 6 work the operator has now decided (option C: bind to independently-held ratification evidence, with the requirement that at least one term come from a store the presenter cannot write).

Sequencing matters here: **Loop 5 makes provenance visible; Loop 6 makes it required.** Doing the second first would force legitimate callers to fake the channel, which is how a control acquires a workaround that outlives it.

## 5. Partial closure — stated so the seal cannot overclaim

After this cycle GAP-ARCH-04 remains **open**. Closed: the self-approval leg. Not closed:

- `review_satisfied=True` plus any non-empty `approval_refs` still discharges `require_review`, 74 times in the suite.
- `require_external_verification` is still dischargeable by assertion.
- `actor_authority_resolved` still defaults `True`.
- `crossing.py:107` and `scope_governance.py:328` still inherit the discharge.

## 6. Risk grade

**L3.** The authority discharge on the write path, with a measured self-approval bypass of the strictest non-blocking outcome.

## 7. Next

`/qor-plan`.
