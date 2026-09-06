# Governed Uncertainty Audit: Slice 2

## Scope

This audit slice measures and remediates the implementation-facing doctrine documents:

- `05-repo-implementation-map.md`
- `06-conformance-test-plan.md`
- `07-integration-roadmap.md`
- `08-source-material-index.md`
- `09-calibration-protocol.md`
- `10-memory-unit-examples.md`

The scoring rubric is defined in `docs/25-governed-uncertainty-documentation-conformance-audit.md`.

## Baseline

```text
baseline_main_commit: e156f48680a27d72951875d88f91ceeed4cc7de6
baseline_source: merged PR #33 / governed uncertainty audit slice 1
```

Scores measure documentation coverage only, not runtime correctness.

## Baseline scores

| Document | GU-1 | GU-2 | GU-3 | GU-4 | GU-5 | GU-6 | GU-7 | GU-8 | GU-9 | GU-10 | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `05-repo-implementation-map.md` | 4 | 2 | 4 | 1 | 3 | 3 | 2 | 0 | 1 | 1 | 53% |
| `06-conformance-test-plan.md` | 3 | 1 | 4 | 1 | 4 | 3 | 4 | 0 | 2 | 4 | 65% |
| `07-integration-roadmap.md` | 2 | 0 | 2 | 0 | 2 | 1 | 2 | 0 | 2 | 3 | 35% |
| `08-source-material-index.md` | N/A | 3 | 3 | 3 | N/A | N/A | N/A | N/A | 1 | 2 | 60% |
| `09-calibration-protocol.md` | N/A | 4 | 4 | 2 | 3 | 3 | 3 | N/A | 2 | 4 | 78% |
| `10-memory-unit-examples.md` | 3 | 3 | 4 | 1 | 3 | 3 | 2 | 0 | 1 | 1 | 53% |

## Baseline findings

### 05 implementation map

Strong role ownership existed for identity, confidence, authority, and runtime memory, but the map did not require implementations to expose the boundary between estimator output, governance outcome, bounded action selection, and committed state change.

### 06 conformance test plan

Existing traps covered access spam, confident falsehood, contradiction, unauthorized mutation, and pruning. Missing tests were concentrated exactly where governed uncertainty becomes falsifiable:

- threshold jitter
- estimator disagreement
- cross-tenant high relevance
- stochastic retrieval under policy
- unsafe multi-memory composition
- uncertainty in sensitivity classification
- irreversible deletion from uncertain utility
- policy-versus-estimator version drift
- concurrent conflicting mutation

### 07 integration roadmap

The roadmap substantially predated the governed-uncertainty doctrine. It scheduled threshold calibration and PAMA, but not boundary inventory, estimator provenance, decision receipts, repeated-seed testing, abstention, drift, or evidence required to move ADR-020 from Proposed to Accepted.

### 08 source material index

The evidence-transfer rule was already strong, but the index did not yet formalize support versus challenge evidence, research accessibility preference, runtime-assurance evidence, memory uncertainty, or a doctrine challenge ledger.

### 09 calibration protocol

The protocol correctly treated saturation as calibrated routing rather than truth, but calibration focused on class separation and one operating threshold. It did not yet distinguish probability from arbitrary normalized score, measure boundary stability, support abstention/hysteresis, track estimator disagreement and distribution shift, or version calibration separately from estimator and policy.

### 10 memory examples

Examples preserved identity, evidence, saturation, PAMA, and certification, but they modeled point estimates without enough information to reconstruct:

- what the score meant
- which estimator produced it
- which calibration applied
- how uncertain it was
- which policy version consumed it
- what actions were permitted or prohibited
- what transition was actually committed

## Remediation applied

### 05 implementation map

- added governed-uncertainty posture per system
- added cross-repo control classes: deterministic substrate, probabilistic epistemics, governance envelope, bounded action selection, committed consequence
- added implementation evidence requirements
- made read-time and write-time enforcement responsibilities explicit

