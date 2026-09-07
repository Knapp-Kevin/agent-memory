# Capability behavior contract

Status: implementation contract for #280 / ADR-033

Agent Memory separates **what a capability is**, **how its state behaves**, and **what authority may act on its result**.

Those are independent dimensions.

```text
capability identity
  != lifecycle behavior
  != maturity
  != authority
```

## Why v2 exists

`component-capability-v1` established independently matured capability declarations with explicit identity, version, maturity, state posture, scope posture, failure posture, evidence, limitations, and authority effect.

That was sufficient to answer questions such as:

- which implementation can provide `code_graph_traversal`;
- whether its maturity is high enough;
- whether it is canonical or derived;
- whether it is scope-compatible;
- whether failure must be explicit;
- whether several eligible providers create ambiguity.

It was not sufficient to answer a different class of questions:

- does this capability write, read, or only nominate recall candidates;
- how does it determine whether its output is current;
- what makes its output stale or invalid;
- what happens when canonical memory is corrected;
- what happens when canonical memory is deleted;
- can residue remain after deletion;
- can the capability rebuild from canonical state;
- does a structural mutation require PAMA or another authorization boundary.

Those behaviors materially affect safe composition. `component-capability-v2` makes them machine-readable.

## Backward compatibility

Legacy declarations remain valid:

```text
component-capability-v1
  -> behavior metadata optional / absent
  -> valid when the consuming route does not require behavior semantics
```

New behavior-aware declarations use:

```text
component-capability-v2
  -> behavior_contract required for every capability
```

A route that explicitly requires lifecycle behavior cannot be satisfied by a v1 provider that does not declare it.

This is deliberate fail-closed behavior, not a claim that every v1 provider is unsafe. It means the runtime refuses to infer lifecycle guarantees the provider never declared.

## Behavior fields

Each v2 capability declares an operation surface:

```text
write
read
recall_candidate
```

These Booleans are descriptive. `write = true` means the capability exposes a write surface. It does **not** authorize a write.

Each capability also declares one value for the following lifecycle dimensions.

### Currentness model

```text
not_applicable
canonical_version
basis_versioned
provider_revalidated
external_asserted
```

Examples:

- canonical retained memory may be current by canonical version;
- a derived projection may be current only while its basis version matches canonical state;
- an external provider may require revalidation.

### Invalidation model

```text
not_applicable
version_relation
explicit_signal
provider_revalidation
```

This describes how the implementation determines that prior state is no longer current. Invalidation remains a write-channel-sensitive operation under Agent Memory governance. Declaring an invalidation model does not authorize recomputation.

### Correction model

```text
not_applicable
canonical_supersession
invalidate_derived
candidate_only
provider_revalidation
```

A canonical memory capability can declare that correction supersedes prior canonical state. A derived capability can declare that correction invalidates the derived basis without automatically rebuilding it.

### Deletion model

```text
not_applicable
canonical_delete
derived_residue_then_purge
candidate_drop
provider_revalidation
```

Deletion semantics remain subordinate to deletion dominance. A derived component that declares `derived_residue_then_purge` explicitly admits that deleting canonical state does not prove physical derived residue disappeared at the same instant.

### Residue model

```text
not_applicable
none_expected
scan_required
derived_residual
provider_managed
```

This describes the residual-state obligation after correction/deletion/removal. It does not weaken the existing must-not-surface and residue-verification contracts.

### Migration / rebuild model

```text
not_applicable
rebuild_from_canonical
explicit_migration
requires_requalification
unsupported
```

`rebuild_from_canonical` is particularly important for disposable derived components. It permits the runtime to reason that a removed index can be reconstructed from canonical state without treating the index as canonical memory.

### Structural mutation requirement

```text
none
proposal_only
pama_required
external_authorization_required
```

This field describes which governance boundary a structural mutation would require.

It is **not** an authority field.

For example:

```text
structural_mutation_requirement = pama_required
authority_effect = proposal_only
```

means the component may at most propose the structural change, while PAMA remains the independent authority boundary defined elsewhere.

## Behavior-aware routing

`CapabilityRequirement` may include a `CapabilityBehaviorRequirement`.

The requirement can constrain any subset of the behavior dimensions. Providers with missing or incompatible behavior contracts are not eligible.

This allows two implementations with the same nominal capability to remain distinguishable.

Example:

```text
Provider A
  capability = rebuild_projection
  currentness = basis_versioned
  rebuild = rebuild_from_canonical

Provider B
  capability = rebuild_projection
  currentness = external_asserted
  rebuild = rebuild_from_canonical
```

A route requiring `basis_versioned` currentness can deterministically select A without pretending A and B are behaviorally interchangeable.

The portable runtime schema exposes the same constraints as `behavior_requirements` on a route. The v2 validation layer checks the resolved primary and any configured fallback against them.

## Reference composed runtime

`reference/fixtures/runtime-configuration/reference-composed-runtime.json` uses v2 behavior declarations for:

### `semantic_fact_memory`

```text
write/read = true
currentness = canonical_version
correction = canonical_supersession
deletion = canonical_delete
residue = scan_required
migration = explicit_migration
```

### `exact_identity_retrieval`

```text
write = false
read = true
recall_candidate = true
currentness = canonical_version
```

### `rebuild_projection`

```text
write/read = true
currentness = basis_versioned
invalidation = version_relation
correction = invalidate_derived
deletion = derived_residue_then_purge
residue = derived_residual
migration/rebuild = rebuild_from_canonical
```

Those declarations match the executable composition evidence established by the reference runtime rather than inventing guarantees not present in the implementation.

## No new logical state algebra

The v2 vocabulary does not introduce new Agent Memory logical memory states.

It describes implementation behavior using already-established lifecycle concepts:

- canonical/current versioning;
- derived basis currentness;
- supersession;
- deletion dominance;
- residue verification;
- rebuild/migration;
- structural-mutation governance.

The contract exists so configuration and routing can inspect those semantics before composing components.

## Evidence

Targeted tests:

```bash
python -m unittest discover -s reference/tests -t reference -p 'test_capability_behavior_contract.py'
```

Exact-head evidence:

```bash
python reference/run_capability_behavior_contract.py \
  --agent-memory-commit <exact-40-character-commit> \
  --output capability-behavior-contract.json
```

The `Capability Behavior Contract` workflow also runs the full reference regression suite and refuses non-Boolean structural invariants.

## Authority boundary

The invariant is intentionally boring:

```text
behavior metadata
  -> may constrain eligibility / routing
  -> may expose required governance boundaries
  -> may describe lifecycle behavior

behavior metadata
  != mutation authority
  != recall-admission authority
  != structural authority
  != action authority
```

That separation keeps configuration useful without allowing descriptive metadata to launder a component into a decision-maker.