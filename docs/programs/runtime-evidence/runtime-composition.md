# Configured multi-capability runtime composition

Status: implementation evidence for #280

This slice proves that the runtime-configuration contract can drive more than provider selection. It composes canonical retained memory with a materially distinct derived-state capability and exercises correction, retrieval isolation, component disable/removal/rebuild, and deletion without allowing derived lifecycle operations to redefine canonical memory identity.

## Reference profile

Fixture:

`reference/fixtures/runtime-configuration/reference-composed-runtime.json`

The profile intentionally uses first-party reference components so the composition semantics can be tested deterministically without introducing another external dependency.

Configured capabilities:

```text
reference-governed-memory
  -> semantic_fact_memory@1.0
  -> exact_identity_retrieval@1.0

reference-projection-sidecar
  -> rebuild_projection@1.0
```

The canonical component therefore demonstrates multiple independently declared capabilities, while the projection capability is supplied by a materially distinct component.

All three are bounded `runtime_wired` capabilities in this fixture. This evidence does not retroactively grant broader qualification or maturity.

## Composition flow

```text
governed proposal
  -> semantic_fact_memory canonical commit
  -> stable logical memory identity + current fact
  -> configured derived projection declaration
  -> projection currentness computed from canonical basis
  -> governed retrieval/admission
```

The derived projection is the existing deterministic/reproducible reference sidecar. It is intentionally modest. This slice is testing composition invariants, not pretending a sidecar index is GraphRAG, a vector database, or a product recommendation.

## Correction

A governed correction commits a new canonical fact under the same logical memory identity and advances canonical version.

The existing projection basis then becomes `stale` by relation.

```text
canonical correction committed
  -> canonical version advances
  -> old canonical fact remains historical/superseded
  -> projection freshness = stale
  -> projection admission refused
  -> NO automatic rebuild
```

Staleness alone does not trigger recomputation. That preserves the established boundary that invalidation cannot become an implicit write channel.

A later deterministic/reproducible rebuild is categorically permitted by the existing projection contract. The rebuild rebases derived state to current canonical version without changing canonical fact UUID or logical version.

## Retrieval isolation

The same composed runtime routes retrieval through the governed canonical adapter.

The acceptance scenario verifies:

- same-project recall is admitted;
- a foreign project receives `project_scope_mismatch`;
- derived component availability never bypasses canonical recall admission.

## Disable, removal, and rebuild

The derived component lifecycle is exercised in three distinct states.

### Disable

The component becomes unavailable while its physical projection declaration may still exist.

Projection admission returns:

`component_disabled`

Canonical fact UUID and canonical state version remain unchanged.

### Remove

The projection declaration and retained projection versions are physically removed from the sidecar.

Canonical fact UUID and canonical state version remain unchanged.

### Restore and rebuild

The derived component is restored and reconstructs its projection from the current canonical logical memory basis.

The rebuilt projection becomes current again.

Canonical fact UUID and canonical state version remain unchanged.

Therefore:

```text
derived component lifecycle
  != canonical memory lifecycle
```

## Deletion

After permanent deletion of the current canonical fact, any still-present projection based on the logical memory becomes `residual`, not merely stale or current.

Projection admission refuses the residual state.

The sidecar may then be removed without recreating canonical memory.

This composes the existing deletion-dominance rule with configurable component lifecycle instead of treating derived component removal as proof that canonical deletion happened.

## Authority boundary

Component disable, removal, restore, projection admission, and deterministic derived rebuild evidence all expose:

`authority_effect = none`

The configured router decides which implementation path is eligible. The canonical adapter and existing governance contracts continue to decide consequential memory mutation and recall admission.

## Evidence

Targeted tests:

```bash
python -m unittest discover -s reference/tests -t reference -p 'test_runtime_composition.py'
```

Exact-head evidence:

```bash
python reference/run_runtime_composition.py \
  --agent-memory-commit <exact-40-character-commit> \
  --output runtime-composition-evidence.json
```

The workflow also runs the complete reference regression suite before preserving the artifact.

## Relationship to #280

This slice is intended to discharge the remaining executable composition/lifecycle portions of #280:

- at least two materially different capabilities compose successfully;
- correction/currentness/isolation/deletion paths cross the composed runtime;
- derived component disable/removal/rebuild is exercised;
- canonical logical state does not change merely because the derived component is rebuilt;
- routing and component lifecycle do not create authority.

Provider overlap, no-weaker fallback, source-rights validation, qualification binding, deterministic configuration validation, and public configuration guidance are already covered by the earlier #300/#312 work.

#280 should close only after the final exact-head workflow matrix confirms this composition evidence alongside those existing surfaces.

## Remaining product work after #280

Closing the component-routing implementation issue would not mean the application is packaged.

The next product-facing layers would still include:

- a process/service boundary that consumes the validated plan;
- minimal CLI surfaces such as configuration validation and doctor/status;
- installation/package metadata;
- optional discovery/adapters for common existing runtimes;
- only later, an interactive setup wizard or recommended-component UX.

Those layers should consume this contract rather than redefining it.