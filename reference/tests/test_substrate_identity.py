"""GAP-SEC-08: identifiers are substrate-scoped, not adapter-scoped.

Two adapters over one substrate previously ran independent counters and
collided on every identifier -- fact uuid, receipt_id, correlation_id, and all
four event ids -- silently replacing each other's facts and merging each
other's evidence records.
"""
import unittest

from agentmem_ref import policy
from agentmem_ref.adapter import GovernedMemoryAdapter
from agentmem_ref.substrate import DeterministicIds, Fact, InMemoryTemporalGraph


def _proposal(proposal_id, actor_id, tenant, target_reference):
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id=actor_id,
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


def _event_ids(result):
    return [event["event_id"] for event in result.events]


def _all_identifiers(result):
    return {result.fact_uuid, result.receipt["receipt_id"], *_event_ids(result)}


class SharedSubstrateIdentityTest(unittest.TestCase):
    def setUp(self):
        self.substrate = InMemoryTemporalGraph()
        self.a = GovernedMemoryAdapter(self.substrate, tenant="tenant-A")
        self.b = GovernedMemoryAdapter(self.substrate, tenant="tenant-B")

    def _commit_both(self):
        ra = self.a.commit_proposal(
            _proposal("p-a", "agent:a", "tenant-A", "mem:A"), "TENANT A CONFIDENTIAL"
        )
        rb = self.b.commit_proposal(
            _proposal("p-b", "agent:b", "tenant-B", "mem:B"), "tenant B value"
        )
        return ra, rb

    def test_both_tenants_facts_survive(self):
        ra, rb = self._commit_both()
        self.assertTrue(ra.committed)
        self.assertTrue(rb.committed)
        texts = {fact.fact_text for fact in self.substrate.all_facts()}
        self.assertIn("TENANT A CONFIDENTIAL", texts)
        self.assertIn("tenant B value", texts)
        self.assertEqual(2, len(list(self.substrate.all_facts())))

    def test_fact_uuids_are_disjoint(self):
        ra, rb = self._commit_both()
        self.assertNotEqual(ra.fact_uuid, rb.fact_uuid)

    def test_no_identifier_is_shared_across_tenants(self):
        """The evidence surface, not just storage: receipts and events too."""
        ra, rb = self._commit_both()
        shared = _all_identifiers(ra) & _all_identifiers(rb)
        self.assertEqual(set(), shared, f"tenants share identifiers: {sorted(shared)}")

    def test_receipt_and_correlation_ids_are_disjoint(self):
        ra, rb = self._commit_both()
        self.assertNotEqual(ra.receipt["receipt_id"], rb.receipt["receipt_id"])
        self.assertNotEqual(
            ra.events[0]["correlation_id"], rb.events[0]["correlation_id"]
        )

    def test_adapters_bind_to_the_substrate_counter(self):
        self.assertIs(self.a._ids, self.substrate._ids)
        self.assertIs(self.b._ids, self.substrate._ids)


class SingleAdapterSequenceTest(unittest.TestCase):
    """DoD 6: LD1 must not change what one adapter emits."""

    def test_single_adapter_sequence_is_unchanged(self):
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant="tenant-A")
        result = adapter.commit_proposal(
            _proposal("p-1", "agent:a", "tenant-A", "mem:A"), "value"
        )
        self.assertEqual("ref-0004", result.fact_uuid)
        self.assertEqual("ref-0006", result.receipt["receipt_id"])
        self.assertEqual(
            ["ref-0002", "ref-0003", "ref-0005", "ref-0007"], _event_ids(result)
        )
        self.assertEqual("ref-0001", result.events[0]["correlation_id"])


class WriteFactCollisionGuardTest(unittest.TestCase):
    """LD2: defence in depth for substrates without a shared counter."""

    def setUp(self):
        self.substrate = InMemoryTemporalGraph()
        self.fact = Fact(
            uuid="dup-1",
            fact_text="original",
            group_id="tenant-A",
            episode_uuids=(),
            created_at="2026-01-01T00:00:00Z",
        )
        self.substrate.write_fact(self.fact)

    def test_differing_fact_on_same_uuid_raises(self):
        intruder = Fact(
            uuid="dup-1",
            fact_text="replacement",
            group_id="tenant-B",
            episode_uuids=(),
            created_at="2026-01-01T00:00:00Z",
        )
        with self.assertRaises(ValueError) as ctx:
            self.substrate.write_fact(intruder)
        self.assertIn("dup-1", str(ctx.exception))
        self.assertEqual("original", self.substrate.get_fact("dup-1").fact_text)

    def test_identical_rewrite_is_a_noop(self):
        self.substrate.write_fact(self.fact)
        self.assertEqual("original", self.substrate.get_fact("dup-1").fact_text)

    def test_guard_catches_a_substrate_without_a_shared_counter(self):
        """A foreign substrate falls back to per-adapter counters; the guard
        is what stops the resulting collision from destroying data."""

        class ForeignSubstrate(InMemoryTemporalGraph):
            def __init__(self):
                super().__init__()
                del self._ids  # no shared counter to discover

        foreign = ForeignSubstrate()
        a = GovernedMemoryAdapter(foreign, tenant="tenant-A")
        b = GovernedMemoryAdapter(foreign, tenant="tenant-B")
        self.assertIsNot(a._ids, b._ids)
        self.assertIsInstance(a._ids, DeterministicIds)

        a.commit_proposal(_proposal("p-a", "agent:a", "tenant-A", "mem:A"), "A value")
        with self.assertRaises(ValueError):
            b.commit_proposal(
                _proposal("p-b", "agent:b", "tenant-B", "mem:B"), "B value"
            )


if __name__ == "__main__":
    unittest.main()
