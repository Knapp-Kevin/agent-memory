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

Executable evidence:

- `schemas/pama-decision.schema.json`
- `reference/agentmem_ref/core/policy.py`
- `reference/agentmem_ref/memory/domain_schema_mutation.py`
- `reference/tests/test_domain_schema_mutation_policy.py`
- `reference/tests/test_domain_schema_mutation_compatibility.py`
- `.github/workflows/domain-schema-mutation-contract.yml`

Research source: #226. Implementation: #236.
