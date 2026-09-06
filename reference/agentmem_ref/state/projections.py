"""Tier-3 projection declarations, freshness, and residue.

Implements the design spike in
`docs/programs/runtime-evidence/canonical-and-derived-state.md`.

The spike's headline finding is that P4 is mostly a tier-3 problem: indices,
embeddings, caches, and materialized views are not memory units, so nothing
obliges them to declare what they were built from, and that is exactly where
deletion residue hides. This module gives tier-3 state the declaration surface
it lacked.

Two design commitments carry through:

**Freshness is a computed relation, not a flag.** Nothing sets a `stale` bit.
`current`, `stale`, and `residual` are derived at read time from a recorded
basis against current canonical state, so a substrate that never
self-invalidates is still governable.

**Stale and residual are different states with different authorities.** Stale
is a correctness problem that recomputation may fix. Residual is a governance
problem only the deletion authority may resolve. Collapsing them would lose
the distinction the architecture exists to protect.

The declaration lives in an adapter-owned sidecar, which the spike names as the
obvious home for substrates that cannot store it, and which reintroduces the
consistency problem one level up. That trade is recorded rather than hidden.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace

# transform
DETERMINISTIC = "deterministic"
ESTIMATOR_MEDIATED = "estimator_mediated"

# content_class
REFERENCE_ONLY = "reference_only"
DERIVED_CONTENT = "derived_content"
RECOVERABLE_CONTENT = "recoverable_content"

# rebuild
REPRODUCIBLE = "reproducible"
APPROXIMABLE = "approximable"
IRREPRODUCIBLE = "irreproducible"

# freshness relation
CURRENT = "current"
STALE = "stale"
RESIDUAL = "residual"

#: Content classes that can carry a source's content past its deletion.
CONTENT_BEARING = frozenset({DERIVED_CONTENT, RECOVERABLE_CONTENT})


@dataclass(frozen=True)
class Projection:
    """A declaration of tier-3 state's relationship to canonical state.

    `basis` maps each source identifier to the version read at build time. A
    source may itself be a projection: derivation graphs are not flat, which is
    why residue closure must be transitive.
    """

    projection_id: str
    basis: tuple[tuple[str, int], ...]
    transform: str
    content_class: str
    rebuild: str
    scope: str
    version: int = 1
    superseded_by: str | None = None
    reachable: bool = True
    note: str = ""

    @property
    def basis_map(self) -> dict[str, int]:
        return dict(self.basis)

    @property
    def is_content_bearing(self) -> bool:
        return self.content_class in CONTENT_BEARING

    @property
    def requires_authority_to_rebuild(self) -> bool:
        """Deterministic reproducible rebuilds may be authorized categorically.

        Everything else commits estimator-derived content and must pass through
        governance, or invalidation becomes a write channel.
        """
        return not (self.transform == DETERMINISTIC and self.rebuild == REPRODUCIBLE)


class CanonicalView:
    """What the freshness relation needs to know about canonical state."""

    def __init__(self, versions: dict[str, int], tombstoned: set[str], purged: set[str]) -> None:
        self._versions = versions
        self._tombstoned = tombstoned
        self._purged = purged

    def version(self, memory_id: str) -> int | None:
        return self._versions.get(memory_id)

    def is_tombstoned(self, memory_id: str) -> bool:
        return memory_id in self._tombstoned

    def is_purged(self, memory_id: str) -> bool:
        return memory_id in self._purged


class ProjectionStore:
    """Sidecar registry of projection declarations and superseded versions."""

    def __init__(self) -> None:
        self._live: dict[str, Projection] = {}
        self._superseded: dict[str, list[Projection]] = {}

    # -- declaration ----------------------------------------------------

    def declare(self, projection: Projection) -> Projection:
        self._live[projection.projection_id] = projection
        return projection

    def get(self, projection_id: str) -> Projection | None:
        return self._live.get(projection_id)

    def live(self) -> tuple[Projection, ...]:
        return tuple(self._live.values())

    def superseded(self, projection_id: str) -> tuple[Projection, ...]:
        return tuple(self._superseded.get(projection_id, ()))

    def all_versions(self) -> tuple[Projection, ...]:
        retained: list[Projection] = list(self._live.values())
        for versions in self._superseded.values():
            retained.extend(versions)
        return tuple(retained)

    def supersede(self, projection_id: str, new_basis: tuple[tuple[str, int], ...]) -> Projection | None:
        """Retain the prior version rather than overwriting it.

        A decision that used the earlier content must remain reconstructable.
        Deletion may later override this; see `drop_version`.
        """
        current = self._live.get(projection_id)
        if current is None:
            return None
        retired = replace(current, superseded_by=f"{projection_id}@v{current.version + 1}")
        self._superseded.setdefault(projection_id, []).append(retired)
        updated = replace(current, basis=new_basis, version=current.version + 1)
        self._live[projection_id] = updated
        return updated

    def drop(self, projection_id: str) -> None:
        """Remove a projection and every retained version of it."""
        self._live.pop(projection_id, None)
        self._superseded.pop(projection_id, None)

    # -- relations ------------------------------------------------------

    def freshness(self, projection: Projection, view: CanonicalView) -> str:
        """Compute the freshness relation. Residual dominates stale."""
        basis = projection.basis_map
        for source, read_version in basis.items():
            if view.is_tombstoned(source) or view.is_purged(source):
                return RESIDUAL
        for source, read_version in basis.items():
            if view.version(source) != read_version:
                return STALE
        return CURRENT

    def dependents_of(self, source_id: str) -> tuple[Projection, ...]:
        return tuple(p for p in self._live.values() if source_id in p.basis_map)

    def derivation_closure(self, source_id: str) -> tuple[str, ...]:
        """Every projection reachable from a source through the basis relation.

        Transitive, because projections are routinely built from projections
        and a one-hop purge measures its own optimism. Cycles are possible once
        projections feed consolidation that feeds projections, so the walk
        carries a seen-set rather than assuming the graph is well-founded.
        """
        found: list[str] = []
        seen: set[str] = set()
        frontier = [source_id]
        while frontier:
            current = frontier.pop()
            for projection in self.dependents_of(current):
                if projection.projection_id in seen:
                    continue
                seen.add(projection.projection_id)
                found.append(projection.projection_id)
                frontier.append(projection.projection_id)
        return tuple(found)
