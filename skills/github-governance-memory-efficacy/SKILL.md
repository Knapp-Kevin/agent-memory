---
name: github-governance-memory-efficacy
description: Build a reproducible GitHub repository or organization baseline for governed memory, quantify ambiguity and work amplification, define evidence-based Agent Memory benefit targets, and prepare a matched 30-day post-implementation evaluation.
---

# GitHub Governance + Memory Efficacy Review

Use this skill when evaluating whether a GitHub repository or organization has problems with canonical truth, decision memory, authority, supersession, drift, repeated work, or governance-induced coordination cost, especially when Agent Memory/PAMA may be an implementation candidate.

The output is a longitudinal evidence instrument, not a one-time opinionated score.

## Core rule

Preserve three different states and never collapse them:

```text
T0 observed baseline
  !=
expected benefit target
  !=
T3 measured result
```

The target state is a falsifiable hypothesis derived from named mechanisms. It is not the post-implementation result.

Do not invent a universal Agent Memory quality score. Follow `docs/32-memory-quality-metrics.md`: hard invariants first, failure rates second, optimization metrics third, outcome metrics last.

## Scope

The skill may be applied to:

- one GitHub repository;
- several related repositories;
- an entire GitHub organization;
- a governance/system-of-record repository plus downstream repositories it influences.

Define the scope before collecting evidence. Record inactive repositories separately rather than silently omitting them.

## Phase 1: freeze T0 before implementation

Record:

```text
scope
repository/org identifiers
exact baseline commit(s)
snapshot timestamp
operational lookback window
active repositories
excluded/inactive repositories
metric definitions
sampling rules
publication boundary
```

Recommended operational lookback: 30 complete days ending before the frozen snapshot day unless a different window is justified.

Do not change T0 after implementation begins merely because later data looks more convenient.

## Phase 2: collect evidence

Prefer reconstructable evidence:

- pull requests;
- reviews and review rounds;
- commits;
- issues and decision threads;
- governance/documentation history;
- workflow results and checks;
- explicit policy changes;
- drift/reconciliation incidents;
- correction and rollback events;
- current documentation authority surfaces;
- usage telemetry when it can be independently reconciled.

For large corpora, use a two-pass process:

1. automated candidate screening;
2. evidence-based adjudication on candidate events plus a reproducible unflagged control sample.

Candidate detection is a filter, not a causal verdict.

## Phase 3: classify evidence quality

Every consequential observation should be classified as one of:

```text
OBSERVED
Directly reconstructable from durable evidence.

DERIVED
A deterministic calculation over observed evidence.

ADJUDICATED
A causal or semantic classification supported by evidence and an explicit rule.

MODELED
A transparent scenario using editable assumptions.

UNAVAILABLE
The historical evidence was never recorded or cannot be reconstructed safely.
```

Never present MODELED time, tokens, or dollars as observed spend.

## Phase 4: measure memory and governance tax

Look for measurable work amplification rather than only document-quality defects.

Candidate metrics include:

```text
competing_active_authority_rate
bootstrap_ambiguity_rate
stale_current_recall_rate
supersession_chain_integrity_rate
policy_version_reconstruction_rate
decision_traceability_completeness
current_truth_reconstruction_rate
drift_detection_latency
conflict_resolution_latency
correction_propagation_completeness
time_to_answer_current_rule
source_hops_per_governed_answer
decision_relitigation_rate
governance_ambiguity_rework_rate
wrong_authority_action_rate
policy_propagation_latency
review_exposure_amplification
reconciliation_work_share
stale_copy_propagation_miss
repeated_failure_avoidance
```

Also capture concrete work units when available:

- repeated PRs;
- duplicate commit-review appearances;
- repeated CI/test failures caused by rule ambiguity;
- manual rewrites caused by governance mismatch;
- stranded tasks/messages;
- duplicate or stale artifacts;
- agent idle time caused by false-positive health/control state;
- corrective PR chains triggered by known governance/control defects.

## Work amplification

Prefer ratios that explain consequence.

Example:

```text
review_exposure_amplification
  = total commit-review appearances / unique intended commit review set
```

A count of six repeated PRs is useful. Showing that the same final eleven-commit backlog produced fifty-one review appearances is stronger because it quantifies repeated exposure.

Keep units explicit. Do not compare unlike counts as if they share one scale.

## Resource-cost modeling

If repeated work can be converted into time or token estimates, keep the model separate from observed evidence.

Use low/base/high assumptions and make every assumption editable.

Example:

```text
observed work units
  × minutes per unit
  = modeled friction hours

modeled friction hours
  × loaded hourly rate
  = illustrative labor-equivalent cost
```

For token-dollar estimates, independently validate the usage collector first. If telemetry is materially distorted, report the telemetry defect as a baseline finding and do not claim Agent Memory savings from it.

## Phase 5: define expected Agent Memory benefit

For each target metric, record:

