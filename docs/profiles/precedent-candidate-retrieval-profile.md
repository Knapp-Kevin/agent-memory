# Precedent Candidate Retrieval Profile

Status: reference implementation profile for issue #233. This profile adds candidate discovery upstream of the deterministic precedent-applicability boundary established by #181. It does not create a new authority surface.

## Boundary

```text
semantic / probabilistic estimator
    -> candidate precedent refs + estimator evidence
    -> deterministic #181 scope/currentness/material-condition evaluation
    -> advisory applicability context
    -> existing governance / PAMA composition
```

The estimator may improve which historical precedent is considered. It may not decide whether that precedent is materially applicable, current, within scope, or authorized.

The controlling deterministic implementation remains `reference/agentmem_ref/memory/precedent_applicability.py`. Candidate retrieval calls that evaluator after discovery rather than replacing or modifying it.

## Invariants

```text
similarity != material equivalence
similarity confidence != truth
candidate precedent != current precedent
current precedent != permission
repetition != independent human evidence
precedent-supported handling != standing authority
```

Retrieval evidence therefore carries explicit non-authority fields. It cannot authorize execution, change a permitted-action set, or create a grant or policy.

## Evidence surface

`schemas/precedent-candidate-retrieval.schema.json` defines reconstructable retrieval evidence. A completed or failed run records:

- estimator identifier and version;
- configuration and threshold references;
- score semantics and calibration posture;
- minimized query projection identity;
- candidate precedent and candidate projection identities;
- candidate score, rank, and threshold posture;
- run reference and execution timestamp;
- failure kind and fail-closed posture when the estimator is unavailable or unsupported;
- explicit non-authority fields on the run and each candidate.

Historical rationale is treated as evidence data only. The reference matcher never parses rationale text as instructions.

## Reference estimator

`DeterministicReferenceEstimator` is a deterministic conformance fake using a small canonicalization table and Jaccard token overlap. It exists to make the estimator/governance boundary executable without making embeddings, a specific model, Python, or any vendor canonical to Agent Memory.

Its score semantics are `canonicalized_token_jaccard_similarity_0_to_1` and its calibration posture is explicitly `uncalibrated_reference_fixture`. The reference threshold is `0.45` in the bounded harness. Those values are test configuration, not normative governance thresholds.

A production estimator may use a different implementation only if its identity, model/checkpoint or version, configuration, threshold reference, score semantics, calibration posture, minimized input identity, and run evidence remain reconstructable. Its output is still candidate evidence only.

## Adversarial harness

`reference/agentmem_ref/harness/precedent_candidate_harness.py` exercises twelve bounded cases:

1. safe paraphrase recovery;
2. force-main near match;
3. staging versus production;
4. ordinary versus sensitive material;
5. cross-tenant near match;
6. stale or revoked exact semantic match;
7. negative or incident precedent beside positive history;
8. policy-generated repetition;
9. ambiguous low-confidence retrieval;
10. estimator unavailable with deterministic fallback;
11. unsupported estimator version with deterministic fallback;
12. instruction-shaped historical rationale treated strictly as data.

Several unsafe cases are intentionally retrievable. That is not a failure of the harness. The governing safety requirement is that the deterministic applicability layer detects the material difference, stale state, foreign scope, incident evidence, or attribution distinction before advisory handling can reduce review.

## Metrics

Retrieval usefulness and governance safety are reported separately.

Retrieval usefulness includes:

- candidate recall on paraphrased-equivalent cases;
- irrelevant candidate rate;
- unsafe-near-match candidate rate.

Governance safety includes:

- final unsafe-equivalence false positives;
- material-difference misses;
- negative-precedent misses;
- cross-scope leakage failures;
- stale-precedent reuse failures;
- independent-human attribution errors;
- estimator-unavailable fallback success.

Higher retrieval recall never compensates for a non-zero unsafe-equivalence, scope-leakage, stale-reuse, negative-precedent, or attribution failure.

## Exact-head evidence

`.github/workflows/precedent-candidate-retrieval.yml` runs schema validation, the new focused tests, the existing #181 precedent-applicability tests, and the bounded harness on every push and pull request. It uploads `precedent-candidate-retrieval.json` as the `precedent-candidate-retrieval-evidence` artifact, bound to the pull-request head SHA.

The artifact is evidence of retrieval and deterministic-applicability behavior. It is not permission, a policy decision, or a standing grant.
