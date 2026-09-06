"""GAP-SEC-08 / LD6: the substrate counter must survive a restart.

Audit ground V1: restart_runtime previously rebound `adapter._ids` to a fresh
private DeterministicIds, which detached the adapter from the substrate counter
and silently reverted the collision fix on the first restart.
"""
import unittest

from agentmem_ref import policy, restart_runtime
from agentmem_ref.adapter import GovernedMemoryAdapter
from agentmem_ref.restart_runtime import CapabilityBinding, RuntimeProfile
from agentmem_ref.substrate import Fact, InMemoryTemporalGraph

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


def _snapshot(adapter):
    return restart_runtime._snapshot_governance(
        adapter, profile=_PROFILE, visibility_snapshots={}
    )


def _restore(snapshot, substrate):
    adapter, _ = restart_runtime._restore_adapter(substrate, snapshot)
    return adapter


def _proposal(proposal_id, tenant, target_reference):
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="agent:a",
        charter_version="v1",
        target_reference=target_reference,
        target_class=policy.M1,
        scope=tenant,
        operation="runtime_assembly",
        current_strength="observed",
        proposed_strength="tentative",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("ep-1",),
        tenant_ref=tenant,
        isolation_domain_refs=(tenant,),
    )


class RestartCounterTest(unittest.TestCase):
    def test_restored_adapter_stays_bound_to_the_substrate_counter(self):
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant="tenant-A")
        adapter.commit_proposal(_proposal("p-1", "tenant-A", "mem:A"), "value")

        snapshot = _snapshot(adapter)
        restored_substrate = InMemoryTemporalGraph()
        restored = _restore(snapshot, restored_substrate)
        self.assertIs(
            restored._ids,
            restored_substrate._ids,
            "restart detached the adapter from the substrate counter",
        )

    def test_counter_advances_past_restored_identifiers(self):
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant="tenant-A")
        first = adapter.commit_proposal(_proposal("p-1", "tenant-A", "mem:A"), "value")

        snapshot = _snapshot(adapter)
        restored_substrate = InMemoryTemporalGraph()
        restored_substrate._facts = dict(substrate._facts)
        restored = _restore(snapshot, restored_substrate)

        after = restored.commit_proposal(
            _proposal("p-2", "tenant-A", "mem:B"), "second value"
        )
        self.assertNotEqual(first.fact_uuid, after.fact_uuid)
        self.assertGreater(after.fact_uuid, first.fact_uuid)
        self.assertEqual(2, len(list(restored_substrate.all_facts())))

    def test_missing_counter_raises_rather_than_destroying_a_restored_fact(self):
        """DoD 11: the disclosed residual is loud, not silent."""
        substrate = InMemoryTemporalGraph()
        substrate.write_fact(
            Fact(
                uuid="ref-0004",
                fact_text="restored fact",
                group_id="tenant-A",
                episode_uuids=(),
                created_at="2026-01-01T00:00:00Z",
            )
        )
        adapter = GovernedMemoryAdapter(substrate, tenant="tenant-A")
        with self.assertRaises(ValueError):
            adapter.commit_proposal(_proposal("p-1", "tenant-A", "mem:A"), "new value")
        self.assertEqual("restored fact", substrate.get_fact("ref-0004").fact_text)


if __name__ == "__main__":
    unittest.main()
