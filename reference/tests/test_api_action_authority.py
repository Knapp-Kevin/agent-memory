"""Sprint 4c-2 (plan LD3/LD6): `authorize` and `witness` at the boundary, contract 1.2.0.

Every assertion drives the surface and observes the result envelope the builder produced."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.api import contract, surface  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "reference" / "fixtures" / "api"
ACTION = json.loads((FIXTURES / "action-envelope.example.json").read_text(encoding="utf-8"))
OBSERVATION = json.loads((FIXTURES / "execution-observation.example.json").read_text(encoding="utf-8"))
PROPOSAL = json.loads((FIXTURES / "proposal-envelope.example.json").read_text(encoding="utf-8"))
ORG = "org:example"
KEYS = {"decision_ref", "bound", "execution_status", "ledger_required", "requirement", "composition_id"}


def _blocked() -> dict:
    return {**ACTION, "isolation_domain_refs": [], "required_isolation_domain_refs": ["project:example"]}


class Authorize(unittest.TestCase):
    def setUp(self):
        self.memory = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=ORG)

    def test_authorize_low_binds(self):
        result = surface.authorize(self.memory, ACTION)
        self.assertEqual((result["stage"], result["compatibility"], result["outcome"]), ("action_authority", contract.CURRENT, policy.ALLOW_WITH_LEDGER))
        authority = result["action_authority"]
        self.assertEqual(set(authority), KEYS)
        self.assertTrue(authority["bound"]); self.assertTrue(authority["ledger_required"])
        self.assertEqual(authority["execution_status"], "authorized_not_executed")
        self.assertEqual(authority["requirement"], "")
        self.assertTrue(authority["composition_id"].startswith("decision-composition:"))
        self.assertEqual(authority["decision_ref"], f"pama-decision:{ACTION['proposal_id']}")
        self.assertEqual(result["decision"]["constraints"], ["risk_cell"])

    def test_authorize_medium_parks_and_names_the_step(self):
        result = surface.authorize(self.memory, {**ACTION, "risk_class": "medium"})
        authority = result["action_authority"]
        self.assertEqual(set(authority), KEYS)
        self.assertFalse(authority["bound"]); self.assertIsNone(authority["execution_status"]); self.assertIsNone(authority["composition_id"])
        self.assertEqual(authority["requirement"], "enter_pending_verification")
        self.assertEqual(result["outcome"], policy.REQUIRE_REVIEW)

    def test_authorize_a4_parks_even_with_evidence(self):
        from agentmem_ref.core.evidence_qualification import EvidenceItem
        item = EvidenceItem(ref="evidence:release-notes-v1", artifact_ref="artifact:notes", digest="sha256:" + "0" * 64,
                            verifier="unregistered", failure_domain="test")
        result = surface.authorize(self.memory, {**ACTION, "downstream_authority": "A4_EXTERNAL_ACTION"}, evidence=[item])
        self.assertEqual(result["outcome"], policy.ALLOW_WITH_LEDGER)
        self.assertFalse(result["action_authority"]["bound"])
        self.assertEqual(result["action_authority"]["requirement"], "enter_pending_verification")
        self.assertIn("authority_floor:A4_EXTERNAL_ACTION", result["decision"]["constraints"])

    def test_authorize_refuses_assertion_fields(self):
        for field in ("requires_governance", "outcome", "decision_ref", "review_satisfied"):
            with self.subTest(field=field):
                result = surface.authorize(self.memory, {**ACTION, field: True})
                self.assertEqual(result["stage"], "none")
                self.assertIn(field, result["validation_error"])

    def test_authorize_refuses_other_operations(self):
        result = surface.authorize(self.memory, {**ACTION, "operation": "correction"})
        self.assertEqual(result["stage"], "none"); self.assertIn("operation", result["validation_error"])

    def test_memory_stages_refuse_action_execution(self):
        envelope = {**PROPOSAL, "operation": "action_execution"}
        self.assertIn("operation", surface.propose(self.memory, envelope)["validation_error"])
        self.assertIn("operation", surface.approve(self.memory, envelope)["validation_error"])
        self.assertIn("operation", surface.commit(self.memory, envelope, "value")["validation_error"])

    def test_reauthorise_returns_refusal(self):
        surface.authorize(self.memory, ACTION)
        same_action = surface.authorize(self.memory, {**ACTION, "proposal_id": "proposal-action-2"})
        self.assertEqual(same_action["refusal"], "action already evaluated"); self.assertNotIn("action_authority", same_action)
        same_proposal = surface.authorize(self.memory, {**ACTION, "action_id": "action:release-workflow@v1:2"})
        self.assertEqual(same_proposal["refusal"], "proposal already evaluated for an action"); self.assertNotIn("action_authority", same_proposal)

    def test_older_contract_version_is_current(self):
        result = surface.authorize(self.memory, {**ACTION, "contract_version": "1.1.0"})
        self.assertEqual((result["compatibility"], result["stage"]), (contract.CURRENT, "action_authority"))
        self.assertEqual(surface.authorize(self.memory, {**ACTION, "contract_version": "1.3.0"})["stage"], "none")


class Witness(unittest.TestCase):
    def setUp(self):
        self.memory = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=ORG)

    def test_witness_after_authorize(self):
        bound = surface.authorize(self.memory, ACTION)
        result = surface.witness(self.memory, OBSERVATION)
        self.assertEqual((result["stage"], result["compatibility"]), ("execution_evidence", contract.CURRENT))
        self.assertEqual(result["witness"]["composition_id"], bound["action_authority"]["composition_id"])
        self.assertEqual(result["witness"]["decision_alignment"], "consistent")
        self.assertEqual(result["witness"]["action_ref"], ACTION["action_id"])

    def test_second_witness_is_refused(self):
        surface.authorize(self.memory, ACTION)
        surface.witness(self.memory, OBSERVATION)
        again = surface.witness(self.memory, {**OBSERVATION, "witness_ref": "runtime:audit:release-2"})
        self.assertEqual(again["refusal"], "execution authorization already consumed"); self.assertNotIn("witness", again)

    def test_witness_without_bound_decision_refuses(self):
        result = surface.witness(self.memory, OBSERVATION)
        self.assertEqual(result["refusal"], "no bound decision for action"); self.assertNotIn("witness", result)
        surface.authorize(self.memory, {**ACTION, "risk_class": "medium"})
        parked = surface.witness(self.memory, OBSERVATION)
        self.assertEqual(parked["refusal"], "no bound decision for action"); self.assertNotIn("witness", parked)

    def test_observation_refuses_alignment_fields(self):
        surface.authorize(self.memory, ACTION)
        for field in ("effective_decision", "decision_alignment", "approval_verification"):
            with self.subTest(field=field):
                result = surface.witness(self.memory, {**OBSERVATION, field: "allow"})
                self.assertEqual(result["stage"], "none"); self.assertIn(field, result["validation_error"])

    def test_witness_violation_is_recorded_not_refused(self):
        bound = surface.authorize(self.memory, _blocked())
        self.assertEqual(bound["action_authority"]["execution_status"], "blocked_by_governance")
        result = surface.witness(self.memory, OBSERVATION)
        self.assertEqual(result["witness"]["decision_alignment"], "violation")
        self.assertEqual(result["witness"]["effective_decision"], "deny")


if __name__ == "__main__":
    unittest.main()
