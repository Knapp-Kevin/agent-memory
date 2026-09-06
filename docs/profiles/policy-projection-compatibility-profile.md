# Policy Projection Compatibility Profile

Status: reference profile under #256. ADR-030 is Accepted (2026-08-13).

## Boundary

A memory-derived projection is current policy input only when it is compatible with the exact target schema, policy identity, capabilities, and isolation assumptions.

```text
serializable projection != semantically current projection
unknown != current
```

The provider-neutral evaluation binds projection/source-schema identity, source currentness, target consumer/version, action/event schemas, policy identity, temporal horizon, isolation evidence, and actual evaluated context where relevant.

States are `current`, `migration_required`, `incompatible`, and `unknown`. Compatibility has no authority effect and does not establish admission, approval, execution, enforcement, or certification.

Schema: `schemas/policy-projection-compatibility.schema.json`  
Evaluator: `reference/agentmem_ref/policy_projection_compatibility.py`

## Historical/current split

Compatibility evidence is append-only. A later schema or currentness change does not rewrite an earlier projection. A migrated/rebuilt projection receives a new identity.

## Dogwood

Public comparator pin: `dogwood-policy/dogwood@c6237c88099b3f492ecc5fcee42df06a19224b97`.

Dogwood's temporal trace is derived consumer state, not canonical Agent Memory history. The adapter owns event/action-schema mapping, temporal-window capability, policy identity, provider/context mapping, and target isolation evidence.

A Dogwood `pin` alone does not prove partitioning. A `universal_symmetric_pin` isolation claim must be validated against the target event schema. If the policy question requires more history than the target temporal horizon supports, the result is incompatibility, not evidence that an event never occurred.

## Cedar and Cedarling

Cedar-family consumers bind authorization schema and current policy-validation state. A changed schema can require policy revalidation before compatibility returns to `current`.

For Cedarling pushed context, decision evidence must bind the context actually evaluated. Inline request context can shadow pushed values, so merely proving that Agent Memory pushed a value is insufficient.

## Policy decisions

Existing monotonic composition is unchanged:

```text
PAMA deny + external allow -> deny
PAMA review + external allow -> review
PAMA allow + external deny -> deny
```

External policy output remains decision evidence, not human adjudication, reusable authority, or execution evidence.

## Evidence

- `fixtures/policy-projection-compatibility-adversarial.json`
- `reference/tests/test_policy_projection_compatibility.py`
- `.github/workflows/policy-projection-compatibility.yml`
- `docs/research/temporal-policy-semantic-mediation.md`
- ADR-030