```text
T0 observed value
expected target
unit
direction
target class
attribution
Agent Memory mechanism / implementation wedge
why the target is defensible
T3 measurement rule
```

Allowed target classes:

```text
HARD INVARIANT
The architecture must enforce this. Example: unauthorized canonical mutation escape = 0.

CONTRACT TARGET
A required field or lifecycle contract should make this structurally complete. Example: explicit supersession for applicable new governed mutations = 100%.

OPERATIONAL BOUND
The active implementation establishes a measurable latency or failure bound. Example: detectable drift <= one daily sweep.

JOINT OUTCOME
Expected to improve only with Agent Memory plus repository/process controls.

NON-MEMORY PREREQUISITE
Must improve for measurement integrity or confounder control, but must not be credited to Agent Memory.
```

Do not choose targets because they look attractive. Tie each target to an implementation mechanism and explain the causal path.

Examples of defensible direct targets after the relevant mechanisms are active:

```text
unresolved high-risk current-truth conflicts -> 0
new governed canonical mutations with reconstructable authority -> 100%
applicable new policy/decision replacements with explicit supersession -> 100%
stale derived current-truth projections after a sampled canonical change -> 0%
```

Latency targets must match the actual enforcement schedule. A daily drift sweep can justify a <=24-hour detectable-drift bound. It cannot justify an invented five-minute guarantee.

## Attribution discipline

Classify every target/result:

```text
Agent Memory direct
Agent Memory + repository control
repository/process control
non-memory measurement prerequisite
attribution unclear
```

Record intervention state during T3. Do not credit Agent Memory for improvements primarily caused by branch protection, reviewer identity, transport fixes, telemetry corrections, or unrelated process changes.

## Required workbook structure

When a spreadsheet is an appropriate output, use the template in `references/workbook-template.md`.

Minimum front-of-workbook order:

```text
00_T0_DASHBOARD
01_EXEC_SUMMARY
02_QUANT_DATA
03_EXPECTED_BENEFIT
04_TARGET_DASHBOARD
05_T3_DASHBOARD
06_T3_DATA_ENTRY
```

Supporting evidence sheets follow after those surfaces.

The user-facing rule is:

```text
dashboards tell the story
data sheets prove the story
evidence sheets audit the story
```

Do not place charts on top of source tables. Keep chart/dashboard tabs separate from data tabs.

## Dashboard visual contract

Each dashboard should:

- fit the primary narrative into one scrollable presentation surface;
- use a small set of headline KPI cards;
- arrange charts in an even grid with no overlap;
- use consistent category names across T0, target, and T3;
- use distinct series treatments for observed baseline, expected target, and measured T3;
- clearly label modeled or non-memory metrics;
- avoid mixing incomparable units in the same chart;
- include concise subtitles explaining attribution or measurement caveats.

Recommended series semantics:

```text
T0 observed      = risk/warm tone
Expected target  = green/goal tone
T3 measured      = blue/measured tone
Unknown/TBD      = neutral gray
```

Color is explanatory, not evidence.

## T3 measurement protocol

Recommended sequence:

```text
T0: frozen baseline
T1: implementation acceptance
T2: 14-day stabilization
T3: matched 30-day post-stabilization window
T4: optional 90-day durability review
```

The T3 data-entry surface should be blank until measurements exist.

A measured value should carry:

```text
metric
T0
expected target
T3 measured value
unit
direction
target-met result
measurement window
evidence reference
attribution
notes/confounders
captured by/date
```

Do not populate the T3 measured field with the expected target.

## Qualitative companion benchmark

Run the same bounded current-truth questions at T0 and T3, preferably in fresh sessions/harnesses.

Examples:

1. What is the current rule for action X?
2. Who authorized it?
3. What did it supersede?
4. What was the rule on historical date Y?
5. Is anything in conflict for this scope?
6. What proves the rule is enforced rather than merely documented?

Measure:

```text
correctness
provenance completeness
scope correctness
historical reconstruction
conflict visibility
time to answer
source hops
human clarification required
```

## Publication safety

For private organizations, keep raw evidence and the working workbook private until an authorized owner reviews what may be published.

A public case study should contain only sanitized metrics and evidence that the organization has approved for disclosure.

Do not expose secrets, customer/member data, private identifiers, proprietary runtime topology, or sensitive security details merely because they were useful for internal measurement.

## Definition of done

A review is complete when:

- T0 is immutable and reproducible;
- the raw population and denominators reconcile;
- observed, derived, adjudicated, and modeled values are visually distinguishable;
- the executive dashboard communicates the current state without requiring the reader to inspect raw data;
- expected targets are tied to named mechanisms and attribution classes;
- T3 has a blank measured-data surface ready before implementation completes;
- hard invariant failures cannot be hidden by aggregate efficiency gains;
- private evidence remains governed separately from publication-safe output;
- the same process can be rerun against another repository or organization without redefining success after the fact.
