# Scoring and Decay

## Purpose

This document consolidates the scoring logic from UOR saturation, EvolveAI memory tier routing, CodeGenome confidence fusion, and PAMA authority into one coherent model.

The scoring model exists to support lifecycle decisions. It must not be mistaken for truth.

A second rule follows from that distinction:

**A score is an estimate with scope, method, calibration limits, and uncertainty. It must not be treated as a deterministic fact merely because software represents it as a number.**

## Signal taxonomy

| Signal | Purpose | Typical owner |
|---|---|---|
| Identity | Exact object reference | UOR, content addressing |
| Confidence | Evidence quality or relation probability | CodeGenome, observers |
| Saturation | Lifecycle persistence pressure | PRISM, EvolveAI, memory runtime |
| Authority | Permission to mutate or promote | PAMA, Arbiter, policy layer |
| Certification | Confirmation of durable transition | Verification or approval gate |
| Risk | Potential harm from wrong mutation or permanence | PAMA, governance layer |
| Uncertainty | Limits, spread, calibration, or disagreement around an estimate | estimator + calibration harness |

## Canonical scoring shape

A memory candidate should be evaluated using a composite model:

```text
memory_lifecycle_score = f(
  identity_resolved,
  evidence_confidence,
  saturation,
  corroboration,
  cross_reference_weight,
  contradiction_pressure,
  access_quality,
  temporal_pressure,
  pama_authority,
  certification_status,
  risk_class
)
```

This is not a single universal equation yet. It is the required signal family.

The function output should be interpreted as an estimator output, not a command.

## Score metadata

When a probabilistic, learned, or calibrated score materially affects a consequential memory decision, preserve enough metadata to interpret it:

```text
score_name
score_value
estimator_id
estimator_version
calibration_version
calibration_scope
sample_or_evidence_refs
uncertainty_representation
confidence_interval_or_equivalent
out_of_distribution_signal
computed_at
```

Not every implementation needs a classical confidence interval. Some estimators may use posterior spread, ensemble disagreement, conformal sets, calibration bins, categorical uncertainty, or another justified representation.

The requirement is to avoid false precision.

## Saturation

Saturation is a calibrated lifecycle score.

```text
sigma = pinned_fiber_weight / total_available_fiber_weight
```

Where pinned fibers may include:

- corroboration
- verification
- meaningful re-access
- cross-reference
- dependency strength
- user approval
- policy relevance
- runtime reuse
- successful recall history

Raw access should never dominate saturation.

A saturation value should carry the calibration scope under which it is meaningful. `sigma = 0.92` without calibration context is weaker evidence than the number's apparent precision suggests.

## Effective decay

A UOR-aligned decay model may use:

```text
lambda_eff = lambda_base * T_ctx
```

Where:

```text
T_ctx = free_fiber_count * ln(2) / n
```

Interpretation:

- higher saturation lowers effective decay
- unresolved or weakly pinned memory decays faster
- fully crystallized memory may enter a non-decaying regime inside its certified scope

Decay decisions should distinguish uncertainty in the decay estimator from authority to archive, prune, delete, or retain.

## EvolveAI memory tier routing

EvolveAI uses a memory tier score shape:

```text
MTS = (S * Ws) + (A * Wa) + (P * Wp) - (C * Wc)
```

Where:

- S = sensitivity
- A = accuracy requirement
- P = privilege level
- C = compute constraint

Canonical interpretation:

MTS is a routing heuristic. It should be integrated with saturation, confidence, and authority rather than treated as a complete promotion rule.

If any MTS input is itself estimated, the implementation should retain its uncertainty rather than assuming the composite score erased it.

## CodeGenome confidence fusion

CodeGenome contributes confidence fusion for code-reality observations.

Confidence describes support for graph relations, not lifecycle durability.

Example distinction:

```text
high confidence relation != crystallized memory
high saturation != correct relation
certified relation == confirmed within scope
```

If multiple observers or estimators disagree, fusion should preserve disagreement information when it materially affects downstream governance.

## PAMA authority weighting

PAMA should evaluate whether a memory transition is permitted.

Inputs may include:

- risk class
- scope of change
- source authority
- user approval state
- confidence spread
- contradiction pressure
- reversibility
- blast radius
- implementation maturity
- estimator uncertainty
- calibration quality
- estimator disagreement
- distribution-shift indicators

