# Memory Economics and Budget Policy

## Purpose

Agent memory has costs. Storage is the cheapest of them. The expensive budgets are context, retrieval, compute, attention, and governance review — and a memory architecture that ignores them will be "correct" right up until it is unusable.

This document defines the budget dimensions, how budget pressure is allowed to influence decay, recall, and context assembly, and — critically — the boundary: **budget pressure shapes priority; it never manufactures authority.** Cost may decide what to look at first. It may not decide what is true, what is durable, or what may be deleted.

## Budget dimensions

| Budget | What it limits | Typical pressure signal |
|---|---|---|
| Context budget | tokens/slots available to assemble for one decision | assembly overflow, truncation frequency |
| Storage budget | retained bytes per tier, tenant, or horizon | tier occupancy, growth rate |
| Retrieval budget | candidate-generation and admission work per query | query latency, candidate fan-out |
| Compute budget | scoring, consolidation, and re-evaluation cycles | estimator queue depth |
| Attention budget | what an agent (or human) can act on per episode | admitted-but-unused rate |
| Governance review budget | human/authoritative review capacity | review queue depth, latency |

Budgets are declared per scope (tenant, memory type, consequence class), not globally averaged — a shared global budget is how one noisy tenant starves another's governance queue.

## How budget affects decay and recall

Budget-aware behavior enters through the channels that already exist — decay pressure ([`03-scoring-and-decay.md`](03-scoring-and-decay.md)), recall planning ([`26-governed-recall-planner.md`](26-governed-recall-planner.md)), and forgetting modes ([`28-retention-deletion-and-tombstones.md`](28-retention-deletion-and-tombstones.md)) — never as a new bypass around them.

Permitted budget effects:

```text
storage pressure   -> increased decay pressure -> earlier demotion to archive tiers
retrieval pressure -> narrower candidate generation, cheaper retrieval modes first
context pressure   -> stricter admission ranking among ALREADY-authorized memory
compute pressure   -> deferred re-scoring of low-consequence memory
review pressure    -> longer queues, conservative interim outcomes
```

Prohibited budget effects:

```text
storage pressure   -> permanent deletion without the doc 28 authority path
context pressure   -> dropping an applicable policy or scope filter to save tokens
retrieval pressure -> skipping admission governance for "cheap" candidates
review pressure    -> auto-approving queued mutations to drain the queue
any pressure       -> lowering certification, PAMA, or sensitivity requirements
```

The last line is the doctrine boundary: a budget crisis escalates to policy, which may *explicitly* change operating points under authority. Pressure never silently rewrites them.

## High-value low-frequency memory

Frequency-driven economics systematically undervalue the memory that matters most at the worst moment: incident postmortems, rarely-triggered compliance rules, failure memories, disaster-recovery knowledge.

Requirements:

- Value is multi-dimensional: consequence-of-absence counts, not just access frequency. A memory whose absence is expensive is valuable however rarely it is touched.
- Such memory is marked with a durability dimension (e.g. `consequence_of_absence`) that decay pressure respects; access-count starvation must not demote it out of reach.
- The access-spam trap is the mirror image: high frequency must not inflate value ([`../fixtures/access-spam-junk.json`](../fixtures/access-spam-junk.json)). Both directions are calibration obligations under [`09-calibration-protocol.md`](09-calibration-protocol.md).

## Cost-aware context assembly

Context assembly optimizes within authorization, in this order:

1. **Obligations first.** Applicable policies, safety constraints, and scope filters are not rankable against cost — they are admission preconditions per [`36-policy-as-memory.md`](36-policy-as-memory.md).
2. **Then value density.** Among authorized candidates, rank by expected decision value per token: deduplicate, prefer certified summaries with intact provenance refs over raw duplicates, prefer scoped precision over bulk.
3. **Truncation is visible.** If budget forces omission of authorized, relevant memory, the assembly records what was omitted and why; a silently truncated context misrepresents what the agent knew.
4. **Compression preserves provenance.** Summarization to save tokens keeps source refs (the summary-as-authority anti-pattern of `04-governance-and-pama.md`); a cheap summary that launders away provenance is a threat, not a saving.

## The verification budget

The budgets above meter storing, recalling, and reviewing memory. There is a cost they do not capture: the cost of *earning the right to ask*. Gathering corroboration for a promotion proposal, running conflict and trap checks, assembling the evidence bundle a certifier will accept — the evidence-sufficiency step has its own compute, retrieval, and attention price, paid before any gate is reached.

