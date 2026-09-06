"""Deletion residue as a partition, with one cell that must stay empty.

Implements the residue accounting of the canonical-and-derived-state design
spike. The metric is not a volume of removed bytes; it is a four-way partition
of everything derived from a purged source:

```text
purged                              demonstrated removed
declared_residual_controlled        survives, reported, within reach
declared_residual_uncontrollable    survives, reported, outside reach
undeclared_residual                 survives and was not reported
```

`undeclared_residual = 0` is a hard invariant gate: disqualifying and
un-averageable. A deletion that leaves recoverable content it did not report is
a failed deletion however much it removed.

Two honesty constraints from the spike are load-bearing here:

1. **Unknown is not a fourth bucket.** State whose derivation cannot be
   enumerated is declared uncontrollable — declared and reported — never
   omitted because it was inconvenient to find.
2. **Traversal completeness is itself the measurement.** `independent_sweep`
   does not ask the purge whether it finished. It re-derives residual status
   from the freshness relation over every retained declaration, including
   superseded versions, so a purge that traversed one hop is caught rather than
   believed.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .projections import CanonicalView, ProjectionStore, RESIDUAL

PURGED = "purged"
DECLARED_CONTROLLED = "declared_residual_controlled"
DECLARED_UNCONTROLLABLE = "declared_residual_uncontrollable"
UNDECLARED = "undeclared_residual"


@dataclass
class ResiduePlan:
    """What a purge intends to do with each projection in the closure."""

    purged: list[str] = field(default_factory=list)
    declared_residual_controlled: list[str] = field(default_factory=list)
    declared_residual_uncontrollable: list[str] = field(default_factory=list)

    @property
    def declared(self) -> set[str]:
        return set(self.declared_residual_controlled) | set(self.declared_residual_uncontrollable)

    def as_receipt_buckets(self) -> dict[str, list[str]]:
        return {
            PURGED: sorted(self.purged),
            DECLARED_CONTROLLED: sorted(self.declared_residual_controlled),
            DECLARED_UNCONTROLLABLE: sorted(self.declared_residual_uncontrollable),
        }


def plan_purge(
    store: ProjectionStore,
    source_id: str,
    retained_by_policy: set[str] | None = None,
) -> ResiduePlan:
    """Classify the transitive closure of a source into residue buckets.

    The closure is transitive by construction. A one-hop plan would leave
    projections-of-projections holding the purged content, which is the failure
    the independent sweep exists to catch.
    """
    held = retained_by_policy or set()
    plan = ResiduePlan()
    for projection_id in store.derivation_closure(source_id):
        projection = store.get(projection_id)
        if projection is None:
            continue
        if not projection.is_content_bearing:
            # Reference-only state carries no content past its source.
            plan.purged.append(projection_id)
        elif not projection.reachable:
            # Exports, third-party copies, model weights: known, reported, unreachable.
            plan.declared_residual_uncontrollable.append(projection_id)
        elif projection_id in held:
            plan.declared_residual_controlled.append(projection_id)
        else:
            plan.purged.append(projection_id)
    return plan


def apply_purge(store: ProjectionStore, plan: ResiduePlan, purged: set[str]) -> None:
    """Remove what the plan says is purged, including superseded versions.

    Deletion dominates correction: a superseded version retained for
    reconstructability is, once its basis is purged, exactly the recoverable
    residue the deletion was meant to eliminate.

    Purged identifiers are recorded in `purged` because a projection built on a
    purged projection is residual, not merely stale. Without that, a partial
    purge would look like a correctness problem instead of a governance one.
    """
    for projection_id in plan.purged:
        store.drop(projection_id)
        purged.add(projection_id)


def independent_sweep(
    store: ProjectionStore,
    view: CanonicalView,
    declared: set[str],
) -> list[str]:
    """Re-derive residual state without consulting the purge's traversal.

    Any retained declaration — live or superseded — that still carries content
    and whose basis includes a tombstoned or purged source is residue. If it
    was not declared in the deletion receipt, it is undeclared, and that is a
    hard-gate failure.
    """
    undeclared: list[str] = []
    for projection in store.all_versions():
        if not projection.is_content_bearing:
            continue
        if store.freshness(projection, view) != RESIDUAL:
            continue
        if projection.projection_id in declared:
            continue
        undeclared.append(projection.projection_id)
    return sorted(set(undeclared))


def partition(
    store: ProjectionStore,
    view: CanonicalView,
    plan: ResiduePlan,
) -> dict[str, list[str]]:
    """The full four-way partition, with the swept result in the last cell."""
    buckets = plan.as_receipt_buckets()
    buckets[UNDECLARED] = independent_sweep(store, view, plan.declared)
    return buckets
