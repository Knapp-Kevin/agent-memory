"""GAP-ARCH-18: candidates without scope metadata are refused, not admitted.

docs/34:139 -- "candidates that arrive without scope metadata are rejected from
admission; unknown scope is treated as out-of-scope, never as local."

The refusal string is dictated, not chosen: the JS runtime already returns
exactly `unknown_scope` at integrations/agent-memory-runtime/src/index.mjs:114,
and test/runtime-adapter.test.mjs:122 enumerates the vocabulary. This closes a
Python/JS divergence on a shared contract.
"""
import unittest

from agentmem_ref import policy
from agentmem_ref.adapter import GovernedMemoryAdapter, RecallContext
from agentmem_ref.substrate import Fact, InMemoryTemporalGraph

TENANT = "tenant-A"
OTHER_TENANT = "tenant-B"


def _scopeless_fact(uuid="no-scope-1", group_id=TENANT, episode_uuids=()):
    return Fact(
        uuid=uuid,
        fact_text="secret deploy window",
        group_id=group_id,
        episode_uuids=episode_uuids,
        created_at="2026-01-01T00:00:00Z",
    )


def _proposal(proposal_id="p-1", target_reference="mem:A"):
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="agent:a",
        charter_version="v1",
        target_reference=target_reference,
        target_class=policy.M1,
        scope=TENANT,
        operation="runtime_assembly",
        current_strength="observed",
        proposed_strength="tentative",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("ep-1",),
        tenant_ref=TENANT,
        isolation_domain_refs=(TENANT,),
    )


class UnknownScopeRefusalTest(unittest.TestCase):
    def setUp(self):
        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant=TENANT)

    def test_scopeless_fact_is_refused(self):
        self.substrate.write_fact(_scopeless_fact())
        result = self.adapter.governed_recall("deploy")
        self.assertNotIn("no-scope-1", result.admitted)
        self.assertEqual("unknown_scope", result.refusals["no-scope-1"])

    def test_refused_even_with_empty_target_domains(self):
        """The pre-fix probe admitted this exact case."""
        self.substrate.write_fact(_scopeless_fact())
        result = self.adapter.governed_recall(
            "deploy", RecallContext(target_domain_refs=())
        )
        self.assertEqual([], result.admitted)
        self.assertEqual("unknown_scope", result.refusals["no-scope-1"])

    def test_refusal_string_matches_the_js_runtime(self):
        """Parity source: integrations/agent-memory-runtime/src/index.mjs:114."""
        self.substrate.write_fact(_scopeless_fact())
        result = self.adapter.governed_recall("deploy")
        self.assertEqual("unknown_scope", result.refusals["no-scope-1"])

    def test_governed_facts_are_still_admitted(self):
        """The refusal must not swallow facts written through the governed path."""
        committed = self.adapter.commit_proposal(_proposal(), "deploy window Thursday")
        result = self.adapter.governed_recall("deploy window")
        self.assertIn(committed.fact_uuid, result.admitted)


class RefusalOrderingTest(unittest.TestCase):
    """DoD 3: the blast-radius argument depends on earlier checks firing first."""

    def setUp(self):
        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant=TENANT)

    def test_foreign_tenant_is_filtered_before_scope(self):
        """benchmark_security's shield: the fact never becomes a candidate."""
        self.substrate.write_fact(_scopeless_fact(uuid="foreign-1", group_id=OTHER_TENANT))
        result = self.adapter.governed_recall("deploy")
        self.assertNotIn("foreign-1", result.candidates)

    def test_tombstoned_source_outranks_unknown_scope(self):
        """forbidden_hits' shield: derived_from_tombstoned_source fires first."""
        committed = self.adapter.commit_proposal(_proposal(), "deploy window Thursday")
        self.substrate.write_fact(
            _scopeless_fact(uuid="derived-1", episode_uuids=(committed.fact_uuid,))
        )
        self.adapter.governed_delete(
            _proposal(proposal_id="p-del", target_reference="mem:A"),
            committed.fact_uuid,
        )
        result = self.adapter.governed_recall("deploy")
        self.assertEqual(
            "derived_from_tombstoned_source", result.refusals["derived-1"]
        )


if __name__ == "__main__":
    unittest.main()
