# Governed Memory Evidence: Slice 7B

## Baseline

```text
baseline_main_commit: bf0baa69f268e5ed2b97ec98eed9199bed1ff1ac
```

At baseline the repository had:

- 2 JSON Schemas
- 8 original conformance fixtures
- a fixture validator focused on lifecycle/saturation/PAMA structure
- conformance-report schema capped at Level 5
- no decision-receipt schema
- no audit-event schema
- no repository CI workflow validating doctrine evidence

## Scope

This slice moves governed uncertainty from documentation into machine-readable contracts and adversarial fixture definitions.

### New contracts

- `docs/30-memory-observability-and-audit-events.md`
- `docs/31-recovery-rollback-and-replay.md`
- `docs/32-memory-quality-metrics.md`

### Schema work

Updated:

- `schemas/memory-unit.schema.json`
- `schemas/conformance-report.schema.json`

Added:

- `schemas/decision-receipt.schema.json`
- `schemas/memory-audit-event.schema.json`

### Validation tooling

Updated:

- `scripts/validate_fixtures.py`

Added:

- `scripts/validate_schemas.py`
- `.github/workflows/validate-doctrine-evidence.yml`

## Schema changes

### Memory unit

The schema remains backward-compatible with the original required fixture shape while adding optional doctrine fields for:

- schema version
- richer memory types and acquisition modes
- archive/tombstone states
- scope and tenancy
- sensitivity
- derivation provenance
- typed signals and signal semantics
- estimator/calibration provenance
- uncertainty representations
- policy version
- permitted/prohibited action sets
- selection mode
- certification revocation
- retention/deletion state
- decision-receipt references

### Conformance report

The schema now supports **Level 6 governed uncertainty** and metrics including:

- calibration error
- boundary instability
- abstention
- estimator disagreement
- out-of-calibration-scope rate
- unsafe recall
- cross-scope admission
- blocked-action escape
- stochastic action-set violation
- deletion residue
- replay reconstruction
- correction propagation

### Decision receipt

The new schema records:

```text
request
state snapshot
estimator/calibration context
policy version
authority refs
permitted/prohibited actions
selected action
selection mode
before/after state
evidence
recovery reference
```

The fixture validator enforces the cross-field invariant that a selected action must be in the permitted action set because portable JSON Schema cannot conveniently express that sibling-array membership constraint.

### Audit event

The new audit-event schema represents structured memory events, uncertainty-bearing signals, policy/authority context, action envelopes, and receipt references.

## New governed-uncertainty fixtures

This slice adds 16 adversarial fixture definitions:

1. `high-confidence-false-promotion.json`
2. `threshold-jitter.json`
3. `estimator-disagreement.json`
4. `cross-tenant-relevance-trap.json`
5. `stochastic-retrieval-policy-envelope.json`
6. `unsafe-multi-memory-composition.json`
7. `uncertain-sensitivity-before-export.json`
8. `irreversible-deletion-under-uncertain-utility.json`
9. `policy-estimator-version-drift.json`
10. `concurrent-conflicting-mutation.json`
11. `sleeper-memory-poisoning.json`
12. `authority-laundering.json`
13. `deletion-residue.json`
14. `out-of-calibration-scope.json`
15. `expired-delegation.json`
16. `stochastic-replay-reconstruction.json`

Together with the 8 original fixtures, the repository contains 24 fixture definitions on this branch.

## What fixture validation proves

Structural validation demonstrates:

- fixture JSON parses
- required memory fields exist
- lifecycle/PAMA enums are valid
- action envelopes have no permitted/prohibited overlap
- selected actions belong to permitted sets
- governed-uncertainty fixtures declare expected invariants
- memory units conform to the doctrine schema
- JSON Schemas themselves are valid Draft 2020-12 schemas

## What fixture validation does **not** prove

Passing these files does not prove that any runtime implementation:

- detects poisoning correctly
- calibrates uncertainty correctly
- blocks cross-tenant memory in production
- contains stochastic planners across repeated trials
- deletes derived memory completely
- resolves concurrency correctly
- satisfies ADR-020 end to end

These fixtures are executable **test definitions and structural evidence**, not runtime behavioral evidence.

## ADR implications

- ADR-013 through ADR-019 now have their dedicated contracts and repository-level schema/fixture prerequisites substantially satisfied.
- Their doctrine-acceptance status may be reconsidered in a separate incremental status PR.
- ADR-020 must remain **Proposed** because its acceptance criteria still require at least one real implementation mapped and tested end-to-end from estimate -> governance -> permitted action set -> commit, including repeated stochastic behavioral evidence where applicable.

## Validation gate

The exact PR #40 head `a485e7b5c9ac0ad3aae505c606020f0848adf9a7` was validated by GitHub Actions run `31437263174` before this audit-status update.

Both substantive validation steps completed successfully:

```text
Validate fixture invariants: success
Validate JSON Schemas and fixture memory units: success
```

Workflow:

```text
.github/workflows/validate-doctrine-evidence.yml
```

Because this audit update creates a new head, the workflow must pass again on the final PR head before merge.

## Merge criteria

- [x] docs 30-32 created
- [x] memory-unit schema reconciled additively
- [x] conformance schema supports Level 6
- [x] decision-receipt schema added
- [x] audit-event schema added
- [x] fixture validator enforces action-envelope invariants
- [x] schema validator added
- [x] 16 governed-uncertainty fixture definitions added
- [x] repeatable GitHub Actions validation added
- [x] substantive validators passed on pre-audit-update PR head
- [x] branch diff reviewed against main
- [ ] workflow passes again on final PR head
- [ ] merge by exact validated head SHA
