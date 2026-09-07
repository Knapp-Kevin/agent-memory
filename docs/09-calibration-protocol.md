# Saturation Calibration Protocol

## Purpose

This protocol defines how to calibrate saturation before using it to route, retain, evict, or propose crystallization for memory units.

Saturation is useful only when it separates objects that should persist from objects that should evaporate. Until calibrated, saturation is just a number with confidence issues. So, naturally, we must supervise it.

Calibration must also establish what the score **does not mean**. A calibrated lifecycle score is still not identity, truth, authority, certification, or permission.

## Calibration question

The calibration question is:

```text
Does sigma separate persist-worthy memory from evaporate-worthy memory across the durability dimensions this implementation claims to support, with acceptable uncertainty and decision-boundary stability?
```

It is not:

```text
Does sigma look intuitively reasonable?
```

Human intuition is how we got password reuse and meetings that could have been emails. Do not use it as a thresholding method.

## Is sigma a probability?

Do not assume so.

If an implementation claims that `sigma = 0.80` means an 80% probability that a memory belongs in a durable class, then probabilistic calibration metrics may apply directly.

If sigma is merely an ordinal, composite, heuristic, or routing score, evaluate ranking quality, separation, stability, and consequence performance instead.

A non-probability score should not acquire fake probabilistic meaning because it happens to fit between 0 and 1. Decimals are persuasive little creatures.

## Required labeled classes

### PERSIST

Objects that should remain durable or enter a non-decaying regime within a defined scope.

Examples:

- corroborated project decision
- verified code artifact relationship
- user-approved preference
- policy rule with provenance
- recurring, meaningful, cross-referenced memory

### EVAPORATE

Objects that should decay, expire, or remain outside durable memory.

Examples:

- one-time transient context
- uncorroborated single-source assertion
- stale runtime trace
- temporary task note
- contradicted observation

### TRAP

Objects designed to fool naive saturation logic.

Required traps:

- access-spam junk
- confidently-wrong memory
- overfit single-source fact
- stale-but-frequently-recalled memory
- threshold-jitter candidate
- estimator disagreement
- distribution-shift candidate

## Calibration process

1. Build a labeled fixture set.
2. Partition by memory class, risk class, and consequence class when sample size allows.
3. Drive each fixture through realistic interaction history.
4. Record sigma and supporting estimator outputs at the decision point.
5. Repeat stochastic components across multiple seeds or trials where relevant.
6. Plot or compare PERSIST, EVAPORATE, and TRAP distributions.
7. Measure overlap and calibration error where the score supports probabilistic interpretation.
8. Measure decision-boundary stability under small perturbations.
9. Measure estimator disagreement where multiple estimators contribute.
10. Identify an abstention or review region when uncertainty near a consequential boundary is unacceptable.
11. Choose the operating point based on explicit operational cost.
12. Report scope of validity, estimator version, calibration version, and known exclusions.

## Required measurements

```text
threshold
sample_size
persist_retention_rate
false_permanence_rate
evaporation_rate_for_true_ephemeral
trap_class_failure_rate
durability_dimensions_tested
scope_of_validity
boundary_instability_rate
abstention_rate
estimator_disagreement_rate
out_of_scope_rate
estimator_version
calibration_version
```

If the score is explicitly probabilistic, additionally report suitable calibration metrics such as:

```text
calibration_error
reliability_curve_or_bins
proper_scoring_rule_if_used
confidence_interval_or_uncertainty_band
```

Examples of proper scoring rules include Brier score or log loss. Their use is optional and appropriate only when the output has a probabilistic interpretation.

## Threshold selection

| Goal | Threshold behavior |
|---|---|
| Avoid false permanence | raise threshold, use uncertainty band, require certification |
| Avoid losing valuable memory | lower candidate threshold but require review |
| Balance costs | choose threshold from explicit tradeoff curve |
| Avoid unstable decisions near boundary | add hysteresis, abstention, review, or more evidence |
| High consequence + invalid calibration scope | block promotion or require external verification |

## Thresholds are policy operating points

A threshold does not make the underlying estimate deterministic.

```text
sigma >= 0.80
```

may be a deterministic comparison over a probabilistic or noisy estimate.

Therefore:

```text
deterministic comparison != deterministic truth
```

The comparison can propose a policy branch. It does not erase uncertainty in sigma.

## Overlap rule

Distribution overlap matters more than mean score.

A persist mean of 0.92 and evaporate mean of 0.33 is not enough if trap objects still cross the crystallization threshold.

Report performance specifically in the region where policy consequences change.

