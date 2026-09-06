# Canonical and Derived State

> Status: **design spike. Not doctrine, not evidence.** This document defines vocabulary and proposes invariants for the P4 slice of the [runtime evidence program](README.md). It discharges no [ADR-020](../../adr/ADR-020-probabilistic-discovery-deterministic-governance.md) validation item, and nothing here is adopted until an ADR says so. Its purpose is to make the P4 requirements *expressible* — a claim like "this projection is stale with respect to canonical state" currently has no defined meaning in this repository, which makes it untestable rather than merely unproven.

## Why this slice exists

ADR-020 cannot be accepted until item 12, *derived-memory deletion residue is tested*, is discharged. Item 12 is a single line, and underneath it sits the largest unmodelled surface in the architecture.

The doctrine already asserts the requirements. [Doc 28](../../28-retention-deletion-and-tombstones.md) requires deletion to traverse derivation relationships and lists summaries, embeddings, index records, graph edges, caches, and exports as dependents. [Doc 31](../../31-recovery-rollback-and-replay.md) requires dependency repair and names derived-memory deletion residue as a failure case. The [first substrate mapping](graphiti-conformance.md) classifies derived projections as *CONFIGURABLE, weak by default* — embeddings, indices, and communities all exist, and none self-invalidate.

What is missing is not conviction. It is a definition of what derived state *is*, what it must declare, and what "stale" means precisely enough to fail a test.

## Three tiers, not two

The framing "canonical memory versus derived projections" is a useful headline and a misleading model, because it implies one boundary where there are two.

```text
tier 1   canonical memory units
         authoritative; wrong only on their own terms

tier 2   derived memory units
         governed; carry identity, lifecycle, authority, provenance.derived_from
         wrong on their own terms OR by being out of date with their sources

tier 3   projections
         indices, embeddings, caches, materialized views, community summaries
         not memory units; no identity, no lifecycle, no authority, no schema
```

Tier 2 is already partly modelled: [`memory-unit.schema.json`](../../../schemas/memory-unit.schema.json) carries `provenance.derived_from`, and [`deletion-residue`](../../../fixtures/deletion-residue.json) exercises exactly that shape — a `summary` whose raw source was deleted.

**Tier 3 has no vocabulary in this repository at all**, and tier 3 is where deletion residue actually hides. An index entry is not a memory unit, so nothing obliges it to declare what it was built from; a cache is not a memory unit, so no lifecycle state applies to it; an embedding is not a memory unit, so no authority governs its refresh. The governed tiers are the ones already under observation. The residue risk is concentrated in the tier the schema cannot see.

This is the spike's headline finding: **P4 is mostly a tier-3 problem, and tier 3 currently has no declaration surface.**

## The canonical test

Storage location does not determine canonicity, and neither does the word "cache" appearing in a variable name. The operational test is disagreement:

> If this state and its putative source disagree, which one is wrong?
>
> Canonical state can only be wrong on its own terms. Derived state can additionally be wrong by being out of date with respect to something else.

A corollary is more useful in practice than the definition: derived state has a *second* failure mode that canonical state does not have, and every invariant in this document exists to make that second failure mode visible.

## What a projection must declare

For staleness and residue to be computable at all, tier-3 state needs a declaration — not a schema for its contents, which are the substrate's business, but a declaration of its relationship to canonical state.

```text
basis           the canonical units read, each with the state version read
transform       deterministic | estimator_mediated
content_class   reference_only | derived_content | recoverable_content
rebuild         reproducible | approximable | irreproducible
scope           the tenancy and sensitivity envelope the projection inherits
```

`content_class` and `rebuild` are the two that carry consequence, and they are independent:

| | reproducible | approximable | irreproducible |
|---|---|---|---|
| **reference_only** | index of IDs | — | orphaned ID list |
| **derived_content** | embedding, pinned model | embedding, drifted model | embedding, model retired |
| **recoverable_content** | deterministic extract | LLM summary | LLM summary, model retired |

