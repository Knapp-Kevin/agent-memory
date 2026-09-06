"""GAP-SEC-03: governed_delete enforces the authority the write path enforces.

Before this cycle, deletion honoured none of it. Each test below corresponds to
a probe case that previously committed.
"""
import unittest

from agentmem_ref import policy, restart_runtime
from agentmem_ref.adapter import GovernedMemoryAdapter
from agentmem_ref.restart_runtime import CapabilityBinding, RuntimeProfile
from agentmem_ref.substrate import InMemoryTemporalGraph

TENANT = "tenant-A"
OTHER = "tenant-B"

_PROFILE = RuntimeProfile(
    runtime_version="0.1.0-reference",
    profile_id="reference-project-memory",
    profile_version="1.0.0",
    bindings=(
        CapabilityBinding(
            component_id="reference-governed-memory",
            component_version="1.0.0",
            capability_id="governed-memory-core",
            capability_version="1.0.0",
            maturity="reference_qualified",
            evidence_ref="evidence:reference-runtime-core-v1",
        ),
    ),
)


def _proposal(pid, target, tenant=TENANT, operation="runtime_assembly",
              risk="low", snapshot=""):
    return policy.Proposal(
        proposal_id=pid, actor_id="agent:a", charter_version="v1",
        target_reference=target, target_class=policy.M1, scope=tenant,
        operation=operation, current_strength="observed",
        proposed_strength="tentative", downstream_authority=policy.A1,
        reversibility="reversible", risk_class=risk, evidence_refs=("ep-1",),
        tenant_ref=tenant, isolation_domain_refs=(tenant,),
        state_snapshot=snapshot, review_satisfied=True,
        approval_refs=("approver:1",),
    )


class DeletionAuthorityTest(unittest.TestCase):
    def setUp(self):
        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant=TENANT)
        self.victim = self.adapter.commit_proposal(
            _proposal("p1", "mem:A"), "victim value"
        )

    def test_stale_snapshot_refuses_the_delete(self):
        """D1: previously committed -- blocked_by_stale was hardcoded False."""
        result = self.adapter.governed_delete(
            _proposal("p-del", "mem:A", operation="pruning", snapshot="v99"),
            self.victim.fact_uuid,
        )
        self.assertFalse(result.committed)
        self.assertEqual("stale_decision", result.refusal)
        self.assertIsNotNone(self.substrate.get_fact(self.victim.fact_uuid))

    def test_target_binding_mismatch_refuses_and_writes_no_tombstone(self):
        """D2 + D3: previously committed AND wrote a tombstone attributing the
        fact to a memory it never belonged to."""
        result = self.adapter.governed_delete(
            _proposal("p-del", "mem:UNRELATED", operation="pruning"),
            self.victim.fact_uuid,
        )
        self.assertFalse(result.committed)
        self.assertEqual("target_binding_mismatch", result.refusal)
        self.assertIsNone(self.adapter.tombstone(self.victim.fact_uuid))

    def test_cross_tenant_delete_refuses_and_the_fact_survives(self):
        """D4: previously the fact was physically removed by another tenant."""
        intruder = GovernedMemoryAdapter(self.substrate, tenant=OTHER)
        proposal = _proposal("p-del", "mem:B", tenant=OTHER,
                             operation="permanent_deletion", risk="critical")
        result = intruder.governed_delete(
            proposal,
            self.victim.fact_uuid,
            external_verification=policy.ExternalVerification(
                bound_proposal_id=proposal.proposal_id,
                verifier_principal_id="principal:operator",
                authority_kind="human_confirmation",
                max_risk_class="critical",
            ),
        )
        self.assertFalse(result.committed)
        self.assertEqual("cross_tenant_delete", result.refusal)
        self.assertIsNotNone(self.substrate.get_fact(self.victim.fact_uuid))

    def test_nonexistent_fact_refuses_and_writes_no_tombstone(self):
        """D5: previously committed and manufactured a governance record."""
        result = self.adapter.governed_delete(
            _proposal("p-del", "mem:A", operation="pruning"), "does-not-exist"
        )
        self.assertFalse(result.committed)
        self.assertEqual("fact_not_found", result.refusal)
        self.assertIsNone(self.adapter.tombstone("does-not-exist"))

    def test_positive_path_still_prunes(self):
        result = self.adapter.governed_delete(
            _proposal("p-del", "mem:A", operation="pruning"), self.victim.fact_uuid
        )
        self.assertTrue(result.committed)
        self.assertIsNone(result.refusal)
        self.assertIsNotNone(self.adapter.tombstone(self.victim.fact_uuid))

    def test_positive_path_still_permanently_deletes(self):
        # AMENDED Loop 7 (ledger Entry #17): permanent_deletion/critical resolves
        # to require_external_verification, which is no longer dischargeable by
        # assertion. A critical permanent deletion now carries an attestation --
        # which is what a caller performing one should always have had.
        proposal = _proposal("p-del", "mem:A", operation="permanent_deletion", risk="critical")
        result = self.adapter.governed_delete(
            proposal,
            self.victim.fact_uuid,
            external_verification=policy.ExternalVerification(
                bound_proposal_id=proposal.proposal_id,
                verifier_principal_id="principal:operator",
                authority_kind="human_confirmation",
                max_risk_class="critical",
            ),
        )
        self.assertTrue(result.committed)
        self.assertIsNone(self.substrate.get_fact(self.victim.fact_uuid))

    def test_empty_snapshot_still_permits_deletion(self):
        """DoD 6: the staleness guard stays opt-in for the 16 default callers."""
        result = self.adapter.governed_delete(
            _proposal("p-del", "mem:A", operation="pruning", snapshot=""),
            self.victim.fact_uuid,
        )
        self.assertTrue(result.committed)


