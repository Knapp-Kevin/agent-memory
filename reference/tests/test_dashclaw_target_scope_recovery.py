from __future__ import annotations

import unittest

from agentmem_ref import policy
from agentmem_ref.adapter import GovernedMemoryAdapter
from agentmem_ref.dashclaw_external_verdict import (
    ACTION_MUTATION,
    StaticAuthorityGrant,
    StaticAuthorityResolver,
    parse_mutation_request,
    sha256_text,
)
from agentmem_ref.dashclaw_governed_commit import (
    DashClawGovernedCommitter,
    ProjectScopedAuthorityResolver,
)
from agentmem_ref.substrate import InMemoryTemporalGraph


ORG = "fixture-org"
AGENT = "release-agent"
PROJECT = "project:fixture"
MEMORY_ID = "repo:fixture:release-branch"

AUTHORITY = ProjectScopedAuthorityResolver(
    StaticAuthorityResolver(
        (
            StaticAuthorityGrant(
                org_id=ORG,
                agent_id=AGENT,
                isolation_domain_refs=(PROJECT,),
                evidence_ref="authority-grant:fixture",
            ),
        )
    )
)


def request(*, operation: str, state_snapshot: str, value: str, risk: str) -> dict:
    return {
        "request_id": f"evr-{operation}",
        "org_id": ORG,
        "agent_id": AGENT,
        "action_type": ACTION_MUTATION,
        "declared_goal": "retain release branch memory",
        "act": {
            "kind": ACTION_MUTATION,
            "memory_value": value,
            "proposal": {
                "proposal_id": f"proposal-{operation}",
                "charter_version": "fixture-charter-v1",
                "target_reference": MEMORY_ID,
                "target_class": policy.M2,
                "scope": PROJECT,
                "operation": operation,
                "current_strength": "observed" if state_snapshot == "v0" else "promoted",
                "proposed_strength": "promoted",
                "downstream_authority": policy.A1,
                "reversibility": "reversible",
                "risk_class": risk,
                "state_snapshot": state_snapshot,
                "purpose": "release planning",
                "isolation_domain_refs": [PROJECT],
                "required_isolation_domain_refs": [PROJECT],
                "project_ref": PROJECT,
                "evidence_refs": ["fixture:user-statement"],
                "content_sha256": sha256_text(value),
            },
        },
        "input_identity": f"sha256:dashclaw-{operation}",
    }


class TargetScopeRecoveryTests(unittest.TestCase):
    def test_existing_memory_without_target_scope_binding_fails_closed(self) -> None:
        substrate = InMemoryTemporalGraph()
        memory = GovernedMemoryAdapter(substrate, tenant=ORG)

        # Simulate state that survives/reappears without the #279 integration's
        # target-scope registry. The direct adapter commit is intentionally used
        # only to construct this missing-metadata condition.
        seed = parse_mutation_request(
            request(operation="promotion", state_snapshot="v0", value="release branch release", risk="low"),
            AUTHORITY,
        )
        seeded = memory.commit_proposal(seed.proposal, seed.fact_text)
        self.assertTrue(seeded.committed)
        self.assertEqual(memory.state_version(MEMORY_ID), 1)

        # A newly constructed committer has no target-scope registry entry. It
        # must not infer the old memory's project from the incoming correction.
        committer = DashClawGovernedCommitter(memory, AUTHORITY)
        correction = parse_mutation_request(
            request(operation="correction", state_snapshot="v1", value="release branch main", risk="medium"),
            AUTHORITY,
        )
        before = tuple(substrate.write_log)
        result = committer.commit(
            correction,
            approval_ref="approval:correction",
            approval_actor_id="operator",
            approved_input_identity=correction.input_identity,
        )

        self.assertFalse(result.committed)
        self.assertEqual(result.refusal, "target_scope_unresolved")
        self.assertEqual(tuple(substrate.write_log), before)
        self.assertEqual(memory.state_version(MEMORY_ID), 1)


if __name__ == "__main__":
    unittest.main()
