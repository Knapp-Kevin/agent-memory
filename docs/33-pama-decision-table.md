# PAMA Decision Table

## Purpose

This document turns the Agent Memory specialization of PAMA in [`04-governance-and-pama.md`](04-governance-and-pama.md) into an inspectable decision table: requested operation and operational risk map to a minimum authority outcome, and named modifiers raise or lower that minimum under defined conditions.

PAMA itself is native Agent Memory doctrine authored by Kevin R. Knapp. Its foundational taxonomy is defined in [`pama/README.md`](pama/README.md): **M0-M5 target classes**, lifecycle strength, **A0-A5 downstream authority classes**, adaptive charters, and proportional handling lanes.

The table below is therefore **one policy projection of PAMA, not the definition of PAMA**.

The table is policy data, not code. An implementation may encode it as configuration, rules, or a policy engine, but the mapping must satisfy the authority resolution invariant: for fixed committed inputs, current state, and policy version, the resulting authority envelope is deterministic or formally bounded.

This document implements the decision-table requirement of [`adr/ADR-004-pama-controls-mutation-authority.md`](adr/ADR-004-pama-controls-mutation-authority.md).

## Required PAMA dimensions before table lookup

A compliant implementation must classify more than an operation name and generic risk score.

Before resolving this table, the request should establish at least:

```text
target_class: M0 | M1 | M2 | M3 | M4 | M5
lifecycle_strength
requested_operation
requested_downstream_authority: A0 | A1 | A2 | A3 | A4 | A5
scope
reversibility
actor / charter
operational_risk
```

These dimensions are orthogonal.

For example:

- `promotion` is an **operation**;
- an M3 reusable procedure is a **target class**;
- `Promoted` is a **lifecycle strength**;
- A1 recommendation influence is a **downstream authority ceiling**.

Calling all four of these a "mutation class" makes the policy easier to implement incorrectly, which is a charming quality in diagrams and a terrible one in governance.

A high-confidence M3 capability promoted successfully under this table does not gain A4 external-action authority unless a separate PAMA decision authorizes that authority.

## How to read the table

Outcomes are ordered by strictness:

```text
allow < allow_with_ledger < require_review < require_external_verification < block
```

- A cell is the **minimum** outcome for that requested operation at that operational risk class. Policy may always be stricter; it must not be weaker.
- Target class, lifecycle strength, downstream authority, scope, sensitivity, reversibility, and actor authority may escalate the base cell.
- Modifiers move the outcome along this ordering. A modifier can only relax an outcome when the table row explicitly marks it relaxable.
- `abstain`, `quarantine`, and `collect_more_evidence` are lateral outcomes: they defer the decision without granting authority. A deferral never counts as satisfaction of a review or verification requirement.
- `block` is absorbing. No modifier, score, or estimator output relaxes a `block` produced by a prohibited-action rule.

## Foundational class floors

The operation table must not undercut PAMA's target and downstream-authority semantics.

| PAMA dimension | Minimum consequence rule |
|---|---|
| **M0** execution-local context | may be transient when it cannot escape local context or create durable/external effects |
| **M1** low-risk preference | may be retained tentatively when visible, scoped, reversible, and barred from higher authority |
| **M2** operational association | meaningful recommendation influence requires evidence and correction/conflict handling |
| **M3** reusable capability | promotion requires validation, versioning, authority ceiling, rollback/revocation, and monitoring |
| **M4** shared or identity-bearing state | requires authoritative evidence and controlled review appropriate to consequence |
| **M5** governance/security/autonomous authority | requires explicit authorized review; proposing agent may not self-approve |
| **A4** external action | never granted merely because a memory or capability is reliable |
| **A5** governance change | never granted through a lower-authority mutation pathway |

If a base operation/risk cell is weaker than one of these floors, the PAMA class floor wins.

## Base decision table

Operational mutation types are defined in `04-governance-and-pama.md`. Risk classes follow the same doc: low, medium, high, critical.

