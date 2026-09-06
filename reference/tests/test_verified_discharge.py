"""GAP-ARCH-04: external verification is dischargeable only by attestation.

Before this cycle, `review_satisfied=True` plus the literal string "i-said-so"
collapsed `policy_mutation/critical` to `allow_with_ledger` -- which made
`require_review` and `require_external_verification` the same thing under
assertion, erasing the distinction the decision table exists to draw.
"""
import unittest

from agentmem_ref import policy


def _proposal(operation="policy_mutation", risk="critical", **overrides):
    base = dict(
        proposal_id="p-1", actor_id="agent:x", charter_version="v1",
        target_reference="mem:A", target_class=policy.M1, scope="t",
        operation=operation, current_strength="observed",
        proposed_strength="tentative", downstream_authority=policy.A1,
        reversibility="reversible", risk_class=risk,
        evidence_refs=("ep-1",), tenant_ref="t", isolation_domain_refs=("t",),
    )
    base.update(overrides)
    return policy.Proposal(**base)


def _attestation(proposal, **overrides):
    base = dict(
        bound_proposal_id=proposal.proposal_id,
        verifier_principal_id="principal:operator",
        authority_kind="human_confirmation",
        max_risk_class="critical",
    )
    base.update(overrides)
    return policy.ExternalVerification(**base)


class AssertionCannotDischargeExternalVerificationTest(unittest.TestCase):
    ASSERTED = dict(review_satisfied=True, approval_refs=("i-said-so",))

    def test_policy_mutation_critical_is_no_longer_discharged(self):
        """DoD 1: previously allow_with_ledger on the string 'i-said-so'."""
        decision = policy.evaluate(_proposal(**self.ASSERTED))
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)
        self.assertIn("external_verification_requires_attestation", decision.reasons)
        self.assertEqual("", decision.review_discharge)

    def test_other_external_verification_outcomes_are_capped_too(self):
        """DoD 2."""
        for operation, risk in (("scope_expansion", "high"),
                                ("permanent_deletion", "critical")):
            with self.subTest(operation=operation, risk=risk):
                decision = policy.evaluate(_proposal(operation, risk, **self.ASSERTED))
                self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)

    def test_require_review_discharge_is_no_longer_asserted_either(self):
        """ADR-037 step 4b-2: expected semantic change (entry #24).

        Loop 7's DoD 3 asserted that capping external verification left the
        review-level discharges working. 4b-2 removes those too: the cap and the
        flip together mean **no** outcome is dischargeable by assertion. This
        test now records the completion of what Loop 7 started.
        """
        decision = policy.evaluate(_proposal(
            "correction", "low", review_satisfied=True, approval_refs=("approver:1",)
        ))
        self.assertEqual(policy.REQUIRE_REVIEW, decision.outcome)
        self.assertEqual("", decision.review_discharge)


class AttestedDischargeTest(unittest.TestCase):
    def test_bound_human_confirmation_discharges(self):
        """DoD 4."""
        proposal = _proposal()
        decision = policy.evaluate_with_external_verification(
            proposal, _attestation(proposal)
        )
        self.assertEqual(policy.ALLOW_WITH_LEDGER, decision.outcome)
        self.assertEqual("verified", decision.review_discharge)

    def test_unbound_attestation_is_refused(self):
        """DoD 5, 6: an attestation cannot be replayed on another proposal."""
        proposal = _proposal()
        decision = policy.evaluate_with_external_verification(
            proposal, _attestation(proposal, bound_proposal_id="some-other-proposal")
        )
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)
        self.assertIn("attestation_not_bound_to_proposal", decision.reasons)

    def test_self_verification_is_refused(self):
        """DoD 5: derived from identity, as Loop 5 did for self-approval."""
        proposal = _proposal()
        decision = policy.evaluate_with_external_verification(
            proposal, _attestation(proposal, verifier_principal_id="agent:x")
        )
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)
        self.assertIn("attestation_self_verified", decision.reasons)

    def test_delegated_policy_cannot_verify_critical_risk(self):
        """DoD 5: high and critical risk require human confirmation."""
        proposal = _proposal()
        decision = policy.evaluate_with_external_verification(
            proposal, _attestation(proposal, authority_kind="delegated_policy")
        )
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)
        self.assertIn("human_confirmation_required", decision.reasons)

    def test_risk_ceiling_is_enforced(self):
        """DoD 5."""
        proposal = _proposal()
        decision = policy.evaluate_with_external_verification(
            proposal, _attestation(proposal, max_risk_class="medium")
        )
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)
        self.assertIn("attestation_risk_ceiling_exceeded", decision.reasons)

    def test_attestation_does_not_override_a_block(self):
        """An attestation discharges review, never an absorbing block."""
        proposal = _proposal(approval_refs=("agent:x",), review_satisfied=True)
        decision = policy.evaluate_with_external_verification(
            proposal, _attestation(proposal)
        )
        self.assertEqual(policy.BLOCK, decision.outcome)


class StructuralMutationCoverageTest(unittest.TestCase):
    """DoD 8b (audit V1): this path had zero coverage before this cycle.

    `structural_mutation.evaluate_pama_v13` passes
    base_outcome=REQUIRE_EXTERNAL_VERIFICATION for high/critical risk, so the cap
    reaches it -- and no test exercised the discharge, so a green suite would
    have proved nothing about the behaviour change.
    """

    def test_evaluate_with_base_outcome_is_capped(self):
        decision = policy.evaluate_with_base_outcome(
            _proposal("domain_schema_mutation", "critical",
                      review_satisfied=True, approval_refs=("i-said-so",)),
            base_outcome=policy.REQUIRE_EXTERNAL_VERIFICATION,
        )
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)
        self.assertIn("external_verification_requires_attestation", decision.reasons)

    def test_attested_base_outcome_discharges(self):
        proposal = _proposal("domain_schema_mutation", "critical")
        decision = policy.evaluate_with_external_verification(
            proposal, _attestation(proposal),
            base_outcome=policy.REQUIRE_EXTERNAL_VERIFICATION,
        )
        self.assertEqual(policy.ALLOW_WITH_LEDGER, decision.outcome)
        self.assertEqual("verified", decision.review_discharge)


if __name__ == "__main__":
    unittest.main()
