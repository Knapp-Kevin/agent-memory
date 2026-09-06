"""ADR-037 step 4a: require_review discharges on evidence, never on assertion.

Written against the plausible wrong implementation. That one mirrors Loop 7's
base computation and lets an asserting caller through untouched, discharges any
outcome it is handed, relaxes the authority axis once the evidence axis is
satisfied, counts estimators, and records no authority at all.
"""

from __future__ import annotations

import unittest

from agentmem_ref import evidence_qualification as eq
from agentmem_ref import policy

_BASE = dict(
    charter_version="v1", target_class="semantic", scope="project",
    operation="write", current_strength=0.1, proposed_strength=0.2,
    downstream_authority=False, evidence_refs=("e1",),
)

_VERIFIERS = {"digest-check": lambda item: True}


def _proposal(risk="low", **kw):
    kwargs = dict(
        _BASE, proposal_id="prop-1", actor_id="actor-1", target_reference="memory-1",
        reversibility="reversible", risk_class=risk,
    )
    kwargs.update(kw)
    return policy.Proposal(**kwargs)


def _artifact(ref="ev-1", **kw):
    base = dict(artifact_ref="art://x", digest="sha256:abc", verifier="digest-check")
    base.update(kw)
    return eq.EvidenceItem(ref=ref, **base)


def _estimator(ref="est-1"):
    return eq.EvidenceItem(
        ref=ref, estimator_id="model-x", estimator_version="v1",
        calibration_ref="cal://2026-09",
    )


def _analysis(items, verified=False):
    return eq.group_by_dependence(items, verifiers=_VERIFIERS if verified else None)


def _attestation(pid="prop-1", principal="human-1", kind=None, ceiling="critical"):
    return policy.ExternalVerification(
        bound_proposal_id=pid, verifier_principal_id=principal,
        authority_kind=kind or policy.HUMAN_CONFIRMATION, max_risk_class=ceiling,
    )


class LowAndMediumDischargeOnEvidence(unittest.TestCase):
    """DoD 1, 1b -- LD9: the discharge IS the delegated policy."""

    def test_one_qualifying_group_discharges_at_low_and_medium(self):
        for risk in ("low", "medium"):
            proposal = _proposal(risk)
            self.assertEqual(policy.evaluate(proposal).outcome, policy.REQUIRE_REVIEW)

            decision = policy.evaluate_with_qualified_evidence(
                proposal, _analysis([_artifact()])
            )

            self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER, risk)

    def test_the_discharge_records_delegated_policy_as_its_authority(self):
        """DoD 1b / audit V3. The low/medium authority row is not vacuous."""
        for risk in ("low", "medium"):
            decision = policy.evaluate_with_qualified_evidence(
                _proposal(risk), _analysis([_artifact()])
            )
            self.assertEqual(decision.discharge_authority, policy.DELEGATED_POLICY)

    def test_the_discharged_envelope_permits_the_operation(self):
        decision = policy.evaluate_with_qualified_evidence(
            _proposal("low"), _analysis([_artifact()])
        )
        self.assertIn("write", decision.permitted_actions)
        self.assertNotIn("write", decision.prohibited_actions)


class AssertionGetsNoFreePass(unittest.TestCase):
    """DoD 7b / audit V1 -- the single defect this cycle exists to prevent."""

    def test_asserting_with_no_evidence_does_not_discharge(self):
        """The base is computed with allow_review_discharge=False.

        With Loop 7's default the caller would arrive already allow_with_ledger,
        pass the early return untouched, and never reach the ladder -- making
        4b's migration a no-op wearing the appearance of enforcement.
        """
        proposal = _proposal("low", review_satisfied=True, approval_refs=("approver-1",))
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # Loop 12 asserted here that ordinary `evaluate` still discharged this.
        # The flip removed that route, so the assertion inverts: plain evaluate
        # now refuses too. The property this test exists for is unchanged and
        # now holds on both paths.
        self.assertEqual(policy.evaluate(proposal).outcome, policy.REQUIRE_REVIEW)

        decision = policy.evaluate_with_qualified_evidence(proposal, _analysis([]))

        self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW)
        self.assertEqual(decision.discharge_authority, "")

    def test_assertion_plus_unqualified_evidence_still_does_not_discharge(self):
        proposal = _proposal("low", review_satisfied=True, approval_refs=("approver-1",))
        opinions = [eq.EvidenceItem(ref=f"opinion-{n}") for n in range(10)]

        decision = policy.evaluate_with_qualified_evidence(proposal, _analysis(opinions))

        self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW)
        self.assertIn(policy.INSUFFICIENT_EVIDENCE_CLASS, decision.reasons)

    def test_the_asserted_route_is_gone(self):
        """ADR-037 step 4b-2: expected semantic change (entry #24).

        Loop 12 asserted the asserted route still worked, because 4a was
        deliberately additive. Step 4b-2 removes it: `review_satisfied` plus
        arbitrary `approval_refs` no longer discharges `require_review`, and the
        refusal names the route out.
        """
        proposal = _proposal("low", review_satisfied=True, approval_refs=("approver-1",))
        decision = policy.evaluate(proposal)
        self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW)
        self.assertIn(policy.REVIEW_REQUIRES_QUALIFIED_EVIDENCE, decision.reasons)
        self.assertNotIn("review discharged by", " ".join(decision.reasons))


