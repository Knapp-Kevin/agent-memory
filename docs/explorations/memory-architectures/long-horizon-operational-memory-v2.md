# Long-Horizon Operational Memory Benchmark V2

Status: exploratory benchmark evidence under #67 / #246. This is not canonical doctrine and is not a product ranking.

## Question

The V1 benchmark in #230 compared explicit, retrieval, learned, hybrid, and frozen V-JEPA 2.1 representations on a short-horizon workload. V2 keeps those same representation families and asks a harder question:

> What changes when state evolves across several stages and a previously valid trajectory is corrected/revoked?

The workload uses three sequential four-frame stages. Half of the episodes change trajectory after stage 0. The previous trajectory remains visually present as a stale distractor in later stages, so a representation must separate current state from remembered-but-invalid state.

## Evidence boundary

Evidence status: `benchmark_or_conformance_evidence` plus `implementation_observed` for the local reference harness. It is not production evidence.

Dataset properties:

- deterministic seed `2462026`;
- 64 training episodes and 32 test episodes;
- 16 corrected/revoked test episodes;
- three stages and three forecast horizons;
- stable episode identifiers;
- hidden host memory disabled by fixture;
- current-only and intentionally stale-contaminated variants measured separately.

Frozen V-JEPA comparator remains pinned to the V1 boundary:

```text
repository: facebookresearch/vjepa2
source commit: 45d025f636dfc58fc2426905fc4a1ab755b1c3e5
model: vjepa2_1_vit_base_384
checkpoint sha256: 848a77c33cc9e6649ed2119c9bea1e2c569bcdab9539ff3e7c02ccc2959ddf4d
```

The benchmark does not reproduce a published V-JEPA benchmark and does not test action-conditioned V-JEPA planning. The encoder is frozen and used only as the representation source for the same local V2 task.

## Methodology correction before interpretation

The first V2 execution exposed a one-step forecast-boundary error: the target started one time step after the first genuinely unobserved state. That produced a suspicious approximately one-pixel error even for the exact explicit-state baseline.

The workload was corrected before any result was accepted. The final runner now fails if the explicit current-state baseline exceeds `0.05 px` mean plan error at any stage. Pre-correction artifacts are not evidence for the findings below.

This is a useful benchmark-governance lesson in its own right:

```text
workflow success != benchmark validity
```

## Corrected results

The table reports the current-only condition at stage 2 plus correction/revocation adaptation behavior. Higher final success is better. Lower error/adaptation steps/stale influence is better.

| Representation | Stage-2 final success | Stage-2 mean error | Mean adaptation steps | Recovered by confirmation | Stale-influence rate |
|---|---:|---:|---:|---:|---:|
| Explicit extracted state | 1.00000 | 0.030802 px | 0.0000 | 1.0000 | 1.0000 |
| Retrieval | 0.15625 | 7.019894 px | 1.5625 | 0.2500 | 0.8125 |
| Learned compact | 0.09375 | 8.915362 px | 1.9375 | 0.0625 | 0.8125 |
| Hybrid explicit + learned | 0.09375 | 6.538845 px | 1.6875 | 0.1875 | 0.8750 |
| Frozen V-JEPA 2.1 representation | 0.21875 | 7.327938 px | 1.6250 | 0.3125 | 0.5000 |

`stale-influence rate` measures the intentionally stale-contaminated variant, not the governed current-only condition. The explicit representation's value of `1.0` therefore means the deliberately stale explicit state predictably follows the revoked trajectory. Its current-only path recovers immediately and remains essentially exact. This distinction is why currentness/admission cannot be inferred from representation quality alone.

## What this evidence supports

### 1. Explicit state is unusually strong when correction precision dominates

On this deterministic trajectory task, explicit extracted state remains essentially exact after the correction event. It also recovers immediately because the current state can directly replace the superseded trajectory.

This is evidence for a workload-specific strength, not a universal claim that explicit memory is superior.

### 2. Added representation complexity did not automatically improve adaptation

The hybrid representation did not outperform explicit state and did not outperform frozen V-JEPA on final task success. In this workload, adding learned features increased representational complexity without buying better correction/revocation behavior.

The result challenges any assumption that hybridization is intrinsically beneficial.

### 3. Frozen V-JEPA was the strongest non-explicit condition on final success here

Frozen V-JEPA reached `0.21875` stage-2 final success, compared with `0.15625` for retrieval and `0.09375` for learned/hybrid conditions. It also showed the lowest stale-influence rate among those non-explicit conditions at `0.50`.

The benchmark has only 32 test episodes, so this is not evidence of statistical superiority or a general V-JEPA memory advantage. It is a bounded observation worth preserving for follow-up.

### 4. Correction/revocation remains materially harder for learned/retrieval state

Every non-explicit representation required more than one benchmark step on average to recover from the changed trajectory, while explicit state recovered immediately.

This reinforces a cross-architecture governance question from #67:

> A representation may be useful and predictive while still being difficult to correct, revoke, or prove current.

### 5. Model-internal/currentness gating remains independently necessary

The benchmark does not turn representation quality into an admission decision. #240 remains the governing model for conditional/internal influence:

```text
representation/address available
!= state current
!= scope allowed
!= influence admitted
```

The frozen encoder's checkpoint remaining available after source correction/revocation is not evidence that the old influence has been forgotten.

## What this evidence does not support

Do not infer from this benchmark that:

- explicit memory is universally best;
- V-JEPA is an agent-memory implementation;
- frozen predictive features are current merely because they remain useful;
- retrieval or learned memory is inherently unsafe;
- hybrid memory is generally inferior;
- one 32-episode evaluation establishes statistical ranking;
- benchmark success changes PAMA authority or lifecycle semantics.

## Next research pressure

The strongest next questions are not “add another representation.” They are:

1. repeat the matched comparison on a workload where exact explicit state is incomplete and abstraction is genuinely useful;
2. add confidence intervals or repeated seeds before making comparative performance claims;
3. measure rebuild/update cost when a learned/frozen representation must actually remove stale influence;
4. test whether #240-style admission changes downstream task behavior when a stale internal representation remains physically resolvable;
5. preserve the V1/V2 workloads as separate evidence rather than retrofitting one benchmark into every memory question.

## Reconstructability

Executable evidence lives in:

- `reference/agentmem_ref/long_horizon_dataset.py`
- `reference/agentmem_ref/long_horizon_benchmark.py`
- `reference/run_long_horizon_memory_benchmark.py`
- `.github/workflows/long-horizon-memory-benchmark.yml`
- workflow artifacts `long-horizon-memory-local` and `long-horizon-memory-vjepa2`

Related: #67, completed #230, #240, and #246.
