# P5 benchmark and security scorecard

P5 converts the hard-invariant rules in [`../../32-memory-quality-metrics.md`](../../32-memory-quality-metrics.md) into an executable scorecard for the Agent Memory reference governed adapter.

This is a benchmark harness, not a universal memory score.

## Why this slice exists

The repository already has many executable negative paths, but isolated tests do not by themselves provide a benchmark-shaped answer to a basic question:

> Across a defined workload, which governance/security boundaries were exercised, what were their denominators, and did any disqualifying failure occur?

The P5 scorecard answers that without averaging critical failures into a friendly aggregate.

```text
hard invariant gates      pass/fail, un-averageable
        |
        +-- cross-scope admission
        +-- blocked-action escape
        +-- authority from confidence
        +-- stochastic action-set escape
        +-- stale-authorization rejection
        +-- silent concurrent overwrite
        +-- undeclared deletion residue
```

The only aggregate verdict is `hard_gates_passed`. It means every named gate passed. It is not a quality score.

## Executed cases

### Cross-scope admission

The permissive substrate is seeded with a foreign-tenant fact that an unfiltered substrate query can see. Governed recall is then executed through the adapter for another tenant.

Metric:

```text
cross_scope_admission_rate = admitted foreign candidates / substrate-visible foreign candidates
required: 0
```

The denominator is therefore not manufactured from an empty workload. The benchmark first proves that the underlying substrate exposes a cross-scope candidate when called permissively, then measures whether the governed boundary admits it.

### Blocked-action escape

Three consequential operations are attempted without the authority required to commit them:

- high-risk policy mutation;
- critical scope expansion;
- irreversible permanent deletion without completed review.

Metric:

```text
blocked_action_escape_rate = escaped blocked attempts / blocked attempts
required: 0
```

An escape includes committing the requested operation, selecting the prohibited operation, or reaching a substrate fact write.

### Authority from confidence

Two otherwise-identical high-risk durable proposals are executed with estimator confidence `0.99` and `0.01`.

The outcome and permitted/prohibited action sets must remain identical, and the high-confidence proposal must not acquire commit authority.

Metric:

```text
authority_from_confidence_count
required: 0
```

Confidence remains evidence input. It is not authority.

### Stochastic action-set containment

The stochastic selector is exercised across a configurable number of seeded trials. Each selected action must remain inside the governance envelope.

Metric:

```text
stochastic_action_set_violation_rate = escapes / stochastic trials
required: 0
```

The trials are reproducible by seed, but identical selected actions are not required. The invariant is containment.

### Stale authorization rejection

A first mutation advances canonical state from `v0` to `v1`. A second proposal still bound to `v0` attempts to commit.

Metric:

```text
stale_authorization_rejection_rate = correctly rejected stale attempts / stale attempts
required: 1
```

This metric is intentionally separate from concurrent conflict behavior. A system can reject one stale write path while still mishandling multi-writer conflict semantics elsewhere.

### Concurrent silent overwrite

P5 reuses the executable concurrency evidence introduced in PR #80. Two incompatible proposals originate from the same prior state. The later stale proposal must be refused and the conflict must remain reconstructable.

Metric:

```text
silent_overwrite_rate = silent last-writer-wins outcomes / conflict scenarios
required: 0
```

### Clean deletion residue

A canonical memory with a two-hop derived chain is permanently deleted through the governed projection path. The transitive purge and independent residue gate must report zero undeclared survivors.

Metric:

```text
deletion_residue_rate = undeclared residual projections / derived projections under test
required: 0
```

The separate deletion-completeness evidence remains the stronger adversarial proof that a deliberately broken one-hop purge is detected. P5 does not duplicate that fixture merely to inflate its case count.

## Machine-readable output

Run locally:

```bash
python reference/run_benchmark_security.py \
  --agent-memory-commit <exact-40-hex-commit> \
  --output benchmark-security.json
```

The result conforms to [`../../../schemas/benchmark-security-report.schema.json`](../../../schemas/benchmark-security-report.schema.json) and records:

- exact Agent Memory commit;
- adapter, doctrine, and policy versions;
- sample counts;
- each case numerator and denominator;
- metric values;
- each hard-gate rule and observed value;
- the aggregate boolean `hard_gates_passed`;
- explicit limitations.

CI emits the same report at the exact PR head or merge commit and uploads it as an artifact.

## Negative testing of the benchmark itself

The harness is not trusted merely because it emits JSON. Its unit tests mutate each zero-tolerance metric to a failing value and verify that the overall hard-gate verdict becomes false. The stale-authorization gate is separately tested to fail when rejection coverage drops below 100%.

This prevents a later scorecard refactor from quietly converting a hard invariant into a weighted or averaged metric.

## Scope and limitations

This P5 slice demonstrates security/governance benchmark behavior for the reference governed adapter and the already-mapped substrate boundary.

It does **not** establish:

- production workload performance;
- task-success improvement;
- long-horizon memory utility;
- latency, storage, token, or cost efficiency;
- exhaustive poisoning or extraction red-team coverage;
- production memory-layer comparison;
- a higher conformance level;
- ADR-020 acceptance.

P6 is the intended production-oriented adversarial comparator expansion. P8 and P9 own telemetry and systems/economic characterization respectively.

## Governing rule

> A benchmark that can average away an authority escape, cross-scope admission, or undeclared deletion residue is measuring the wrong thing.
