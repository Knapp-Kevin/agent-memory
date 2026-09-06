"""Focused negative-path evidence for explicit required isolation domains."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402


class RequiredCompartmentSemanticsTests(unittest.TestCase):
    def _proposal(self, *, bound: tuple[str, ...], required: tuple[str, ...]) -> policy.Proposal:
        return policy.Proposal(
            proposal_id="proposal:required-compartment",
            actor_id="agent:planner",
            charter_version="charter-1",
            target_reference="mem:compartmented",
            target_class=policy.M2,
            scope="tenant-a",
            operation="promotion",
            current_strength="reinforced",
            proposed_strength="promoted",
            downstream_authority=policy.A1,
            reversibility="reversible",
            risk_class="low",
            evidence_refs=("evidence:scope-policy",),
            tenant_ref="tenant-a",
            isolation_domain_refs=bound,
            required_isolation_domain_refs=required,
            project_ref="project-a",
            task_ref="task-1",
        )

    def test_required_domain_must_also_be_bound_to_memory(self):
        decision = policy.evaluate(
            self._proposal(
                bound=("domain:project-a", "compartment:export-controlled"),
                required=("compartment:export-controlled", "compartment:legal"),
            )
        )

        self.assertEqual(decision.outcome, policy.BLOCK)
        self.assertIn("promotion", decision.prohibited_actions)
        self.assertIn("required isolation domains must be bound", decision.reasons[0])

    def test_coherent_required_domains_do_not_change_pama_strength_by_themselves(self):
        decision = policy.evaluate(
            self._proposal(
                bound=("domain:project-a", "compartment:export-controlled", "compartment:legal"),
                required=("compartment:export-controlled", "compartment:legal"),
            )
        )

        self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertIn("promotion", decision.permitted_actions)


if __name__ == "__main__":
    unittest.main()
