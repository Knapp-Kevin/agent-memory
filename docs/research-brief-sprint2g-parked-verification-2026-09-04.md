# Research Brief: Sprint 2g — parked verification state

**Date**: 2026-09-04
**Analyst**: The Qor-logic Analyst
**Program**: ADR-035 build-toward, research-led `/qor-enterprise-auto-dev`. Loop 8.
**Implements**: ADR-037 implementation order **step 1 of 4**, and only step 1.

## 1. Scope, stated first because the order is part of the decision

ADR-037 fixes a rigid order: parked state → evidence qualification and dependence lineage → governed resumption → fail-closed conversion of the 51 callers. **This cycle builds step 1 only.**

Explicitly out of scope, and not to be smuggled in because they are adjacent:

- **Evidence qualification** (R2/R3, step 2). No dependence-group logic, no evidential-class ranking.
- **Resumption** (step 3). Nothing in this cycle may resume a parked proposal. The parked record is written and read; it is not discharged.
- **Fail-closed conversion** (step 4). `_apply_review` is untouched. Assertion still discharges `require_review` after this cycle, by design.

The temptation is to build resumption while the lifecycle is in hand. ADR-037's ordering exists because a half-built resumption is worse than none: it would let a proposal leave the parked state without the qualification machinery that decides whether it should.

## 2. What exists to generalize

`decision_overwrite.DurableDecisionRegistry` carries the whole lifecycle already (`:127-141`):

```python
def propose(self, proposal: OverwriteProposal) -> OverwriteResult:
    if proposal.proposal_id in self._proposals:
        raise ValueError(f"overwrite proposal already exists: {proposal.proposal_id}")
    self._validate_proposal_shape(proposal)
    event = self._event("memory.decision_overwrite_proposed", proposal, self._now(), status=PENDING)
    result = OverwriteResult(proposal=proposal, status=PENDING, events=[event])
    self._proposals[proposal.proposal_id] = result
    self.events.append(event)
    return result
```

Four properties worth carrying over exactly:

1. **Duplicate proposal ids are refused**, not overwritten — parking is append-oriented like the ratification registry.
2. **Parking emits an event.** It is a governed outcome with evidence, not a silent failure return.
3. **The record holds the decision**, so a later reader knows what was refused and why, without re-deriving it.
4. **Status is explicit** and gates the later transition (`commit` refuses anything not `PENDING`).

This is the fifth control this program has found implemented in one module and absent from the shared evaluator, after derived self-approval, verified/unverified provenance, the ratification registry, and the version-derivation constant.

## 3. What the parked record must carry

From ADR-037 §3: the decision, its unmet criteria, and its correlation identity.

- `proposal_id`, `actor_id`, `target_reference`, `operation`, `risk_class` — identity of what was refused
- the `Decision` — `outcome`, `reasons`, `permitted_actions`, `review_discharge`
- `correlation_id` — so the parked record joins the same evidence chain as the attempt
- `parked_at`, `policy_version` — when, and under what policy

**`permitted_actions` is the remediation route, and it already exists.** `_envelope` returns `("enter_pending_verification", "collect_more_evidence", "defer")` for `REQUIRE_REVIEW`. Recording it on the parked record means the actor is told what it may do, from the same structure that decided it may not proceed.

## 4. Contract-surface findings

**The audit event needs no schema change.** `memory-audit-event.schema.json` constrains `event_type` only as `{"type": "string"}`, so `memory.pending_verification` is legal. It sets `additionalProperties: False`, so the record detail goes under `payload` (`additionalProperties: true`) — the same placement Loop 3 established for `memory.recall`. Existing event types follow a `memory.<verb>` convention, including three from the decision-overwrite lifecycle.

**The parked record itself must not get a schema this cycle.** Adding one is a public contract addition, which belongs to Sprint 4's boundary freeze (#362). The record stays an internal dataclass; the *evidence* it emits is schema-valid. This mirrors Loop 3's decision to add defaulted fields to `AdmissionResult` rather than schema-back it.

**A new module, not the adapter.** `PendingVerificationRegistry` in its own module follows the `DurableDecisionRegistry` precedent and avoids widening `GovernedMemoryAdapter`, which #362 will re-shape.

## 5. Blast radius: near zero, deliberately

Nothing calls the parked state yet. It is opt-in until step 4 flips the gate. So this cycle adds a module and its tests and changes no existing caller — which is what makes it a safe first step and why the order puts it first.

`_apply_review` is not touched, so the 51 assertion sites keep working unchanged.

## 6. Risk grade

**L2.** New isolated module, no existing caller, no schema change, no policy path modified. It is not L1 because the record shape it establishes is what steps 2–4 build on, and a wrong shape here is expensive later.

## 7. Next

`/qor-plan`.
