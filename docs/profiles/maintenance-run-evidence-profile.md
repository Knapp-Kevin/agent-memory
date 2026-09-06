# Maintenance Run Evidence Profile

Status: reusable evidence profile for governed background/autonomous memory maintenance.

## Purpose

A maintenance cycle may contain several proposals and several PAMA decisions. This profile records what happened at the **run/transaction level** without replacing those constituent decisions.

```text
maintenance run != one new authority decision
run evidence != proof that every inner mutation was allowed
```

## Required separation

The record keeps these facts distinct:

```text
transaction status
commit status
validation status
source currentness
cursor before / after
```

A successful write that fails post-commit validation is not a clean completed run. A stale-source stop is not a successful no-op. A rollback is not a commit.

## Cursor rule

```text
clean committed + validated run -> cursor may advance
all other outcomes              -> cursor_after == cursor_before
```

A run identity is single-use for cursor progression. Replaying the same run must not advance the cursor twice.

## Constituent PAMA decisions

Each governed semantic operation is represented by its exact PAMA decision reference and actual operation/outcome. The run wrapper may aggregate evidence but may not weaken a stricter constituent decision.

PAMA 1.2 `domain_schema_mutation` is preserved as that exact operation rather than flattened to `other`.

Housekeeping such as an unchanged-semantic index/cache/projection rebuild may be represented without a constituent mutation decision when `housekeeping_only=true` and `semantic_memory_changed=false`.

## Scope and source state

Resolved constituent PAMA evidence must bind to the same tenant/purpose as the run. A stale or revoked input source cannot produce a clean committed run.

If policy changes between staging and commit, a clean commit requires explicit revalidation evidence.

## Recovery

Partial apply, failed validation, rollback, or quarantine must preserve the pre-run cursor. Recovery references remain evidence about what happened; they do not silently convert the run into success.

## Evidence shape

The machine-readable contract includes:

- run and actor identity;
- policy and commit-policy versions;
- tenant/project/purpose/isolation scope;
- cursor before/after;
- input snapshot and source evidence;
- proposal refs and planned operation set;
- constituent PAMA decision refs;
- transaction/atomicity/commit/validation state;
- outputs, supersession/tombstone refs;
- rollback/quarantine refs when relevant;
- estimator evidence refs;
- timestamps;
- evidence identity and SHA-256 digest.

## Nonclaims

```text
confidence != permission
maintenance scheduling != mutation permission
run completion != semantic correctness beyond recorded validation
transaction evidence != production enforcement proof
```

## Conformance evidence

- `schemas/maintenance-run-evidence.schema.json`
- `reference/agentmem_ref/maintenance_run_state.py`
- `reference/agentmem_ref/maintenance_run_rules.py`
- `reference/agentmem_ref/maintenance_run_bindings.py`
- `reference/agentmem_ref/maintenance_run.py`
- `reference/tests/test_maintenance_run_state.py`
- `reference/tests/test_maintenance_run_binding_positive.py`
- existing `reference/tests/test_autonomous_maintenance.py`
- `.github/workflows/maintenance-evidence.yml`

Related research: #227. Implementation: #238.
