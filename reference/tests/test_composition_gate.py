"""Executable cross-domain composition evidence for issue #68."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext  # noqa: E402
from agentmem_ref.composition import (  # noqa: E402
    CompositionCandidate,
    CompositionConstraint,
    evaluate_composition,
)
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

TENANT = "tenant-a"
DOMAIN_RED = "domain:project-red"
DOMAIN_BLUE = "domain:project-blue"


def proposal(reference: str, domain: str) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=f"proposal:{reference}",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference=reference,
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:source",),
        tenant_ref=TENANT,
        purpose="assistance",
        isolation_domain_refs=(domain,),
    )


class CompositionGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=TENANT, clock=Clock())
        red = self.adapter.commit_proposal(
            proposal("mem:red", DOMAIN_RED),
            "rotation evidence shared composition token",
        )
        blue = self.adapter.commit_proposal(
            proposal("mem:blue", DOMAIN_BLUE),
            "rotation evidence shared composition token",
        )
        self.assertTrue(red.committed)
        self.assertTrue(blue.committed)
        self.red_uuid = red.fact_uuid
        self.blue_uuid = blue.fact_uuid

    def _recall_both(self):
        recall = self.adapter.governed_recall(
            "rotation evidence shared composition token",
            RecallContext(target_domain_refs=(DOMAIN_RED, DOMAIN_BLUE), purpose="assistance"),
        )
        self.assertIn(self.red_uuid, recall.admitted)
        self.assertIn(self.blue_uuid, recall.admitted)
        return recall

    def _candidates(self):
        return (
            CompositionCandidate(self.red_uuid, (DOMAIN_RED,)),
            CompositionCandidate(self.blue_uuid, (DOMAIN_BLUE,)),
        )

    def test_individually_admitted_memories_can_be_blocked_as_a_combination(self):
        recall = self._recall_both()

        result = evaluate_composition(
            self._candidates(),
            admitted_memory_refs=tuple(recall.admitted),
            constraints=(
                CompositionConstraint(
                    constraint_ref="policy:separate-red-blue",
                    prohibited_domain_set=(DOMAIN_RED, DOMAIN_BLUE),
                    reason="project separation forbids combined context",
                ),
            ),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "cross_domain_composition_prohibited")
        self.assertEqual(result.violated_constraint_refs, ("policy:separate-red-blue",))
        self.assertEqual(set(result.domain_refs), {DOMAIN_RED, DOMAIN_BLUE})

    def test_no_explicit_composition_constraint_does_not_invent_a_block(self):
        recall = self._recall_both()

        result = evaluate_composition(
            self._candidates(),
            admitted_memory_refs=tuple(recall.admitted),
            constraints=(),
        )

        self.assertTrue(result.allowed)
        self.assertEqual(result.violated_constraint_refs, ())

    def test_composition_cannot_reintroduce_a_candidate_recall_did_not_admit(self):
        recall = self._recall_both()
        admitted_without_blue = tuple(ref for ref in recall.admitted if ref != self.blue_uuid)

        result = evaluate_composition(
            self._candidates(),
            admitted_memory_refs=admitted_without_blue,
            constraints=(),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "composition_candidate_not_admitted")

    def test_unresolved_domain_provenance_fails_closed(self):
        recall = self._recall_both()
        unresolved = (
            CompositionCandidate(self.red_uuid, (DOMAIN_RED,)),
            CompositionCandidate(self.blue_uuid, ()),
        )

        result = evaluate_composition(
            unresolved,
            admitted_memory_refs=tuple(recall.admitted),
            constraints=(),
        )

        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "composition_candidate_scope_unresolved")


if __name__ == "__main__":
    unittest.main()
