from __future__ import annotations

import json
import unittest

from agentmem_ref import policy
from agentmem_ref.adapter import GovernedMemoryAdapter
from agentmem_ref.dashclaw_external_verdict import (
    ACTION_CONNECTION_TEST,
    ACTION_MUTATION,
    DashClawRequestError,
    StaticAuthorityGrant,
    StaticAuthorityResolver,
    evaluate_request,
    parse_mutation_request,
    sha256_text,
)
from agentmem_ref.dashclaw_governed_commit import DashClawGovernedCommitter
from agentmem_ref.substrate import InMemoryTemporalGraph


ORG = "fixture-org"
AGENT = "release-agent"
OTHER_AGENT = "other-project-agent"
PROJECT = "project:fixture"
OTHER_PROJECT = "project:other"
MEMORY_ID = "repo:fixture:release-branch"
OTHER_MEMORY_ID = "repo:other:release-branch"

AUTHORITY = StaticAuthorityResolver(
    (
        StaticAuthorityGrant(
            org_id=ORG,
            agent_id=AGENT,
            isolation_domain_refs=(PROJECT,),
            evidence_ref="authority-grant:fixture-release-agent",
        ),
        StaticAuthorityGrant(
            org_id=ORG,
            agent_id=OTHER_AGENT,
            isolation_domain_refs=(OTHER_PROJECT,),
            evidence_ref="authority-grant:other-project-agent",
        ),
    )
)


def mutation_request(
    *,
    value: str = "release branch release",
    operation: str = "promotion",
    risk: str = "low",
    state_snapshot: str = "v0",
    input_identity: str = "sha256:dashclaw-fixture",
    target_class: str = policy.M2,
    downstream_authority: str = policy.A1,
    project_ref: str = PROJECT,
    agent_id: str = AGENT,
    memory_id: str = MEMORY_ID,
) -> dict:
    return {
        "request_id": "evr-fixture",
        "org_id": ORG,
        "agent_id": agent_id,
        "action_type": ACTION_MUTATION,
        "declared_goal": "retain release branch memory",
        "act": {
            "kind": ACTION_MUTATION,
            "memory_value": value,
            "proposal": {
                "proposal_id": "proposal-fixture",
                "charter_version": "fixture-charter-v1",
                "target_reference": memory_id,
                "target_class": target_class,
                "scope": project_ref,
                "operation": operation,
                "current_strength": "observed" if state_snapshot == "v0" else "promoted",
                "proposed_strength": "promoted",
                "downstream_authority": downstream_authority,
                "reversibility": "reversible",
                "risk_class": risk,
                "state_snapshot": state_snapshot,
                "purpose": "release planning",
                "isolation_domain_refs": [project_ref],
                "required_isolation_domain_refs": [project_ref],
                "project_ref": project_ref,
                "evidence_refs": ["fixture:user-statement"],
                "content_sha256": sha256_text(value),
            },
        },
        "input_identity": input_identity,
    }


