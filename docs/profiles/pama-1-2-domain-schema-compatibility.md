# PAMA 1.2 Domain-Schema Compatibility

PAMA decision `1.2.0` adds the closed operation `domain_schema_mutation`.

Compatibility remains cumulative:

```text
1.0.0  historical operation set
1.1.0  adds decision_overwrite
1.2.0  adds domain_schema_mutation
```

Older records remain valid and are not rewritten. A `domain_schema_mutation` record claiming an older PAMA decision version is invalid. A consequential consumer that does not understand 1.2.0 must report a compatibility failure rather than reinterpret the operation as `other`.

The operation identifies durable application/domain model changes that can alter future extraction, typing, relation meaning, migration, or recall. It does not represent ordinary fact insertion, Agent Memory core-schema changes, unchanged-semantic index rebuilds, or policy changes.

Reference minimum outcomes are:

| Risk | Outcome |
|---|---|
| low | `require_review` |
| medium | `require_review` |
| high | `require_external_verification` |
| critical | `require_external_verification` |

Existing PAMA dimensions remain controlling. If the same request also widens scope, the existing `scope_expansion` posture still applies. M5 and A5 floors remain unchanged. Estimator confidence does not lower the operation's required outcome.

## Review and verification discharge

PAMA 1.2's operation/version remains valid after ADR-037, but its original caller-asserted review implementation does not. New evaluations use the shared PAMA authority mechanisms:

- `review_satisfied=True` plus arbitrary `approval_refs` is legacy proposal state and does not discharge review;
- low/medium `require_review` may discharge only through qualified evidence meeting ADR-037's risk/evidence ladder;
- high/critical `require_external_verification` requires a proposal-bound external attestation satisfying the shared binding, separation, authority-kind, and risk-ceiling checks;
- a requested scope expansion, M5/A5 floor, self-approval block, missing evidence, or other stricter shared constraint remains controlling.

Historical 1.2.0 decision documents are not rewritten. This is evaluator hardening for new decisions, not a schema-version migration.

Executable evidence:

- `schemas/pama-decision.schema.json`
- `reference/agentmem_ref/core/policy.py`
- `reference/agentmem_ref/memory/domain_schema_mutation.py`
- `reference/tests/test_domain_schema_mutation_policy.py`
- `reference/tests/test_domain_schema_mutation_compatibility.py`
- `.github/workflows/domain-schema-mutation-contract.yml`

Research source: #226. Initial implementation: #236. ADR-037 reconciliation: #401.