class HighAndCriticalRequireBothAxes(unittest.TestCase):
    """DoD 2, 3, 4 -- LD4. The authority axis does not relax."""

    def test_qualified_asserted_evidence_alone_does_not_discharge(self):
        for risk in ("high", "critical"):
            decision = policy.evaluate_with_qualified_evidence(
                _proposal(risk), _analysis([_artifact()])
            )
            self.assertNotEqual(decision.outcome, policy.ALLOW_WITH_LEDGER, risk)
            self.assertIn(policy.INSUFFICIENT_BINDING_STATUS, decision.reasons)

    def test_verified_evidence_without_attestation_names_the_missing_authority(self):
        for risk in ("high", "critical"):
            decision = policy.evaluate_with_qualified_evidence(
                _proposal(risk), _analysis([_artifact()], verified=True)
            )
            self.assertNotEqual(decision.outcome, policy.ALLOW_WITH_LEDGER, risk)
            self.assertIn("human_confirmation_required", decision.reasons)

    def test_attestation_without_verified_evidence_names_the_missing_binding(self):
        """DoD 4. Both axes required -- not either-or, in either direction."""
        for risk in ("high", "critical"):
            decision = policy.evaluate_with_qualified_evidence(
                _proposal(risk), _analysis([_artifact()]), attestation=_attestation()
            )
            self.assertNotEqual(decision.outcome, policy.ALLOW_WITH_LEDGER, risk)
            self.assertIn(policy.INSUFFICIENT_BINDING_STATUS, decision.reasons)

    def test_verified_evidence_plus_human_confirmation_discharges(self):
        for risk in ("high", "critical"):
            decision = policy.evaluate_with_qualified_evidence(
                _proposal(risk), _analysis([_artifact()], verified=True),
                attestation=_attestation(),
            )
            self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER, risk)
            self.assertEqual(decision.discharge_authority, policy.HUMAN_CONFIRMATION)

    def test_the_two_discharge_paths_are_distinguishable_afterwards(self):
        """DoD 1d / audit C2.

        Once 4b converts 51 sites, a decision with no authority recorded is
        indistinguishable from one that never went through the ladder.
        """
        low = policy.evaluate_with_qualified_evidence(
            _proposal("low"), _analysis([_artifact()])
        )
        high = policy.evaluate_with_qualified_evidence(
            _proposal("high"), _analysis([_artifact()], verified=True),
            attestation=_attestation(),
        )
        self.assertEqual(low.outcome, high.outcome)
        self.assertNotEqual(low.discharge_authority, high.discharge_authority)


class SeparationComesFromTheSharedEvaluator(unittest.TestCase):
    """DoD 9, 10 -- LD5. Reached, never re-derived."""

    def test_attestation_cross_checks_arrive_from_the_evaluator(self):
        decision = policy.evaluate_with_qualified_evidence(
            _proposal("high"), _analysis([_artifact()], verified=True),
            attestation=_attestation(pid="some-other-proposal"),
        )
        self.assertIn("attestation_not_bound_to_proposal", decision.reasons)
        self.assertNotEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)

    def test_self_verified_attestation_refuses(self):
        decision = policy.evaluate_with_qualified_evidence(
            _proposal("high"), _analysis([_artifact()], verified=True),
            attestation=_attestation(principal="actor-1"),
        )
        self.assertIn("attestation_self_verified", decision.reasons)

    def test_self_approval_still_refuses_with_perfect_evidence(self):
        """DoD 9. Entry #15's derived self-approval, inherited from _apply_modifiers."""
        proposal = _proposal("low", approval_refs=("actor-1",))
        decision = policy.evaluate_with_qualified_evidence(
            proposal, _analysis([_artifact()], verified=True)
        )
        self.assertEqual(decision.outcome, policy.BLOCK)
        self.assertEqual(decision.discharge_authority, "")