class DashClawExternalVerdictTests(unittest.TestCase):
    def test_connection_test_is_side_effect_free_contract_allow(self) -> None:
        request = {
            "request_id": "evr-test",
            "org_id": ORG,
            "agent_id": "dashclaw-connection-test",
            "action_type": ACTION_CONNECTION_TEST,
            "declared_goal": "DashClaw provider connection test (synthetic act — no real action follows)",
            "act": {"synthetic": True, "source": "dashclaw-policies-panel"},
            "input_identity": "sha256:dashclaw-connection-test",
        }
        response = evaluate_request(request)
        self.assertEqual(response["decision"], "allow")
        self.assertEqual(response["reason"], "connection_test_ok")
        self.assertEqual(response["input_identity"], request["input_identity"])
        self.assertEqual(response["evidence"], {"connection_test": True, "accepted": True})

    def test_identity_alone_does_not_resolve_scope_authority(self) -> None:
        response = evaluate_request(mutation_request())
        self.assertEqual(response["decision"], "deny")
        self.assertEqual(response["reason"], "pama_block")
        self.assertFalse(response["evidence"]["authority_resolved"])
        self.assertEqual(response["evidence"]["authority_reason"], "authority_resolver_missing")

    def test_input_identity_is_echoed_verbatim(self) -> None:
        request = mutation_request(input_identity="opaque:not-a-provider-digest")
        response = evaluate_request(request, AUTHORITY)
        self.assertEqual(response["input_identity"], "opaque:not-a-provider-digest")

    def test_low_risk_promotion_maps_allow_with_ledger_to_allow(self) -> None:
        response = evaluate_request(mutation_request(), AUTHORITY)
        self.assertEqual(response["decision"], "allow")
        self.assertEqual(response["reason"], "pama_allow_with_ledger")
        self.assertEqual(response["evidence"]["pama_outcome"], policy.ALLOW_WITH_LEDGER)
        self.assertTrue(response["evidence"]["authority_resolved"])
        self.assertEqual(response["evidence"]["authority_evidence_ref"], "authority-grant:fixture-release-agent")
        self.assertFalse(response["evidence"]["execution_evidence"])

    def test_unauthorized_project_scope_is_blocked(self) -> None:
        request = mutation_request(project_ref=OTHER_PROJECT)
        response = evaluate_request(request, AUTHORITY)
        self.assertEqual(response["decision"], "deny")
        self.assertEqual(response["reason"], "pama_block")
        self.assertFalse(response["evidence"]["authority_resolved"])
        self.assertEqual(response["evidence"]["authority_reason"], "authority_grant_not_found")

    def test_correction_maps_review_to_escalate(self) -> None:
        response = evaluate_request(
            mutation_request(operation="correction", risk="medium", state_snapshot="v1"),
            AUTHORITY,
        )
        self.assertEqual(response["decision"], "escalate")
        self.assertEqual(response["reason"], "pama_require_review")

    def test_critical_authority_scope_expansion_maps_to_deny(self) -> None:
        request = mutation_request(
            value="release branch main for every project",
            operation="scope_expansion",
            risk="critical",
            state_snapshot="v2",
            target_class=policy.M5,
            downstream_authority=policy.A5,
        )
        request["act"]["proposal"]["requested_scope_change"] = "organization"
        response = evaluate_request(request, AUTHORITY)
        self.assertEqual(response["decision"], "deny")
        self.assertEqual(response["reason"], "pama_block")

    def test_unsupported_action_fails_conservatively(self) -> None:
        request = mutation_request()
        request["action_type"] = "shell"
        response = evaluate_request(request, AUTHORITY)
        self.assertEqual(response["decision"], "deny")
        self.assertEqual(response["reason"], "unsupported_action_type")

    def test_content_drift_is_denied_before_pama(self) -> None:
        request = mutation_request()
        request["act"]["memory_value"] = "release branch main"
        response = evaluate_request(request, AUTHORITY)
        self.assertEqual(response["decision"], "deny")
        self.assertEqual(response["reason"], "content_binding_mismatch")

    def test_act_cannot_inject_actor_tenant_scope_authority_or_review(self) -> None:
        for field, value in (
            ("actor_id", "different-agent"),
            ("tenant_ref", "other-org"),
            ("actor_authority_resolved", True),
            ("approval_refs", ["fake-approval"]),
            ("review_satisfied", True),
        ):
            with self.subTest(field=field):
                request = mutation_request()
                request["act"]["proposal"][field] = value
                response = evaluate_request(request, AUTHORITY)
                self.assertEqual(response["decision"], "deny")
                self.assertEqual(response["reason"], "authority_injection_attempt")

    def test_conflicting_org_isolation_binding_is_denied(self) -> None:
        request = mutation_request()
        request["act"]["proposal"]["isolation_domain_refs"].append("org:other-org")
        response = evaluate_request(request, AUTHORITY)
        self.assertEqual(response["decision"], "deny")
        self.assertEqual(response["reason"], "conflicting_trusted_binding")

    def test_scope_must_match_project_ref(self) -> None:
        request = mutation_request()
        request["act"]["proposal"]["scope"] = OTHER_PROJECT
        response = evaluate_request(request, AUTHORITY)
        self.assertEqual(response["decision"], "deny")
        self.assertEqual(response["reason"], "scope_project_mismatch")

    def test_missing_input_identity_cannot_fake_contract_verdict(self) -> None:
        request = mutation_request()
        del request["input_identity"]
        with self.assertRaises(DashClawRequestError):
            evaluate_request(request, AUTHORITY)

    def test_provider_evidence_is_bounded(self) -> None:
        response = evaluate_request(mutation_request(), AUTHORITY)
        serialized = json.dumps(response["evidence"], sort_keys=True, separators=(",", ":"))
        self.assertLessEqual(len(serialized), 4096)

    def test_review_commit_requires_exact_approval_identity_and_external_actor(self) -> None:
        memory = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=ORG)
        committer = DashClawGovernedCommitter(memory, AUTHORITY)
        mutation = parse_mutation_request(
            mutation_request(operation="correction", risk="medium", state_snapshot="v0"),
            AUTHORITY,
        )

        missing = committer.commit(mutation)
        wrong_identity = committer.commit(
            mutation,
            approval_ref="approval:1",
            approval_actor_id="operator",
            approved_input_identity="different",
        )
        self_approval = committer.commit(
            mutation,
            approval_ref="approval:2",
            approval_actor_id=AGENT,
            approved_input_identity=mutation.input_identity,
        )

        self.assertEqual(missing.refusal, "approval_required")
        self.assertEqual(wrong_identity.refusal, "approval_identity_mismatch")
        self.assertEqual(self_approval.refusal, "self_approval_forbidden")
        self.assertEqual(memory.state_version(mutation.proposal.target_reference), 0)

    def test_blocked_provider_result_cannot_reach_substrate_via_governed_committer(self) -> None:
        substrate = InMemoryTemporalGraph()
        memory = GovernedMemoryAdapter(substrate, tenant=ORG)
        committer = DashClawGovernedCommitter(memory, AUTHORITY)
        request = mutation_request(
            value="release branch main for every project",
            operation="scope_expansion",
            risk="critical",
            target_class=policy.M5,
            downstream_authority=policy.A5,
        )
        request["act"]["proposal"]["requested_scope_change"] = "organization"
        mutation = parse_mutation_request(request, AUTHORITY)
        before = tuple(substrate.write_log)
        result = committer.commit(mutation)
        self.assertFalse(result.committed)
        self.assertEqual(result.refusal, "pama_blocked")
        self.assertEqual(tuple(substrate.write_log), before)

    def test_unauthorized_requested_scope_cannot_reach_substrate(self) -> None:
        substrate = InMemoryTemporalGraph()
        memory = GovernedMemoryAdapter(substrate, tenant=ORG)
        committer = DashClawGovernedCommitter(memory, AUTHORITY)
        mutation = parse_mutation_request(mutation_request(project_ref=OTHER_PROJECT), AUTHORITY)
        before = tuple(substrate.write_log)
        result = committer.commit(mutation)
        self.assertFalse(result.committed)
        self.assertEqual(result.refusal, "requested_scope_authority_unresolved")
        self.assertEqual(tuple(substrate.write_log), before)

    def test_current_target_scope_is_revalidated_for_current_actor(self) -> None:
        substrate = InMemoryTemporalGraph()
        memory = GovernedMemoryAdapter(substrate, tenant=ORG)
        committer = DashClawGovernedCommitter(memory, AUTHORITY)

        seed_request = mutation_request(
            value="other release branch release",
            project_ref=OTHER_PROJECT,
            agent_id=OTHER_AGENT,
            memory_id=OTHER_MEMORY_ID,
            input_identity="sha256:other-seed",
        )
        seed = parse_mutation_request(seed_request, AUTHORITY)
        seed_result = committer.commit(seed)
        self.assertTrue(seed_result.committed)

        attack_request = mutation_request(
            value="other release branch main",
            operation="correction",
            risk="medium",
            state_snapshot="v1",
            project_ref=PROJECT,
            agent_id=AGENT,
            memory_id=OTHER_MEMORY_ID,
            input_identity="sha256:cross-target-attack",
        )
        # Requested Project A scope is valid for AGENT, so the stateless provider
        # projection legitimately reaches review. The stateful commit seam must
        # additionally prove AGENT controls the target's existing Project B scope.
        provider = evaluate_request(attack_request, AUTHORITY)
        self.assertEqual(provider["decision"], "escalate")
        attack = parse_mutation_request(attack_request, AUTHORITY)
        before = tuple(substrate.write_log)
        result = committer.commit(
            attack,
            approval_ref="approval:cross-target",
            approval_actor_id="operator",
            approved_input_identity=attack.input_identity,
        )
        self.assertFalse(result.committed)
        self.assertEqual(result.refusal, "target_scope_authority_unresolved")
        self.assertEqual(tuple(substrate.write_log), before)
        other_uuid = memory.current_fact_uuid(OTHER_MEMORY_ID)
        self.assertIsNotNone(other_uuid)
        self.assertEqual(substrate.get_fact(other_uuid).fact_text, "other release branch release")


if __name__ == "__main__":
    unittest.main()
