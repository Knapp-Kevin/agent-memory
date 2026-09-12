# Workbook template: GitHub governance + memory field efficacy

This reference defines the spreadsheet shape for the `github-governance-memory-efficacy` skill.

The workbook is intended to preserve an immutable current-state baseline, make expected Agent Memory benefit falsifiable before implementation, and provide a blank matched post-implementation measurement surface.

## Front-of-workbook order

### `00_T0_DASHBOARD`

Human-facing current-state dashboard.

Recommended content:

- title and exact T0 snapshot reference;
- 5 to 7 KPI cards;
- concise current-state finding;
- six or fewer charts arranged in a two-column grid;
- no source-data tables underneath charts.

Typical KPI candidates:

```text
reconciliation work share
review exposure amplification
longest drift lag
reconcile-needed active docs
open truth conflicts
usage-telemetry distortion
relative reporting error
```

The exact KPIs depend on available evidence. Do not force unavailable metrics.

### `01_EXEC_SUMMARY`

One-screen written assessment.

Recommended sections:

```text
overall assessment
what is already strong
what is weak
what creates the most measurable waste
what Agent Memory directly addresses
what Agent Memory does not address
```

Avoid a universal quality score. If a letter/ordinal assessment is used for human readability, keep the actual multidimensional metrics visible and do not use the grade as an efficacy claim.

### `02_QUANT_DATA`

Human-readable quantitative source table.

Each row should identify:

```text
observed signal
value
unit
interpretation
evidence reference
classification: observed | derived | adjudicated | modeled
```

Keep scenario-cost assumptions in a clearly labeled section separate from observed evidence.

### `03_EXPECTED_BENEFIT`

Pre-implementation target contract.

Columns:

```text
Metric
T0
Expected target
Unit
Direction
Target class
Attribution
Mechanism / wedge
Why target is defensible
T3 measurement rule
```

Target classes:

```text
Hard invariant
Implementation completion
Contract target
Architecture target
Operational bound
Joint operational target
Recurrence target
Control prerequisite
Measurement prerequisite
```

Do not use a target that cannot be traced to a named mechanism.

### `04_TARGET_DASHBOARD`

Presentation-ready visualization of T0 versus expected target.

This dashboard must say `EXPECTED, NOT MEASURED` prominently.

Use the same metric names and chart families that will later appear in T3.

Recommended direct-Agent-Memory KPI cards:

```text
open truth conflicts
reconcile-needed active docs
explicit supersession linkage
longest detectable drift lag
canonization lag
stale-copy propagation miss
decision-memory completeness
```

Joint and non-memory metrics may appear in charts with explicit subtitles identifying the attribution boundary.

### `05_T3_DASHBOARD`

Blank post-implementation dashboard prepared before T3 begins.

Requirements:

- same categories and chart layout as the target dashboard;
- T0 and target context may remain visible;
- measured T3 values must remain blank/TBD until evidence exists;
- title clearly identifies the matched 30-day T3 window;
- no expected value may be copied into a measured field.

When T3 measurements are populated, the dashboard should visually distinguish:

```text
T0 observed
Expected target
T3 measured
```

### `06_T3_DATA_ENTRY`

Controlled measured-result input surface.

Columns:

```text
Metric
T0
Expected target
T3 measured
Unit
Direction
Target met?
Measurement window
Evidence URL
Attribution
Notes / confounders
Captured by / date
```

T0 and expected target should link to the target contract rather than be manually copied.

`Target met?` should be formula-driven where practical.

Measured cells should use an obvious editable fill and remain empty until evidence exists.

## Supporting evidence sheets

Use only what the study needs. Common examples:

```text
README / methodology
DATA_DICTIONARY
ANALYSIS_PLAYBOOK
PR_CORPUS
ADJUDICATION
DECISION_SAMPLE
POLICY_CONFLICTS
DRIFT_CASES
METRIC_REGISTRY
PIVOT_SUMMARIES
INTERVENTIONS
BEFORE_AFTER
PUBLICATION_VIEW
INGESTION_LEDGER
DOWNSTREAM_CASES
```

Do not hide unique evidence merely to simplify the user interface. If helper-only pivot/chart sheets are visually noisy, they may be hidden, but raw evidence and audit tables should remain available.

## Visual layout

Recommended dashboard geometry:

```text
Rows 1-3   title / subtitle / evidence caveat
Rows 5-7   KPI cards
Rows 8-9   one-sentence interpretation
Rows 11-25 chart 1 | chart 2
Rows 28-42 chart 3 | chart 4
Rows 45-59 chart 5 | chart 6
```

Use generous whitespace between chart rows.

Charts should not overlap cells the reader needs to inspect.

## Recommended chart pairings

Only compare compatible units.

Useful pairings:

```text
Canonical debt counts
  open truth conflicts
  reconcile-needed active docs

Latency in days
  drift-detection latency
  canonization / propagation latency

Decision-memory percentages
  core completeness
  authority captured
  supersession linkage

Propagation percentage
  stale-copy propagation miss

Work amplification ratio
  review exposure amplification

Measurement integrity ratio
  usage telemetry distortion
```

Do not place counts, percentages, days, and ratios on one shared magnitude chart merely because they are all bad.

## Color semantics

Use a restrained palette with semantic consistency.

Suggested roles:

```text
T0 observed        warm risk tone
Expected target    green
T3 measured        blue
TBD / unavailable  neutral gray
Joint attribution  amber annotation
Non-memory metric  gray annotation
```

Avoid relying on color alone. Titles, legends, and subtitles must communicate the same distinction.

## Formula and provenance rules

- Derived metrics should be formulas where possible.
- T0 and target values on `06_T3_DATA_ENTRY` should reference their source sheets.
- Every publishable T3 measurement should carry an evidence URL or durable evidence reference.
- Store GitHub URLs in evidence columns when available.
- For modeled cost, expose low/base/high assumptions rather than embedding hidden constants.
- If a collector is known to be wrong, fix or reconcile the measurement instrument before using it to claim resource savings.

## Reusable measurement lifecycle

```text
T0 baseline
  freeze repository/org state and historical lookback

T1 acceptance
  verify the Agent Memory/PAMA mechanisms exist and preserve hard invariants

T2 stabilization
  14 days recommended

T3 efficacy
  30-day matched window using the same definitions

T4 durability
  optional 90-day regression review
```

The workbook should exist before T1 implementation completes so the evaluation cannot redefine success after observing the result.