The dangerous cell is the bottom-right region: state that both *holds recoverable content* and *cannot be rebuilt*. It survives deletion of its source while carrying the source's content, and it cannot be repaired after a correction without producing something materially new. Every hard case in P4 lives there. Doc 28 already refuses to let this be waved away: *the system should not claim full deletion where it cannot demonstrate it.*

Note that `scope` is inherited, not declared freely. A projection over tenant-scoped canonical units is tenant-scoped whether or not its substrate knows what a tenant is — and per the substrate mapping, isolation is frequently a query-filter convention rather than an enforced boundary. A projection is a cross-tenant leak waiting for a missing filter.

## Staleness is a relation, not a flag

A boolean `stale` field on a projection is unmaintainable and dishonest under concurrency: it is only correct if something reliably sets it, and the substrates in scope reliably do not. Push-invalidation is precisely what the mapping found absent.

Define staleness instead as a computable relation between the projection's recorded basis and current canonical state:

```text
current(P)   ⟺  ∀ m ∈ basis(P) : version(m) = basis(P)[m]  ∧  ¬tombstoned(m)
stale(P)     ⟺  ∃ m ∈ basis(P) : version(m) ≠ basis(P)[m]  ∧  ¬tombstoned(m)
residual(P)  ⟺  ∃ m ∈ basis(P) : tombstoned(m) ∨ purged(m)
```

Three consequences follow, and they are the reason to prefer the relation.

**It is a pull-model invariant.** No notification is required. The check runs at read time, which is where [ADR-020 Rule 7](../../adr/ADR-020-probabilistic-discovery-deterministic-governance.md) already places governance. A substrate that never self-invalidates is therefore governable without modification — the wrapper computes freshness at admission rather than trusting the substrate to have maintained it.

**Staleness is not an error.** Admitting a stale projection is often legitimate. Admitting one *without recording that it was stale* is not. Staleness belongs in the admission decision and the receipt, not in a background job whose job is to make the flag briefly true.

**Stale and residual are different states with different authorities.** A stale projection has a correctness problem, and recomputation may resolve it. A residual projection has a governance problem, and only the deletion authority may resolve it. Collapsing the two into one "invalid" state loses exactly the distinction ADR-020 exists to protect. This trichotomy is the design's load-bearing element.

## Correction propagation

Correction is not deletion — doc 28 is explicit, and the reason is that correction preserves the fact that an earlier claim was wrong.

When canonical unit `m` is corrected from v12 to v13, every projection with `m` in its basis becomes stale. What must *not* happen is silent recomputation of a content-bearing projection that has already been used in a consequential decision, because that erases the evidence that the decision rested on the earlier value. The supersede-don't-erase rule that governs canonical memory governs its projections for the same reason.

```text
correction  ->  projections become stale
            ->  content-bearing projections are superseded, not overwritten
            ->  the superseded version remains reconstructable for decisions that used it
            ->  unless privacy or deletion policy requires otherwise
```

## Deletion propagation, and where it collides with correction

Deletion inverts the preservation rule. A superseded projection version retained for reconstructability is, after its source is purged, exactly the recoverable residue the deletion was supposed to eliminate.

The two rules therefore genuinely conflict, and the conflict must be resolved by stated precedence rather than discovered at runtime:

> **Deletion dominates correction.** Where a projection has been superseded for reconstructability and its basis is later purged, the retained superseded versions are in scope for the purge. Reconstructability degrades to content-free evidence — receipts, hashes, tombstones — as doc 28 already contemplates for the evidence-retention tension.

Purge scope is the transitive closure over the basis relation, not one hop. Projections are routinely built from other projections, and the existing `undeclared_residue()` probe in the reference adapter checks a single hop against a single substrate. That is a start, not the requirement.

## Rebuild is a governed mutation

The most consequential finding in this spike, and the least obvious.

For an `estimator_mediated` transform, rebuild is not idempotent. Rebuilding a summary after its source changed does not restore a projection; it *commits new content* derived from an estimator. If staleness detection is allowed to trigger rebuild automatically, then an estimator has acquired the ability to write content into memory whenever it can cause a version bump — which is authority laundering with a maintenance job in front of it, structurally identical to [`authority-laundering`](../../../fixtures/authority-laundering.json).

