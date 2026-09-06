# Governed Uncertainty Audit: Slice 3

## Scope

This slice audits the architectural-composition documents:

- `11-component-architecture.md`
- `12-concept-segmentation-matrix.md`
- `13-system-composition-boundaries.md`
- `14-expanded-scope-recommendations.md`

The emphasis is not individual component correctness. It is whether uncertainty, authority, scope, and provenance survive composition across component boundaries.

## Baseline

```text
baseline_main_commit: 880dc1946ad22b6a2ef2208b666653992344bfa1
baseline_source: merged PR #34 / governed uncertainty audit slice 2
```

## Baseline scores

| Document | GU-1 | GU-2 | GU-3 | GU-4 | GU-5 | GU-6 | GU-7 | GU-8 | GU-9 | GU-10 | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `11-component-architecture.md` | 4 | 2 | 4 | 1 | 3 | 3 | 2 | 0 | 1 | 2 | 55% |
| `12-concept-segmentation-matrix.md` | 4 | 2 | 4 | 1 | 3 | 2 | 1 | 0 | 1 | 2 | 50% |
| `13-system-composition-boundaries.md` | 4 | 2 | 4 | 1 | 4 | 3 | 3 | 0 | 1 | 2 | 60% |
| `14-expanded-scope-recommendations.md` | 2 | 2 | 3 | 1 | 2 | 3 | 1 | 0 | 1 | 2 | 43% |

## Key baseline findings

### Composition lost signal semantics

The existing component and handoff models preserved evidence, policy, authority, and ledger references, but not enough information to distinguish:

- deterministic fact from probabilistic estimate
- confidence from probability
- estimator version from policy version
- uncertain classification from negative classification
- recommendation from authority

That creates a type-erasure risk at exactly the point components compose.

### Safe components were implicitly treated as sufficient

The architecture described bounded responsibilities well, but did not explicitly model composition failures such as:

- scope laundering through summaries
- stale authorization after state change
- cross-tenant high-relevance retrieval
- unsafe multi-memory composition
- utility estimates becoming deletion instructions
- uncertainty being coerced into booleans

### Conflict resolution wording was overly deterministic

`14-expanded-scope-recommendations.md` described the future conflict engine as needing a deterministic conflict-resolution method. That was too broad.

Conflict detection, classification, source comparison, and causal interpretation may remain probabilistic. The governed requirement belongs at the consequence boundary: dispute, correction, split scope, escalation, retention of both claims, or other policy-defined outcomes.

This is recorded as an actual doctrine correction, not merely an expansion.

## Remediation applied

### `11-component-architecture.md`

- classified each component by typical control character
- added uncertainty-preserving handoffs
- separated proposal, authority envelope, selection, and commit
- added composition failure as first-class failure mode
- added handoff metadata for estimator/version/calibration/policy/action set
- expanded maturity levels to include handoff and composition testing

### `12-concept-segmentation-matrix.md`

- added estimator provenance, uncertainty representation, calibration scope, abstention, hysteresis, disagreement, action sets, policy/estimator versions, and receipts
- added control-character classification
- added explicit question: estimate, authority decision, action selection, or committed consequence?
- corrected conflict handling to allow probabilistic interpretation with governed consequences

### `13-system-composition-boundaries.md`

- expanded contracts to preserve signal semantics and uncertainty
- added action-selection contract
- added recall-admission semantics
- added handoff invariants
- added semantic type erasure, boolean coercion, authority leakage, scope laundering, stale authorization, unsafe composition, and deterministic-wrapper failure modes
- added end-to-end composition conformance paths

### `14-expanded-scope-recommendations.md`

- classified future components by governed-uncertainty posture
- changed conflict resolution from globally deterministic to probabilistic interpretation plus governed consequence
- added explicit control rules for source trust, temporal causality, sensitivity, economics, recall planning, multi-agent memory, and memory compiler
- added new threat classes for estimator manipulation, calibration drift, policy bypass, unsafe composition, and authority laundering

## Post-remediation scores

| Document | GU-1 | GU-2 | GU-3 | GU-4 | GU-5 | GU-6 | GU-7 | GU-8 | GU-9 | GU-10 | Coverage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `11-component-architecture.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 98% |
| `12-concept-segmentation-matrix.md` | 4 | 4 | 4 | 4 | 4 | 3 | 3 | 4 | 4 | 4 | 95% |
| `13-system-composition-boundaries.md` | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 4 | 100% |
| `14-expanded-scope-recommendations.md` | 3 | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 | 95% |

## Remaining non-maximal scores

- `11` defines architecture rather than calibration algorithms, so GU-9 is intentionally delegated.
- `12` is a taxonomy and placement matrix, not the primary owner of consequence-proportionality or full receipts.
- `14` recommends future work rather than defining exact substrate and replay implementations.

## Verification requirements

- [x] all four documents read before remediation
- [x] baseline anchored to merged slice 2
- [x] actual contradictory wording identified and corrected rather than preserved by inertia
- [x] component handoffs now preserve estimate semantics and authority boundaries
- [x] composition failure is independently testable
- [x] bounded stochastic selection is explicit
- [x] no recommendation grants authority from confidence, trust, relevance, utility, or classification alone
- [ ] final branch diff reviewed against `main`
- [ ] PR head verified mergeable
- [ ] commit status checked
- [ ] merged using exact verified head SHA

## Next slice

Audit documents `15` through `19` where present. These are high-value because they own threat modeling, source trust, conflict resolution, temporal causality, and privacy/sensitivity, all of which directly determine whether probabilistic memory behavior remains governable.