| Mutation operation | Low | Medium | High | Critical |
|---|---|---|---|---|
| Runtime assembly | allow_with_ledger | allow_with_ledger | require_review | require_review |
| Score adjustment | allow_with_ledger | allow_with_ledger | require_review | block |
| Link creation | allow_with_ledger | allow_with_ledger | require_review | require_review |
| Link deletion | allow_with_ledger | require_review | require_review | require_external_verification |
| Correction | require_review | require_review | require_review | require_external_verification |
| Decision overwrite | require_review | require_review | require_external_verification | require_external_verification |
| Domain schema mutation | require_review | require_review | require_external_verification | require_external_verification |
| Promotion | allow_with_ledger | require_review | require_review | require_external_verification |
| Crystallization | require_review | require_review | require_external_verification | require_external_verification |
| Pruning | allow_with_ledger | allow_with_ledger | require_review | require_external_verification |
| Permanent deletion | require_review | require_review | require_external_verification | require_external_verification |
| Scope expansion | require_review | require_review | require_external_verification | block |
| Policy mutation | require_review | require_external_verification | require_external_verification | require_external_verification |

Operations admitted by `pama-decision.schema.json` but deliberately absent from
this table: `capability_promotion`, `authority_change`, and `other`. They carry no
base cell by decision, not by omission -- they resolve through the reference
implementation's conservative `require_review` fallback
(`reference/agentmem_ref/core/policy.py` `_base_outcome`), which is the correct floor
for an operation whose risk profile this table has not characterised. Removing the
fallback would turn an unknown operation into a `KeyError` on the authority path.

`Domain schema mutation` was introduced by ADR-032 after this table was first
written; its cells are transcribed from the reference implementation, which has
carried them since.

## Discharging a decision

An outcome of `require_review` or `require_external_verification` is not final:
an external authority can satisfy it. What that authority has to present differs
by outcome, and the difference is enforced rather than advisory.

**`require_review`** is discharged by an approval the proposer did not give.
The reference implementation accepts a caller-asserted `review_satisfied` with a
non-empty `approval_refs`, and records `review_discharge: "asserted"` on the
resulting decision so a reader can see what the discharge rested on. Self-approval
is derived from identity -- an actor naming itself among its own approval refs is
`block`, regardless of what it asserts about itself.

**`require_external_verification` cannot be discharged by assertion at all.**
It requires an attestation bound to the specific proposal, naming a verifier
distinct from the actor, carrying `human_confirmation` for high or critical risk,
and declaring a risk ceiling the proposal does not exceed. Decisions discharged
this way record `review_discharge: "verified"`.

The distinction matters because without it the two outcomes collapse into one:
an asserted boolean plus any string discharged both, so the table's strictest
non-blocking cell became indistinguishable from its second-strictest. Reference
implementation: `policy.evaluate_with_external_verification` and
`policy.ExternalVerification`.

**Limit, stated plainly.** The attestation is constructed by the caller, so it
proves the caller performed the checks it claims, not that a verifier exists.
What it removes is the assertion path -- ordinary evaluation can no longer reach
the discharge. Binding an attestation to evidence the presenter cannot write is
the same problem `reusable_grants.RatificationRegistry` solves for grants, and
applying that pattern to attestations remains open work.

Reading notes:

- Score adjustment at critical risk is `block` because a score change on identity, credential, compliance, or safety-boundary memory is not merely a score change; it is an attempt to route around governance. Re-evaluation of such memory goes through correction or policy mutation instead.
- Decision overwrite is distinct from correcting a decision record. Fixing a typo or evidence link may be a correction; changing what was decided is a supersession/reversal authority event. Low/medium overwrite requires explicit review. High/critical overwrite requires external verification. The durable-decision profile defines which authority records may satisfy those outcomes for decision memory.
- A prior human-confirmed durable decision is not downgraded by agent agreement, repetition, confidence, or a historical approval. Its overwrite requires a fresh authority transition under [`profiles/durable-decision-memory-profile.md`](profiles/durable-decision-memory-profile.md).
- Scope expansion at critical risk is `block` because cross-tenant expansion of critical-class memory has no autonomous path. It requires a policy-level decision, which is a policy mutation, not a scope-expansion request.
- `require_external_verification` means verification by an authority outside the requesting component: a human approver, an independent certification service, or an equivalently authoritative system. The requesting estimator can never be its own verifier.
- Policy mutation never resolves below `require_review` at any risk class, and human or equivalently authoritative approval remains the default expectation per `04-governance-and-pama.md`.
- M5 and A5 requests must not be relabeled as lower-risk operations merely to reach a weaker row.

## Modifier rules

Modifiers apply after the base cell is selected, in the order listed. Escalating modifiers accumulate; the outcome is the strictest produced.

### Escalating modifiers

