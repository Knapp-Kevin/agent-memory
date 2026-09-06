# P9 Systems and Economic Characterization

## Purpose

Characterize the operational cost shape of the Agent Memory reference runtime without turning performance or cost into authority.

P9 answers a narrower question than conformance:

> What work does the reference implementation perform as retained state, recall candidate volume, and derived-state closure grow?

It does **not** answer whether a memory operation is authorized. PAMA, lifecycle, scope, deletion, and recall rules remain authoritative regardless of whether a faster implementation exists.

## Evidence surface

`reference/run_systems_characterization.py` executes a provider-neutral characterization and emits an exact-commit JSON artifact.

The report separates two classes of evidence.

### Deterministic structural cost

These measurements are portable enough to compare across runs because they describe work performed rather than wall-clock speed:

- audit-event and decision-receipt amplification for one governed canonical mutation;
- serialized governance-evidence bytes emitted by that mutation;
- recall candidate count as retained facts increase;
- derivation-closure size and required projection purge operations as projection depth increases.

### Environment-specific timing

The same executed paths record minimum, median, and maximum `perf_counter_ns` observations across repeated samples.

Timing is deliberately **non-gating**. The artifact records Python implementation/version, platform, and machine architecture because CI runner speed is not reproducible enough to become a conformance threshold.

```text
lower latency != more authority
higher cost    != governance failure
faster recall  != permission to admit
cheaper write  != permission to persist
```

## Default workload

The CI characterization uses workload sizes:

```text
10 -> 100 -> 500
```

with five timing samples per measured path.

The workload is intentionally small enough to execute on every validation run while still exposing growth shape. It is not a production capacity benchmark.

## Characterized paths

### Governed write amplification

One successful governed canonical mutation is executed through the normal adapter path.

The report records:

- canonical mutations;
- audit events;
- decision receipts;
- evidence records per canonical mutation;
- serialized receipt bytes;
- serialized audit-event bytes;
- total serialized governance-evidence bytes.

This measures the explicit governance overhead the reference path chooses to retain for reconstructability. It is not a claim that every implementation must use the same encoding or storage layout.

### Recall scaling

For each workload size, the local reference substrate is populated with same-tenant facts and a governed recall is executed.

The report records retained fact count, candidate count, admitted count, and observational latency.

For this reference substrate, candidate work grows with the scanned retained set. P9 records that fact rather than disguising the in-memory reference adapter as an optimized production retrieval engine.

### Deletion propagation scaling

For each workload size, a deterministic chain of declared tier-3 projections is created from one canonical root. The existing transitive derivation-closure algorithm is executed.

The report records projection depth, closure nodes, required projection purge operations, and observational latency.

The structural invariant is important: deletion work follows the reachable derived-state closure. A cheaper implementation may improve traversal mechanics, but it may not obtain the savings by silently skipping reachable residue.

## CI gates

P9 fails CI only for structural contradictions, such as:

- candidate count no longer matching the controlled retained-set workload;
- transitive closure failing to include every declared projection in the controlled chain;
- structural work not increasing when the controlled workload increases;
- malformed exact-commit or workload parameters.

Latency values never fail CI merely for being slow.

## Economic interpretation

The P9 artifact intentionally reports provider-neutral work units and bytes rather than dollars.

Dollar cost depends on deployment choices that this repository does not control, including database engine, storage class, compute architecture, cloud region, retention period, indexing strategy, observability backend, and vendor pricing.

A deployment may map the structural measurements to its own unit economics later. That mapping is operational evidence, not Agent Memory doctrine.

## Claim boundary

P9 demonstrates systems/economic characterization of the **reference runtime** and its implemented algorithms. It does not establish:

- universal production throughput or latency;
- a service-level objective;
- cloud or hardware pricing;
- maximum supported memory volume;
- superiority over an external memory product;
- permission to weaken governance for performance;
- a new conformance level.

## Reproduction

```bash
python reference/run_systems_characterization.py \
  --agent-memory-commit <exact-40-hex-commit> \
  --sizes 10,100,500 \
  --repeats 5 \
  --output systems-characterization.json
```

The generated JSON artifact is uploaded by `Validate Doctrine Evidence` for exact-head inspection.
