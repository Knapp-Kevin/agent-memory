"""OPA adapter-edge tests that do not require an installed OPA binary."""

from __future__ import annotations

import unittest

from agentmem_ref.opa_policy_comparator import (
    OPA_POLICY_REVISION,
    minimized_opa_input,
    parse_opa_eval_document,
)
from agentmem_ref import policy
from agentmem_ref.enforcement_composition import build_projection


class OpaPolicyComparatorTests(unittest.TestCase):
    def _document(self, **overrides):
        value = {
            "decision": "allow",
            "reason": "fixture",
            "input_identity": "sha256:" + "a" * 64,
            "policy_revision": OPA_POLICY_REVISION,
        }
        value.update(overrides)
        return {
            "result": [
                {
                    "expressions": [
                        {
                            "value": value,
                            "text": "data.agentmemory.decision",
                        }
                    ]
                }
            ]
        }

    def test_parse_valid_opa_eval_document(self):
        value = parse_opa_eval_document(self._document())
        self.assertEqual(value["decision"], "allow")
        self.assertEqual(value["policy_revision"], OPA_POLICY_REVISION)

    def test_parse_rejects_missing_result(self):
        with self.assertRaisesRegex(ValueError, "exactly one result"):
            parse_opa_eval_document({})

    def test_parse_rejects_missing_required_fields(self):
        with self.assertRaisesRegex(ValueError, "missing required fields"):
            parse_opa_eval_document(self._document(reason=""))

    def test_parse_rejects_unknown_decision(self):
        with self.assertRaisesRegex(ValueError, "unsupported OPA decision"):
            parse_opa_eval_document(self._document(decision="permit_forever"))

    def test_minimized_input_has_no_raw_payload_surface(self):
        proposal = policy.Proposal(
            proposal_id="proposal:opa:minimize",
            actor_id="actor:test",
            charter_version="charter:v1",
            target_reference="mem:opa:minimize",
            target_class=policy.M2,
            scope="scope:tenant-a/project-a",
            operation="promotion",
            current_strength="reinforced",
            proposed_strength="promoted",
            downstream_authority=policy.A1,
            reversibility="reversible",
            risk_class="low",
            evidence_refs=("evidence:opa",),
            state_snapshot="v0",
            tenant_ref="tenant-a",
            purpose="opa-allow",
            isolation_domain_refs=("scope:tenant-a/project-a",),
            project_ref="project-a",
        )
        projection = build_projection(proposal, policy.evaluate(proposal))
        minimized = minimized_opa_input(projection)
        self.assertEqual(minimized["input_identity"], projection["input_identity"])
        self.assertEqual(minimized["operation"], "promotion")
        self.assertEqual(minimized["purpose"], "opa-allow")
        for forbidden in (
            "evidence_refs",
            "authority_refs",
            "raw_memory",
            "memory_content",
            "prompt",
            "hidden_reasoning",
        ):
            self.assertNotIn(forbidden, minimized)

    def test_parse_does_not_adopt_extra_opa_authority_fields(self):
        document = self._document()
        value = document["result"][0]["expressions"][0]["value"]
        value.update(
            {
                "approval": "granted",
                "standing_authority": True,
                "execution_status": "executed",
                "enforcement_status": "enforced",
            }
        )
        parsed = parse_opa_eval_document(document)
        self.assertEqual(
            set(parsed),
            {"decision", "reason", "input_identity", "policy_revision"},
        )


if __name__ == "__main__":
    unittest.main()
