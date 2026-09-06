# Autonomous Maintenance, Consolidation, and Evidence Fusion

Status: **active exploratory research** under #227 and parent #67. This document is not canonical doctrine.

## Research question

Agent Memory already defines memory metabolism, forgetting, consolidation, semanticization, correction, pruning, scoring, uncertainty, provenance, currentness, and PAMA authority.

The missing question is operational:

> **How can a long-running maintenance actor improve memory structure continuously without turning background execution, estimator confidence, or repeated self-observation into durable authority?**

The answer should permit useful autonomous housekeeping while keeping consequential mutation reconstructable and bounded.

## Primary comparators

### BeliefMem

Primary paper:

- *Belief Memory: Agent Memory Under Partial Observability*, arXiv:2605.05583
- https://arxiv.org/abs/2605.05583

BeliefMem preserves multiple candidate conclusions with probabilities and updates support as observations arrive rather than collapsing partial observations immediately into one deterministic conclusion. The paper uses Noisy-OR-style evidence accumulation and evaluates the resulting memory on agent-memory benchmarks.

Useful challenge for Agent Memory:

```text
uncertain conclusion
!= failed memory
```

A candidate may remain probabilistic and useful before any durable epistemic promotion is justified.

### Zeph BeliefMem implementation

Pinned source inspected for this research:

```text
repository: bug-ops/zeph
commit: 785d8e4a0cf7da36a1b8c438da5f8c81c11d8775
file: crates/zeph-memory/src/graph/belief.rs
```

Zeph implements a distinct pre-commit belief store. Evidence for a candidate graph edge accumulates through Noisy-OR. Crossing the configured threshold returns a promotion candidate, but the caller still performs the committed graph insertion separately through the graph store.

This separation is architecturally valuable:

```text
belief threshold crossed
-> candidate ready for promotion
!= committed graph edge
```

Agent Memory should preserve at least that separation and strengthen it where governance consequence requires more than a threshold.

### Auto-Dreamer

Primary paper:

- *Auto-Dreamer: Learning Offline Memory Consolidation for Language Agents*, arXiv:2605.20616
- https://arxiv.org/abs/2605.20616

Auto-Dreamer separates fast online acquisition from slower offline consolidation. Its consolidator treats a selected memory region and provenance-linked trajectories as read-only evidence, synthesizes a compact replacement set, and supersedes the prior region.

Useful challenge for Agent Memory:

```text
online acquisition
!= offline consolidation
```

A maintenance actor may need broad read access to reason across many episodes while still having tightly bounded write authority.

## Noisy-OR is an estimator, not a governance rule

For independent positive evidence probabilities `p_i`, Noisy-OR computes:

```text
P = 1 - product(1 - p_i)
```

That arithmetic is useful only when its evidence assumptions are visible.

### Independence must be explicit

A source replay, summary, paraphrase, policy-generated restatement, or derivative observation does not become independent evidence merely because it appears as another row.

A governed implementation should group support by independent root or declared dependence group before fusion.

For example:

```text
root A: 0.40
root B: 0.50
-> independent Noisy-OR = 0.70

root A original: 0.40
root A replay:   0.40
root A summary:  0.80
-> still one independent root
```

The exact within-group reducer is an estimator choice. The representation-neutral harness uses the maximum bounded signal per dependence group so duplicate/derived restatements cannot recursively inflate support.

### Challenge evidence remains first-class

Positive support and negative/challenging evidence should not be collapsed into one comforting scalar unless a calibrated estimator explicitly defines that semantics.

A useful evidence record preserves separately:

```text
positive_support
challenge_pressure
independent_support_groups
independent_challenge_groups
estimator/version/configuration
calibration posture
```

A high support score in the presence of material challenge is not a certified truth claim.

### Threshold crossing is not authority

A high fused score may make a memory **eligible for a proposal**. It does not satisfy the PAMA decision that governs the durable consequence.

```text
Noisy-OR >= threshold
-> promotion candidate
-> PAMA / policy
-> allowed | ledger | review | verification | block
```

No threshold is permitted to skip the right side of that sequence.

## Maintenance operation taxonomy

Autonomous maintenance should not receive one universal mutation authority. The batch decomposes into the actual consequences it proposes.

| Maintenance behavior | Existing Agent Memory consequence |
|---|---|
| reweight score / decay | `score_adjustment` |
| add graph relation | `link_creation` |
| remove/tombstone graph relation | `link_deletion` |
| correct current interpretation | `correction` |
| promote candidate/semantic abstraction | `promotion` |
| crystallize stronger durable state | `crystallization` |
| prune active state | `pruning` |
| permanently delete governed content | `permanent_deletion` |
| widen tenant/project/purpose scope | `scope_expansion` |
| alter authority/policy | `policy_mutation` / authority-specific path |
| rebuild non-authoritative indexes/projections | bounded maintenance/runtime operation, no semantic promotion by itself |
| summarize/abstract | derived transformation with provenance; any later promotion is separately governed |
| fuse confidence/belief | estimator evidence; no mutation authority by score alone |
| resolve contradiction | correction/reconciliation path, not majority vote |

