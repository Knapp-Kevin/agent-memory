# ADR-030: Temporal policy consumers require versioned compatible projections

- **Status:** Accepted
- **Date:** 2026-08-13
- **Accepted:** 2026-08-13
- **Related:** #255, #256, ADR-014, ADR-029

## Decision

Agent Memory requires a versioned compatibility/currentness evaluation before a memory-derived projection is treated as current input for an external temporal or authorization consumer.

```text
canonical memory
  -> governed projection
  -> compatibility/currentness evaluation
  -> consumer-specific evaluation
```

Serialization success is not semantic compatibility.

The compatibility contract uses four states:

- `current`
- `migration_required`
- `incompatible`
- `unknown`

`unknown` is not current.

## Binding

The evaluation binds the projection and source semantics to the exact target contract. Relevant evidence can include source currentness, domain-schema identity, projection identity/version, target schema and policy identity, temporal horizon, isolation evidence, and the context actually evaluated.

Changed semantics require new evidence. A rebuilt projection after migration receives a new identity rather than rewriting historical projection evidence.

Consumer-specific traces and caches remain derived representations rather than canonical Agent Memory history.

## Composition boundary

This decision does not change Agent Memory's existing governance decisions. External policy evaluation may add constraints but cannot silently make an otherwise disallowed memory consequence permissible.

External results remain decision evidence. They do not independently establish memory admission, human adjudication, reusable permission, or execution.

## Acceptance evidence

PR #257 comment `5286466614` records the fourteen-gate acceptance audit.

Pre-acceptance head:

`388bf2236bd222518605d09198856a2c469aee5a`

That head passed all 25 repository workflows.

Focused artifact:

- id `9198386134`
- digest `sha256:8a2effee0d3deadee88311cf12bbd1fdb650d22349a63d34a1103a1379591391`

Review added explicit post-migration projection-identity evidence and an explicit Cedarling schema-drift/revalidation case before promotion.

The Accepted head must pass the complete matrix before merge.

## Integration boundary

Dogwood, Cedar, and Cedarling remain optional peer systems behind adapters. Their schemas, traces, and caches do not define Agent Memory's canonical data model.

The initial Dogwood comparator is pinned to public source commit `c6237c88099b3f492ecc5fcee42df06a19224b97`.

## Canonical detail

- `docs/research/temporal-policy-semantic-mediation.md`
- `docs/profiles/policy-projection-compatibility-profile.md`
- `reference/agentmem_ref/memory/policy_projection_compatibility.py`
- `reference/tests/test_policy_projection_compatibility.py`
- `wiki-src/Temporal-Policy-and-Governed-Memory.md`