| Modifier | Condition | Effect |
|---|---|---|
| M-TARGET | PAMA target class imposes a stricter floor than the base cell | raise to the target-class floor |
| M-AUTHORITY | requested downstream authority A4/A5 exceeds the authority normally associated with the mutation | raise to explicit review or external verification; A5 never self-approved |
| M-IRREV | mutation is irreversible or destroys its own rollback path | raise to at least require_review; at high/critical risk raise to at least require_external_verification |
| M-EVID | evidence quality below policy floor for this mutation type | raise one step and require collect_more_evidence before re-evaluation |
| M-DISPUTE | target memory is disputed or contradiction pressure is material | raise to at least require_review |
| M-DISAGREE | material estimator disagreement on a required input | raise one step |
| M-OOD | out-of-distribution or out-of-calibration-scope signal on a required estimate | raise to at least require_external_verification for promotion, crystallization, deletion, and scope expansion |
| M-CERT | certification missing, expired, or revoked where the mutation type requires it | block crystallization; raise promotion to require_review |
| M-AUTH | actor authority cannot be reconstructed | block |
| M-POLICY | policy version missing or ambiguous | block for high/critical; require_review otherwise |
| M-SCOPE | target actor, tenant, or purpose is unclear | block any sharing or scope expansion; raise others to require_review |
| M-EVIDENCE-DESTRUCTION | mutation would remove evidence referenced by audit, dispute, or hold | block until the retention conflict is resolved per `28-retention-deletion-and-tombstones.md` |

### Relaxing modifiers

Relaxation exists so reversible, well-evidenced, narrow mutations are not buried under review queues. It is deliberately harder to trigger than escalation.

| Modifier | Condition | Effect |
|---|---|---|
| R-REV | mutation is cheaply reversible with a verified rollback path and a reversible tombstone | may lower require_review to allow_with_ledger, only for rows marked relaxable below |
| R-DELEG | acting under an explicit, unexpired, in-scope delegation record | may lower one step, never below allow_with_ledger, never for policy mutation or scope expansion |

Relaxable rows: link deletion (low/medium), pruning (high), promotion (medium). No other cell is relaxable. Decision overwrite, crystallization, permanent deletion, scope expansion, policy mutation, M5 governance/security authority, and A5 governance changes are never relaxable through these modifiers.

Reversibility works in both directions and asymmetrically: irreversibility escalates everywhere, reversibility relaxes only where the table says so. A verified rollback path is a precondition for relaxation, not evidence of safety.

### What modifiers never do

```text
high confidence        -> never relaxes any outcome
high saturation        -> never relaxes any outcome
repetition / access    -> never relaxes any outcome
validated capability   -> never expands its authority ceiling by itself
prior similar approval -> never substitutes for current authority
deferral outcomes      -> never satisfy review or verification
```

Confidence is an input to evidence quality at most. It has no direct lane to authority.

## Worked mutation examples

Each example gives the request, the resolved outcome, the before and after state, and the ledger requirement. Receipts follow [`../schemas/decision-receipt.schema.json`](../schemas/decision-receipt.schema.json); events follow [`30-memory-observability-and-audit-events.md`](30-memory-observability-and-audit-events.md).

### 1. Score adjustment

Request: decay pass lowers sigma on a task note after two weeks without meaningful reuse.

- PAMA shape: M2 operational association, reinforced, A1 ceiling, score-adjustment operation, low risk.
- Base cell: score adjustment × low = `allow_with_ledger`. No modifiers trigger.
- Before: `sigma 0.58`, state `reinforced`. After: `sigma 0.44`, state `reinforced`.
- Ledger: score-adjustment event with estimator refs, estimator version, and decay-profile ref. No receipt approval refs required.

### 2. Link creation

Request: planner proposes an evidence-backed relation between a decision memory and the commit that implemented it.

- Base cell: link creation × medium = `allow_with_ledger`. M-EVID does not trigger: both endpoints carry provenance and the relation cites the commit as evidence.
- Before: no relation. After: `implements` edge with evidence ref.
- Ledger: graph-mutation event recording both endpoint ids, relation type, and evidence refs.

### 3. Link deletion

Request: remove a `supports` edge that a retracted source had justified.

- Base cell: link deletion × medium = `require_review`. R-REV applies (edge restoration is cheap, tombstone retained): relaxed to `allow_with_ledger`.
- Before: edge present, source marked retracted. After: edge tombstoned, not destroyed; dependent saturation re-scored.
- Ledger: graph-mutation event plus tombstone ref; the retraction that motivated the deletion is cited as evidence.

