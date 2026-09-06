"""Executable governance paths over a permissive substrate.

One positive path and eight negative paths. The negative paths are the point:
each one is a way the substrate would happily misbehave if the adapter were
not in front of it, and several assert *both* that the substrate is permissive
and that the adapter refuses anyway. A test that only checked the adapter
would not prove the governance was load-bearing.

Run: python -m unittest discover -s reference/tests -t reference
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy, receipts  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.substrate import Episode, Fact, InMemoryTemporalGraph  # noqa: E402

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
        evidence_refs=("ev:source-1",),
        estimator_refs=("est:saturation",),
        estimator_versions=("v2",),
        confidence=0.86,
        tenant_ref=TENANT,
        purpose="assistance",
    )
    base.update(overrides)
    return policy.Proposal(**base)


class GovernedPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant=TENANT, clock=Clock())

    # -- positive path --------------------------------------------------

    def test_positive_path_commits_and_reconstructs(self):
        episode = Episode("ep-1", "The deploy window moved to Thursday.", "chat", "2026-01-01T00:00:00Z", TENANT)
        result = self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday", episode)

        self.assertTrue(result.committed)
        self.assertEqual(result.decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertIn(result.receipt["selected_action"], result.receipt["permitted_actions"])

        # The receipt reconstructs estimate -> authority -> selection -> consequence.
        self.assertEqual(result.receipt["estimator_versions"], {"est:saturation": "v2"})
        self.assertEqual(result.receipt["policy_version"], policy.POLICY_VERSION)
        self.assertEqual(result.receipt["before_state"], "v0")
        self.assertEqual(result.receipt["after_state"], "v1")
        self.assertIn("rollback_or_recovery_ref", result.receipt)

        # The event chain is causally linked.
        types = [event["event_type"] for event in result.events]
        self.assertEqual(types, ["memory.propose", "memory.authorize", "memory.commit", "memory.receipt"])
        for earlier, later in zip(result.events, result.events[1:]):
            self.assertEqual(later["causation_id"], earlier["event_id"])

        admitted = self.adapter.governed_recall("deploy window")
        self.assertEqual(admitted.admitted, [result.fact_uuid])

    # -- negative paths -------------------------------------------------

    def test_high_confidence_cannot_self_authorize_durability(self):
        """Confidence is evidence input, never authority."""
        confident = make_proposal(
            proposal_id="prop-hc", target_class=policy.M4, risk_class="high", confidence=0.99
        )
        doubtful = make_proposal(
            proposal_id="prop-hc", target_class=policy.M4, risk_class="high", confidence=0.01
        )

        high = self.adapter.commit_proposal(confident, "claimed fact")
        low = self.adapter.commit_proposal(doubtful, "claimed fact")

        self.assertFalse(high.committed)
        self.assertEqual(high.decision.outcome, policy.REQUIRE_REVIEW)
        self.assertNotIn("promotion", high.decision.permitted_actions)
        # Identical envelope regardless of confidence.
        self.assertEqual(high.decision.outcome, low.decision.outcome)
        self.assertEqual(high.decision.permitted_actions, low.decision.permitted_actions)

    def test_relevance_cannot_cross_tenant_boundary(self):
        foreign = Fact(
            uuid="foreign-1",
            fact_text="deploy window is Thursday",
            group_id=OTHER_TENANT,
            created_at="2026-01-01T00:00:00Z",
        )
        self.substrate.write_fact(foreign)

        # The substrate is genuinely permissive: unfiltered search returns it.
        unfiltered = self.substrate.search("deploy window")
        self.assertIn("foreign-1", [fact.uuid for fact, _ in unfiltered])

        # The adapter never reaches that default.
        result = self.adapter.governed_recall("deploy window")
        self.assertNotIn("foreign-1", result.candidates)
        self.assertNotIn("foreign-1", result.admitted)

    def test_prohibited_action_is_never_selectable(self):
        proposal = make_proposal(
            proposal_id="prop-gov",
            operation="policy_mutation",
            target_class=policy.M5,
            downstream_authority=policy.A5,
            risk_class="high",
        )
        result = self.adapter.commit_proposal(proposal, "widen the promotion threshold")

        self.assertFalse(result.committed)
        self.assertIn("policy_mutation", result.decision.prohibited_actions)
        self.assertNotIn("policy_mutation", result.decision.permitted_actions)
        self.assertNotEqual(result.receipt["selected_action"], "policy_mutation")
        with self.assertRaises(ValueError):
            receipts.enforce_selection(result.decision.permitted_actions, "policy_mutation")

    def test_stale_authorization_does_not_commit(self):
        self.adapter.commit_proposal(make_proposal(), "first write")  # state -> v1
        stale = make_proposal(proposal_id="prop-stale", state_snapshot="v0")

        result = self.adapter.commit_proposal(stale, "second write against old state")

        self.assertFalse(result.committed)
        self.assertEqual(result.refusal, "stale_authorization")
        self.assertEqual(result.receipt["selected_action"], "defer")

    def test_self_approval_of_authority_is_blocked(self):
        proposal = make_proposal(
            proposal_id="prop-self",
            operation="authority_change",
            target_class=policy.M5,
            downstream_authority=policy.A5,
            risk_class="critical",
            approves_own_authority=True,
        )
        result = self.adapter.commit_proposal(proposal, "grant myself deploy authority")

        self.assertEqual(result.decision.outcome, policy.BLOCK)
        self.assertEqual(result.decision.permitted_actions, ())
        self.assertEqual(result.receipt["selected_action"], receipts.NO_ACTION)
        self.assertFalse(result.committed)

    def test_unresolved_actor_authority_fails_closed(self):
        proposal = make_proposal(proposal_id="prop-anon", actor_authority_resolved=False)
        result = self.adapter.commit_proposal(proposal, "write from an unattributable actor")

        self.assertEqual(result.decision.outcome, policy.BLOCK)
        self.assertFalse(result.committed)

    def test_superseded_memory_stays_distinguishable(self):
        committed = self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")
        self.substrate.invalidate_fact(committed.fact_uuid, "2026-02-01T00:00:00Z", "2026-02-01T00:00:00Z")

        result = self.adapter.governed_recall("deploy window")

        # Still retrievable as a candidate, refused for current use, not erased.
        self.assertIn(committed.fact_uuid, result.candidates)
        self.assertNotIn(committed.fact_uuid, result.admitted)
        self.assertEqual(result.refusals[committed.fact_uuid], "superseded_not_current")
        self.assertIsNotNone(self.substrate.get_fact(committed.fact_uuid))

    def test_irreversible_deletion_cannot_commit_autonomously(self):
        """Permanent deletion never resolves below review, whatever the risk class."""
        committed = self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")
        deletion = make_proposal(
            proposal_id="prop-del",
            operation="permanent_deletion",
            reversibility="irreversible",
            risk_class="low",
        )

        result = self.adapter.governed_delete(deletion, committed.fact_uuid)

        self.assertFalse(result.committed)
        self.assertIn("permanent_deletion", result.decision.prohibited_actions)
        # The substrate would have executed it; the gate is what stopped it.
        self.assertIsNotNone(self.substrate.get_fact(committed.fact_uuid))

    def test_pruning_tombstones_without_destroying_content(self):
        committed = self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")
        pruning = make_proposal(proposal_id="prop-prune", operation="pruning", risk_class="low")

        result = self.adapter.governed_delete(pruning, committed.fact_uuid)

        self.assertTrue(result.committed)
        tombstone = self.adapter.tombstone(committed.fact_uuid)
        self.assertIsNotNone(tombstone)
        self.assertTrue(tombstone["reversible"])
        # Removed from active recall, retained for recovery.
        self.assertIsNotNone(self.substrate.get_fact(committed.fact_uuid))
        recall = self.adapter.governed_recall("deploy window")
        self.assertNotIn(committed.fact_uuid, recall.admitted)
        self.assertEqual(recall.refusals[committed.fact_uuid], "tombstoned")
        self.assertEqual(self.adapter.undeclared_residue(committed.fact_uuid), [])

    def test_undeclared_derived_residue_is_detected(self):
        committed = self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")
        # A derived projection nobody declared, of exactly the kind the substrate
        # does not invalidate on source change.
        self.substrate.write_fact(
            Fact(
                uuid="derived-1",
                fact_text="summary: deploy window is Thursday",
                group_id=TENANT,
                episode_uuids=(committed.fact_uuid,),
                created_at="2026-01-01T00:00:00Z",
            )
        )
        pruning = make_proposal(proposal_id="prop-del2", operation="pruning", risk_class="low")

        self.adapter.governed_delete(pruning, committed.fact_uuid)

        self.assertEqual(self.adapter.undeclared_residue(committed.fact_uuid), ["derived-1"])

    def test_policy_and_estimator_versions_stay_distinguishable(self):
        result = self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")

        self.assertEqual(result.receipt["policy_version"], policy.POLICY_VERSION)
        self.assertEqual(result.receipt["estimator_versions"], {"est:saturation": "v2"})
        self.assertNotIn(result.receipt["policy_version"], result.receipt["estimator_versions"].values())


if __name__ == "__main__":
    unittest.main()
