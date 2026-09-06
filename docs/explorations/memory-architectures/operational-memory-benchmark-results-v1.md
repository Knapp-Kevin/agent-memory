# Operational-Memory Benchmark Results: V1

Status: **exploratory evidence** for #230 and parent #67. This is not canonical doctrine.

## Evidence boundary

This result binds the first matched visual-dynamics benchmark slice to:

```text
Agent Memory PR head before this results commit:
  eda5157cddcfc9e5c104735d72e34745e4e1015e
benchmark version:
  1.0.0
dataset manifest:
  sha256:c9ae5654e7b668e5f800e9775868af34a3dc833c0257f9b3c463be3ea3afe800
local benchmark artifact:
  sha256:4097f66e031e2fa363c678dc324c745361a3427255be886d8cd806bc166f19be
V-JEPA comparator artifact:
  sha256:363edbbcfdfb54859c89a8a35a32e6678786748dbcbfbfa433feb4a2aed496c5
V-JEPA source:
  facebookresearch/vjepa2@45d025f636dfc58fc2426905fc4a1ab755b1c3e5
V-JEPA model:
  vjepa2_1_vit_base_384
V-JEPA checkpoint SHA-256:
  848a77c33cc9e6649ed2119c9bea1e2c569bcdab9539ff3e7c02ccc2959ddf4d
runtime:
  Python 3.12 / torch 2.7.1+cpu
fixture:
  4 frames, 64x64 RGB, 48 train rows, 24 test rows
```

The V-JEPA checkpoint loads with `strict=True`. The comparator preserves the upstream V-JEPA 2.1 encoder options needed by the official checkpoint surface, including `img_temporal_dim_size=1`, `interpolate_rope=True`, and `uniform_power=False`. Only the benchmark input geometry is reduced.

## Capability result

Current-only evidence:

| Representation | MAE px | Intercept success | Clean MAE | Degraded MAE |
|---|---:|---:|---:|---:|
| explicit extracted | 0.354167 | 0.958333 | 0.000000 | 0.708333 |
| retrieval nearest exemplar | 6.833333 | 0.250000 | 5.500000 | 8.166667 |
| compact learned predictive | 8.559966 | 0.083333 | 6.452178 | 10.667755 |
| hybrid explicit + learned | **0.137280** | **1.000000** | 0.057223 | **0.217337** |
| V-JEPA 2.1 frozen + ridge | 7.689409 | 0.166667 | 5.004262 | 10.374557 |

For this workload, the hybrid is the capability winner. The explicit extractor is a close second and remains substantially better than retrieval-only, the compact learned baseline, and the frozen V-JEPA representation.

This is a workload result, not a universal architecture ranking.

## Stale-evidence sensitivity

| Representation | Current MAE | Stale-contaminated MAE | Delta |
|---|---:|---:|---:|
| explicit extracted | 0.354167 | 0.354167 | **0.000000** |
| retrieval nearest exemplar | 6.833333 | 14.583333 | +7.750000 |
| compact learned predictive | 8.559966 | 9.667059 | +1.107093 |
| hybrid explicit + learned | 0.137280 | 5.644820 | +5.507540 |
| V-JEPA 2.1 frozen + ridge | 7.689409 | 9.047452 | +1.358043 |

The hybrid's current-only capability gain is real, but so is its sensitivity to stale fitting evidence. The deterministic explicit path is the only representation in this slice whose result is unaffected by the injected stale training rows because it does not fit against historical labels.

Current-only rebuild/refit restores retrieval, compact learned, hybrid, and V-JEPA readout results to their original current-only values in this fixture. That demonstrates recovery for this contamination mechanism. It does not prove general deletion from a learned representation or from pretrained checkpoint contents.

## What changes architecturally

### Keep

Keep explicit, source-addressable operational state as a first-class Agent Memory capability. This workload gives no evidence for demoting it. It remains exceptionally strong where the state can be extracted deterministically and is materially easier to correct and re-evidence.

### Promote for further implementation

Treat hybrid explicit + learned predictive state as the strongest candidate for the next operational-memory implementation surface. It materially improves current-only task performance here, including degraded observations, while retaining an explicit channel that can remain independently governed.

The learned component must not inherit durability or currentness merely because the explicit component is trustworthy. Its training-set identity, rebuild boundary, stale influence, and derivation evidence remain separate.

### Do not promote yet

Do not make frozen V-JEPA 2.1 the default operational representation from this result. It underperforms both explicit and hybrid state on this small synthetic next-position workload.

Also do not reject JEPA-style latent state from this result. This comparator uses a 64x64, 4-frame fixture, mean token pooling, and a lightweight ridge readout. It does not exercise the planning and long-horizon behavior for which predictive world-model representations may have more architectural value.

### Demote within this workload

Nearest-exemplar retrieval and the simple PCA/ridge latent baseline should not be treated as competitive operational predictors for this task. They remain useful comparison baselines and may still be appropriate for other memory classes.

## Deployment-profile interpretation

This first slice supports only bounded conclusions:

- **Local / single-user structured state:** explicit or hybrid state is favored when deterministic extraction is available.
- **Team / multi-tenant:** hybrid capability is promising, but stale fitting evidence and scope isolation require explicit lifecycle controls before promotion.
- **Enterprise governed / high-assurance:** explicit state remains the safer default from this evidence because correction and provenance are local and reconstructable. Hybrid state requires stronger rebuild and derivation evidence.
- **Prediction-heavy / embodied:** unresolved. The current fixture is too narrow to decide whether JEPA-style predictive state becomes primary when planning and long-horizon dynamics dominate.

## Next benchmark slice required by #230

Do not close #230 from this result. The next implementation should reuse the same representation families on a workload that adds:

1. multi-step planning rather than one-step coordinate prediction;
2. long-horizon state changes and contradictory evidence;
3. task success, not only prediction error;
4. controlled context/memory channels;
5. correction/revocation latency and rebuild cost;
6. an explicit comparison of whether hybrid state continues to win when prediction must drive sequential action.

That second slice is where a JEPA-style representation gets a more meaningful opportunity to displace or complement the current operational-memory assumptions.