## Decision-boundary stability

A calibration should test how easily the decision changes under small perturbations.

Perturbations may include:

- equivalent paraphrases
- slightly different access histories
- small timing differences
- one additional weak source
- one missing low-weight source
- stochastic retrieval order
- minor model-version variation

Measure whether these changes produce disproportionate lifecycle consequences.

Suggested metric:

```text
boundary_instability_rate = unstable_equivalent_cases / tested_equivalent_cases
```

A system may define a better metric if documented.

## Hysteresis

If small score changes would otherwise cause repeated promotion and demotion, use hysteresis or an equivalent state-stability mechanism.

Example only:

```text
candidate_enter_threshold = 0.80
candidate_exit_threshold  = 0.70
```

These numbers are not doctrine. The requirement is that estimator noise not manufacture lifecycle churn.

## Abstention and review region

For consequential actions, a useful calibration may produce three regions rather than one threshold:

```text
LOW
ordinary non-promotion path

UNCERTAIN
collect evidence / abstain / require review / require external verification

HIGH
eligible for next governance gate
```

Eligibility is not authorization.

## Estimator disagreement

If multiple estimators contribute to lifecycle scoring, measure how often they materially disagree.

Do not automatically average disagreement away.

Record:

```text
estimators_involved
disagreement_measure
decision_region
policy_resolution
```

A disagreement near an irreversible consequence boundary should usually trigger stronger handling than disagreement over an ephemeral cache decision.

## Distribution shift

Calibration expires outside the conditions it was validated for.

Track changes in:

- memory type distribution
- source types
- user population or tenant context
- model version
- retrieval strategy
- environment or product workflow
- adversarial pressure

When shift is material:

```text
old_calibration_claim != automatically_valid
```

Policy may require recalibration, review, or a more conservative operating mode.

## Trap-class rule

If a trap class crystallizes, the calibration failed.

That does not mean the trap object was secretly valuable. It means the scoring model or governance integration is measuring or using the wrong thing.

A calibration can also fail if:

- point estimates appear accurate on average but decisions are unstable near thresholds
- estimator disagreement is hidden
- out-of-scope inputs silently reuse old calibration claims
- abstention is impossible even when uncertainty is high
- a high score bypasses certification or PAMA

## Scope of validity

A calibration is valid only for the durability dimensions and consequence classes tested.

For example, a calibration that tests only cryptographic verification says nothing about social corroboration, repeated meaningful use, decision continuity, sensitivity classification, or cross-tenant retrieval.

## Example calibration report

```yaml
implementation: EvolveAI-reference
version: v0.0.0-example
doctrine_version: v0.3
estimator_version: mts-saturation-example-v2
calibration_version: cal-2026-08-example
threshold: 0.80
review_band:
  lower: 0.70
  upper: 0.85
sample_size: 240
persist_retention_rate: 0.92
false_permanence_rate: 0.01
evaporation_rate_for_true_ephemeral: 0.88
trap_class_failure_rate: 0.00
boundary_instability_rate: 0.03
abstention_rate: 0.11
estimator_disagreement_rate: 0.07
out_of_scope_rate: 0.02
durability_dimensions_tested:
  - corroboration
  - cross_reference
  - verification
  - meaningful_reuse
scope_of_validity:
  memory_types:
    - project_decision
    - code_relation
  consequence_classes:
    - candidate_routing
    - pending_verification
  excluded:
    - permanent_deletion
    - cross_tenant_scope_expansion
known_exemptions:
  - human preference memories require explicit approval regardless of sigma
```

## Certification interaction

Calibration may identify crystallization candidates.

Certification and PAMA decide whether crystallization is allowed.

```text
calibrated_estimate -> candidate proposal
candidate proposal + policy/PAMA -> permitted next action
permitted promotion path + certification -> crystallized
```

A more compact shorthand is:

```text
sigma >= threshold -> candidate
candidate + certification + PAMA allow -> crystallized
```

but implementations must not confuse the shorthand with the full uncertainty and governance path.

## Versioning and replay

A calibration report should allow maintainers to distinguish:

```text
same estimator + new calibration
new estimator + same policy
new policy + same estimator
new environment outside calibration scope
```

A prior authority decision remains evidence of what was authorized under its original policy and estimator context. It should not be silently reinterpreted as though the new versions had produced the old decision.

## Doctrine

Calibrated saturation is a lifecycle signal.

It is not identity, not truth, not certification, and not permission.

A deterministic threshold does not make an uncertain estimate true.

A probabilistic estimate does not make governance optional.
