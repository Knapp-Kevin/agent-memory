"""Substrate driver binding the port to a real temporal knowledge graph.

Implements `TemporalGraphPort` against `graphiti-core` using its no-LLM
direct-write path, so the governed adapter can be exercised against a real
graph database rather than a model.

Three properties make this binding possible without an LLM or an API key,
all verified against the library source and then by execution:

1. the bulk writer invokes the embedder only when an embedding is absent, so
   supplying pre-computed vectors means no embedder is ever called;
2. the Kuzu backend is embedded, so no database server is required; and
3. the driver-level API is reachable without the `Graphiti` facade, which
   force-constructs an LLM client in its constructor even when unused.

The binding deliberately preserves the substrate's permissive default: a
`search` with no partition filter reads across every partition, exactly as the
substrate does. The adapter is what refuses to use it that way.

Declared limitations:

- The Kuzu backend is deprecated upstream. It is used here because it is
  embedded, which makes the probe self-contained. Nothing about the governance
  behavior under test depends on the backend choice.
- Node topology is simplified: each fact becomes one edge between a per-partition
  anchor node and a per-fact node. This binding exercises governance invariants,
  not knowledge modelling.
- Retrieval is a substring match at the driver level rather than the substrate's
  hybrid search, because hybrid ranking needs an embedder. Ranking quality is
  therefore not under test here; scope filtering is.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from .substrate import UNFILTERED, Episode, Fact

_PLACEHOLDER_VECTOR = [0.1, 0.2, 0.3, 0.4]


def graphiti_available() -> bool:
    try:  # pragma: no cover - import probe
        import graphiti_core  # noqa: F401
        import kuzu  # noqa: F401
    except Exception:
        return False
    return True


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _format(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.replace(tzinfo=value.tzinfo or timezone.utc).isoformat()


class GraphitiSubstrate:
    """A `TemporalGraphPort` implementation over a real graph database."""

    def __init__(self, db: str = ":memory:") -> None:
        from graphiti_core.driver.kuzu_driver import KuzuDriver

        self._driver = KuzuDriver(db=db)
        self._loop = asyncio.new_event_loop()
        self._known_groups: set[str] = set()
        self.write_log: list[tuple[str, str]] = []

    def close(self) -> None:
        self._run(self._driver.close())
        self._loop.close()

    def _run(self, coro):
        return self._loop.run_until_complete(coro)

    # -- writes ---------------------------------------------------------

    def add_episode(self, episode: Episode) -> None:
        from graphiti_core.nodes import EpisodeType, EpisodicNode

        node = EpisodicNode(
            uuid=episode.uuid,
            name=episode.uuid,
            group_id=episode.group_id,
            source=EpisodeType.text,
            source_description=episode.source_description,
            content=episode.content,
            valid_at=_parse(episode.valid_at) or datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
        )
        self._run(node.save(self._driver))
        self.write_log.append(("add_episode", episode.uuid))

    def write_fact(self, fact: Fact) -> None:
        """Direct write. No LLM, no authority check, exactly like the substrate."""
        from graphiti_core.edges import EntityEdge
        from graphiti_core.nodes import EntityNode
        from graphiti_core.utils.bulk_utils import add_nodes_and_edges_bulk

        created = _parse(fact.created_at) or datetime.now(timezone.utc)
        anchor = EntityNode(
            uuid=f"anchor:{fact.group_id}",
            name=f"anchor:{fact.group_id}",
            group_id=fact.group_id,
            labels=["Entity"],
            created_at=created,
            name_embedding=list(_PLACEHOLDER_VECTOR),
            summary="partition anchor",
        )
        subject = EntityNode(
            uuid=f"node:{fact.uuid}",
            name=fact.fact_text[:64],
            group_id=fact.group_id,
            labels=["Entity"],
            created_at=created,
            name_embedding=list(_PLACEHOLDER_VECTOR),
            summary=fact.fact_text,
        )
        edge = EntityEdge(
            uuid=fact.uuid,
            source_node_uuid=anchor.uuid,
            target_node_uuid=subject.uuid,
            name="ASSERTS",
            fact=fact.fact_text,
            group_id=fact.group_id,
            created_at=created,
            fact_embedding=list(_PLACEHOLDER_VECTOR),
            episodes=list(fact.episode_uuids),
            valid_at=_parse(fact.valid_at),
            invalid_at=_parse(fact.invalid_at),
            expired_at=_parse(fact.expired_at),
        )
        self._run(add_nodes_and_edges_bulk(self._driver, [], [], [anchor, subject], [edge], None))
        self._known_groups.add(fact.group_id)
        self.write_log.append(("write_fact", fact.uuid))

    def invalidate_fact(self, uuid: str, invalid_at: str, expired_at: str) -> None:
        """Supersession marks the edge; it is never removed."""
        edge = self._load_edge(uuid)
        if edge is None:
            return
        edge.invalid_at = _parse(invalid_at)
        edge.expired_at = _parse(expired_at)
        self._run(edge.save(self._driver))
        self.write_log.append(("invalidate_fact", uuid))

    def delete_fact(self, uuid: str) -> None:
        """Physical removal. The substrate leaves no tombstone behind."""
        edge = self._load_edge(uuid)
        if edge is None:
            return
        self._run(edge.delete(self._driver))
        self.write_log.append(("delete_fact", uuid))

    # -- reads ----------------------------------------------------------

    def _load_edge(self, uuid: str):
        from graphiti_core.edges import EntityEdge

        try:
            return self._run(EntityEdge.get_by_uuid(self._driver, uuid))
        except Exception:
            return None

    def get_fact(self, uuid: str) -> Fact | None:
        edge = self._load_edge(uuid)
        if edge is None:
            return None
        return self._to_fact(edge)

    def all_facts(self) -> tuple[Fact, ...]:
        return tuple(fact for fact, _ in self.search("", group_ids=UNFILTERED, match_all=True))

    def search(
        self, query: str, group_ids: list[str] | None = UNFILTERED, match_all: bool = False
    ) -> list[tuple[Fact, float]]:
        """Candidate generation.

        The unfiltered default is preserved on purpose: omitting `group_ids`
        reads across every partition, which is the substrate behavior the
        adapter must never rely on.
        """
        from graphiti_core.edges import EntityEdge

        groups = group_ids if group_ids is not UNFILTERED else self._all_group_ids()
        if not groups:
            return []
        try:
            edges = self._run(EntityEdge.get_by_group_ids(self._driver, groups))
        except Exception:
            # The substrate raises rather than returning an empty result set
            # when a partition holds no edges. An empty partition is not an error.
            return []
        terms = {token.lower() for token in query.split() if token}
        scored: list[tuple[Fact, float]] = []
        for edge in edges:
            fact = self._to_fact(edge)
            if match_all:
                scored.append((fact, 1.0))
                continue
            overlap = terms & {token.strip(".,").lower() for token in fact.fact_text.split()}
            if overlap:
                scored.append((fact, len(overlap) / max(len(terms), 1)))
        scored.sort(key=lambda pair: (-pair[1], pair[0].uuid))
        return scored

    def _all_group_ids(self) -> list[str]:
        """Partitions this driver has written to.

        Tracked in the driver rather than queried, to avoid coupling the probe
        to the substrate's internal schema. The effect is the same: an
        unfiltered search reads across every partition.
        """
        return sorted(self._known_groups)

    @staticmethod
    def _to_fact(edge) -> Fact:
        return Fact(
            uuid=edge.uuid,
            fact_text=edge.fact,
            group_id=edge.group_id,
            episode_uuids=tuple(edge.episodes or ()),
            valid_at=_format(edge.valid_at),
            invalid_at=_format(edge.invalid_at),
            created_at=_format(edge.created_at),
            expired_at=_format(edge.expired_at),
        )
