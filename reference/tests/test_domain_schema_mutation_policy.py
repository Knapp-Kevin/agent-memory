"""Focused policy cases for PAMA 1.2 domain-schema mutation."""

import unittest

from agentmem_ref import domain_schema_mutation as dsm
from agentmem_ref import policy


def make_proposal(risk="medium", target=policy.M3, authority=policy.A3, evidence=("evidence:schema",), confidence=None, self_approve=False, reviewed=False, approvals=()):
    return policy.Proposal(
        proposal_id=f"schema:{risk}", actor_id="agent:schema-observer", charter_version="charter:1",
        target_reference="domain-model:project-a", target_class=target, scope="tenant-a/project-a",
        operation=dsm.DOMAIN_SCHEMA_MUTATION, current_strength="promoted", proposed_strength="canonical",
        downstream_authority=authority, reversibility="versioned_revocable", risk_class=risk,
        evidence_refs=evidence, estimator_refs=("estimator:schema",) if confidence is not None else (),
        estimator_versions=("schema:1",) if confidence is not None else (), confidence=confidence,
        approves_own_authority=self_approve, review_satisfied=reviewed, approval_refs=approvals,
        state_snapshot="snapshot:model:v4", tenant_ref="tenant-a", purpose="ontology evolution",
        isolation_domain_refs=("tenant-a/project-a",), required_isolation_domain_refs=("tenant-a/project-a",),
        project_ref="project-a",
    )


class DomainSchemaMutationPolicyTests(unittest.TestCase):
    def test_explicit_risk_table(self):
        expected = {"low": policy.REQUIRE_REVIEW, "medium": policy.REQUIRE_REVIEW, "high": policy.REQUIRE_EXTERNAL_VERIFICATION, "critical": policy.REQUIRE_EXTERNAL_VERIFICATION}
        for risk, outcome in expected.items():
            with self.subTest(risk=risk):
                self.assertEqual(dsm.evaluate(make_proposal(risk=risk)).outcome, outcome)

    def test_estimator_confidence_and_missing_evidence_do_not_weaken(self):
        self.assertEqual(dsm.evaluate(make_proposal(risk="high", confidence=0.999999)).outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)
        low = dsm.evaluate(make_proposal(risk="low", evidence=()))
        self.assertEqual(low.outcome, policy.REQUIRE_REVIEW)
        self.assertTrue(any("M-EVID" in reason for reason in low.reasons))

    def test_self_approval_blocks(self):
        result = dsm.evaluate(make_proposal(risk="low", self_approve=True, reviewed=True, approvals=("approval:self",)))
        self.assertEqual(result.outcome, policy.BLOCK)

    def test_scope_and_governance_floors_remain_strict(self):
        scoped = dsm.evaluate(make_proposal(risk="critical"), requested_scope_change="project -> tenant")
        self.assertEqual(scoped.outcome, policy.BLOCK)
        governance = dsm.evaluate(make_proposal(risk="low", target=policy.M5, authority=policy.A5))
        self.assertEqual(governance.outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)

    def test_review_discharges_only_after_floors(self):
        result = dsm.evaluate(make_proposal(risk="high", reviewed=True, approvals=("approval:independent",)))
        self.assertEqual(result.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertIn(dsm.DOMAIN_SCHEMA_MUTATION, result.permitted_actions)


if __name__ == "__main__":
    unittest.main()
