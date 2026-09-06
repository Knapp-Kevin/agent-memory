# Governed Memory Contracts: Slice 7A

## Baseline

```text
baseline_main_commit: 38bedb2e0673dde2f92bee8b124489b355b427fd
```

## Scope

Creates the dedicated contracts required by Proposed ADRs 013 through 016:

- `26-governed-recall-planner.md`
- `27-schema-registry-and-type-evolution.md`
- `28-retention-deletion-and-tombstones.md`
- `29-actor-scope-consent-and-tenancy.md`

## Key boundaries established

### Recall

```text
candidate generation may be probabilistic
recall admission remains governed
relevance != permission
```

### Schema evolution

Compatibility includes semantic meaning, not only field names and JSON types.

Critical concepts remain separate:

```text
confidence
probability
similarity
trust
saturation
relevance
sensitivity
authority
certification
```

### Retention and deletion

Forgetting is split into reversible and irreversible modes. Predicted utility may propose pruning/deletion but cannot authorize irreversible erasure.

Deletion verification must consider derived memories, summaries, indexes, caches, graph relations, exports, and inherited copies where governed by the system.

### Actor scope and tenancy

Authority remains principal-, tenant-, project-, purpose-, consent-, and delegation-scoped.

Probabilistic identity/entity resolution cannot manufacture permission for high-consequence cross-scope operations.

## ADR maturity

ADRs 013-016 remain **Proposed** after this slice because their acceptance requirements also call for schema/fixture reconciliation and executable conformance evidence.

The documents are necessary but not sufficient.

## Next evidence slice

- reconcile `memory-unit.schema.json`
- reconcile `conformance-report.schema.json`
- add decision-receipt and audit-event schemas
- add governed-recall fixtures
- add deletion-residue fixture
- add scope/delegation fixtures

## Verification

- [x] all four missing dedicated contracts created
- [x] no conflict with existing docs 20-25 numbering
- [x] uncertain estimates remain separate from authority
- [x] irreversible deletion remains higher-authority than reversible forgetting
- [x] tenant/scope boundaries cannot be overridden by relevance
- [x] ADRs remain Proposed pending executable evidence
- [ ] final branch diff reviewed
- [ ] PR mergeability/status verified
- [ ] merge by exact head SHA
