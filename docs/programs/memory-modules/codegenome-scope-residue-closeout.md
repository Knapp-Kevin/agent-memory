# CodeGenome Traversal Scope and Residue Closeout

Issue: #293

This evidence supplements, rather than replaces, the existing provider-neutral CodeGenome/Graphify traversal qualification.

## Base qualification

The existing runtime qualification remains:

```text
code-graph-traversal-currentness@1.1.0
CodeGenome@43a6b7147ec78ec5c616723fa1dd30f342174860
Graphify v0.9.43@7281f27eac568f77f50910f59f84543458f5dfd1
```

It already proves requested-file identity, traversal direction, decoy isolation, v1→v2 full-rebuild currentness, explicit provider unavailability, raw evidence retention, bounded fallback, and no authority effect.

The v1→v2 fixture is also a source-deletion case: v1 contains `leaf`; v2 removes it and replaces the active downstream relation with `replacement_leaf`.

## Why this closeout exists

The bounded CodeGenome profile now truthfully declares:

```text
scope_posture = external_scope_bridge
```

That is stronger and more precise than treating provider repository scope as if it were automatically Agent Memory tenant/project scope.

The closeout therefore adds two explicit obligations for the only CodeGenome capability currently above source-level maturity:

1. provider output is admitted only through an exact, version-bound provider-scope → Agent Memory-scope binding;
2. source deletion after full rebuild proves old material is not current without pretending historical provider artifacts were physically erased.

## External scope binding

The reference closeout uses an explicit binding containing:

```text
component_id
component_version
component_profile_digest
provider_scope_ref
agent_memory_scope_ref
tenant_ref
project_ref
binding_ref
binding_version
```

The component revision and component-profile digest are part of the binding. An upgrade or material profile change therefore invalidates the old scope admission rather than silently inheriting it.

Admission is deterministic:

```text
exact component revision
+ exact component-profile digest
+ exact provider scope
+ exact Agent Memory scope
+ explicit binding
  -> candidate may cross the scope bridge

missing binding
stale component revision
stale component-profile digest
foreign provider scope
foreign Agent Memory scope
missing scope identity
  -> refuse
```

The binding is not authority. It only proves which exact external provider/profile scope is allowed to contribute candidate evidence to which Agent Memory scope.

```text
scope binding
!= recall permission
!= mutation authority
!= action authority
```

This closeout is the controlling Agent Memory posture for the CodeGenome profile. Historical comparator/fallback metadata from earlier qualification work does not convert CodeGenome into a component that natively enforces or inherits Agent Memory tenancy.

## Source deletion and residue

The runtime fixture is intentionally interpreted as:

```text
v1: middle -> leaf
v2: middle -> replacement_leaf
```

After a fresh v2 full rebuild, the active v2 CodeGenome query must no longer return the deleted v1 `leaf` line and must return the replacement line.

The workflow also records manifests for both the historical v1 provider store and current v2 provider store.

That proves the narrower currentness statement:

```text
deleted v1 source
-> not admitted as current from the v2 rebuilt store
```

It does **not** prove:

```text
all historical provider bytes erased
all backups erased
all derived systems erased
transitive Agent Memory forgetting complete
```

Instead the evidence records:

```text
historical_provider_artifact_retained = true
historical_provider_artifact_current = false
physical_erasure_proven = false
residue_posture = historical_provider_artifact_disclosed_not_current
```

This is deliberate. Historical qualification evidence may remain retained while being non-current. Physical retention and governed currentness are different properties.

## Relationship to the CodeGenome profile

`docs/programs/memory-modules/codegenome-multicapability-profile.md` remains the capability inventory.

The closeout does not promote vector retrieval, GraphRAG, LSP, or deletion/rebuild to a stronger maturity. It only completes #293-specific negative-path evidence for `code_graph_traversal`, the capability already carrying `evidence_proven` maturity.

Lower-maturity capability rows remain lower maturity by design.

## Exact-head evidence

`CodeGenome Scope and Residue Closeout`:

- runs exact/missing/stale/foreign scope-refusal cases;
- binds scope admission to the exact CodeGenome revision and component-profile digest;
- checks out the exact CodeGenome pin and verifies MIT source rights;
- builds the exact CodeGenome CLI;
- indexes the v1 and v2 fixtures into separate provider stores;
- captures the historical and current downstream query outputs;
- preserves manifests for both provider stores;
- emits an exact-head closeout report;
- requires every scope/currentness/residue invariant to pass;
- keeps `authority_effect = none`.

## Claim boundary

This evidence supports a bounded statement:

> CodeGenome graph traversal may contribute evidence-proven candidates for the qualified fixture when the exact provider revision/profile remains current, the provider repository scope is explicitly bridged to the active Agent Memory scope, and a full rebuild after source deletion no longer admits the deleted source as current. Historical provider artifacts may remain retained as disclosed non-current evidence.

It does not make CodeGenome a canonical Agent Memory graph, scope authority, deletion authority, or universal memory substrate.
