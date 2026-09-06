"""Substrate port and a deliberately permissive in-memory temporal graph.

The port describes the narrow set of operations a governed adapter needs from a
temporal knowledge-graph substrate. `InMemoryTemporalGraph` implements it while
reproducing the **verified** semantics of the mapped substrate documented in
`docs/programs/runtime-evidence/graphiti-conformance.md`, including the
permissive ones:

- identity is an opaque generated identifier, not a content address;
- partition filtering is an optional query argument that defaults to unfiltered;
- supersession marks validity fields rather than deleting a row;
- deletion is physical and leaves no tombstone;
- no operation checks actor identity or authority.

Reproducing the permissiveness is the entire point. A stub that were already
safe would prove nothing about the governance layer under test: the negative
paths need something real to escape through.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Iterable, Protocol

UNFILTERED = None


class DeterministicIds:
    """Counter-based identifier factory, so runs are reproducible."""

    def __init__(self, prefix: str) -> None:
        self._prefix = prefix
        self._n = 0

    def next(self) -> str:
        self._n += 1
        return f"{self._prefix}-{self._n:04d}"


@dataclass(frozen=True)
class Episode:
    """Raw source material, retained verbatim."""

    uuid: str
    content: str
    source_description: str
    valid_at: str
    group_id: str


@dataclass(frozen=True)
class Fact:
    """A temporal assertion with event-time and transaction-time axes."""

    uuid: str
    fact_text: str
    group_id: str
    episode_uuids: tuple[str, ...] = ()
    valid_at: str | None = None
    invalid_at: str | None = None
    created_at: str | None = None
    expired_at: str | None = None
    attributes: dict = field(default_factory=dict)

    @property
    def is_event_invalid(self) -> bool:
        return self.invalid_at is not None

    @property
    def is_transaction_expired(self) -> bool:
        return self.expired_at is not None


class TemporalGraphPort(Protocol):
    """Operations a governed adapter requires from a temporal graph."""

    def add_episode(self, episode: Episode) -> None: ...

    def write_fact(self, fact: Fact) -> None: ...

    def invalidate_fact(self, uuid: str, invalid_at: str, expired_at: str) -> None: ...

    def get_fact(self, uuid: str) -> Fact | None: ...

    def delete_fact(self, uuid: str) -> None: ...

    def search(self, query: str, group_ids: list[str] | None = UNFILTERED) -> list[tuple[Fact, float]]: ...


class InMemoryTemporalGraph:
    """Permissive substrate model. Executes whatever reaches it."""

    def __init__(self) -> None:
        self._episodes: dict[str, Episode] = {}
        self._facts: dict[str, Fact] = {}
        self.write_log: list[tuple[str, str]] = []
        # GAP-SEC-08: identifiers are minted per substrate, not per adapter.
        # Two adapters sharing one substrate previously ran independent
        # counters and collided on every id -- fact uuid, receipt_id,
        # correlation_id, and all four event ids -- silently replacing each
        # other's facts and merging each other's evidence records.
        self._ids = DeterministicIds("ref")

    def next_id(self) -> str:
        """Mint the next substrate-scoped identifier.

        Discovered by attribute rather than declared on ``TemporalGraphPort``:
        adding a Protocol member would break every external implementation,
        and the declared contract is Sprint 4's to change.
        """
        return self._ids.next()

    # -- writes ---------------------------------------------------------

    def add_episode(self, episode: Episode) -> None:
        self._episodes[episode.uuid] = episode
        self.write_log.append(("add_episode", episode.uuid))

    def write_fact(self, fact: Fact) -> None:
        """Direct write. No authority check, by design and by observation.

        GAP-SEC-08 guard: refuse a uuid that already holds a *different* fact
        rather than replacing it. Defence in depth behind the substrate-scoped
        counter -- a foreign substrate without ``next_id`` still falls back to
        per-adapter counters, and this turns the resulting cross-tenant data
        loss into a loud failure at the point of harm. An identical re-write
        stays a no-op, so replay remains idempotent.
        """
        existing = self._facts.get(fact.uuid)
        if existing is not None and existing != fact:
            raise ValueError(
                f"refusing to overwrite fact {fact.uuid!r} "
                f"(stored group_id={existing.group_id!r}, "
                f"incoming group_id={fact.group_id!r}): "
                "identifier collision would destroy a committed fact"
            )
        self._facts[fact.uuid] = fact
        self.write_log.append(("write_fact", fact.uuid))

    def invalidate_fact(self, uuid: str, invalid_at: str, expired_at: str) -> None:
        """Supersession marks; it never deletes."""
        current = self._facts.get(uuid)
        if current is None:
            return
        self._facts[uuid] = replace(current, invalid_at=invalid_at, expired_at=expired_at)
        self.write_log.append(("invalidate_fact", uuid))

    def delete_fact(self, uuid: str) -> None:
        """Physical removal. No tombstone is written by the substrate."""
        self._facts.pop(uuid, None)
        self.write_log.append(("delete_fact", uuid))

    # -- reads ----------------------------------------------------------

    def get_fact(self, uuid: str) -> Fact | None:
        return self._facts.get(uuid)

    def get_episode(self, uuid: str) -> Episode | None:
        return self._episodes.get(uuid)

    def all_facts(self) -> Iterable[Fact]:
        return tuple(self._facts.values())

    def search(self, query: str, group_ids: list[str] | None = UNFILTERED) -> list[tuple[Fact, float]]:
        """Candidate generation by lexical overlap.

        Two modelled behaviors matter more than the ranking quality:

        1. `group_ids` defaults to unfiltered, so a caller that forgets the
           argument reads across every partition;
        2. event-invalid facts remain retrievable, matching the conservative
           reading of an open question the source review could not settle.
        """
        terms = _tokens(query)
        scored: list[tuple[Fact, float]] = []
        for fact in self._facts.values():
            if group_ids is not UNFILTERED and fact.group_id not in group_ids:
                continue
            overlap = terms & _tokens(fact.fact_text)
            if not overlap:
                continue
            scored.append((fact, len(overlap) / max(len(terms), 1)))
        scored.sort(key=lambda pair: (-pair[1], pair[0].uuid))
        return scored


def _tokens(text: str) -> set[str]:
    return {token.strip(".,;:!?").lower() for token in text.split() if token.strip(".,;:!?")}
