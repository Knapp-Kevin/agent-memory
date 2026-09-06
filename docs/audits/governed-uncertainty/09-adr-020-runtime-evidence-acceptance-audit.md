# ADR-020 Runtime Evidence Acceptance Audit

## Purpose

Re-evaluate the fourteen executable-evidence gates in ADR-020 against the current merged runtime-evidence program before any status change.

This audit is evidence reconciliation. It does not itself accept ADR-020, raise a conformance level, or convert a narrow reference adapter into a complete Agent Memory implementation.

## Baseline

Audit baseline:

```text
main: 43b8d23d959b080fce14144c41a7658565d44352
ADR-020 status: Proposed
```

The durable runtime program and reference adapter now include real-substrate execution, stochastic containment, canonical/derived/projection lifecycle evidence, portable governance evidence, Agent Manifest correlation, TRACE/cMCP action-evidence comparison, concurrency-conflict evidence, a benchmark/security scorecard, and a pinned Mem0 adversarial comparator.

Primary evidence surfaces:

- `reference/README.md`
- `docs/programs/runtime-evidence/README.md`
- `docs/programs/runtime-evidence/concurrency-conflict-evidence.md`
- `docs/programs/runtime-evidence/canonical-and-derived-state.md`
- `docs/programs/runtime-evidence/deletion-completeness-evidence.md`
- `docs/programs/runtime-evidence/portable-governance-evidence.md`
- `docs/programs/runtime-evidence/agent-manifest-correlation.md`
- `docs/programs/runtime-evidence/trace-action-evidence.md`
- `docs/programs/runtime-evidence/benchmark-security-scorecard.md`
- `docs/programs/runtime-evidence/mem0-adversarial-comparator.md`
- `docs/06-conformance-test-plan.md`

## Gate-by-gate audit

| # | ADR-020 acceptance gate | Current evidence | Audit result |
|---|---|---|---|
| 1 | High-confidence false memory cannot self-promote | Reference path exercises confidence `0.99` versus `0.01` under an identical authority envelope; confidence has no route to promotion authority. | Satisfied |
| 2 | High-relevance wrong-tenant memory cannot enter context | Real-substrate path demonstrates the permissive substrate could return foreign state while the governed adapter enforces explicit scope before admission. | Satisfied |
| 3 | Probabilistic contradiction detection cannot silently overwrite certified state | Doctrine fixtures and governed mutation boundary require proposal/authority handling; contradictory or superseding state cannot directly commit through estimator output. | Satisfied |
| 4 | Stochastic retrieval/action selection cannot bypass policy filters | Seeded stochastic trials vary selection while remaining inside the permitted action set; a hostile selector that returns a prohibited action is contained and recorded. | Satisfied |
| 5 | Uncertain sensitivity is handled safely for high-consequence disclosure | The governed-uncertainty fixture corpus includes uncertain-sensitivity escalation and prevents high-consequence expansion from assuming non-sensitive state. | Satisfied |
| 6 | Predicted low utility cannot independently authorize irreversible deletion | Irreversible deletion is not autonomously selectable from estimator utility; the substrate would execute it, while the governance layer refuses without consequence-appropriate authority. | Satisfied |
| 7 | Unsafe multi-memory composition is tested | The canonical fixture corpus includes the unsafe-composition path and drives its declared authority envelope through enforcement. | Satisfied |
| 8 | Policy-version drift is distinguishable from estimator/model drift | Reference receipts retain separate policy and estimator versions; the executed version-drift path preserves the distinction. | Satisfied |
| 9 | Concurrent conflicting mutations do not silently become last-writer-wins | `concurrency-conflict-evidence.md` executes two proposals from one prior state; the second stale authorization is deferred, exactly one write survives, and conflict evidence is reconstructable. | Satisfied |
| 10 | Selected action cannot escape its permitted set across stochastic trials | `run_conformance.py --trials` performs repeated seeded trials; the selector varies and no prohibited action becomes selectable. Hostile-selector containment separately tests attempted escape. | Satisfied |
| 11 | Authority and consequence remain reconstructable from receipts | Positive governed paths reconstruct estimate/proposal, authority envelope, permitted actions, selected action, before/after state, and consequence from schema-conformant receipts and linked events. | Satisfied |
| 12 | Derived-memory deletion residue is tested | P4 computes stale versus residual from recorded basis, traverses transitive purge closure, performs an independent residue sweep, and distinguishes declared residual, undeclared hard-gate failure, and zero-residue success. | Satisfied |
| 13 | At least one implementation is mapped end-to-end from estimate -> governance -> action set -> commit | The reference governed adapter executes the full path over a pinned real temporal-graph substrate and records the exact implementation/substrate/evidence versions. | Satisfied |
| 14 | At least one adversarial challenge causes a documented boundary, correction, or rejection rather than being ignored | Multiple adversarial paths do so: hostile selector escape is rejected and recorded; wrong-scope candidates are blocked; stale concurrent authorization is deferred; portable-evidence tamper/replay/domain/trust failures are classified; comparator gaps remain explicit rather than being normalized away. | Satisfied |

## Important claim boundary

Passing the fourteen ADR gates would support accepting the architectural decision. It would **not** imply:

- Level 6 conformance for the reference adapter;
- a complete implementation of decay, calibrated saturation, or every lifecycle state;
- universal correctness across every architecture family;
- production trust infrastructure, distributed serializability, or hardware attestation;
- acceptance of ADR-021 merely by association;
- completion of #46, #67, or #68.

The reference adapter deliberately emits a low conformance claim because the conformance ladder is cumulative and includes capabilities outside the narrow runtime-evidence slices. ADR acceptance and implementation conformance are different questions.

## Findings

All fourteen ADR-020 minimum acceptance gates now have executable or fixture-correlated evidence on the audited baseline.

The material gap recorded in the earlier Slice 7C audit has been closed in substance:

```text
real substrate                -> present
stochastic containment        -> present
cross-scope admission         -> present
concurrency behavior          -> present
deletion propagation/residue  -> present
reconstructable receipts      -> present
adversarial comparator        -> present
```

The remaining work before an ADR status change is procedural and coherence-oriented:

1. validate this audit at an exact PR head;
2. adversarially review the gate mappings for overclaiming;
3. if the audit remains intact, make the ADR status change in a separate focused PR;
4. synchronize the ADR index, canonical documentation index, runtime-evidence status, and reader-facing maturity surfaces;
5. do not raise the reference adapter's conformance level unless its independent cumulative requirements are met.

## Recommendation

**ADR-020 is acceptance-ready, subject to exact-head validation and an explicit status-change PR.**

Do not add more implementation merely to satisfy stale roadmap text when the stated acceptance gates are already evidenced. New runtime work should target broader architecture-family evidence, systems characterization, or unresolved implementation limitations after the decision status is reconciled.
