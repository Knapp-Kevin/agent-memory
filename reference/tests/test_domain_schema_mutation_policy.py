"""Focused policy cases for PAMA 1.2 domain-schema mutation."""

from dataclasses import replace
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule

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


def transition_evidence(proposal):
    corpus = corpus_for(rule(
        rule_id="rule:domain-schema-transition",
        target=proposal.target_reference,
        criterion="domain-schema-transition",
        from_state="v4",
        to_values=("v5",),
    ))
    evidence = corpus.evidence_for(
        target_reference=proposal.target_reference,
        criterion="domain-schema-transition",
        pre_state="v4",
        proposed_value="v5",
    )
    return evidence, registry_for(corpus)


def attestation(proposal, *, proposal_id=None, principal="human:schema-owner"):
    return policy.ExternalVerification(
        bound_proposal_id=proposal_id or proposal.proposal_id,
        verifier_principal_id=principal,
        authority_kind=policy.HUMAN_CONFIRMATION,
        max_risk_class="critical",
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

    def test_asserted_review_no_longer_discharges_medium_or_high(self):
        medium = dsm.evaluate(make_proposal(risk="medium", reviewed=True, approvals=("approval:independent",)))
        self.assertEqual(medium.outcome, policy.REQUIRE_REVIEW)
        self.assertIn(policy.REVIEW_REQUIRES_QUALIFIED_EVIDENCE, medium.reasons)

        high = dsm.evaluate(make_proposal(risk="high", reviewed=True, approvals=("approval:independent",)))
        self.assertEqual(high.outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)
        self.assertIn("external_verification_requires_attestation", high.reasons)

    def test_medium_qualified_transition_evidence_discharges_review(self):
        proposal = make_proposal(risk="medium")
        evidence, registry = transition_evidence(proposal)
        result = dsm.evaluate(proposal, evidence=evidence, verifier_registry=registry)
        self.assertEqual(result.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertIn(dsm.DOMAIN_SCHEMA_MUTATION, result.permitted_actions)
        self.assertEqual(result.discharge_authority, policy.DELEGATED_POLICY)

    def test_high_bound_human_attestation_discharges_external_verification(self):
        proposal = make_proposal(risk="high")
        result = dsm.evaluate(proposal, attestation=attestation(proposal))
        self.assertEqual(result.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(result.review_discharge, "verified")
        self.assertIn(dsm.DOMAIN_SCHEMA_MUTATION, result.permitted_actions)

    def test_high_attestation_still_enforces_binding_and_separation(self):
        proposal = make_proposal(risk="high")
        wrong = dsm.evaluate(
            proposal,
            attestation=attestation(proposal, proposal_id="schema:other"),
        )
        self.assertEqual(wrong.outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)
        self.assertIn("attestation_not_bound_to_proposal", wrong.reasons)

        self_verified = dsm.evaluate(
            proposal,
            attestation=attestation(proposal, principal=proposal.actor_id),
        )
        self.assertEqual(self_verified.outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)
        self.assertIn("attestation_self_verified", self_verified.reasons)

    def test_scope_change_argument_cannot_disagree_with_proposal(self):
        proposal = replace(make_proposal(risk="high"), requested_scope_change="project -> tenant")
        with self.assertRaisesRegex(ValueError, "requested_scope_change disagrees"):
            dsm.evaluate(proposal, requested_scope_change="project -> global")


if __name__ == "__main__":
    unittest.main()