class TheEstimatorBarAndTheCount(unittest.TestCase):
    """DoD 5, 6 -- LD6, LD7."""

    def test_estimator_only_evidence_never_discharges(self):
        """LD6 / R3. Asserted at low risk, where the ladder is most permissive."""
        decision = policy.evaluate_with_qualified_evidence(
            _proposal("low"), _analysis([_estimator("e1"), _estimator("e2")])
        )
        self.assertNotEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertIn(policy.INSUFFICIENT_EVIDENCE_CLASS, decision.reasons)

    def test_ten_unqualified_groups_do_not_discharge(self):
        """DoD 6. Raising the count does not raise the class (section 2b)."""
        opinions = [eq.EvidenceItem(ref=f"opinion-{n}") for n in range(10)]
        analysis = _analysis(opinions)
        self.assertEqual(analysis.independent_group_count, 10)

        decision = policy.evaluate_with_qualified_evidence(_proposal("low"), analysis)

        self.assertNotEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)

    def test_one_qualifying_group_is_enough_at_low_risk(self):
        """LD7. The count is one at every risk class -- existence, not a threshold."""
        analysis = _analysis([_artifact()])
        self.assertEqual(analysis.qualifying_group_count(status=eq.ASSERTED), 1)
        decision = policy.evaluate_with_qualified_evidence(_proposal("low"), analysis)
        self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)

    def test_no_named_constant_holds_a_count(self):
        for name in dir(policy):
            if name.startswith("_"):
                continue
            value = getattr(policy, name)
            if isinstance(value, int) and not isinstance(value, bool):
                self.fail(f"policy.{name} holds an integer: {value!r}")


class NarrowByConstruction(unittest.TestCase):
    """DoD 7, 8 -- LD2. It discharges require_review and nothing else."""

    def _base_no_assertion(self, proposal):
        return policy.evaluate_with_base_outcome(
            proposal,
            base_outcome=policy._base_outcome(proposal),
            allow_review_discharge=False,
        )

    def test_other_outcomes_pass_through_unchanged(self):
        cases = [
            _proposal("low", operation="score_adjustment"),          # allow_with_ledger
            _proposal("high", reversibility="irreversible"),          # require_external
            _proposal("critical", operation="score_adjustment"),      # block
        ]
        for proposal in cases:
            expected = self._base_no_assertion(proposal)
            actual = policy.evaluate_with_qualified_evidence(
                proposal, _analysis([_artifact()], verified=True),
                attestation=_attestation(),
            )
            self.assertEqual(actual, expected, expected.outcome)

    def test_block_is_not_dischargeable_by_anything(self):
        """DoD 8. Absorbing stays absorbing."""
        proposal = _proposal("critical", operation="score_adjustment")
        self.assertEqual(policy.evaluate(proposal).outcome, policy.BLOCK)

        decision = policy.evaluate_with_qualified_evidence(
            proposal, _analysis([_artifact()], verified=True),
            attestation=_attestation(),
        )

        self.assertEqual(decision.outcome, policy.BLOCK)
        self.assertEqual(decision.discharge_authority, "")

    def test_require_external_verification_keeps_its_own_path(self):
        proposal = _proposal("high", reversibility="irreversible")
        self.assertEqual(
            policy.evaluate(proposal).outcome, policy.REQUIRE_EXTERNAL_VERIFICATION
        )
        decision = policy.evaluate_with_qualified_evidence(
            proposal, _analysis([_artifact()], verified=True)
        )
        self.assertEqual(decision.outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)


class TheLadderHasOneDefinition(unittest.TestCase):
    """DoD 12 -- LD3."""

    def test_resumption_delegates_to_policy(self):
        from agentmem_ref import resumption

        for risk in ("low", "medium", "high", "critical"):
            self.assertEqual(
                resumption.strength_for(risk), policy.strength_ladder_for(risk)
            )

    def test_both_track_a_monkeypatched_high_risk(self):
        from agentmem_ref import resumption

        original = policy._HIGH_RISK
        try:
            policy._HIGH_RISK = ("medium", "high", "critical")
            self.assertEqual(policy.strength_ladder_for("medium")["binding_status"], "verified")
            self.assertEqual(resumption.strength_for("medium")["binding_status"], "verified")
        finally:
            policy._HIGH_RISK = original

    def test_review_discharge_is_not_overloaded(self):
        """DoD 1e / audit C1. Two of the four variables stay distinct."""
        decision = policy.evaluate_with_qualified_evidence(
            _proposal("low"), _analysis([_artifact()])
        )
        self.assertEqual(decision.discharge_authority, policy.DELEGATED_POLICY)
        self.assertNotEqual(decision.review_discharge, policy.DELEGATED_POLICY)


if __name__ == "__main__":
    unittest.main()
