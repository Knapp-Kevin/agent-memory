# Platinum README and Navigation Audit: Slice 8

## Purpose

This slice reconciles the repository front door with the architecture, evidence, and ADR maturity created by the prior incremental audits.

The goal is not to make the README contain every detail. It is to make the repository understandable quickly without hiding its depth or evidence boundaries.

## Baseline problem

The first Platinum README pass substantially expanded theory and architecture, but later audit slices added:

- governed-uncertainty refinements
- docs 15 through 32
- ADR maturity changes
- Level 6 conformance
- four JSON Schemas
- 24 validated fixture definitions
- repository validation CI
- explicit runtime-evidence requirements for ADR-020

The README had therefore become stale relative to the repository it introduced.

It was also closer to a long-form paper than a navigational front door.

## Presentation decisions

### Progressive disclosure

The new README prioritizes:

```text
hero + real status
  -> choose-your-path navigation
  -> core thesis
  -> architecture diagrams
  -> conformance/evidence
  -> maturity boundary
  -> deeper theory and contribution paths
```

The complete numbered-doc inventory now lives in `docs/README.md` rather than dominating the root README.

### Badges communicate real state

The README includes:

- actual `Validate Doctrine Evidence` workflow status
- reference-architecture status
- `19 Accepted | 1 Proposed` ADR state
- Level 6 specification status
- 24 validated fixture definitions
- open-evidence research posture

No license badge is included because the repository metadata does not currently declare a license. No runtime-conformance badge is included because no runtime has yet satisfied ADR-020 end to end.

### Reader-specific entry points

The README and docs index provide distinct paths for:

- researchers/theorists
- agent architects
- implementers
- security/privacy reviewers
- conformance evaluators
- product/UX designers
- ADR reviewers
- contributors

### Visual architecture

The README uses compact Mermaid diagrams for:

- governed-uncertainty flow
- lifecycle state progression

Diagrams are explanatory rather than decorative.

### Evidence boundary remains above the fold

The README explicitly distinguishes:

```text
validated doctrine schemas/fixtures
!=
runtime behavioral proof
```

ADR-020 remains visibly Proposed rather than being hidden after the presentation upgrade.

## Supporting navigation added

### `docs/README.md`

Provides the complete documentation index grouped by:

- 00-10 architecture spine
- 11-19 composition/security/trust/time/privacy
- 20-25 interdisciplinary theory
- 26-32 executable/operational contracts
- ADRs
- audit trail
- machine-readable evidence

### `CONTRIBUTING.md`

Defines:

- evidence standards
- challenge evidence as first-class contribution
- biological/cognitive transfer classifications
- architecture invariants
- ADR expectations
- schema migration standards
- fixture expectations
- local validation commands

## Navigation validation

A new standard-library validator checks relative repository links on the highest-value navigation surfaces:

```text
README.md
CONTRIBUTING.md
docs/README.md
docs/adr/README.md
```

Script:

```text
scripts/validate_markdown_links.py
```

The `Validate Doctrine Evidence` workflow now runs this check in addition to fixture and JSON Schema validation.

## Final maturity represented by README

```text
ADRs 001-019: Accepted
ADR-020: Proposed
JSON Schemas: 4
Fixture definitions: 24
Conformance specification: Level 6
Repository evidence validation: active
Runtime ADR-020 proof: incomplete
```

## Merge criteria

- [x] README reconciled with current architecture
- [x] meaningful badges added
- [x] full documentation index added
- [x] contribution guide added
- [x] progressive-disclosure navigation implemented
- [x] runtime evidence boundary remains explicit
- [x] ADR-020 remains Proposed
- [x] internal-link validator added
- [x] CI updated to validate primary navigation links
- [ ] final branch diff reviewed
- [ ] workflow passes on exact PR head
- [ ] merge by exact validated head SHA