```text
prohibited   staleness detected -> estimator recomputes -> content committed
             (invalidation as a write channel)

required     staleness detected -> rebuild proposed -> governance evaluates
             -> permitted action selected -> content committed -> receipt
```

Deterministic, reproducible rebuilds are the exception that proves the rule: they can be authorized categorically in advance, precisely because the committed content is a function of canonical state rather than of an estimator's mood. That is a policy decision about a class of transforms, not an exemption from governance.

## Measuring residue

The metric is not a volume. It is a partition, and one cell of it must be empty:

```text
purged                     demonstrated removed
declared residual          known to survive, reported in the deletion receipt,
  controlled                 within the deleting system's reach
declared residual          known to survive, reported, outside its reach
  uncontrollable             (exports, third-party copies, model weights)
undeclared residual        survives and was not reported
```

`undeclared residual = 0` is a hard invariant gate in the sense of [doc 32](../../32-memory-quality-metrics.md): disqualifying and un-averageable. A deletion that leaves recoverable content it did not report is a failed deletion regardless of how much it did remove.

Two honesty constraints keep the metric from measuring itself:

1. **Unknown is not a fourth bucket to hide in.** State whose derivation cannot be enumerated is `declared residual uncontrollable` — declared, and reported — not omitted because it was hard to find. Doc 28 already forbids `deleted from vector store` as evidence about model weights.
2. **Traversal completeness is itself the measurement.** Undeclared residue is discovered by an independent sweep over the derivation closure, not by asking the purge whether it finished. A purge that reports zero residue because it traversed one hop has measured its own optimism.

## What would discharge ADR-020 item 12

> **Execution status.** All seven items below now run in the reference implementation and in CI. See [`../../../reference/README.md`](../../../reference/README.md); the projection layer is `reference/agentmem_ref/projections.py`, residue accounting is `residue.py`, governed operations are `projection_governance.py`, and the executed bar is `reference/tests/test_canonical_and_derived_state.py`. Items 4, 5, and 6 each carry a paired negative test, because a bar that only passes proves less than one that can also fail. This does not by itself accept ADR-020, which has further validation items.

Stated now so the evidence bar is fixed before the implementation that must clear it:

1. A projection declaration exists for tier-3 state, with basis recorded at build time.
2. `stale` and `residual` are computed from the relation above against a real substrate, not asserted by a flag.
3. Correction of a canonical unit marks dependent projections stale and supersedes content-bearing ones without erasing the superseded version.
4. Purge of a canonical unit reaches the transitive closure of its basis, including superseded projection versions.
5. An independent sweep finds zero undeclared residue, and the deletion receipt's declared-residual buckets match what the sweep found.
6. Automatic rebuild of an estimator-mediated projection is refused without an authority decision, and the refusal is on a negative path in the test corpus.
7. The whole run is pinned, reproducible, and reconstructable from receipts, per the program's evidence rules.

Items 4, 5, and 6 are the ones a persuasive demonstration would skip.

## Open questions

- What basis granularity is affordable? Per-unit versions are exact and expensive; per-partition watermarks are cheap and coarse enough to mark everything stale constantly.
- Derivation graphs may contain cycles once projections feed consolidation that feeds projections. Is the closure well-founded, or does it need an explicit acyclicity constraint?
- Does a projection over a tombstoned unit's *metadata only* count as residual? The trichotomy says yes; that may be too strong for reference-only projections, and the exception needs stating rather than assuming.
- Can a projection legitimately outlive its basis by policy — a lawful-retention aggregate over purged sources — and what makes that different from residue?
- Where does the declaration live for substrates that cannot store it? A sidecar owned by the adapter is the obvious answer and reintroduces the consistency problem one level up.

## Doctrine candidate

Derived state inherits every obligation of the memory it derives from, and acquires one more: it can be wrong by being late.

A system that cannot say when its projections were last true is not caching. It is remembering things it has already been told to forget.
