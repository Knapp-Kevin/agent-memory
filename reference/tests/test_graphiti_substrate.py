"""Governance paths executed against a real temporal knowledge graph.

These are the same invariants as `test_governed_paths.py`, run against
`graphiti-core` backed by an embedded graph database instead of a model. That
difference is what makes these runtime evidence rather than a precondition.

Skipped when the substrate is not installed, so the standard-library gate stays
runnable everywhere:

    pip install graphiti-core kuzu
    python -m unittest discover -s reference/tests -t reference
"""

from __future__ import annotations

import sys
import unittest
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.graphiti_driver import graphiti_available  # noqa: E402
from agentmem_ref.substrate import Episode  # noqa: E402

TENANT = "tenant-a"
OTHER_TENANT = "tenant-b"


def make_proposal(**overrides) -> policy.Proposal:
    base = dict(
        proposal_id="prop-1",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference="mem:alpha",
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("ep-1",),
        estimator_refs=("est:saturation",),
        estimator_versions=("v2",),
        confidence=0.86,
        tenant_ref=TENANT,
        purpose="assistance",
    )
    base.update(overrides)
    return policy.Proposal(**base)


@unittest.skipUnless(graphiti_available(), "graphiti-core and kuzu are not installed")
class GraphitiSubstrateTests(unittest.TestCase):
    """Runtime evidence: the same governance holds over a real substrate."""

    def setUp(self) -> None:
        warnings.simplefilter("ignore", DeprecationWarning)
        from agentmem_ref.graphiti_driver import GraphitiSubstrate

        self.substrate = GraphitiSubstrate(db=":memory:")
        self.addCleanup(self.substrate.close)
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant=TENANT, clock=Clock())

    def _seed(self, text: str = "deploy window is Thursday"):
        episode = Episode("ep-1", text, "chat", "2026-01-01T00:00:00Z", TENANT)
        return self.adapter.commit_proposal(make_proposal(), text, episode)

    def test_positive_path_persists_and_reconstructs(self):
        result = self._seed()

        self.assertTrue(result.committed)
        stored = self.substrate.get_fact(result.fact_uuid)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.fact_text, "deploy window is Thursday")
        self.assertEqual(stored.group_id, TENANT)
        self.assertEqual(stored.episode_uuids, ("ep-1",))
        self.assertIn(result.receipt["selected_action"], result.receipt["permitted_actions"])

        recall = self.adapter.governed_recall("deploy window")
        self.assertEqual(recall.admitted, [result.fact_uuid])

    def test_relevance_cannot_cross_tenant_boundary(self):
        from agentmem_ref.substrate import Fact

        self.substrate.write_fact(
            Fact(
                uuid="foreign-1",
                fact_text="deploy window is Thursday",
                group_id=OTHER_TENANT,
                created_at="2026-01-01T00:00:00Z",
            )
        )
        self._seed()

        # The real substrate is permissive: unfiltered search crosses partitions.
        unfiltered = self.substrate.search("deploy window")
        self.assertIn("foreign-1", [fact.uuid for fact, _ in unfiltered])

        # The adapter never reaches that default.
        recall = self.adapter.governed_recall("deploy window")
        self.assertNotIn("foreign-1", recall.candidates)
        self.assertNotIn("foreign-1", recall.admitted)

    def test_supersession_marks_without_deleting(self):
        result = self._seed()

        self.substrate.invalidate_fact(result.fact_uuid, "2026-02-01T00:00:00Z", "2026-02-01T00:00:00Z")

        stored = self.substrate.get_fact(result.fact_uuid)
        self.assertIsNotNone(stored, "supersession must not delete the record")
        self.assertIsNotNone(stored.invalid_at)
        recall = self.adapter.governed_recall("deploy window")
        self.assertIn(result.fact_uuid, recall.candidates)
        self.assertNotIn(result.fact_uuid, recall.admitted)
        self.assertEqual(recall.refusals[result.fact_uuid], "superseded_not_current")

    def test_high_confidence_cannot_self_authorize_durability(self):
        proposal = make_proposal(
            proposal_id="prop-hc", target_class=policy.M4, risk_class="high", confidence=0.99
        )
        result = self.adapter.commit_proposal(proposal, "unverified but confident claim")

        self.assertFalse(result.committed)
        self.assertIsNone(result.fact_uuid)
        # Nothing reached the substrate.
        self.assertEqual(self.substrate.search("unverified"), [])

    def test_irreversible_deletion_cannot_commit_autonomously(self):
        result = self._seed()
        deletion = make_proposal(
            proposal_id="prop-del",
            operation="permanent_deletion",
            reversibility="irreversible",
            risk_class="low",
        )

        outcome = self.adapter.governed_delete(deletion, result.fact_uuid)

        self.assertFalse(outcome.committed)
        # The substrate would have executed the delete; the gate is what stopped it.
        self.assertIsNotNone(self.substrate.get_fact(result.fact_uuid))

    def test_pruning_tombstones_without_destroying_content(self):
        result = self._seed()
        pruning = make_proposal(proposal_id="prop-prune", operation="pruning", risk_class="low")

        outcome = self.adapter.governed_delete(pruning, result.fact_uuid)

        self.assertTrue(outcome.committed)
        self.assertIsNotNone(self.substrate.get_fact(result.fact_uuid))
        recall = self.adapter.governed_recall("deploy window")
        self.assertEqual(recall.refusals[result.fact_uuid], "tombstoned")

    def test_approved_permanent_deletion_removes_physically(self):
        """The one path the model could not exercise: a real physical delete."""
        result = self._seed()
        self.substrate.delete_fact(result.fact_uuid)

        self.assertIsNone(self.substrate.get_fact(result.fact_uuid))
        recall = self.adapter.governed_recall("deploy window")
        self.assertNotIn(result.fact_uuid, recall.candidates)


if __name__ == "__main__":
    unittest.main()
