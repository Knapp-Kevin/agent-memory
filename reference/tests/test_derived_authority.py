"""GAP-ARCH-04 (self-approval leg): review discharge derives self-approval.

`_apply_review`'s docstring has always said "Review is satisfied by an approver,
never by the proposer." The invariant was checked -- but only against
`approves_own_authority`, a boolean the proposer sets, so nothing reached it.
"""
import unittest

from agentmem_ref import evidence_qualification as _eq


def _qualifying():
    """One qualifying independent group, for tests whose subject is not the
    discharge route itself (ADR-037 step 4b-2)."""
    return _eq.group_by_dependence([
        _eq.EvidenceItem(ref="ev-1", artifact_ref="art://x", digest="sha256:abc",
                         verifier="digest-check")
    ])

from agentmem_ref import policy


def _proposal(operation="policy_mutation", risk="critical", **overrides):
    base = dict(
        proposal_id="p", actor_id="agent:x", charter_version="v1",
        target_reference="mem:A", target_class=policy.M1, scope="t",
        operation=operation, current_strength="observed",
        proposed_strength="tentative", downstream_authority=policy.A1,
        reversibility="reversible", risk_class=risk,
        evidence_refs=("ep-1",), tenant_ref="t", isolation_domain_refs=("t",),
    )
    base.update(overrides)
    return policy.Proposal(**base)


class DerivedSelfApprovalTest(unittest.TestCase):
    def test_actor_in_its_own_approval_refs_blocks(self):
        """DoD 1: previously allow_with_ledger."""
        decision = policy.evaluate(_proposal(
            review_satisfied=True, approval_refs=("agent:x",)
        ))
        self.assertEqual(policy.BLOCK, decision.outcome)
        self.assertIn(
            "invariant 4: an actor may not approve its own authority expansion",
            decision.reasons,
        )

    def test_actor_among_several_refs_blocks(self):
        """DoD 2: hiding behind a legitimate approver does not help."""
        decision = policy.evaluate(_proposal(
            review_satisfied=True, approval_refs=("approver:1", "agent:x")
        ))
        self.assertEqual(policy.BLOCK, decision.outcome)

    def test_derivation_reaches_allow_with_ledger_outcomes(self):
        """DoD 2b (audit V1): placement in _apply_review would miss this.

        _apply_review only runs for review-requiring outcomes, so a self-
        approving proposal at a base outcome of allow_with_ledger would be
        permitted when derived and blocked when asserted. The check belongs in
        _apply_modifiers, beside the flag it generalizes.
        """
        for operation in ("runtime_assembly", "pruning", "score_adjustment"):
            with self.subTest(operation=operation):
                base = policy.evaluate(_proposal(operation, "low"))
                self.assertEqual(policy.ALLOW_WITH_LEDGER, base.outcome)
                derived = policy.evaluate(_proposal(
                    operation, "low", approval_refs=("agent:x",)
                ))
                self.assertEqual(policy.BLOCK, derived.outcome)

    def test_third_party_discharge_still_works(self):
        """DoD 3: the fix must not block legitimate review.

        AMENDED in Loop 7 (ledger Entry #17). This was Loop 5's DoD 3, cited as
        evidence in Entry #15, and it asserted that policy_mutation/critical
        discharged to allow_with_ledger on a third-party assertion. Loop 7
        deliberately removed that: external verification is no longer
        dischargeable by assertion. The test now exercises the same property --
        a third-party discharge works -- at a review-requiring outcome, which is
        what it was actually about.
        """
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # AMENDED AGAIN. The property under test is unchanged -- a legitimate
        # third party is not blocked by the derived self-approval control -- but
        # assertion no longer discharges, so it is exercised through the route
        # that now does. A third party still works; only the door moved.
        proposal = _proposal(
            "correction", "low", review_satisfied=True, approval_refs=("approver:1",)
        )
        decision = policy.evaluate_with_qualified_evidence(proposal, _qualifying())
        self.assertEqual(policy.ALLOW_WITH_LEDGER, decision.outcome)

    def test_asserted_flag_still_blocks_without_derivation(self):
        """DoD 4: non-weakening -- effective = asserted or derived."""
        decision = policy.evaluate(_proposal(
            review_satisfied=True,
            approval_refs=("approver:1",),
            approves_own_authority=True,
        ))
        self.assertEqual(policy.BLOCK, decision.outcome)

    def test_matching_is_exact_not_substring(self):
        """DoD 5: `any(actor_id in ref ...)` would block this legitimate
        discharge. A substring implementation passes DoD 1 and 2 and fails only
        here."""
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # The substring defect this test exists to catch is unaffected by the
        # flip; only the discharge route changed. A substring implementation
        # still fails here, which is the point.
        proposal = _proposal(
            "correction", "low",
            actor_id="a", review_satisfied=True, approval_refs=("grant:human",)
        )
        decision = policy.evaluate_with_qualified_evidence(proposal, _qualifying())
        self.assertEqual(policy.ALLOW_WITH_LEDGER, decision.outcome)

    def test_whitespace_around_refs_does_not_evade(self):
        decision = policy.evaluate(_proposal(
            review_satisfied=True, approval_refs=("  agent:x  ",)
        ))
        self.assertEqual(policy.BLOCK, decision.outcome)