Suggested authority outcomes:

```text
allow
allow_with_ledger
require_review
require_external_verification
block
```

No probabilistic score directly selects its own authority outcome. PAMA or equivalent governance maps estimator outputs into a policy-defined consequence.

## Crystallization threshold

A crystallization threshold must be calibrated.

Do not choose `sigma >= 0.95` by intuition. Calibrate using labeled examples:

- PERSIST objects that should become durable
- EVAPORATE objects that should decay
- trap-class objects that are designed to fool the scoring system

A threshold is an operating point, not a truth boundary.

## Decision-boundary stability

A calibrated system should measure not only whether a threshold performs well on average, but whether decisions are stable near the boundary.

Required questions include:

- How much does the output change under small perturbations to evidence?
- How often do equivalent inputs cross opposite sides of the threshold?
- How much calibration error exists in the region where governance changes consequence?
- Does estimator disagreement increase near the boundary?
- Is the current input inside the calibration scope?
- Has data or environment drift changed the operating point?

Where consequence is meaningful, policy may define an uncertainty or abstention band:

```text
score < lower_bound       -> ordinary non-promotion path
lower_bound <= score <= upper_bound -> collect evidence / review / abstain
score > upper_bound       -> eligible for next governance gate
```

The doctrine does not mandate one mathematical form. It mandates that expensive mistakes not be hidden behind false threshold precision.

## Hysteresis

Where repeated state oscillation is costly, use separate thresholds or equivalent stability controls.

Example only:

```text
promote_candidate_above = 0.80
demote_candidate_below  = 0.70
```

The values require calibration. The principle is that estimator noise should not manufacture lifecycle churn.

## Required trap classes

### Access-spam junk

A low-value object hammered with reads to inflate saturation.

Expected result:

```text
candidate == false
crystallized == false
```

### Confidently-wrong memory

An object strongly reinforced but incorrect.

Expected result:

```text
candidate may be true
certification must fail
crystallized == false
state == disputed or pending_verification
```

### Overfit single-source fact

A fact repeated from one uncorroborated source.

Expected result:

```text
saturation plateau below durable threshold unless corroborated or approved
```

### Threshold-jitter candidate

Equivalent or minimally perturbed observations move repeatedly across a consequential threshold.

Expected result:

```text
boundary_instability_detected == true
repeated automatic promotion/demotion == false
policy outcome in [abstain, require_review, collect_more_evidence, stable_hysteresis_path]
```

### Estimator disagreement

Two otherwise valid estimators materially disagree.

Expected result:

```text
disagreement_preserved == true
no estimator self-authorizes transition
policy resolves or escalates disagreement
```

### Distribution-shift candidate

An estimator is asked to score memory outside the domain on which its calibration was validated.

Expected result:

```text
out_of_scope_or_drift_signal == true
calibration claim is not silently reused
high-consequence promotion requires recalibration, review, or external verification
```

## Calibration report

Every scoring implementation should be able to report:

```text
threshold
sample_size
persist_retention_rate
false_permanence_rate
evaporation_rate_for_true_ephemeral
trap_class_failure_rate
durability_dimensions_tested
scope_of_validity
calibration_error
boundary_instability_rate
abstention_rate
estimator_disagreement_rate
out_of_scope_rate
estimator_version
calibration_version
```

Metrics that are not meaningful for a given estimator may be marked not applicable with justification rather than fabricated.

## Operating-point selection

The threshold should be chosen according to cost:

| Preference | Threshold behavior |
|---|---|
| Avoid false permanence | higher threshold, uncertainty band, require certification |
| Avoid losing valuable memories | lower candidate threshold, stronger review queue |
| Balance both costs | calibrated threshold using explicit tradeoff |
| High uncertainty near irreversible consequence | abstain, collect evidence, or escalate |

## Drift and versioning

Estimator changes and policy changes are different events.

A conforming implementation should be able to distinguish:

```text
same policy + new estimator
new policy + same estimator
new calibration + same estimator
new environment outside prior calibration scope
```

A previous authorization should not be reinterpreted under a new estimator or policy without an explicit replay or migration decision.

## Hard rules

No score should grant permanence alone.

Only a governed transition can do that.

No deterministic threshold should be treated as proof that the underlying estimate is correct.

No probabilistic estimator should be allowed to define its own authority.
