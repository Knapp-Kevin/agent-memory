import hashlib
import unittest

from agentmem_ref import policy
from agentmem_ref.uor_content_reference import evaluate_json_content_reference


def content_ref() -> str:
    result = evaluate_json_content_reference(
        b'{"a":1}',
        address_fn=lambda value: "sha256:" + hashlib.sha256(value).hexdigest(),
        binding_name="fixture",
        binding_version="0",
    )
    return result["generated_label"]


class UorBoundaryTests(unittest.TestCase):
    def test_content_ref_does_not_change_pama_result(self):
        decision = policy.evaluate(policy.Proposal(
            proposal_id="uor-pama-boundary",
            actor_id="agent:fixture",
            charter_version="charter:v1",
            target_reference="memory:logical:alpha",
            target_class=policy.M4,
            scope="tenant:a",
            operation="correction",
            current_strength="medium",
            proposed_strength="medium",
            downstream_authority=policy.A4,
            reversibility="reversible",
            risk_class="high",
            evidence_refs=(content_ref(),),
        ))
        self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW)
        self.assertNotIn("correction", decision.permitted_actions)

    def test_content_ref_does_not_fix_scope_mismatch(self):
        decision = policy.evaluate(policy.Proposal(
            proposal_id="uor-scope-boundary",
            actor_id="agent:fixture",
            charter_version="charter:v1",
            target_reference="memory:logical:alpha",
            target_class=policy.M2,
            scope="tenant:b",
            operation="runtime_assembly",
            current_strength="medium",
            proposed_strength="medium",
            downstream_authority=policy.A1,
            reversibility="reversible",
            risk_class="low",
            evidence_refs=(content_ref(),),
            isolation_domain_refs=("tenant:b",),
            required_isolation_domain_refs=("tenant:a",),
        ))
        self.assertEqual(decision.outcome, policy.BLOCK)
        self.assertEqual(decision.permitted_actions, ())


if __name__ == "__main__":
    unittest.main()