Left unmodeled, this budget fails in two opposite directions:

```text
under-verification  verification feels expensive -> proposals arrive under-evidenced
                    -> gates reject or, worse, reviewers absorb the missing work
over-verification   sufficiency is undefined -> agents gather evidence indefinitely
                    -> valuable candidates never reach the gate at all
```

Both are budget failures wearing epistemic costumes. The requirements:

- **Sufficiency is a declared operating point, not a feeling.** Policy states, per mutation type and risk class, what an adequate evidence bundle contains — so "have I gathered enough to ask?" is a checklist lookup, not an open-ended judgment an agent re-litigates under pressure.
- **Verification cost is metered and attributed** like any other budget dimension: per proposal, per source, per estimator. A proposal's cost trail is part of its receipt.
- **Sufficiency floors are load-bearing against flooding.** The evidence floor is what makes promotion-queue flooding (threat 19 of [`15-memory-threat-model.md`](15-memory-threat-model.md)) expensive for the attacker instead of for the reviewer: candidates pay the verification cost before consuming review capacity.
- **Verification pressure escalates like all pressure.** If the declared sufficiency floor is chronically unaffordable, that is a policy problem solved by a versioned policy mutation (adjusting floors or capacity) — never by agents quietly lowering their own evidence standards, and never by floors silently rising until nothing promotes.
- **Deferral for evidence is bounded.** `collect_more_evidence` outcomes carry a cost budget and a review-by point, so evidence-gathering cannot become either infinite postponement or infinite spend.

Metrics for this budget join the scorecard:

```text
verification_cost_per_consequential_proposal   # by mutation type and risk class
evidence_sufficiency_shortfall_rate            # proposals arriving below the declared floor
verification_abandonment_rate                  # candidates that never reached the gate for cost reasons
```

## Budget pressure and PAMA review paths

Governance review capacity is a budget like any other, and the failure mode is predictable: queues back up, and someone proposes auto-approval.

Rules:

- **Queue pressure produces conservative interim state, never interim approval.** A promotion waiting on review stays in Pending Verification; a deletion waiting on review does not happen; an expiring delegation is not auto-renewed.
- **Triage is governed.** Review ordering may be prioritized by consequence (risk class, blast radius, reversibility) — that is proportionality, and it is legitimate. Review *skipping* is not.
- **Load-shedding is a policy decision.** If review capacity is chronically insufficient, the fix is an explicit policy mutation (raising thresholds, narrowing what requires review) through the full authority path of [`33-pama-decision-table.md`](33-pama-decision-table.md) — visible, versioned, reversible.
- **Deferral has a budget too.** `collect_more_evidence` and `defer` outcomes carry review-by obligations so unbounded deferral does not become de facto denial or de facto rot.

## Quality metric recommendations

Budget behavior is measurable and belongs in the quality scorecard of [`32-memory-quality-metrics.md`](32-memory-quality-metrics.md):

```text
context_truncation_rate            # assemblies that omitted authorized relevant memory
obligation_omission_rate           # assemblies missing an applicable policy/constraint (target: 0)
high_value_low_frequency_loss_rate # consequence-marked memory demoted below recall reach
review_queue_latency               # by risk class
pressure_induced_escalation_rate   # budget events that escalated to policy vs. silently degraded
storage_pressure_deletion_rate     # deletions initiated under pressure (each must carry authority)
admitted_but_unused_rate           # attention-budget waste signal
```

`obligation_omission_rate` is a guardrail metric: any nonzero value is a failure, not a trade-off. The others are optimization metrics with declared operating points.

## Conformance fixture recommendations

| Case | Expectation |
|---|---|
| Storage pressure proposes permanent deletion | routed through retention/dependency/authority checks — [`../fixtures/irreversible-deletion-under-uncertain-utility.json`](../fixtures/irreversible-deletion-under-uncertain-utility.json) pattern with budget as the utility signal |
| Context overflow with applicable policy present | policy admitted; discretionary memory truncated; truncation recorded |
| Review queue saturation | queued mutations remain in conservative state; no auto-approval; triage order reflects consequence |
| Rare critical memory under decay pressure | consequence-of-absence dimension holds it above the demotion floor |
| Budget-driven threshold change | appears only as a versioned policy mutation with approval refs, never as drift |

## Doctrine

Budgets decide what the system attends to. Governance decides what the system may do.

Economics is allowed to make memory slower, smaller, cheaper, and better-prioritized. It is never allowed to make memory less governed — scarcity escalates to authority; it does not substitute for it.