### 4. Correction

Request: user corrects a stored preference that was inferred wrongly.

- PAMA shape: M1 preference, A1 ceiling, correction operation, high handling sensitivity because the value belongs to the user.
- Base cell: correction × high = `require_review`. The user's own correction with explicit approval satisfies review; M-AUTH does not trigger because the actor is the memory's owner principal.
- Before: `preference: weekly summary`, state `crystallized`, dispute open. After: `preference: daily summary`, state `corrected`, prior value preserved as history with supersession link per `18-temporal-causality-layer.md`.
- Ledger: correction event with approval ref (the user's action), before/after state, and rollback path. The old value is superseded, not erased.

### 5. Promotion

Request: recurring, corroborated project decision reaches candidate threshold; system proposes promotion toward durable state.

- Base cell: promotion × high (durable decision) = `require_review`. M-DISAGREE does not trigger; trap-class check passes.
- Before: state `reinforced`, `sigma 0.86`, certification absent. After: state `pending_verification`. Not durable yet.
- Ledger: lifecycle-transition event with PAMA inputs, permitted-action set, and selected action. Receipt records that review is the binding step; saturation alone did not promote.

### 6. Crystallization

Request: the reviewed decision from example 5, now certified, requests crystallization.

- Base cell: crystallization × high = `require_external_verification`. Satisfied by the certification gate: certifier is independent of the proposing estimator. M-CERT does not trigger.
- Before: state `pending_verification`, certification `pass`, dispute clear, scope defined. After: state `crystallized`, bound to evidence set, policy version, estimator context, and scope of approval.
- Ledger: crystallization receipt binding certification ref, approval refs, scope, and rollback path (demotion per `31-recovery-rollback-and-replay.md`). If certification were missing: blocked, regardless of sigma.

### 7. Pruning

Request: eviction pass proposes pruning a stale runtime trace from active recall.

- Base cell: pruning × low = `allow_with_ledger`. M-EVIDENCE-DESTRUCTION does not trigger: nothing references the trace as evidence.
- Before: state `stale`, in active recall. After: state `pruned`, reversible tombstone retained per `28-retention-deletion-and-tombstones.md`; content recoverable within the retention window.
- Ledger: pruning event with tombstone ref. Contrast: the same request against a memory cited in an open dispute is blocked by M-EVIDENCE-DESTRUCTION until the hold resolves, see `fixtures/pruning-with-audit-preservation.json`.

### 8. Reusable capability authority

Request: a validated troubleshooting procedure has been promoted as an M3 capability with an A1 recommendation ceiling and now requests shell execution.

- Capability validation remains valid.
- Requested authority changes from A1 to A4, so M-AUTHORITY escalates.
- The existing capability promotion does not authorize execution.
- Result: `require_review` or stricter policy outcome for the A4 request; if the actor lacks authority to request that expansion, `block`.
- Ledger: separate authority decision receipt. The original capability artifact remains unchanged until the new authority decision resolves.

### 9. Policy mutation

Request: agent proposes lowering the candidate threshold from 0.80 to 0.70 because "too few memories are promoting."

- PAMA shape: M5 governance mutation, A5 downstream authority.
- Base cell: policy mutation × high = `require_external_verification`. No relaxation path exists for policy mutation, M5, or A5.
- Before: `candidate_threshold 0.80`, policy version `p-14`. After, only if approved by human or equivalently authoritative review: `candidate_threshold 0.70`, policy version `p-15`, prior version retained for replay.
- Ledger: policy-mutation receipt with approval refs, both policy versions, and effective time. An agent observing its own promotion rate is an estimator; an estimator proposing to widen its own authority is exactly what this row exists to stop.

### 10. Durable decision overwrite

Request: an agent proposes replacing a durable repository decision that was previously human-confirmed.

- PAMA shape: M4 shared/commitment-bearing state, A3 local workflow effect, decision-overwrite operation, high risk.
- Base cell: decision overwrite × high = `require_external_verification`.
- The agent proposal, its confidence, and agreement from other agents are evidence only. They do not satisfy the external-verification requirement.
- A fresh human confirmation bound to the exact proposal, target, scope, actor eligibility, risk ceiling, state snapshot, and validity window may satisfy the decision-memory authority gate.
- PAMA is then evaluated and may still block for an independent reason such as a required isolation-domain mismatch.
- On success, the prior decision remains historical, the replacement is appended, and the supersession/receipt chain records the exact authority transition. See [`../fixtures/durable-decision-human-confirmed-overwrite.json`](../fixtures/durable-decision-human-confirmed-overwrite.json).

## Interaction with lifecycle gates

The table composes with, and never replaces, the promotion and crystallization gates of `04-governance-and-pama.md`:

```text
can_promote     requires pama_outcome in [allow, allow_with_ledger, require_review]
can_crystallize requires pama_outcome in [allow, allow_with_ledger] and certification pass
```

A table outcome of `require_review` therefore admits a memory to Pending Verification at most. Crystallization additionally requires the review to have resolved and certification to pass. The decision table decides authority; the gates decide sequence.

Decision overwrite has its own sequence because the proposal is already about changing a durable decision rather than promoting a candidate memory:

```text
overwrite proposal
  -> decision-memory authority validation
  -> PAMA outcome
  -> append-only supersession or refusal
```

## Conformance cases

| Case | Expectation | Fixture |
|---|---|---|
| High-confidence false memory requests promotion | confidence does not relax the promotion row | [`../fixtures/high-confidence-false-promotion.json`](../fixtures/high-confidence-false-promotion.json) |
| Sigma jitter at the candidate threshold | outcome stable under M-DISAGREE and hysteresis; no churn | [`../fixtures/threshold-jitter.json`](../fixtures/threshold-jitter.json) |
| Unauthorized actor requests correction | M-AUTH blocks regardless of estimate quality | [`../fixtures/unauthorized-mutation-attempt.json`](../fixtures/unauthorized-mutation-attempt.json) |
| Deletion proposed from predicted low utility | permanent-deletion row plus M-IRREV; utility estimate cannot authorize | [`../fixtures/irreversible-deletion-under-uncertain-utility.json`](../fixtures/irreversible-deletion-under-uncertain-utility.json) |
| Delegated actor acts after delegation expiry | R-DELEG does not apply; expired delegation escalates, not relaxes | [`../fixtures/expired-delegation.json`](../fixtures/expired-delegation.json) |
| Concurrent conflicting mutation requests | no silent last-writer-wins; second request re-resolves against new state | [`../fixtures/concurrent-conflicting-mutation.json`](../fixtures/concurrent-conflicting-mutation.json) |
| Authority laundering through a permissive path | outcome depends on mutation actually requested, target class, and downstream authority, not the path that carried it | [`../fixtures/authority-laundering.json`](../fixtures/authority-laundering.json) |
| Policy applied under drifted estimator version | M-OOD escalates consequential mutations | [`../fixtures/policy-estimator-version-drift.json`](../fixtures/policy-estimator-version-drift.json) |
| Agent overwrite proposal without authority | proposal remains evidence; current decision does not change | [`../fixtures/durable-decision-agent-proposal.json`](../fixtures/durable-decision-agent-proposal.json) |
| Human-confirmed durable overwrite | exact approval can satisfy review; old decision remains historical | [`../fixtures/durable-decision-human-confirmed-overwrite.json`](../fixtures/durable-decision-human-confirmed-overwrite.json) |
| Stale overwrite proposal | current state mismatch rejects before commit | [`../fixtures/durable-decision-stale-overwrite.json`](../fixtures/durable-decision-stale-overwrite.json) |
| Agent consensus attempts to replace human-confirmed decision | consensus cannot substitute for required human confirmation | [`../fixtures/durable-decision-agent-collusion.json`](../fixtures/durable-decision-agent-collusion.json) |
| Bounded delegated low-risk decision overwrite | exact delegation may satisfy low-risk review only inside its declared bounds | [`../fixtures/durable-decision-delegated-low-risk-overwrite.json`](../fixtures/durable-decision-delegated-low-risk-overwrite.json) |

Additional PAMA-native fixtures should cover:

- M3 capability promoted successfully but blocked from exceeding its A1/A2 ceiling;
- M5 governance change disguised as M2 operational association;
- missing target class treated as unknown consequence rather than low risk; and
- charter mismatch between proposing agent and mutation domain.

## Doctrine

The decision table is one operational projection of PAMA, not a replacement for it.

A cell grants nothing by itself. It states the weakest outcome a compliant policy may return, given committed inputs whose provenance, PAMA class, authority ceiling, and uncertainty are inspectable.

Estimates inform the inputs. Authority comes from PAMA's class boundaries, the table, its modifiers, and the approvals they require, never from the estimate.