### 06 conformance test plan

- added Level 6 governed-uncertainty conformance
- added fixtures I through R for uncertainty-specific failure modes
- separated variable-by-design stochastic behavior from required invariants
- added repeated-trial guidance
- expanded conformance report fields with policy, estimator, calibration, and boundary-stability evidence

### 07 integration roadmap

- added governed-uncertainty boundary inventory
- expanded cross-repo alignment tasks
- added runtime enforcement requirements
- expanded calibration into uncertainty/drift testing
- added decision receipts and replay phase
- added research challenge loop
- made ADR-020 acceptance depend on executable evidence

### 08 source material index

- added uncertainty, adaptive memory control, runtime assurance, security composition, and calibration research domains
- added open-access preference without allowing accessibility to outrank evidence quality
- classified research use as support, challenge, boundary, mechanism, failure mode, or design candidate
- added doctrine challenge ledger shape
- expanded open questions to explicitly include determinism/probability challenges

### 09 calibration protocol

- explicitly distinguishes normalized scores from probabilities
- adds probabilistic metrics only when a probabilistic interpretation is claimed
- adds decision-boundary stability, abstention, hysteresis, disagreement, distribution shift, and repeated-trial testing
- separates estimator, calibration, and policy versioning
- adds calibration scope by memory and consequence class

### 10 memory examples

- added score semantics, estimator IDs/versions, calibration versions/scopes, and uncertainty representations
- added policy versions, permitted actions, prohibited actions, and selection mode
- added decision receipts separating proposal, authority, and committed transition
- added an uncertain preference that correctly requests confirmation instead of crystallizing
- added a high-relevance wrong-tenant retrieval that is blocked before context assembly

## Post-remediation scores

`N/A` excludes criteria not materially owned by the document from the denominator.

| Document | GU-1 | GU-2 | GU-3 | GU-4 | GU-5 | GU-6 | GU-7 | GU-8 | GU-9 | GU-10 | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `05-repo-implementation-map.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 95% |
| `06-conformance-test-plan.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 100% |
| `07-integration-roadmap.md` | 3 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 98% |
| `08-source-material-index.md` | N/A | 4 | 4 | 4 | N/A | N/A | N/A | N/A | 4 | 4 | 100% |
| `09-calibration-protocol.md` | N/A | 4 | 4 | 4 | 4 | 4 | 3 | N/A | 4 | 4 | 97% |
| `10-memory-unit-examples.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | N/A | N/A | 100% |

## Why remaining non-maximal scores remain

- `05` maps ownership and evidence expectations but does not itself define detailed drift tests; those belong to `06` and `09`.
- `07` is a roadmap and therefore schedules deterministic-substrate verification rather than specifying every substrate contract.
- `09` preserves the data necessary for calibration replay but does not own the full mutation decision receipt, which belongs to lifecycle/PAMA governance.

## Slice 2 verification requirements

Before merge:

- [x] baseline is anchored to merged slice 1
- [x] all six documents were read before remediation
- [x] baseline scores preserve the pre-remediation state
- [x] all six documents were remediated within their actual purpose
- [x] no score, confidence, relevance, or predicted utility is granted direct authority
- [x] conformance now tests stochastic behavior by invariants rather than requiring identical random outputs
- [x] calibration does not falsely treat every 0-to-1 score as a probability
- [x] roadmap keeps ADR-020 Proposed pending implementation evidence
- [x] examples distinguish estimator output, policy outcome, action set, and committed consequence
- [ ] final branch diff reviewed against `main`
- [ ] PR head verified mergeable
- [ ] commit status checked
- [ ] merged using exact verified head SHA

## Next slice

Slice 3 should audit:

- `11-component-architecture.md`
- `12-concept-segmentation-matrix.md`
- `13-system-composition-boundaries.md`
- `14-expanded-scope-recommendations.md`

The emphasis should be architectural composition: whether uncertainty boundaries remain intact when components are combined rather than inspected individually.
