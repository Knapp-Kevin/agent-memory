"""Executable shared-domain membership evidence for proposed ADR-022."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

TENANT = "tenant-a"
SHARED = "domain:shared-security"
ALICE = "user:alice"
BOB = "user:bob"


def shared_proposal() -> policy.Proposal:
    return policy.Proposal(
        proposal_id="proposal:shared-memory",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference="mem:shared-security-procedure",
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:shared-source",),
        tenant_ref=TENANT,
        purpose="security-review",
        isolation_domain_refs=(SHARED,),
    )


class SharedDomainMembershipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=TENANT, clock=Clock())
        committed = self.adapter.commit_proposal(shared_proposal(), "shared credential rotation guidance")
        self.assertTrue(committed.committed)
        self.fact_uuid = committed.fact_uuid
        self.adapter.set_shared_domain_members(SHARED, (ALICE,))

    def test_current_member_is_eligible_for_normal_admission_checks(self):
        recall = self.adapter.governed_recall(
            "shared credential rotation guidance",
            RecallContext(target_domain_refs=(SHARED,), principal_ref=ALICE, purpose="security-review"),
        )

        self.assertIn(self.fact_uuid, recall.candidates)
        self.assertIn(self.fact_uuid, recall.admitted)

    def test_non_member_is_candidate_but_blocked(self):
        recall = self.adapter.governed_recall(
            "shared credential rotation guidance",
            RecallContext(target_domain_refs=(SHARED,), principal_ref=BOB, purpose="security-review"),
        )

        self.assertIn(self.fact_uuid, recall.candidates)
        self.assertNotIn(self.fact_uuid, recall.admitted)
        self.assertEqual(recall.refusals[self.fact_uuid], "shared_space_non_member")

    def test_unresolved_membership_fails_closed(self):
        recall = self.adapter.governed_recall(
            "shared credential rotation guidance",
            RecallContext(target_domain_refs=(SHARED,), purpose="security-review"),
        )

        self.assertIn(self.fact_uuid, recall.candidates)
        self.assertNotIn(self.fact_uuid, recall.admitted)
        self.assertEqual(recall.refusals[self.fact_uuid], "shared_space_membership_unresolved")

    def test_revocation_changes_subsequent_admission_without_rewriting_memory(self):
        before = self.adapter.governed_recall(
            "shared credential rotation guidance",
            RecallContext(target_domain_refs=(SHARED,), principal_ref=ALICE, purpose="security-review"),
        )
        self.assertIn(self.fact_uuid, before.admitted)

        self.adapter.set_shared_domain_members(SHARED, ())

        after = self.adapter.governed_recall(
            "shared credential rotation guidance",
            RecallContext(target_domain_refs=(SHARED,), principal_ref=ALICE, purpose="security-review"),
        )
        self.assertIn(self.fact_uuid, after.candidates)
        self.assertNotIn(self.fact_uuid, after.admitted)
        self.assertEqual(after.refusals[self.fact_uuid], "shared_space_non_member")

    def test_membership_does_not_override_wrong_target_domain(self):
        recall = self.adapter.governed_recall(
            "shared credential rotation guidance",
            RecallContext(target_domain_refs=("domain:project-private",), principal_ref=ALICE, purpose="security-review"),
        )

        self.assertIn(self.fact_uuid, recall.candidates)
        self.assertNotIn(self.fact_uuid, recall.admitted)
        self.assertEqual(recall.refusals[self.fact_uuid], "isolation_domain_mismatch")


if __name__ == "__main__":
    unittest.main()
