"""Sprint 4a (LD1, LD3): the public envelopes validate, version-check, and convert exactly."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.api import contract  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXAMPLES = REPO / "reference" / "fixtures" / "api"
FORBIDDEN = ("review_satisfied", "approval_refs", "approves_own_authority", "actor_authority_resolved")


def _example(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


class EnvelopeValidation(unittest.TestCase):
    def test_envelope_validates_and_forbidden_fields_are_rejected(self):
        example = _example("proposal-envelope.example.json")
        self.assertEqual(contract.validate_proposal_envelope(example), example)
        for field in FORBIDDEN:
            with self.subTest(field=field):
                with self.assertRaises(ValueError) as ctx:
                    contract.validate_proposal_envelope({**example, field: True})
                self.assertIn(field, str(ctx.exception))
        with self.assertRaises(ValueError):
            contract.validate_proposal_envelope({k: v for k, v in example.items() if k != "contract_version"})
        recall = _example("recall-context.example.json")
        self.assertEqual(contract.validate_recall_context(recall), recall)

    def test_compatibility_states(self):
        # Additive versioning (Sprint 4c-1): an older minor of the same major is current; a newer
        # minor is migration_required; a different major is incompatible. Sprint 4a had the first
        # two inverted; this re-statement is the one existing-test edit of that cycle.
        cases = {
            "1.0.0": contract.CURRENT, "1.1.0": contract.CURRENT, "1.2.0": contract.CURRENT, "1.3.0": contract.MIGRATION_REQUIRED,
            "0.9.0": contract.INCOMPATIBLE, "2.0.0": contract.INCOMPATIBLE, None: contract.UNKNOWN, "one.zero": contract.UNKNOWN,
        }
        for version, expected in cases.items():
            with self.subTest(version=version):
                envelope = {} if version is None else {"contract_version": version}
                self.assertEqual(contract.compatibility(envelope), expected)
        self.assertEqual(contract.CONTRACT_VERSION, "1.2.0")

    def test_target_envelope_validates(self):
        example = _example("target-envelope.example.json")
        self.assertEqual(contract.validate_target_envelope(example), example)
        self.assertEqual(contract.validate_target_envelope({**example, "contract_version": "1.0.0"})["contract_version"], "1.0.0")
        with self.assertRaises(ValueError):
            contract.validate_target_envelope({**example, "extra": 1})

    def test_action_envelope_validates(self):
        example = _example("action-envelope.example.json")
        self.assertEqual(contract.validate_action_envelope(example), example)
        action, proposal = contract.action_from_envelope(example)
        self.assertEqual((action.action_id, action.requires_governance, proposal.operation), (example["action_id"], True, "action_execution"))
        for field in ("requires_governance", "outcome", "decision_ref", "review_satisfied"):
            with self.subTest(field=field), self.assertRaises(ValueError) as ctx:
                contract.validate_action_envelope({**example, field: True})
            self.assertIn(field, str(ctx.exception))
        with self.assertRaises(ValueError):
            contract.validate_action_envelope({**example, "operation": "correction"})
        with self.assertRaises(ValueError):
            contract.validate_action_envelope({k: v for k, v in example.items() if k != "state_snapshot"})

    def test_observation_envelope_validates(self):
        example = _example("execution-observation.example.json")
        self.assertEqual(contract.validate_observation_envelope(example), example)
        for field in ("effective_decision", "decision_alignment", "approval_verification"):
            with self.subTest(field=field), self.assertRaises(ValueError) as ctx:
                contract.validate_observation_envelope({**example, field: "allow"})
            self.assertIn(field, str(ctx.exception))

    def test_decision_projection_carries_constraints(self):
        proposal = contract.proposal_from_envelope({**_example("proposal-envelope.example.json"), "downstream_authority": "A4_EXTERNAL_ACTION"})
        self.assertEqual(contract.decision_projection(policy.evaluate(proposal))["constraints"], ["risk_cell", "authority_floor:A4_EXTERNAL_ACTION"])

    def test_envelope_to_proposal_round_trip(self):
        example = _example("proposal-envelope.example.json")
        proposal = contract.proposal_from_envelope(contract.validate_proposal_envelope(example))
        for name in contract.PUBLIC_PROPOSAL_FIELDS:
            if name in example:
                value = example[name]
                self.assertEqual(getattr(proposal, name), tuple(value) if isinstance(value, list) else value, name)
        self.assertIs(proposal.review_satisfied, False)
        self.assertEqual(proposal.approval_refs, ())
        self.assertIs(proposal.approves_own_authority, False)
        self.assertIs(proposal.actor_authority_resolved, True)

    def test_decision_projection_fields(self):
        example = _example("proposal-envelope.example.json")
        proposal = contract.proposal_from_envelope({**example, "operation": "correction", "risk_class": "medium"})
        projection = contract.decision_projection(policy.evaluate(proposal))
        self.assertEqual(projection["outcome"], policy.REQUIRE_REVIEW)
        # The base evaluation carries no discharge reason: nothing was claimed. The reason
        # review_requires_qualified_evidence appears only when a caller asserts review
        # (the legacy route), which the envelope cannot express.
        self.assertEqual(projection["reasons"], [])
        self.assertIn("enter_pending_verification", projection["permitted_actions"])
        self.assertEqual(set(projection), {"outcome", "permitted_actions", "prohibited_actions", "reasons", "policy_version", "discharge_authority", "review_discharge", "constraints"})

    def test_result_envelope_validates_against_its_schema(self):
        document = contract.result("proposal", contract.CURRENT, outcome="require_review",
                                   decision=contract.decision_projection(policy.evaluate(contract.proposal_from_envelope(
                                       {**_example("proposal-envelope.example.json"), "operation": "correction", "risk_class": "medium"}))))
        self.assertEqual(document["contract_version"], contract.CONTRACT_VERSION)
        with self.assertRaises(ValueError):
            contract.result("proposal", contract.CURRENT, not_a_field=1)


if __name__ == "__main__":
    unittest.main()
