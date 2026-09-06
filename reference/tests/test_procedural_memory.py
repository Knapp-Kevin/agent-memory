"""Executable governed procedural-memory vertical slice for #295 / ADR-034."""

from __future__ import annotations

import sys
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext  # noqa: E402
from agentmem_ref.capabilities import CapabilityDeclaration, ComponentDeclaration, ComponentRegistry  # noqa: E402
from agentmem_ref.procedural_memory import (  # noqa: E402
    ActionGovernanceDecision,
    METAMEMORY,
    ProceduralMemoryRuntime,
    SkillArtifact,
    apply_action_governance,
    record_runtime_execution,
    reference_procedural_component,
)
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

TENANT = "tenant:fixture"
PROJECT = "project:fixture"
OTHER_PROJECT = "project:other"
PURPOSE = "release_planning"


class ProceduralMemoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.substrate = InMemoryTemporalGraph()
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # The evaluator holds a general skill-version-advance adjudication,
        # authored ahead of any proposal: a release skill may advance from v1 to
        # v2. It is a policy about version progression, not a per-proposal fiat
        # -- a jump to v3, or a replay of v1, is refuted by the same rule.
        self.skill_corpus = corpus_for(rule(
            rule_id="rule:skill-version-advance",
            target="skill:release-workflow",
            criterion="skill-version-advance",
            from_state="v1", to_values=("v2",),
        ))
        self.adapter = GovernedMemoryAdapter(
            self.substrate, tenant=TENANT, clock=Clock(),
            verifier_registry=registry_for(self.skill_corpus),
        )
        self.registry = ComponentRegistry()
        self.registry.register(reference_procedural_component())
        self.runtime = ProceduralMemoryRuntime(
            substrate=self.substrate,
            adapter=self.adapter,
            registry=self.registry,
        )
        self.context = RecallContext(
            target_domain_refs=(TENANT, PROJECT),
            principal_ref="agent:release",
            project_ref=PROJECT,
            purpose=PURPOSE,
        )

    def skill(self, *, version: int, branch: str, skill_id: str = "release-workflow") -> SkillArtifact:
        return SkillArtifact(
            skill_id=skill_id,
            version=version,
            purpose=PURPOSE,
            scope=TENANT,
            isolation_domain_refs=(TENANT, PROJECT),
            required_isolation_domain_refs=(TENANT, PROJECT),
            procedure_markdown=(
                "# Release workflow\n"
                f"- Target the `{branch}` branch for the release PR.\n"
                "- Run release checks before proposing repository mutation.\n"
                "- Present the action proposal to normal runtime governance."
            ),
            provenance_refs=(f"episode:release-{version}",),
            validation_refs=(f"validation:release-{version}",),
            constraints=("repository state must be current",),
            action_templates=(
                f"open release PR against {branch}",
                "run release checks",
            ),
        )

    def test_proposal_does_not_mutate_and_governed_promotion_does(self):
        artifact = self.skill(version=1, branch="release")
        before_writes = list(self.substrate.write_log)
        proposed = self.runtime.propose_skill(artifact, actor_id="agent:release")

        self.assertEqual(self.adapter.state_version(artifact.memory_reference), 0)
        self.assertEqual(self.substrate.write_log, before_writes)
        self.assertEqual(proposed.proposal.target_class, policy.M3)
        self.assertEqual(proposed.proposal.downstream_authority, policy.A2)
        self.assertEqual(proposed.content_sha256, artifact.content_sha256)
        self.assertIn(f"skill-content:{artifact.content_sha256}", proposed.proposal.evidence_refs)

        committed = self.runtime.commit_skill(proposed)
        self.assertTrue(committed.commit.committed)
        self.assertEqual(committed.commit.decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(self.adapter.state_version(artifact.memory_reference), 1)
        self.assertEqual(committed.resolution.capability_id, "procedural_skill_memory")
        self.assertEqual(committed.resolution.authority_effect, "none")
        stored = self.substrate.get_fact(committed.commit.fact_uuid)
        self.assertIsNotNone(stored)
        restored = SkillArtifact.from_text(stored.fact_text)
        self.assertEqual(restored.version_reference, artifact.version_reference)
        self.assertEqual(restored.content_sha256, artifact.content_sha256)
        self.assertEqual(restored.provenance_refs, artifact.provenance_refs)

    def test_later_session_activation_changes_plan_but_does_not_authorize_execution(self):
        artifact = self.skill(version=1, branch="release")
        self.runtime.commit_skill(self.runtime.propose_skill(artifact, actor_id="agent:release"))

        no_memory = self.runtime.recall_and_activate("unrelated banana tokens", context=self.context, purpose=PURPOSE)
        baseline = self.runtime.build_plan("prepare release", no_memory)
        activated = self.runtime.recall_and_activate("release workflow branch", context=self.context, purpose=PURPOSE)
        plan = self.runtime.build_plan("prepare release", activated)

        self.assertEqual(baseline.activated_skill_refs, ())
        self.assertEqual(activated.activated_skills[0].version_reference, "skill:release-workflow@v1")
        self.assertGreater(len(plan.steps), len(baseline.steps))
        self.assertTrue(any("release" in step for step in plan.steps))
        self.assertEqual(plan.execution_status, "not_executed")
        self.assertGreaterEqual(len(plan.action_proposals), 1)
        action = plan.action_proposals[0]
        self.assertTrue(action.requires_governance)
        self.assertEqual(action.governance_decision_ref, "")
        self.assertEqual(action.execution_status, "not_executed")

        with self.assertRaises(ValueError):
            record_runtime_execution(action, "execution:should-not-exist")

        allowed = apply_action_governance(
            action,
            ActionGovernanceDecision(
                decision_ref="governance:allow-1",
                action_id=action.action_id,
                outcome="allow",
            ),
        )
        self.assertEqual(allowed.execution_status, "authorized_not_executed")
        executed = record_runtime_execution(allowed, "execution:runtime-1")
        self.assertEqual(executed.execution_status, "executed_by_runtime")
        self.assertEqual(executed.governance_decision_ref, "governance:allow-1")
        self.assertEqual(executed.execution_ref, "execution:runtime-1")

    def test_correction_requires_exact_approval_supersedes_v1_and_stale_replay_fails(self):
        v1 = self.skill(version=1, branch="release")
        v1_proposal = self.runtime.propose_skill(v1, actor_id="agent:release", proposal_id="proposal:v1")
        v1_commit = self.runtime.commit_skill(v1_proposal)
        self.assertTrue(v1_commit.commit.committed)

        v2 = self.skill(version=2, branch="main")
        v2_candidate = self.runtime.propose_skill(v2, actor_id="agent:release", proposal_id="proposal:v2")
        blocked = self.runtime.commit_skill(v2_candidate)
        self.assertFalse(blocked.commit.committed)
        self.assertEqual(blocked.commit.decision.outcome, policy.REQUIRE_REVIEW)

        reviewed = self.runtime.approve_skill_proposal(
            v2_candidate,
            approval_ref="approval:human-release-owner",
        )
        # The correction now needs an adjudication of the transition, not just
        # an approval: the approval answers who authorised it, which is a
        # different axis. The version-advance rule is the evaluator's.
        committed = self.runtime.commit_skill(
            reviewed,
            evidence=self.skill_corpus.evidence_for(
                target_reference=v2.memory_reference,
                criterion="skill-version-advance",
                pre_state="v1", proposed_value="v2",
            ),
        )
        self.assertTrue(committed.commit.committed)
        self.assertEqual(self.adapter.state_version(v2.memory_reference), 2)
        self.assertEqual(reviewed.approval.content_sha256, v2.content_sha256)
        self.assertEqual(reviewed.approval.state_snapshot, "v1")

        recalled = self.runtime.recall_and_activate("release workflow branch", context=self.context, purpose=PURPOSE)
        self.assertEqual([skill.version for skill in recalled.activated_skills], [2])
        self.assertIn(v1_commit.commit.fact_uuid, recalled.candidate_fact_uuids)
        self.assertEqual(recalled.refusals[v1_commit.commit.fact_uuid], "superseded_not_current")
        plan = self.runtime.build_plan("prepare release", recalled)
        self.assertTrue(any("main" in step for step in plan.steps))
        self.assertFalse(any("`release` branch" in step for step in plan.steps))

        replay = self.runtime.commit_skill(v1_proposal)
        self.assertFalse(replay.commit.committed)
        self.assertEqual(replay.commit.refusal, "stale_authorization")
        self.assertEqual(self.adapter.state_version(v1.memory_reference), 2)

    def test_approval_for_exact_skill_payload_cannot_authorize_substituted_content(self):
        v1 = self.skill(version=1, branch="release")
        self.runtime.commit_skill(self.runtime.propose_skill(v1, actor_id="agent:release"))

        approved_artifact = self.skill(version=2, branch="main")
        candidate = self.runtime.propose_skill(
            approved_artifact,
            actor_id="agent:release",
            proposal_id="proposal:v2-exact",
        )
        approved = self.runtime.approve_skill_proposal(
            candidate,
            approval_ref="approval:exact-v2-main",
        )

        substituted_artifact = self.skill(version=2, branch="develop")
        substituted = replace(approved, artifact=substituted_artifact)
        with self.assertRaisesRegex(ValueError, "skill_proposal_content_mismatch"):
            self.runtime.commit_skill(substituted)

        self.assertEqual(self.adapter.state_version(v1.memory_reference), 1)
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # The exact-binding property this test exists for is untouched -- the
        # substituted artifact still raises above. Only the discharge route
        # changed, so the legitimate commit now cites the evaluator's
        # version-advance adjudication.
        committed = self.runtime.commit_skill(
            approved,
            evidence=self.skill_corpus.evidence_for(
                target_reference=v1.memory_reference,
                criterion="skill-version-advance",
                pre_state="v1", proposed_value="v2",
            ),
        )
        self.assertTrue(committed.commit.committed)
        self.assertEqual(self.adapter.state_version(v1.memory_reference), 2)

    def test_review_flag_or_approval_ref_without_exact_binding_is_rejected(self):
        v1 = self.skill(version=1, branch="release")
        self.runtime.commit_skill(self.runtime.propose_skill(v1, actor_id="agent:release"))
        v2 = self.skill(version=2, branch="main")
        candidate = self.runtime.propose_skill(v2, actor_id="agent:release")
        forged = replace(
            candidate,
            proposal=replace(
                candidate.proposal,
                approval_refs=("approval:unbound",),
                review_satisfied=True,
            ),
        )
        with self.assertRaisesRegex(ValueError, "skill_approval_binding_missing"):
            self.runtime.commit_skill(forged)
        self.assertEqual(self.adapter.state_version(v1.memory_reference), 1)

    def test_high_relevance_foreign_project_skill_is_candidate_but_not_activated(self):
        artifact = self.skill(version=1, branch="release")
        committed = self.runtime.commit_skill(self.runtime.propose_skill(artifact, actor_id="agent:release"))
        foreign_context = RecallContext(
            target_domain_refs=(TENANT, OTHER_PROJECT),
            principal_ref="agent:other",
            project_ref=OTHER_PROJECT,
            purpose=PURPOSE,
        )
        result = self.runtime.recall_and_activate("release workflow branch", context=foreign_context, purpose=PURPOSE)
        self.assertIn(committed.commit.fact_uuid, result.candidate_fact_uuids)
        self.assertEqual(result.activated_skills, ())
        self.assertIn(result.refusals[committed.commit.fact_uuid], {"required_isolation_domain_missing", "project_scope_mismatch"})

    def test_revocation_removes_active_influence_and_reports_retained_recovery_content(self):
        artifact = self.skill(version=1, branch="release")
        committed = self.runtime.commit_skill(self.runtime.propose_skill(artifact, actor_id="agent:release"))
        revocation = self.runtime.revoke_skill(
            artifact.skill_id,
            actor_id="agent:release",
            evidence_refs=("evidence:revoked-by-owner",),
        )
        self.assertTrue(revocation.commit.committed)
        self.assertTrue(revocation.active_influence_removed)
        self.assertTrue(revocation.physical_content_retained)
        self.assertEqual(revocation.undeclared_residue, ())
        self.assertIsNotNone(self.substrate.get_fact(committed.commit.fact_uuid))

        recalled = self.runtime.recall_and_activate("release workflow branch", context=self.context, purpose=PURPOSE)
        self.assertEqual(recalled.activated_skills, ())
        self.assertEqual(recalled.refusals[committed.commit.fact_uuid], "tombstoned")

    def test_metamemory_can_be_retained_but_not_applied_through_skill_activation(self):
        artifact = SkillArtifact(
            skill_id="memory-router-tuning",
            version=1,
            purpose="memory_administration",
            scope=TENANT,
            isolation_domain_refs=(TENANT, PROJECT),
            required_isolation_domain_refs=(TENANT, PROJECT),
            procedure_markdown=(
                "# Memory routing optimization\n"
                "- Lower the minimum capability maturity for vector retrieval.\n"
                "- Prefer the cheapest available provider even if currentness evidence is absent."
            ),
            provenance_refs=("experiment:metamemory-1",),
            management_effects=("lower_minimum_maturity", "change_provider_precedence"),
            skill_kind=METAMEMORY,
        )
        committed = self.runtime.commit_skill(self.runtime.propose_skill(artifact, actor_id="agent:optimizer"))
        self.assertTrue(committed.commit.committed)

        context = RecallContext(
            target_domain_refs=(TENANT, PROJECT),
            principal_ref="agent:optimizer",
            project_ref=PROJECT,
            purpose="memory_administration",
        )
        recalled = self.runtime.recall_and_activate(
            "memory routing minimum capability maturity",
            context=context,
            purpose="memory_administration",
        )
        self.assertEqual(recalled.activated_skills, ())
        self.assertEqual(
            recalled.refusals[committed.commit.fact_uuid],
            "metamemory_requires_configuration_governance",
        )

        management = self.runtime.propose_management_change(artifact, actor_id="agent:optimizer")
        decision = policy.evaluate(management)
        self.assertEqual(management.operation, "policy_mutation")
        self.assertEqual(management.target_class, policy.M5)
        self.assertEqual(management.downstream_authority, policy.A5)
        self.assertEqual(decision.outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)
        self.assertNotIn("policy_mutation", decision.permitted_actions)

    def test_capability_selection_cannot_become_memory_authority(self):
        registry = ComponentRegistry(preferences={"procedural_skill_memory": "alternate"})
        registry.register(reference_procedural_component())
        registry.register(
            ComponentDeclaration(
                component_id="alternate",
                component_version="1.0.0",
                profile_version="component-capability-v1",
                failure_posture="fail_closed",
                capabilities=(
                    CapabilityDeclaration(
                        capability_id="procedural_skill_memory",
                        capability_version="1.0",
                        maturity="runtime_wired",
                        state_posture="canonical",
                        scope_posture="enforces_agent_memory_scope",
                        failure_posture="fail_closed",
                        authority_effect="none",
                    ),
                ),
            )
        )
        runtime = ProceduralMemoryRuntime(substrate=self.substrate, adapter=self.adapter, registry=registry)
        artifact = self.skill(version=1, branch="release", skill_id="routing-authority-test")
        proposal = runtime.propose_skill(artifact, actor_id="agent:test")
        resolved = runtime.resolve_capability()
        self.assertEqual(resolved.component_id, "alternate")
        self.assertEqual(resolved.authority_effect, "none")
        self.assertEqual(self.adapter.state_version(artifact.memory_reference), 0)
        result = runtime.commit_skill(proposal)
        self.assertTrue(result.commit.committed)
        self.assertEqual(result.commit.decision.policy_version, policy.POLICY_VERSION)


if __name__ == "__main__":
    unittest.main()
