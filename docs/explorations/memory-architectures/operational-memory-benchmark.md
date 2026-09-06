# Matched Operational-Memory Benchmark

Status: **active exploratory benchmark** under #230 and parent #67. This document is not canonical doctrine.

## Purpose

This benchmark asks a capability question that Agent Memory's governance-first implementation intentionally did not answer:

> **Which representation should actually carry operational memory for a task, and when should Agent Memory prefer explicit, retrieval, learned predictive, or hybrid state?**

The benchmark is deliberately willing to show that an existing Agent Memory representation is worse on a target workload.

No architecture receives authority or lifecycle credit for predictive accuracy.

## Workload: visual dynamics / next-state prediction

The same deterministic generator produces short RGB clips containing a moving object. The task is to predict the object's next `(x, y)` position after the observed clip.

The workload has two observation profiles:

```text
clean
  clear target, deterministic motion

degraded
  noise, distractors, and selected occlusion
```

This gives explicit state extraction a fair domain where it should work well while also testing whether learned representations remain useful when the visual signal becomes less tidy.

Every representation receives the same train/test clip identities and target positions.

## Compared operational representations

### A. Explicit extracted memory

A deterministic extractor identifies target-colored pixels, records observed centroids, and extrapolates velocity from the latest valid observations.

Strengths tested:

- exact, inspectable state;
- cheap correction/deletion;
- no learned readout required.

Weakness deliberately exposed:

- extraction can be brittle when the observation is occluded/noisy.

### B. Retrieval-oriented memory

A compact downsampled clip descriptor is stored with the observed outcome. Prediction uses nearest-neighbor retrieval over current records.

Strengths tested:

- source-addressable exemplar memory;
- local update/delete;
- no global fitting step.

Weaknesses tested:

- nearest historical similarity may not represent dynamics robustly;
- stale exemplars can directly influence prediction unless lifecycle filtering occurs before retrieval.

### C. Compact learned predictive state

The benchmark learns a low-dimensional PCA/SVD representation from the training clips and fits a small ridge readout for next-state prediction.

This is **not JEPA**. It is the representation-neutral learned-state baseline:

```text
raw observation stream
-> compact learned representation
-> predictive readout
```

It tests whether learned compression helps operational prediction before assigning any advantage to a named architecture.

### D. Hybrid explicit + learned state

The deterministic explicit features and compact learned state are concatenated before the same ridge readout.

The hybrid is included because the research question is not required to produce one universal winner. Complementary representations are a valid outcome.

### E. Pinned V-JEPA 2.1 frozen representation

The external comparator uses Meta's official V-JEPA 2 repository and official 80M V-JEPA 2.1 ViT-B checkpoint as a **frozen representation encoder**, then fits the same lightweight ridge readout used by the local learned baseline.

Pinned source:

```text
repository: facebookresearch/vjepa2
release-era source commit: 45d025f636dfc58fc2426905fc4a1ab755b1c3e5
model: vjepa2_1_vit_base_384
parameter scale: ~80M
checkpoint filename: vjepa2_1_vitb_dist_vitG_384.pt
official checkpoint URL:
  https://dl.fbaipublicfiles.com/vjepa2/vjepa2_1_vitb_dist_vitG_384.pt
```

The source commit corresponds to the repository's V-JEPA 2.1 announcement work. The direct checkpoint URL is the one published in the official README.

Important reproducibility note: the hub helper at this source pin contains a temporary localhost checkpoint-base setting. The comparator therefore downloads the explicit official checkpoint URL and records its SHA-256 digest instead of pretending `torch.hub.load(..., pretrained=True)` is currently self-contained.

### What this V-JEPA comparator proves

If the job succeeds, it proves only:

```text
pinned official V-JEPA 2.1 encoder weights
+
this synthetic workload
+
this input-resolution/frame adaptation
+
this frozen pooling/readout method
-> measured benchmark result
```

It does **not** reproduce the V-JEPA 2 or V-JEPA 2.1 published benchmark suite, action-conditioned world model, or robot planning results.

The encoder is instantiated at a smaller fixture resolution/frame count than its published checkpoint training configuration so exact-head CPU CI remains tractable. Transformer weights are loaded from the official checkpoint; the altered fixture geometry is recorded as a benchmark limitation rather than described as an official V-JEPA evaluation configuration.

## Metrics

Capability metrics are reported independently:

```text
mean absolute next-position error (pixels)
intercept success rate within a fixed radius
clean vs degraded delta
stale-evidence contamination delta
recovery after current-only rebuild
```

Resource metrics are also reported separately:

```text
representation dimension
training/readout rows
stored exemplar rows where applicable
fit/rebuild elapsed time
inference elapsed time
```

Do not collapse these into one universal memory score.

## Stale-evidence phase

The benchmark adds conflicting stale training exemplars/targets to a bounded subset of the training set.

The purpose is not to simulate every lifecycle event. It tests one invariant across representations:

```text
useful representation
!= lifecycle-aware representation
```

- explicit extraction is unaffected because it predicts from the current clip rather than historical training rows;
- retrieval may be contaminated by stale exemplars unless they are filtered;
- compact learned/hybrid/V-JEPA readouts may be contaminated if stale labels enter fitting data;
- rebuilding/refitting from current-only evidence should remove that specific contamination path.

The benchmark records both contaminated and current-only results. It does not report a high-quality representation as safe merely because stale evidence happened not to change one score.

## Governance/evidence comparison

Capability metrics remain separate from governance properties.

| Representation | Source-addressable output basis | Exact local correction/delete | Global rebuild after changed training evidence | Provenance posture |
|---|---|---|---|---|
| explicit | current clip/derived features | strong | none | direct/feature-level |
| retrieval | nearest exemplar ref | strong | none | direct exemplar |
| compact learned | training-set manifest, not one source | weak/local change requires refit | yes | set/derivation-level |
| hybrid | explicit refs + learned train manifest | mixed | learned component refit | mixed |
| V-JEPA frozen + readout | external checkpoint + local train manifest | local readout evidence requires refit | readout yes; frozen encoder no | checkpoint + set-level readout |

This table describes the benchmark implementation, not all possible implementations of each architecture family.

## Fairness / contamination rules

The harness binds:

```text
generator version + seed
train/test sample IDs
observation profile
representation implementation version
ridge/PCA configuration
stale-row construction
metric implementation
external model source/checkpoint identity
```

No host/native memory may inject target labels into evaluation.

The V-JEPA feature extractor receives pixels only. The readout receives only training targets and frozen features. Test targets are used only for scoring.

## Architecture decision rule

The output should support deployment-profile conclusions such as:

- explicit state is preferable when exact structured observations are cheap/reliable;
- learned predictive state earns operational value when it materially improves degraded/partially observable prediction enough to justify rebuild/inspectability cost;
- hybrid state is preferable when capability gain is complementary rather than redundant;
- frozen pretrained representations may be useful operational modules without becoming canonical source-of-truth memory;
- a representation may win capability while still requiring stronger lifecycle/currentness controls.

A no-change result is valid. A JEPA win is valid. A JEPA loss is valid.

## Non-claims

This benchmark does not establish:

- one universal best memory architecture;
- V-JEPA 2.1 planning performance;
- production robustness;
- general semantic/episodic memory superiority;
- deletion from pretrained weights;
- per-source provenance inside a pretrained model;
- regulatory/production governance compliance;
- that synthetic visual dynamics represent every Agent Memory deployment.
