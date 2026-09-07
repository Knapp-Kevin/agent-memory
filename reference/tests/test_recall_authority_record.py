"""GAP-SEC-02 (record leg): every governed recall leaves a governance record.

Before this cycle, governed_recall emitted zero events and never recorded a
decision. Every built-in refusal reason was computed and discarded:
ContextualRecallAdapter only ever sees candidates that already passed built-in
admission, so built-in decisions were recorded by neither layer.
"""
import unittest

from agentmem_ref import policy, receipts
from agentmem_ref.adapter import GovernedMemoryAdapter, RecallContext
from agentmem_ref.substrate import Fact, InMemoryTemporalGraph

TENANT = "tenant-A"


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


class RecallEventTest(unittest.TestCase):
    def setUp(self):
        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant=TENANT)
        self.adapter.commit_proposal(_proposal(), "deploy window Thursday")
        self.before = len(self.adapter.events)

    def _recall(self, **kwargs):
        context = RecallContext(target_domain_refs=(TENANT,), **kwargs)
        return self.adapter.governed_recall("deploy window", context)

    def _last_event(self):
        return self.adapter.events[-1]

    def test_exactly_one_event_per_recall(self):
        self._recall()
        self.assertEqual(1, len(self.adapter.events) - self.before)
        self._recall()
        self.assertEqual(2, len(self.adapter.events) - self.before)

    def test_event_validates_against_the_schema(self):
        """DoD 4's discriminating check: additionalProperties is False, so any
        stray top-level field fails here."""
        self._recall()
        receipts.validate("memory-audit-event.schema.json", self._last_event())

    def test_event_carries_the_docs34_handoff_fields(self):
        """docs/34:136 requires signal_type: recall_admission and the admission
        outcome inside signal_semantics."""
        self._recall(principal_ref="alice")
        event = self._last_event()
        self.assertEqual("memory.recall", event["event_type"])
        self.assertEqual("recall_admission", event["signal"]["signal_type"])
        self.assertIn("admitted", event["signal"]["signal_semantics"])
        self.assertEqual("alice", event["principal"])
        self.assertEqual(policy.POLICY_VERSION, event["policy_version"])

    def test_event_payload_carries_context_and_counts(self):
        self._recall(principal_ref="alice", project_ref="proj-1", purpose="deploy review")
        payload = self._last_event()["payload"]
        self.assertEqual([TENANT], payload["target_domain_refs"])
        self.assertEqual("proj-1", payload["project_ref"])
        self.assertEqual("deploy review", payload["purpose"])
        self.assertEqual(1, payload["candidate_count"])
        self.assertEqual(1, payload["admitted_count"])

    def test_a_refused_read_is_recorded_too(self):
        """The point of the gap: a cross-domain read must leave a trace."""
        self.adapter.governed_recall(
            "deploy window",
            RecallContext(target_domain_refs=("other-domain",), principal_ref="mallory"),
        )
        event = self._last_event()
        self.assertEqual("mallory", event["principal"])
        self.assertEqual(0, event["payload"]["admitted_count"])
        self.assertEqual(1, event["payload"]["candidate_count"])


class RecallDecisionTest(unittest.TestCase):
    def setUp(self):
        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant=TENANT)
        self.committed = self.adapter.commit_proposal(_proposal(), "deploy window Thursday")

    def test_every_candidate_has_a_schema_valid_decision(self):
        result = self.adapter.governed_recall("deploy window")
        self.assertEqual(set(result.candidates), set(result.decisions))
        for decision in result.decisions.values():
            receipts.validate("contextual-recall-admission.schema.json", decision)

    def test_admitted_decision_shape(self):
        result = self.adapter.governed_recall("deploy window")
        decision = result.decisions[self.committed.fact_uuid]
        self.assertEqual("admit", decision["outcome"])
        self.assertEqual("builtin_admission", decision["reason_code"])

    def test_refused_decision_carries_the_reason_code(self):
        self.substrate.write_fact(
            Fact(
                uuid="no-scope-1",
                fact_text="deploy window leaked",
                group_id=TENANT,
                episode_uuids=(),
                created_at="2026-01-01T00:00:00Z",
            )
        )
        result = self.adapter.governed_recall("deploy window")
        decision = result.decisions["no-scope-1"]
        self.assertEqual("block", decision["outcome"])
        self.assertEqual("unknown_scope", decision["reason_code"])

    def test_policy_status_is_unavailable_not_evaluated(self):
        """LD6 / audit V3: the recall path does not call policy.evaluate, so
        recording `evaluated` would fabricate a decision. Pinned by name so a
        silent switch is a test failure."""
        result = self.adapter.governed_recall("deploy window")
        decision = result.decisions[self.committed.fact_uuid]
        self.assertEqual("unavailable", decision["policy"]["status"])
        self.assertEqual("contextual-recall-policy:none", decision["policy"]["policy_ref"])

    def test_interpretation_pins_the_doctrinal_invariants(self):
        result = self.adapter.governed_recall("deploy window")
        interpretation = result.decisions[self.committed.fact_uuid]["interpretation"]
        self.assertEqual("current_recall_only", interpretation["authority_effect"])
        self.assertEqual("none", interpretation["prior_admission_authority"])
        self.assertEqual("not_performed", interpretation["memory_mutation"])

    def test_result_carries_policy_version_and_timestamp(self):
        result = self.adapter.governed_recall("deploy window")
        self.assertEqual(policy.POLICY_VERSION, result.policy_version)
        self.assertTrue(result.evaluated_at)


if __name__ == "__main__":
    unittest.main()
