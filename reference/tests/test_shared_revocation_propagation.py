"""Executable shared-memory revocation propagation evidence for issue #68."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext  # noqa: E402
from agentmem_ref.scope_governance import SourceScope, derive_scope  # noqa: E402
from agentmem_ref.shared_revocation import propagate_shared_membership_revocation  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

TENANT = "tenant-a"
SHARED = "domain:shared-security"
AGGREGATE = "domain:security-aggregate"
ALICE = "user:alice"
BOB = "user:bob"


def proposal(reference: str) -> policy.Proposal:
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
        evidence_refs=("evidence:shared",),
        tenant_ref=TENANT,
        purpose="security-review",
        isolation_domain_refs=(SHARED,),
    )


class SharedRevocationPropagationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=TENANT, clock=Clock())
        self.adapter.set_shared_domain_members(SHARED, (ALICE, BOB))
        commit = self.adapter.commit_proposal(
            proposal("mem:shared"),
            "shared revocation evidence token",
        )
        self.assertTrue(commit.committed)
        self.fact_uuid = commit.fact_uuid
        self.sources = (
            SourceScope(
                source_ref="mem:shared",
                domain_refs=frozenset({SHARED}),
                allowed_audiences=frozenset({ALICE, BOB}),
                allowed_purposes=frozenset({"security-review"}),
            ),
        )
        self.derived = derive_scope(self.sources)

    def test_revocation_blocks_future_shared_recall_and_invalidates_broader_derived_scope(self):
        before = self.adapter.governed_recall(
            "shared revocation evidence token",
            RecallContext(
                target_domain_refs=(SHARED,),
                principal_ref=ALICE,
                purpose="security-review",
            ),
        )
        self.assertIn(self.fact_uuid, before.admitted)

        result = propagate_shared_membership_revocation(
            self.adapter,
            domain_ref=SHARED,
            revoked_principal=ALICE,
            remaining_members=(BOB,),
            current_derived_scope=self.derived,
            source_scopes=self.sources,
        )

        after = self.adapter.governed_recall(
            "shared revocation evidence token",
            RecallContext(
                target_domain_refs=(SHARED,),
                principal_ref=ALICE,
                purpose="security-review",
            ),
        )
        self.assertNotIn(self.fact_uuid, after.admitted)
        self.assertEqual(after.refusals[self.fact_uuid], "shared_space_non_member")
        self.assertEqual(result.affected_source_refs, ("mem:shared",))
        self.assertFalse(result.reconciliation.current_for_use)
        self.assertTrue(result.reconciliation.requires_narrowing)
        self.assertEqual(result.reconciliation.inherited_scope.allowed_audiences, frozenset({BOB}))

    def test_revocation_does_not_remotely_rewrite_the_derived_object(self):
        result = propagate_shared_membership_revocation(
            self.adapter,
            domain_ref=SHARED,
            revoked_principal=ALICE,
            remaining_members=(BOB,),
            current_derived_scope=self.derived,
            source_scopes=self.sources,
        )

        self.assertIn(ALICE, self.derived.allowed_audiences)
        self.assertFalse(result.reconciliation.current_for_use)
        self.assertNotIn(ALICE, result.reconciliation.inherited_scope.allowed_audiences)

    def test_unrelated_source_scope_is_not_mutated_by_shared_domain_revocation(self):
        shared = SourceScope(
            source_ref="mem:shared",
            domain_refs=frozenset({SHARED, AGGREGATE}),
            allowed_audiences=frozenset({ALICE, BOB}),
            allowed_purposes=frozenset({"security-review"}),
        )
        private = SourceScope(
            source_ref="mem:private",
            domain_refs=frozenset({"domain:private", AGGREGATE}),
            allowed_audiences=frozenset({ALICE, BOB}),
            allowed_purposes=frozenset({"security-review"}),
        )
        sources = (shared, private)
        current = derive_scope(sources)

        result = propagate_shared_membership_revocation(
            self.adapter,
            domain_ref=SHARED,
            revoked_principal=ALICE,
            remaining_members=(BOB,),
            current_derived_scope=current,
            source_scopes=sources,
        )

        self.assertEqual(result.affected_source_refs, ("mem:shared",))
        self.assertFalse(result.reconciliation.current_for_use)
        self.assertEqual(result.reconciliation.inherited_scope.allowed_audiences, frozenset({BOB}))

    def test_revoked_principal_cannot_be_listed_as_remaining_member(self):
        with self.assertRaises(ValueError):
            propagate_shared_membership_revocation(
                self.adapter,
                domain_ref=SHARED,
                revoked_principal=ALICE,
                remaining_members=(ALICE, BOB),
                current_derived_scope=self.derived,
                source_scopes=self.sources,
            )


if __name__ == "__main__":
    unittest.main()
