"""Stochastic selection stays inside the authority envelope across repeated runs.

This is the containment property ADR-020's acceptance checklist asks for.
Three things have to hold together, and testing only the first would be
self-flattering:

1. **Safety.** Across many trials and seeds, no selected action is ever
   outside the permitted set, and never a prohibited one.
2. **Liveness.** The selector genuinely varies. A selector that always
   returned the first permitted action would pass any safety check while
   proving nothing, so the tests assert that more than one distinct action is
   actually observed.
3. **Containment under a hostile selector.** A selector that deliberately
   returns a prohibited action must not escape. The guarantee has to come from
   the adapter, not from the selector's good manners.

Run: python -m unittest discover -s reference/tests -t reference
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy, receipts  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, StochasticSelector  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

TENANT = "tenant-a"
TRIALS = 200


def make_proposal(**overrides) -> policy.Proposal:
    base = dict(
        proposal_id="prop-stoch",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference="mem:alpha",
        target_class=policy.M4,
        scope=TENANT,
        operation="crystallization",
        current_strength="reinforced",
        proposed_strength="canonical",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="high",
        evidence_refs=("ev:source-1",),
        tenant_ref=TENANT,
        purpose="assistance",
    )
    base.update(overrides)
    return policy.Proposal(**base)


class HostileSelector:
    """Always tries to take an action the envelope prohibits."""

    mode = "stochastic"

    def __init__(self, forbidden: str) -> None:
        self._forbidden = forbidden

    def select(self, permitted: tuple[str, ...], preferred: str | None) -> str:
        return self._forbidden


class StochasticContainmentTests(unittest.TestCase):
    def _adapter(self, selector) -> GovernedMemoryAdapter:
        return GovernedMemoryAdapter(
            InMemoryTemporalGraph(), tenant=TENANT, clock=Clock(), selector=selector
        )

    def test_selection_never_escapes_the_permitted_set(self):
        observed: set[str] = set()
        for seed in range(TRIALS):
            adapter = self._adapter(StochasticSelector(seed=seed))
            result = adapter.commit_proposal(make_proposal(), "a claim")

            permitted = result.decision.permitted_actions
            prohibited = result.decision.prohibited_actions
            selected = result.receipt["selected_action"]

            self.assertIn(selected, permitted, f"seed {seed} escaped the permitted set")
            self.assertNotIn(selected, prohibited, f"seed {seed} selected a prohibited action")
            self.assertEqual(adapter.containment_violations, [])
            observed.add(selected)

        # Liveness: the selector must actually vary, or safety proved nothing.
        self.assertGreater(len(observed), 1, "selector never varied; the safety assertion is vacuous")

    def test_crystallization_is_never_reachable_by_sampling(self):
        """The requested operation is prohibited here; no seed may reach it."""
        for seed in range(TRIALS):
            adapter = self._adapter(StochasticSelector(seed=seed))
            result = adapter.commit_proposal(make_proposal(), "a claim")

            self.assertFalse(result.committed, f"seed {seed} committed a prohibited operation")
            self.assertNotEqual(result.receipt["selected_action"], "crystallization")

    def test_selection_mode_is_recorded_as_stochastic(self):
        adapter = self._adapter(StochasticSelector(seed=1))
        result = adapter.commit_proposal(make_proposal(), "a claim")

        self.assertEqual(result.receipt["selection_mode"], "stochastic")
        self.assertEqual(result.pama_decision["decision"]["selection_mode"], "stochastic")

    def test_hostile_selector_is_contained_not_trusted(self):
        adapter = self._adapter(HostileSelector("crystallization"))
        result = adapter.commit_proposal(make_proposal(), "a claim")

        self.assertFalse(result.committed)
        self.assertNotEqual(result.receipt["selected_action"], "crystallization")
        self.assertIn(result.receipt["selected_action"], result.decision.permitted_actions)
        self.assertTrue(adapter.containment_violations, "the violation must be recorded, not silently fixed")

    def test_blocked_envelope_yields_no_action_under_sampling(self):
        blocked = make_proposal(
            proposal_id="prop-blocked",
            operation="authority_change",
            target_class=policy.M5,
            downstream_authority=policy.A5,
            risk_class="critical",
            approves_own_authority=True,
        )
        for seed in range(20):
            adapter = self._adapter(StochasticSelector(seed=seed))
            result = adapter.commit_proposal(blocked, "grant myself authority")

            self.assertEqual(result.decision.outcome, policy.BLOCK)
            self.assertEqual(result.decision.permitted_actions, ())
            self.assertEqual(result.receipt["selected_action"], receipts.NO_ACTION)
            self.assertFalse(result.committed)

    def test_repeated_runs_are_reproducible_per_seed(self):
        first = self._adapter(StochasticSelector(seed=7)).commit_proposal(make_proposal(), "a claim")
        second = self._adapter(StochasticSelector(seed=7)).commit_proposal(make_proposal(), "a claim")

        self.assertEqual(first.receipt["selected_action"], second.receipt["selected_action"])
        self.assertEqual(first.receipt, second.receipt)


if __name__ == "__main__":
    unittest.main()
