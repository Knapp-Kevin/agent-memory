"""Sprint 4c-2 (ADR-038, plan LD4/LD4b/LD5): the memory-layer action path over the runtime adapter.

Every assertion drives `authorize_action` / `witness_execution` and observes the adapter's ledger,
the seam's state, or the witness the builder produced; none reads source."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy, receipts  # noqa: E402
from agentmem_ref import procedural_memory as pm  # noqa: E402
from agentmem_ref.adapter import GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.core.evidence_qualification import EvidenceItem  # noqa: E402
from agentmem_ref.memory import action_authority as aa  # noqa: E402
from agentmem_ref.restart_runtime import CapabilityBinding, RestartSafeRuntime, RuntimeProfile, _restore_adapter, _snapshot_governance  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

ORG = "org:example"
SKILL = pm.SkillArtifact(skill_id="release-workflow", version=1, purpose="release", scope="project", isolation_domain_refs=("domain:project-a",),
                         required_isolation_domain_refs=("domain:project-a",), procedure_markdown="- cut the branch", provenance_refs=("prov-1",))
TARGET = SKILL.version_reference
PROFILE = RuntimeProfile(runtime_version="0.1.0-reference", profile_id="reference-project-memory", profile_version="1.0.0",
                         bindings=(CapabilityBinding(component_id="reference-governed-memory", component_version="1.0.0",
                                                     capability_id="governed-memory-core", capability_version="1.0.0",
                                                     maturity="reference_qualified", evidence_ref="evidence:reference-runtime-core-v1"),))


def _proposal(pid: str, risk: str = "low", authority: str = policy.A3, **extra) -> policy.Proposal:
    fields = dict(
        proposal_id=pid, actor_id="agent:release", charter_version="v1", target_reference=TARGET, target_class=policy.M3,
        scope="project:example", operation="action_execution", current_strength="promoted", proposed_strength="promoted",
        downstream_authority=authority, reversibility="reversible", risk_class=risk, evidence_refs=("evidence:release-notes",),
        state_snapshot="v1", isolation_domain_refs=("domain:project-a",), required_isolation_domain_refs=("domain:project-a",),
    )
    fields.update(extra)
    return policy.Proposal(**fields)


def _action(action_id: str) -> pm.ActionProposal:
    return pm.ActionProposal(action_id=action_id, description="cut the release branch", skill_version_ref=TARGET)


def _observation(status: str = "executed", **extra) -> dict:
    return {"witness_ref": "runtime:audit:1", "enforcement_mode": "mechanical", "delivery_status": "delivered",
            "enforcement_point_status": "reached", "action_status": status, "liveness_status": "healthy",
            "observed_at": "2026-09-07T15:00:00Z", **extra}


def _events(memory, action_id):
    return [event["event_type"] for event in memory.events if event.get("memory_id") == action_id]


class Authorize(unittest.TestCase):
    def setUp(self):
        self.memory = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=ORG)

    def test_allow_with_ledger_materialises_the_ledger_then_binds(self):
        authority = aa.authorize_action(self.memory, _action("a1"), _proposal("p1"))
        self.assertTrue(authority.bound); self.assertTrue(authority.ledger_required)
        self.assertEqual(authority.action.execution_status, "authorized_not_executed")
        self.assertEqual(authority.pama_decision["decision"]["outcome"], policy.ALLOW_WITH_LEDGER)
        self.assertEqual(authority.receipt["decision_ref"], authority.decision_ref)
        self.assertEqual(authority.composition["local_decision_ref"], authority.decision_ref)
        self.assertEqual(authority.receipt["memory_id"], TARGET)
        self.assertEqual(authority.receipt["requested_action"], "action_execution")
        self.assertEqual(authority.receipt["selection_mode"], "deterministic")
        self.assertEqual(_events(self.memory, "a1"), ["action.propose", "action.authorize", "action.receipt"])
        self.assertEqual(authority.action.governance_decision_ref, authority.decision_ref)

    def test_ledger_failure_fails_closed(self):
        with mock.patch.object(receipts, "build_receipt", side_effect=ValueError("ledger unavailable")):
            with self.assertRaises(ValueError):
                aa.authorize_action(self.memory, _action("a1"), _proposal("p1"))
        self.assertNotIn(aa.SLOT, self.memory.extension_state)
        self.assertEqual(_events(self.memory, "a1"), [])

    def test_block_binds_deny_with_its_ledger(self):
        blocked = _proposal("p1", isolation_domain_refs=(), required_isolation_domain_refs=("domain:project-a",))
        authority = aa.authorize_action(self.memory, _action("a1"), blocked)
        self.assertEqual(authority.decision.outcome, policy.BLOCK)
        self.assertTrue(authority.bound)
        self.assertEqual(authority.action.execution_status, "blocked_by_governance")
        self.assertEqual(authority.pama_decision["decision"]["outcome"], policy.BLOCK)
        self.assertEqual(authority.receipt["selected_action"], receipts.NO_ACTION)
        self.assertEqual(authority.composition["effective_decision"], "deny")

    def test_review_binds_nothing(self):
        authority = aa.authorize_action(self.memory, _action("a1"), _proposal("p1", risk="medium"))
        self.assertEqual(authority.decision.outcome, policy.REQUIRE_REVIEW)
        self.assertIsNone(authority.action); self.assertIsNone(authority.composition)
        self.assertIsNone(authority.receipt); self.assertIsNone(authority.pama_decision)
        self.assertEqual(authority.requirement, aa.ENTER_PENDING)
        self.assertEqual(_events(self.memory, "a1"), ["action.propose", "action.authorize"])
        self.assertIn("a1", self.memory.extension_state[aa.SLOT]["authorities"])

    def test_a4_low_parks_without_evidence(self):
        authority = aa.authorize_action(self.memory, _action("a1"), _proposal("p1", authority=policy.A4))
        self.assertFalse(authority.bound); self.assertEqual(authority.requirement, aa.ENTER_PENDING)
        self.assertIn(f"authority floor {policy.A4}", authority.decision.reasons)

    def test_a4_floor_is_not_discharged_by_evidence(self):
        item = EvidenceItem(ref="evidence:release-notes", artifact_ref="artifact:notes", digest="sha256:" + "0" * 64,
                            verifier="unregistered", failure_domain="test")
        authority = aa.authorize_action(self.memory, _action("a1"), _proposal("p1", authority=policy.A4), evidence=[item])
        self.assertEqual(authority.decision.outcome, policy.ALLOW_WITH_LEDGER)  # policy discharged the review...
        self.assertFalse(authority.bound)  # ...but the floor constraint stays and nothing binds
        self.assertEqual(authority.requirement, aa.ENTER_PENDING)
        self.assertIn(f"authority_floor:{policy.A4} is not dischargeable on the action path", authority.reasons)

    def test_a5_floor_is_not_discharged_by_attestation(self):
        attestation = policy.ExternalVerification(bound_proposal_id="p1", verifier_principal_id="policy:delegate",
                                                  authority_kind=policy.DELEGATED_POLICY, max_risk_class="critical")
        authority = aa.authorize_action(self.memory, _action("a1"), _proposal("p1", authority=policy.A5), attestation=attestation)
        self.assertEqual(authority.decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertFalse(authority.bound); self.assertEqual(authority.requirement, aa.REQUEST_EXTERNAL)

    def test_evidence_discharges_and_binds_a3(self):
        authority = aa.authorize_action(self.memory, _action("a1"), _proposal("p1", risk="medium"), evidence=list(pm.evidence_for(SKILL)))
        self.assertTrue(authority.bound)
        self.assertEqual(authority.decision.outcome, policy.ALLOW_WITH_LEDGER)

    def test_reauthorising_a_known_action_id_raises(self):
        aa.authorize_action(self.memory, _action("a1"), _proposal("p1"))
        aa.authorize_action(self.memory, _action("a2"), _proposal("p2", risk="medium"))
        for action_id in ("a1", "a2"):
            with self.assertRaises(ValueError):
                aa.authorize_action(self.memory, _action(action_id), _proposal(f"p-{action_id}"))

    def test_reusing_a_proposal_id_raises(self):
        first = aa.authorize_action(self.memory, _action("a1"), _proposal("p1"))
        aa.witness_execution(self.memory, "a1", _observation())
        with self.assertRaises(ValueError) as ctx:
            aa.authorize_action(self.memory, _action("a2"), _proposal("p1"))
        self.assertEqual(str(ctx.exception), "proposal already evaluated for an action")
        self.assertEqual(len(self.memory.extension_state[aa.SLOT]["authorities"]), 1)
        self.assertEqual(self.memory.extension_state[aa.SLOT]["authorities"]["a1"]["decision_ref"], first.decision_ref)

    def test_wrong_operation_raises(self):
        with self.assertRaises(ValueError):
            aa.authorize_action(self.memory, _action("a1"), _proposal("p1", operation="correction"))


class Witness(unittest.TestCase):
    def setUp(self):
        self.memory = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=ORG)

    def test_witness_refused_without_bound_decision(self):
        with self.assertRaises(ValueError) as ctx:
            aa.witness_execution(self.memory, "unknown", _observation())
        self.assertEqual(str(ctx.exception), aa.NO_BOUND_DECISION)
        aa.authorize_action(self.memory, _action("parked"), _proposal("p1", risk="medium"))
        with self.assertRaises(ValueError):
            aa.witness_execution(self.memory, "parked", _observation())
        self.assertIn("action.unbound_execution_reported", _events(self.memory, "parked"))
        self.assertNotIn("action.witness", _events(self.memory, "parked"))

    def test_witness_binds_to_the_exact_composition(self):
        authority = aa.authorize_action(self.memory, _action("a1"), _proposal("p1"))
        witness = aa.witness_execution(self.memory, "a1", _observation())
        self.assertEqual(witness["composition_id"], authority.composition["composition_id"])
        self.assertEqual(witness["input_identity"], authority.composition["input_identity"])
        self.assertEqual(witness["decision_alignment"], "consistent")
        stored = aa._load(self.memory)[0]["a1"]
        self.assertTrue(stored.consumed)
        self.assertEqual(stored.action.execution_status, "executed_by_runtime")
        self.assertEqual(stored.action.execution_ref, witness["witness_id"])
        self.assertIn("action.witness", _events(self.memory, "a1"))

    def test_second_execution_is_refused_at_the_seam(self):
        aa.authorize_action(self.memory, _action("a1"), _proposal("p1"))
        aa.witness_execution(self.memory, "a1", _observation())
        seen = []
        real = pm.record_runtime_execution

        def recording(action, ref):
            seen.append(action.execution_status)
            return real(action, ref)

        with mock.patch("agentmem_ref.memory.action_authority.record_runtime_execution", side_effect=recording):
            with self.assertRaises(ValueError) as ctx:
                aa.witness_execution(self.memory, "a1", _observation(witness_ref="runtime:audit:2"))
        self.assertEqual(str(ctx.exception), aa.ALREADY_CONSUMED)
        self.assertEqual(seen, ["executed_by_runtime"])  # the seam was asked, and refused
        self.assertIsInstance(ctx.exception.__cause__, ValueError)
        self.assertIn("requires a bound external governance allow decision", str(ctx.exception.__cause__))
        self.assertEqual(_events(self.memory, "a1").count("action.witness"), 1)

    def test_deny_bound_execution_is_a_violation_witness(self):
        blocked = _proposal("p1", isolation_domain_refs=(), required_isolation_domain_refs=("domain:project-a",))
        aa.authorize_action(self.memory, _action("a1"), blocked)
        witness = aa.witness_execution(self.memory, "a1", _observation())
        self.assertEqual(witness["decision_alignment"], "violation")
        self.assertFalse(aa._load(self.memory)[0]["a1"].consumed)

    def test_observation_cannot_supply_alignment(self):
        blocked = _proposal("p1", isolation_domain_refs=(), required_isolation_domain_refs=("domain:project-a",))
        aa.authorize_action(self.memory, _action("a1"), blocked)
        witness = aa.witness_execution(self.memory, "a1", _observation(effective_decision="allow", decision_alignment="consistent"))
        self.assertEqual(witness["decision_alignment"], "violation")
        self.assertEqual(witness["effective_decision"], "deny")

    def test_non_executed_witness_does_not_consume(self):
        aa.authorize_action(self.memory, _action("a1"), _proposal("p1"))
        witness = aa.witness_execution(self.memory, "a1", _observation("prevented"))
        self.assertEqual(witness["decision_alignment"], "stricter_than_decision")
        self.assertFalse(aa._load(self.memory)[0]["a1"].consumed)

    def test_witness_never_reaches_mutation_seams(self):
        class Recording(GovernedMemoryAdapter):
            writes = 0

            def commit_proposal(self, *args, **kwargs):
                self.writes += 1
                return super().commit_proposal(*args, **kwargs)

            def governed_delete(self, *args, **kwargs):
                self.writes += 1
                return super().governed_delete(*args, **kwargs)

        memory = Recording(InMemoryTemporalGraph(), tenant=ORG)
        aa.authorize_action(memory, _action("a1"), _proposal("p1"))
        aa.witness_execution(memory, "a1", _observation())
        self.assertEqual(memory.writes, 0)


class Restart(unittest.TestCase):
    def test_consumption_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            session = RestartSafeRuntime.create(Path(tmp), tenant=ORG, profile=PROFILE)
            aa.authorize_action(session.adapter, _action("a1"), _proposal("p1"))
            aa.witness_execution(session.adapter, "a1", _observation())
            session.checkpoint()  # the host's obligation: consumption is durable for state a checkpoint captured
            restored = RestartSafeRuntime.recover(Path(tmp), profile=PROFILE)
            self.assertEqual(restored.adapter.extension_state[aa.SLOT]["proposals"], ["p1"])
            with self.assertRaises(ValueError) as ctx:
                aa.witness_execution(restored.adapter, "a1", _observation(witness_ref="runtime:audit:2"))
            self.assertEqual(str(ctx.exception), aa.ALREADY_CONSUMED)
            with self.assertRaises(ValueError):
                aa.authorize_action(restored.adapter, _action("a2"), _proposal("p1"))

    def test_malformed_action_state_fails_closed(self):
        adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=ORG)
        aa.authorize_action(adapter, _action("a1"), _proposal("p1"))
        aa.witness_execution(adapter, "a1", _observation())
        snapshot = _snapshot_governance(adapter, profile=PROFILE, visibility_snapshots={})
        del snapshot["adapter"]["extension_state"][aa.SLOT]["authorities"]["a1"]["consumed"]
        restored, _ = _restore_adapter(InMemoryTemporalGraph(), snapshot)
        with self.assertRaises(ValueError) as ctx:
            aa.authorize_action(restored, _action("a2"), _proposal("p2"))
        self.assertEqual(str(ctx.exception), aa.MALFORMED)
        self.assertEqual(_events(restored, "a2"), [])


if __name__ == "__main__":
    unittest.main()
