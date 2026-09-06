# Derivation Currentness and Scope Propagation Profile

Status: V0.1 implementation profile for #210.

## Purpose

A derivation is historical evidence of what was transformed from which sources, by which transformer, under which scope, at a particular time.

That historical record should not be rewritten when the world changes later.

```text
historical derivation
!= mutable current-truth object
```

If a root source is later disputed, revoked, superseded, tombstoned, deleted, or placed under a narrower current scope, Agent Memory emits a **separate currentness evaluation**.

```text
source changes later
-> derivation evidence remains intact
-> current applicability is re-evaluated
-> consequential use fails closed when currentness is not established
```

This profile completes the useful unfinished derived-state semantics that existed in #202 / draft PR #203 while retaining the canonical `derivation-evidence` model merged through #204 / PR #205.

It deliberately does not introduce a second `transformation-evidence` ontology.

## Two records, two jobs

### Derivation evidence

`schemas/derivation-evidence.schema.json`

Answers:

- what was derived;
- from which root origins;
- from which immediate source;
- by which transformer/version;
- under which scope;
- with which evidence/confidence metadata.

It is historical and identity-stable.

### Derivation currentness evaluation

`schemas/derivation-currentness-evaluation.schema.json`

Answers:

- what is the current state of every root origin;
- what is the current scope/authority posture;
- is this derivation currently applicable;
- which reasons force revalidation or uncertainty.

It is append-only evidence about the current applicability of the historical derivation.

## Root-source accounting

The currentness evaluator operates on `root_origin_refs`, not only `immediate_source_refs`.

This matters for multi-hop derived state:

```text
source A
 -> derivation B
 -> derivation C
```

C's immediate source is B, but its root origin remains A.

If A is later revoked:

```text
B remains historical evidence
C remains historical evidence
currentness(B) -> revalidation_required
currentness(C) -> revalidation_required
```

A trusted transformer in B or C cannot hide the non-current root basis.

## Source states

Every expected root source is accounted for explicitly as one of:

```text
current
disputed
revoked
superseded
tombstoned
deleted
unknown
```

The evaluation preserves per-origin evidence refs and an evidence class.

A missing root observation is represented as:

```text
observed = false
state = unknown
```

and causes current applicability to remain `unknown`.

An unrelated source observation is retained only in `unexpected_source_refs`. It cannot substitute for a missing expected root.

## Applicability

The aggregate applicability states are:

```text
current
revalidation_required
unknown
```

### Current

Requires:

- every root source explicitly observed as current;
- current tenant/project identity compatible with the derivation;
- scope observation established as unchanged/current.

### Revalidation required

Triggered by definite non-current evidence such as:

- disputed source;
- revoked source;
- superseded source;
- tombstoned source;
- deleted source;
- source scope reduction;
- shared scope/membership revocation;
- tenant/project mismatch;
- a supposedly unchanged scope that no longer matches the historical scope.

### Unknown

Used where consequential current applicability cannot be established, for example:

- missing root-source observation;
- root state explicitly unknown;
- current scope state unknown.

`unknown` is not a permissive fallback.

```text
unknown currentness
!= current
```

The evaluation records `revalidation_required = true` for both `unknown` and `revalidation_required`, because either posture requires further governed evidence before consequential use.

## Deletion and tombstone distinction

The evaluator preserves distinct reason codes:

```text
source_tombstoned:<ref>
source_deleted:<ref>
```

These are not collapsed into a generic invalid bit.

A tombstone may represent retained governance history around a removed/pruned value. Physical deletion is a different lifecycle fact. Derived-state handling may need that distinction later even though both currently require revalidation.

## Evidence character

Current source observations preserve an evidence class:

```text
ordinary
negative
adversarial
correction
incident
```

The evaluation exposes a bounded aggregate evidence character:

```text
ordinary
negative_or_adversarial
correction_or_incident
```

A trusted summarizer cannot neutralize adversarial or negative source evidence merely by restating it.

```text
trusted transformation of adversarial evidence
!= ordinary corroboration
```

Evidence character is still evidence, not authority.

## Currentness is not authority

Every currentness evaluation fixes:

```text
authority_effect = none
memory_admission = not_established
certification_claim = none
remote_mutation = not_established
historical_derivation_mutated = false
prior_authorization_reusable = false
currentness_evidence_authority = none
```

A current result means only that the supplied source/scope observations establish current applicability under this bounded evaluation contract.

It does not independently authorize:

- durable promotion;
- crystallization;
- recall admission;
- certification;
- correction;
- remote cleanup or deletion.

Consequential behavior still crosses normal Agent Memory governance.

## Currentness evaluations are append-only

`evaluation_id` is deterministic over:

- derivation ID;
- ordered root observations;
- current scope observation;
- resulting applicability/evidence character;
- evaluation timestamp;
- fixed interpretation.