This decomposition is preferable to creating a broad `background_maintenance` operation that could hide a more consequential inner mutation.

## Low-consequence pre-authorization

Some maintenance can safely run under explicit standing policy when all relevant boundaries are narrow and reconstructable.

Candidates include:

- reversible score decay;
- rebuilding a non-authoritative index from unchanged current canonical state;
- cache/projection refresh;
- low-risk reversible link cleanup where the decision table permits it;
- emitting proposals without committing them.

Pre-authorization is authority granted by policy for a bounded class. It is **not** authority produced by the maintenance agent itself.

Required conditions include:

```text
known actor / charter
current policy version
exact tenant/project/purpose scope
bounded operation set
bounded target classes
reversibility / rollback
current source evidence
run-level receipt
```

## High-consequence maintenance

The following should not become silent background privilege merely because a scheduler initiated them:

- deleting protected, pinned, disputed, held, or identity-bearing memory;
- semantic consolidation that changes current truth;
- dropping exceptions from a generalized rule;
- cross-tenant/project composition;
- authority-bearing memory promotion;
- policy or delegation changes;
- irreversible deletion;
- migration while source/currentness evidence is stale;
- schema/ontology mutation governed separately under #226/#236.

The existing PAMA consequence remains controlling.

## Concrete missing evidence contract: maintenance-run transaction

Current Agent Memory contracts can authorize the individual mutations, but the repository lacks a reusable evidence contract for an **autonomous maintenance run as a transaction**.

That run needs to prove more than a collection of successful function calls.

A useful maintenance-run record should bind at least:

```text
run_id
maintenance_actor / charter
policy_version
scope / tenant / purpose
cursor_before
input snapshot / source refs
proposal refs
constituent PAMA decision refs
planned operation set
transaction / staging ref
commit status
validation/probe refs
output / supersession / tombstone refs
rollback/quarantine refs
cursor_after
started_at / completed_at
```

### Cursor invariant

The strongest negative case is simple:

```text
maintenance batch fails or rolls back
-> cursor_after == cursor_before
```

The system must not mark evidence as consumed when its corresponding transformation did not commit.

Only after commit and required validation succeeds may the durable processing cursor advance.

### Atomicity invariant

For a multi-object semantic transformation:

```text
all authorized constituent changes commit
or
none become current
```

If the substrate cannot supply strict atomicity, the run needs an explicit compensating/quarantine state and must not report a clean committed outcome until recovery obligations are satisfied.

### Validation invariant

A successful write is not a successful consolidation.

Post-write probes should test the invariants appropriate to the operation, for example:

- critical facts/exceptions still answer correctly after summarization;
- no cross-scope state appears;
- provenance links still resolve;
- old state is superseded rather than silently erased where history must survive;
- deleted/revoked sources were not resurrected by rebuild;
- expected dependent projections were rebuilt or invalidated.

A failed probe should trigger rollback or quarantine, not optimistic cursor advancement.

## Representation-neutral adversarial cases

The executable harness covers:

1. independent positive signals increase fused support;
2. duplicated/replayed evidence does not count as independent support;
3. derived self-citation does not recursively increase independent support;
4. correlated sources remain one dependence group;
5. negative/challenge evidence remains visible separately;
6. high fused confidence cannot self-authorize durable promotion;
7. background deletion of protected/high-risk state remains externally governed;
8. cross-scope consolidation cannot be authorized by semantic similarity;
9. revoked source state cannot be silently reintroduced during rebuild;
10. failed/partial maintenance leaves the cursor unchanged;
11. successful committed + validated maintenance advances the cursor exactly once;
12. summarization that drops a required exception fails validation and retains the original region;
13. non-authoritative index rebuild remains distinct from semantic memory mutation.

## Research finding

The current architecture does **not** need Noisy-OR as canonical doctrine. Noisy-OR is one useful estimator with explicit dependence/calibration assumptions.

The current architecture also does **not** need a broad background-maintenance authority primitive. Existing PAMA operations are safer because they classify the actual inner consequences.

The concrete missing reusable surface is narrower:

> **a maintenance-run transaction/evidence profile that binds constituent decisions to commit, validation, rollback/quarantine, and cursor continuity.**

That profile can make autonomous consolidation genuinely testable without granting an LLM a standing right to rewrite memory.

## Promotion recommendation

Create a bounded implementation issue for the maintenance-run evidence profile and reference harness. It should reuse existing PAMA decisions for constituent mutations and must prove failure/cursor/rollback behavior before any real autonomous consolidator is integrated.

Only after that generic seam exists should a real maintenance system such as a Zeph background pass or an Auto-Dreamer-style consolidator be used as an optional comparator.

## Non-claims

This research does not establish:

- Noisy-OR as the preferred confidence model;
- BeliefMem benchmark results as Agent Memory results;
- Zeph conformance with Agent Memory;
- Auto-Dreamer conformance with Agent Memory;
- automatic deletion authority;
- universal transaction semantics across every storage backend;
- production safety of autonomous consolidation.
