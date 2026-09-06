# Calibration Report: EvolveAI-reference v0.0.0-example

**Overall assessment**: PASS

## Versioning

| Field | Value |
|---|---|
| implementation | EvolveAI-reference |
| version | v0.0.0-example |
| doctrine_version | v0.3 |
| estimator_version | mts-saturation-example-v2 |
| calibration_version | cal-2026-08-example |
| sigma_is_probabilistic | false |

## Operating point

- threshold: 0.8
- review_band: 0.7 to 0.85

## Required measurements

| Measurement | Value |
|---|---|
| threshold | 0.8 |
| sample_size | 13 |
| persist_retention_rate | 0.8 |
| false_permanence_rate | 0.0 |
| evaporation_rate_for_true_ephemeral | 0.75 |
| trap_class_failure_rate | 0.0 |
| boundary_instability_rate | 0.2 |
| abstention_rate | 0.1538 |
| estimator_disagreement_rate | 0.3333 |
| out_of_scope_rate | 0.0769 |
| durability_dimensions_tested | corroboration, cross_reference, verification, meaningful_reuse |
| estimator_version | mts-saturation-example-v2 |
| calibration_version | cal-2026-08-example |

## Class distributions

| Class | Cases | sigma min | sigma mean | sigma max |
|---|---|---|---|---|
| PERSIST | 5 | 0.820 | 0.862 | 0.910 |
| EVAPORATE | 4 | 0.220 | 0.415 | 0.680 |
| TRAP | 4 | 0.770 | 0.797 | 0.830 |

Distribution overlap matters more than mean score. Performance must be read in the region where policy consequences change.

## Trap-class outcomes

| Case | sigma | Observed outcome |
|---|---|---|
| trap-access-spam-junk | 0.790 | evaporated |
| trap-confidently-wrong | 0.830 | review |
| trap-threshold-jitter | 0.800 | abstained |
| trap-out-of-distribution | 0.770 | review |

## Scope of validity

```yaml
memory_types:
  - project_decision
  - code_relation
consequence_classes:
  - candidate_routing
  - pending_verification
excluded:
  - permanent_deletion
  - cross_tenant_scope_expansion
```

This calibration is valid only for the durability dimensions and consequence classes tested.

## Known exemptions

- human preference memories require explicit approval regardless of sigma

## Doctrine

Calibrated saturation is a lifecycle signal. It is not identity, not truth, not
certification, and not permission. Eligibility is not authorization: candidates
identified by this calibration still require certification and PAMA authority
before crystallization.