A later source state therefore produces a new evaluation record rather than modifying the earlier derivation.

Example:

```text
T1: source current
 -> evaluation E1: current

T2: source revoked
 -> evaluation E2: revalidation_required

historical derivation D remains unchanged
E1 remains evidence of T1 evaluation
E2 is current evidence at T2
```

## Explicit scope narrowing

The canonical derivation contract now supports optional scope metadata:

```text
scope.relation = preserved | narrowed
scope.basis_refs
```

Scope narrowing is intentionally **not** accepted from arbitrary transformer metadata.

A caller must use the explicit `derive_from(..., narrowed_scope=..., scope_basis_refs=...)` API.

V0.1 rules:

```text
new scope_ref must differ from source scope_ref
basis refs required
same tenant_ref required
same project_ref required
```

This is an explicit operation, not string-based hierarchy inference.

### What narrowing does not mean

V0.1 does not attempt to prove that one opaque scope ref is mathematically a subset of another from its name.

The caller supplies the narrowed scope plus bounded basis refs. Agent Memory preserves that evidence and enforces the non-widening tenant/project constraints it can evaluate deterministically.

## Arbitrary scope overrides remain ignored

A transformer may emit a payload that includes:

```text
scope = tenant-b / project-b / everything
```

That field is not consumed by `derive_from`.

Only the explicit narrowing parameters can change the inherited scope.

This keeps transformer convenience metadata from becoming scope authority.

## Scope-reduction fixture

The harness consumes:

`fixtures/scope-reduction-propagates-to-derived-state.json`

The fixture requires:

```text
source_scope_reduced = true
derived_scope_recomputed = true
old_derived_scope_current = false
narrowing_required = true
```

Behavioral proof:

1. a historical derivation is current under its original derived scope;
2. a later source-scope reduction is supplied as current evidence;
3. the old derivation evaluates `revalidation_required`;
4. the old derivation remains byte/identity stable;
5. a new child derivation is explicitly created under the narrower scope with basis refs;
6. the narrowed child can then evaluate current under that narrowed current scope.

The old record is not silently edited into the new scope.

## Shared-revocation fixture

The harness also consumes:

`fixtures/shared-memory-revocation-propagation.json`

The fixture requires:

```text
shared_membership_revoked = true
future_shared_recall_admitted = false
downstream_scope_recomputed = true
old_downstream_scope_current = false
remote_mutation_implied = false
```

Behavioral proof:

1. the shared derivation is initially current;
2. current shared membership/scope evidence becomes revoked;
3. dependent derived applicability becomes `revalidation_required`;
4. prior shared authorization is not reusable;
5. the evaluation does not imply a remote mutation command;
6. the historical derivation remains intact.

Revocation creates a governance obligation to re-evaluate/rebuild/narrow, not an invented authority to mutate some remote system.

## Confidence and transformer trust

Currentness depends on current source and scope evidence.

The harness/tests vary derivation confidence and transformer trust while holding current source state constant.

Required result:

```text
confidence 0.99 + source revoked
and
confidence 0.01 + source revoked
-> same revalidation posture
```

Likewise, trusted versus untrusted transformer identity cannot make a revoked source current.

## Privacy and minimization

The evaluation requires refs/state classifications, not raw source bodies.

It does not require:

- source text;
- derived text;
- prompts;
- hidden reasoning;
- credentials;
- full transformation payloads.

A source-state observation may use stable evidence refs instead.

## Evidence depth

The focused exact-head report registers three bounded claims:

1. root-source currentness propagation across multi-hop derivation;
2. source-scope reduction propagation;
3. shared revocation propagation.

Each is reported as:

```text
D + F + H
R = explicitly unproven
P = explicitly unproven
```

The structural fixtures are not runtime proof. The reference behavioral harness is not production proof.

## Relationship to #202 / PR #203

Draft PR #203 explored useful concepts including source lifecycle state, derived scope propagation, and multi-hop lineage, but it did so using a separate `transformation-evidence` schema beside the already-merged canonical `derivation-evidence` model.

This profile intentionally consolidates those useful semantics into the canonical model:

```text
canonical derivation evidence
+
append-only currentness evaluation
+
explicit governed scope narrowing
```

Once #210 is merged and validated, #202/#203 can be closed as superseded rather than carrying two competing provenance abstractions.

## Non-claims

V0.1 does not claim:

- automatic discovery of source revocation;
- automatic derived-state rebuild/deletion;
- generic scope hierarchy inference;
- remote mutation authority;
- currentness equals truth;
- currentness equals admission authority;
- runtime R evidence;
- production P evidence;
- external certification.

## Stop line

Keep historical derivation evidence immutable. When current source/scope state changes, append currentness evidence and route any rebuild, narrowing, deletion, admission, or other consequence through normal governance.