class GuardOrderingTest(unittest.TestCase):
    """DoD 6b: a refusal must name the real problem, not a later check."""

    def setUp(self):
        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant=TENANT)

    def test_nonexistent_outranks_tenant_and_binding(self):
        result = self.adapter.governed_delete(
            _proposal("p-del", "mem:WRONG", operation="pruning"), "does-not-exist"
        )
        self.assertEqual("fact_not_found", result.refusal)

    def test_foreign_tenant_outranks_binding(self):
        other = GovernedMemoryAdapter(self.substrate, tenant=OTHER)
        foreign = other.commit_proposal(
            _proposal("p-o", "mem:B", tenant=OTHER), "other tenant value"
        )
        result = self.adapter.governed_delete(
            _proposal("p-del", "mem:WRONG", operation="pruning"), foreign.fact_uuid
        )
        self.assertEqual("cross_tenant_delete", result.refusal)


class BindingSurvivesRestartTest(unittest.TestCase):
    """DoD 6c: without LD2b this fails with target_binding_unknown."""

    def test_delete_still_commits_after_a_restart(self):
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant=TENANT)
        committed = adapter.commit_proposal(_proposal("p1", "mem:A"), "value")

        snapshot = restart_runtime._snapshot_governance(
            adapter, profile=_PROFILE, visibility_snapshots={}
        )
        restored_substrate = InMemoryTemporalGraph()
        restored_substrate._facts = dict(substrate._facts)
        restored, _ = restart_runtime._restore_adapter(restored_substrate, snapshot)

        self.assertEqual("mem:A", restored._fact_memory.get(committed.fact_uuid))
        result = restored.governed_delete(
            _proposal("p-del", "mem:A", operation="pruning"), committed.fact_uuid
        )
        self.assertTrue(result.committed, f"refused: {result.refusal}")


class ProceduralMemoryRevocationTest(unittest.TestCase):
    """DoD 6: the one call site passing a non-empty snapshot to governed_delete
    (procedural_memory.py:485), exercised end to end rather than argued from
    inspection (audit V3). LD1 must leave it committing."""

    SKILL_TENANT = "tenant:fixture"
    SKILL_PROJECT = "project:fixture"
    PURPOSE = "release_planning"

    def setUp(self):
        from agentmem_ref.adapter import Clock
        from agentmem_ref.capabilities import ComponentRegistry
        from agentmem_ref.procedural_memory import (
            ProceduralMemoryRuntime,
            SkillArtifact,
            reference_procedural_component,
        )

        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(
            self.substrate, tenant=self.SKILL_TENANT, clock=Clock()
        )
        registry = ComponentRegistry()
        registry.register(reference_procedural_component())
        self.runtime = ProceduralMemoryRuntime(
            substrate=self.substrate, adapter=self.adapter, registry=registry
        )
        self.artifact = SkillArtifact(
            skill_id="release-workflow",
            version=1,
            purpose=self.PURPOSE,
            scope=self.SKILL_TENANT,
            isolation_domain_refs=(self.SKILL_TENANT, self.SKILL_PROJECT),
            required_isolation_domain_refs=(self.SKILL_TENANT, self.SKILL_PROJECT),
            procedure_markdown=(
                "# Release workflow\n"
                "- Target the `release` branch for the release PR.\n"
                "- Run release checks before proposing repository mutation.\n"
                "- Present the action proposal to normal runtime governance."
            ),
            provenance_refs=("episode:release-1",),
            validation_refs=("validation:release-1",),
            constraints=("repository state must be current",),
        )

    def test_skill_revocation_still_commits_with_a_matching_snapshot(self):
        committed = self.runtime.commit_skill(
            self.runtime.propose_skill(self.artifact, actor_id="agent:release")
        )
        revocation = self.runtime.revoke_skill(
            self.artifact.skill_id,
            actor_id="agent:release",
            evidence_refs=("evidence:revoked-by-owner",),
        )
        self.assertTrue(
            revocation.commit.committed,
            f"LD1 broke the one snapshot-passing caller: {revocation.commit.refusal}",
        )
        self.assertIsNone(revocation.commit.refusal)
        self.assertTrue(revocation.active_influence_removed)
        # pruning retains recoverable content; only permanent_deletion removes it
        self.assertIsNotNone(self.substrate.get_fact(committed.commit.fact_uuid))


if __name__ == "__main__":
    unittest.main()
