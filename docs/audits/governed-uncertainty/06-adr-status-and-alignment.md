# Governed Uncertainty Audit: Slice 6

## Scope

This slice audits all Agent Memory ADRs for:

- status accuracy
- consistency with the governed-uncertainty doctrine
- stale follow-up links
- accidental conflation of doctrine acceptance with implementation completion

## Baseline

```text
baseline_main_commit: 48201ebf3b42c62053ea48fc04129cb4a8eae66a
```

## Baseline finding

Every ADR from 001 through 020 was marked `Proposed`.

That no longer reflected repository reality. Several early decisions had become foundational assumptions throughout the canonical docs, while later ADRs still had unfinished dedicated contracts or explicit validation requirements.

Several ADRs also pointed to document numbers later occupied by the interdisciplinary theory corpus:

- ADR-013 -> stale `docs/20-governed-recall-planner.md`
- ADR-014 -> stale `docs/21-schema-registry-and-type-evolution.md`
- ADR-015 -> stale `docs/23-retention-deletion-and-tombstones.md`
- ADR-016 -> stale `docs/24-actor-scope-consent-and-tenancy.md`
- ADR-017 -> stale `docs/25-memory-observability-and-audit-events.md`
- ADR-018 -> stale `docs/26-recovery-rollback-and-replay.md`
- ADR-019 -> stale `docs/27-memory-quality-metrics.md`

## Status semantics added

`docs/adr/README.md` now defines:

```text
Proposed   = architecture candidate; required doctrine/evidence incomplete
Accepted   = canonical architecture decision; implementation may still be partial or absent
Superseded = replaced by a later ADR
Rejected   = intentionally not adopted
```

This prevents `Accepted` from being misread as `implemented everywhere`.

## Status decisions

| ADR | Result | Reason |
|---|---|---|
| 001 Identity vs memory | Accepted | deeply integrated into layer model and doctrine |
| 002 Saturation vs truth | Accepted | canonical scoring invariant; now also explicitly not authority |
| 003 Certification for crystallization | Accepted | canonical durable-transition boundary |
| 004 PAMA / equivalent mutation authority | Accepted | canonical authority boundary |
| 005 CodeGenome role | Accepted | canonical implementation-map role, not implementation-completeness claim |
| 006 Neurospace role | Accepted | canonical runtime role, not implementation-completeness claim |
| 007 Component architecture | Accepted | canonical architecture structure |
| 008 Threat model required | Accepted | dedicated threat-model doctrine now exists |
| 009 Source trust signal | Accepted | dedicated trust doctrine now exists; trust explicitly not authority |
| 010 Conflict resolution component | Accepted | dedicated conflict doctrine exists; deterministic overclaim corrected |
| 011 Temporal causality | Accepted | dedicated temporal doctrine exists; chronology/causality distinction clarified |
| 012 Privacy/sensitivity | Accepted | dedicated privacy doctrine exists; uncertain != non-sensitive |
| 013 Governed recall planner | Proposed | dedicated contract and executable recall-admission evidence still missing |
| 014 Schema registry/evolution | Proposed | registry/type-evolution doctrine and schema reconciliation still missing |
| 015 Retention/deletion/tombstones | Proposed | dedicated lifecycle-wide retention/deletion contract and residue fixtures still missing |
| 016 Actor scope/consent/tenancy | Proposed | dedicated scope/delegation contract and tests still missing |
| 017 Observability/audit events | Proposed | common event doctrine/schema still missing |
| 018 Recovery/rollback/replay | Proposed | dedicated recovery/replay contract and tests still missing |
| 019 Memory quality metrics | Proposed | dedicated ongoing-metrics contract and schema mapping still missing |
| 020 Governed uncertainty | Proposed | explicitly requires executable implementation/conformance evidence |

## Alignment corrections

### ADR-002

Saturation is now explicitly neither truth nor authority.

### ADR-003

Crystallization gate now refers to lifecycle candidacy rather than implying one scalar threshold is universally sufficient.

### ADR-004

PAMA now explicitly consumes uncertain signals without allowing those signals to self-authorize.

### ADR-006

Runtime recall now distinguishes relevance from context permission.

### ADR-007

Component architecture now requires uncertainty/provenance/authority semantics to survive handoffs.

### ADR-009

Source trust is explicitly scoped evidence, not authority or certification.

### ADR-010

Corrected prior deterministic overclaim:

```text
conflict interpretation may be probabilistic
resolution consequence is governed
```

### ADR-011

Corrected sequence/causality conflation:

```text
chronology may be exact
causal attribution may remain uncertain
```

### ADR-012

Added:

```text
classifier_uncertain != non_sensitive
```

### ADR-013 through ADR-019

Stale follow-up numbering is replaced with reserved slots 26 through 32 and specific evidence requirements.

### ADR-020

Title is refined in-file to **Probabilistic Discovery, Governed Consequences** while retaining the existing filename for history/link stability.

The ADR now explicitly distinguishes:

- deterministic
- probabilistic
- learned
- heuristic
- formally bounded
- governed

and requires authority boundedness/reconstructability rather than claiming authority certainty.

## Next canonical slots

Reserved by the updated Proposed ADRs:

```text
26 governed recall planner
27 schema registry and type evolution
28 retention, deletion, and tombstones
29 actor scope, consent, and tenancy
30 memory observability and audit events
31 recovery, rollback, and replay
32 memory quality metrics
```

These documents should be created in subsequent incremental slices before their corresponding ADRs are reconsidered for acceptance.

## Verification requirements

- [x] ADR status semantics documented
- [x] foundational ADRs accepted only where doctrine is already canonical
- [x] implementation maturity kept separate from ADR status
- [x] unresolved ADRs remain Proposed
- [x] stale document-number references removed
- [x] ADR-020 remains Proposed
- [x] ADR-020 acceptance evidence made stricter, not weaker
- [ ] final branch diff reviewed
- [ ] PR head verified mergeable
- [ ] commit status checked
- [ ] merge by exact verified head SHA
