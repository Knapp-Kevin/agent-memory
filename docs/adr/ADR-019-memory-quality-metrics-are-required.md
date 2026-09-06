# ADR-019: Memory Quality Metrics Are Required

## Status

Accepted

## Context

Conformance fixtures test defined cases, but implementations can still degrade over time through stale recall, poor correction, over-retention, under-retention, unsafe context assembly, calibration drift, or authority-boundary failures.

Ongoing metrics are required to distinguish a memory system that passed yesterday's fixture from one that remains healthy today.

## Decision

Agent Memory defines ongoing memory-quality metrics across retention, forgetting, retrieval, uncertainty, correction, governance, security, privacy, recovery, and agent outcomes.

Metrics should be segmented by memory class and consequence class where aggregate numbers would hide risk.

## Required metric families

At minimum:

- false permanence rate
- valuable-memory loss / false evaporation
- stale recall rate
- disputed canonical use rate
- correction latency and propagation
- provenance retention rate
- source-trust calibration/degradation
- unsafe recall and overbroad context rate
- cross-scope leakage rate
- deletion completeness/residue
- successful rollback or recovery rate
- certification failure catch rate
- boundary instability rate
- abstention rate and quality
- estimator disagreement rate
- out-of-calibration-scope rate
- blocked-action escape rate
- stochastic action-set violation rate
- memory-guided task success
- repeated-failure avoidance

## Consequences

### Positive

- supports continuous evaluation beyond fixture snapshots
- detects drift and degradation
- gives implementations comparable outcome families
- makes optimization tradeoffs visible

### Negative

- requires telemetry, workloads, and reporting
- metrics can be gamed if detached from adversarial fixtures and evidence
- some metrics require domain-specific interpretation

## Acceptance evidence

Canonical contract:

- [`../32-memory-quality-metrics.md`](../32-memory-quality-metrics.md)

Machine-readable mapping:

- `schemas/conformance-report.schema.json`

The schema now supports Level 6 governed uncertainty and standardized metric fields for calibration, action-set violations, scope admission, deletion residue, replay reconstruction, and correction propagation, with an extension surface for implementation-specific metrics.

## Acceptance scope

Accepted establishes metric families and reporting semantics as canonical doctrine. Product-specific operating thresholds remain implementation and risk-policy decisions.

## Doctrine

Conformance shows a system can satisfy defined invariants under test.

Quality metrics show whether it continues to do so under real memory pressure and drift.