class ReviewDischargeProvenanceTest(unittest.TestCase):
    """DoD 6: a receipt must be able to say what a discharge rested on."""

    def test_asserted_discharge_no_longer_exists(self):
        """ADR-037 step 4b-2: expected semantic change (entry #24).

        Loop 7 amended this to exercise provenance where an asserted discharge
        could still occur. 4b-2 removes the asserted route entirely, so there is
        no such place left. The subject of the original test is gone, and what
        replaces it is the assertion that it is gone: an asserted discharge
        neither happens nor is recorded.
        """
        decision = policy.evaluate(_proposal(
            "correction", "low", review_satisfied=True, approval_refs=("approver:1",)
        ))
        self.assertEqual(policy.REQUIRE_REVIEW, decision.outcome)
        self.assertNotEqual("asserted", decision.review_discharge)

    def test_qualified_discharge_records_its_authority(self):
        """The provenance property DoD 6 was written for, on the surviving route."""
        proposal = _proposal(
            "correction", "low", review_satisfied=True, approval_refs=("approver:1",)
        )
        decision = policy.evaluate_with_qualified_evidence(proposal, _qualifying())
        self.assertEqual(policy.ALLOW_WITH_LEDGER, decision.outcome)
        self.assertEqual(policy.DELEGATED_POLICY, decision.discharge_authority)

    def test_no_discharge_leaves_the_field_empty(self):
        decision = policy.evaluate(_proposal())
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)
        self.assertEqual("", decision.review_discharge)

    def test_refused_discharge_is_not_recorded_as_one(self):
        """The refusal path returns a non-empty reason list too, so detecting a
        discharge by reasons alone would misfire."""
        decision = policy.evaluate(_proposal(
            review_satisfied=True, approval_refs=()
        ))
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)
        self.assertEqual("", decision.review_discharge)

    def test_verified_is_not_produced_by_this_cycle(self):
        """LD3: "verified" is reserved for the evidence-bound discharge."""
        for refs in (("approver:1",), ("grant:human", "approver:2")):
            decision = policy.evaluate(_proposal(
                "correction", "low", review_satisfied=True, approval_refs=refs
            ))
            self.assertNotEqual("verified", decision.review_discharge)


class CrossingReachTest(unittest.TestCase):
    """DoD 2c (audit V2): crossing.py:107 calls policy.evaluate directly, so the
    derivation reaches boundary crossings. The deep audit's R3 probe recorded a
    `share` crossing committing on a self-approved proposal."""

    def _request(self):
        from agentmem_ref.crossing import CrossingRequest

        return CrossingRequest(
            operation="share",
            source_domain_refs=("tenant-a",),
            destination_domain_refs=("tenant-b",),
            actor="agent:x",
            principal="agent:x",
            purpose="security-review",
            representation_kind="summary",
            source_refs=("mem:security-summary",),
        )

    def _proposal(self, **overrides):
        base = dict(
            proposal_id="crossing-1", actor_id="agent:x",
            charter_version="charter-1", target_reference="mem:security-summary",
            target_class=policy.M4, scope="tenant-a", operation="scope_expansion",
            current_strength="crystallized", proposed_strength="crystallized",
            downstream_authority=policy.A2, reversibility="reversible",
            risk_class="medium", evidence_refs=("evidence:source-scope",),
            tenant_ref="tenant-a", purpose="security-review",
        )
        base.update(overrides)
        return policy.Proposal(**base)

    def test_self_approved_share_crossing_now_blocks(self):
        from agentmem_ref.crossing import evaluate_crossing

        result = evaluate_crossing(
            self._request(),
            self._proposal(review_satisfied=True, approval_refs=("agent:x",)),
            receipt_id="crossing:self-approved",
            timestamp="2026-08-11T20:00:00Z",
        )
        self.assertFalse(result.committed)
        self.assertEqual(policy.BLOCK, result.decision.outcome)

    def test_third_party_approved_crossing_is_unaffected(self):
        from agentmem_ref.crossing import evaluate_crossing

        result = evaluate_crossing(
            self._request(),
            self._proposal(review_satisfied=True, approval_refs=("approver:1",)),
            receipt_id="crossing:third-party",
            timestamp="2026-08-11T20:00:00Z",
        )
        self.assertNotEqual(policy.BLOCK, result.decision.outcome)


if __name__ == "__main__":
    unittest.main()
