"""Identity, replacement, collision, and deployment cases."""

import copy
import unittest

from agentmem_ref import policy
from agentmem_ref.conditional_memory_harness import _find_collision
from agentmem_ref.conditional_memory_influence import validate_table_replacement
from tests.test_conditional_memory_influence_gate import record, request, table


class ConditionalMemoryInfluenceIdentityTests(unittest.TestCase):
    def test_same_physical_address_does_not_merge_partition_identity(self):
        address = [3, 5]
        allowed = record(address=address)
        foreign = record(
            influence_id="influence:foreign",
            lookup_ref="lookup:foreign",
            address=address,
            table=table(partition="tenant-b/project-b", table_id="table:foreign", char="b"),
            request=request("tenant-a/project-a"),
        )
        self.assertEqual(allowed["opaque_address_digest"], foreign["opaque_address_digest"])
        self.assertEqual(allowed["gate"]["result"], "allow")
        self.assertEqual(foreign["gate"]["result"], "block_scope")
        self.assertNotEqual(allowed["table"]["table_id"], foreign["table"]["table_id"])

    def test_deliberate_collision_is_quality_evidence_not_equivalence(self):
        collision = _find_collision()
        first = record(address=collision["address"], collision_ref="collision:test")
        second = record(
            influence_id="influence:collision-2",
            lookup_ref="lookup:collision-2",
            address=collision["address"],
            collision_ref="collision:test",
        )
        self.assertNotEqual(collision["first_tokens"], collision["second_tokens"])
        self.assertEqual(first["opaque_address_digest"], second["opaque_address_digest"])
        self.assertIn("collision_is_not_equivalence", first["nonclaims"])

    def test_table_replacement_preserves_old_evidence_and_new_identity(self):
        old = record(currentness="stale")
        historical = copy.deepcopy(old)
        new = record(
            influence_id="influence:t2",
            lookup_ref="lookup:t2",
            table=table(table_id="table:t2", char="b"),
            currentness="current",
        )
        validate_table_replacement(old, new)
        self.assertEqual(old, historical)
        self.assertNotEqual(old["table"]["table_id"], new["table"]["table_id"])
        self.assertEqual(new["gate"]["result"], "allow")

    def test_lookup_evidence_does_not_create_table_deployment_authority(self):
        influence = record(enforcement_posture="cooperative")
        self.assertNotIn("decision", influence)
        self.assertIn("configured_gate_is_not_enforcement_proof", influence["nonclaims"])

        deploy = policy.evaluate(policy.Proposal(
            proposal_id="table:deploy", actor_id="agent:builder", charter_version="v1",
            target_reference="table:t2", target_class=policy.M3, scope="tenant-a/project-a",
            operation="promotion", current_strength="promoted", proposed_strength="canonical",
            downstream_authority=policy.A3, reversibility="versioned_revocable", risk_class="high",
            evidence_refs=("evidence:table-build",),
        ))
        widen = policy.evaluate(policy.Proposal(
            proposal_id="table:widen", actor_id="agent:builder", charter_version="v1",
            target_reference="table:t2", target_class=policy.M5, scope="tenant-a/project-a",
            operation="scope_expansion", current_strength="promoted", proposed_strength="canonical",
            downstream_authority=policy.A5, reversibility="irreversible", risk_class="critical",
            evidence_refs=("evidence:table-build",),
        ))
        self.assertEqual(deploy.outcome, policy.REQUIRE_REVIEW)
        self.assertEqual(widen.outcome, policy.BLOCK)


if __name__ == "__main__":
    unittest.main()
