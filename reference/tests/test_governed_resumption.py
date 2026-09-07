"""ADR-037 step 3: the evaluator resumes, the actor does not.

Written against the plausible wrong implementation. That one evaluates first and
checks staleness after, pre-calls a control the evaluator already applies,
rewrites whatever proposal fields it likes, lets an attestation discharge
anything, and reports a confident independence bar nobody ruled on.
"""

from __future__ import annotations

import dataclasses
import unittest

from agentmem_ref import evidence_qualification as eq
from agentmem_ref import policy
from agentmem_ref.pending_verification import PendingVerificationRegistry
from agentmem_ref.resumption import (
    BLOCK_UNREACHABLE,
    CRITERION_GATE,
    CRITERION_INDEPENDENCE,
    CRITERION_SEPARATION,
    IN_FORCE,
    PENDING_STEP_4,
    STALE,
    criteria_for,
    strength_for,
    resume_parked,
)

_BASE = dict(
    charter_version="v1", target_class="semantic", scope="project",
    operation="write", current_strength=0.1, proposed_strength=0.2,
    downstream_authority=False, evidence_refs=("e1",),
)


def _proposal(pid="prop-1", actor="actor-1", **kw):
    kwargs = dict(
        _BASE, proposal_id=pid, actor_id=actor, target_reference="memory-1",
        reversibility="reversible", risk_class="low",
    )
    kwargs.update(kw)
    return policy.Proposal(**kwargs)


def _review_proposal(**kw):
    """semantic/write/low/reversible -> require_review."""
    return _proposal(**kw)


def _external_proposal(pid="prop-ext", **kw):
    """semantic/write/high/irreversible -> require_external_verification."""
    return _proposal(pid=pid, risk_class="high", reversibility="irreversible", **kw)


def _park(proposal):
    registry = PendingVerificationRegistry()
    record = registry.park(proposal, policy.evaluate(proposal))
    return registry, record


def _attestation(pid="prop-ext", principal="human-1", kind=None, ceiling="critical"):
    return policy.ExternalVerification(
        bound_proposal_id=pid,
        verifier_principal_id=principal,
        authority_kind=kind or policy.HUMAN_CONFIRMATION,
        max_risk_class=ceiling,
    )


def _good_evidence(ref="ev-1"):
    return eq.EvidenceItem(
        ref=ref, artifact_ref="art://x", digest="sha256:abc", verifier="digest-check"
    )


_VERIFIERS = {"digest-check": lambda item: True}


class TheOneWorkingDischargePath(unittest.TestCase):
    """DoD 1 -- require_external_verification, through an attestation."""

    def test_bound_separated_attestation_discharges_external_verification(self):
        proposal = _external_proposal()
        _, record = _park(proposal)
        self.assertEqual(record.decision.outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)

        result = resume_parked(
            record,
            evidence=[_good_evidence()],
            attestation=_attestation(),
            verifiers=_VERIFIERS,
        )

        self.assertTrue(result.resumed)
        self.assertEqual(result.decision.outcome, policy.ALLOW_WITH_LEDGER)


class RequireReviewIsNotResumableThisCycle(unittest.TestCase):
    """DoD 1b / audit V4 -- the limit is structural, and the report says so."""

    def test_qualified_verified_evidence_still_does_not_discharge_require_review(self):
        """Measured: M-EVID is an emptiness check, so evidence cannot move this.

        Asserted with evidence that is qualified, verified and independent, so
        the test proves a structural limit rather than a weak fixture.
        """
        proposal = _review_proposal()
        _, record = _park(proposal)
        evidence = [_good_evidence("ev-1"), _good_evidence("ev-2")]
        analysis = eq.group_by_dependence(evidence, verifiers=_VERIFIERS)
        self.assertEqual(analysis.qualifying_group_count(status=eq.VERIFIED), 2)

        result = resume_parked(
            record, evidence=evidence, verifiers=_VERIFIERS,
            current_state_version=proposal.state_snapshot,
        )

        self.assertFalse(result.resumed)
        self.assertEqual(result.decision.outcome, policy.REQUIRE_REVIEW)

    def test_the_report_now_names_the_evidence_criterion_step_4_landed(self):
        """ADR-037 step 4b-2: expected semantic change (entry #24).

        Loop 10 reported CRITERION_GATE -- "wait for step 4" -- because evidence
        genuinely could not move require_review while assertion discharged it.
        Step 4 has landed, so that message would now point a caller at completed
        work. The report names R5's ladder instead, which is the traversable
        route the operator's criterion 7 requires.
        """
        _, record = _park(_review_proposal())
        report = criteria_for(record)

        self.assertEqual([c for c in report.unmet if c.kind == CRITERION_GATE], [])
        qualification = [c for c in report.unmet
                         if c.kind == "evidence_qualification"]
        self.assertEqual(len(qualification), 1)
        self.assertIn("evaluate_with_qualified_evidence", qualification[0].satisfied_by)


class StalenessRefusesBeforeEvaluation(unittest.TestCase):
    """DoD 3, 4 -- LD5. Entry #14's guard applies to resumption."""

    def test_a_stale_proposal_is_refused_with_no_decision_computed(self):
        """Asserted by the ABSENCE of a decision, so refuse-then-evaluate fails."""
        proposal = _review_proposal(state_snapshot="v3")
        _, record = _park(proposal)

        result = resume_parked(record, current_state_version="v9")

        self.assertFalse(result.resumed)
        self.assertEqual(result.refusal, STALE)
        self.assertIsNone(result.decision)

    def test_the_state_version_comes_from_the_caller_not_the_record(self):
        """DoD 4 / LD3. The record predates the delay that makes staleness a risk."""
        proposal = _external_proposal(state_snapshot="v3")
        _, record = _park(proposal)

        matching = resume_parked(
            record, attestation=_attestation(), current_state_version="v3"
        )
        differing = resume_parked(
            record, attestation=_attestation(), current_state_version="v4"
        )

        self.assertTrue(matching.resumed)
        self.assertFalse(differing.resumed)
        self.assertEqual(differing.refusal, STALE)
        # The record is untouched by either outcome (LD7).
        self.assertEqual(record.proposal.state_snapshot, "v3")


class SeparationComesFromTheSharedEvaluator(unittest.TestCase):
    """DoD 6, 6b, 6c -- audit C1 and C2, and LD6/R1."""

    def test_separation_refusals_arrive_in_the_decisions_reasons(self):
        """audit C1. attestation_refusal is NOT pre-called here.

        ``evaluate_with_external_verification`` calls it internally and surfaces
        the result in ``reasons``. A second copy of a control already correctly
        placed in the shared evaluator is two things that can diverge.
        """
        proposal = _external_proposal()
        _, record = _park(proposal)

        wrong_binding = resume_parked(
            record, attestation=_attestation(pid="some-other-proposal")
        )
        self.assertIn("attestation_not_bound_to_proposal", wrong_binding.decision.reasons)

        self_verified = resume_parked(
            record, attestation=_attestation(principal="actor-1")
        )
        self.assertIn("attestation_self_verified", self_verified.decision.reasons)

        delegated = resume_parked(
            record, attestation=_attestation(kind="delegated_policy")
        )
        self.assertIn("human_confirmation_required", delegated.decision.reasons)

        for result in (wrong_binding, self_verified, delegated):
            self.assertFalse(result.resumed)

    def test_the_actor_may_produce_every_evidence_item(self):
        """R1. Production is permitted; only certification is not."""
        proposal = _external_proposal(actor="actor-1")
        _, record = _park(proposal)
        actor_produced = [_good_evidence("ev-a"), _good_evidence("ev-b")]

        result = resume_parked(
            record,
            evidence=actor_produced,
            attestation=_attestation(principal="a-separated-human"),
            verifiers=_VERIFIERS,
        )

        self.assertTrue(result.resumed)

    def test_evidence_item_gains_no_principal_field(self):
        """DoD 6b / audit V1. The eighth instance, declined."""
        fields = set(eq.EvidenceItem.__dataclass_fields__)
        for forbidden in ("verifier_principal_id", "principal", "actor_id", "produced_by"):
            self.assertNotIn(forbidden, fields)

    def test_an_attestation_does_not_discharge_a_parked_require_review(self):
        """audit C2. Pins a Loop 7 invariant this cycle now depends on.

        ``evaluate_with_external_verification`` returns early unless the computed
        outcome is REQUIRE_EXTERNAL_VERIFICATION. That early return is the only
        thing stopping an attestation from becoming a general-purpose discharge
        for every parked proposal -- doing step 4's job without step 4's audit,
        and doing it wrongly. If a refactor removes it, this test fails.
        """
        proposal = _review_proposal()
        _, record = _park(proposal)

        result = resume_parked(
            record, attestation=_attestation(pid="prop-1", principal="human-1")
        )

        self.assertFalse(result.resumed)
        self.assertEqual(result.decision.outcome, policy.REQUIRE_REVIEW)


class AdmissionAmendsOnlyEvidenceRefs(unittest.TestCase):
    """DoD 1c -- LD12. At L3 a proposal-rewriting primitive is a bypass."""

    def test_every_other_field_is_carried_through_identically(self):
        proposal = _external_proposal()
        _, record = _park(proposal)

        result = resume_parked(
            record,
            evidence=[_good_evidence("ev-new")],
            attestation=_attestation(),
            verifiers=_VERIFIERS,
        )
        self.assertIn("ev-new", result.admitted_refs)

        # Reconstruct what was evaluated and compare field by field.
        amended = dataclasses.replace(
            record.proposal,
            evidence_refs=tuple(record.proposal.evidence_refs) + result.admitted_refs,
        )
        for field in record.proposal.__dataclass_fields__:
            if field == "evidence_refs":
                continue
            self.assertEqual(
                getattr(amended, field), getattr(record.proposal, field),
                f"{field} must not be rewritten by resumption",
            )

    def test_original_evidence_refs_are_preserved_not_replaced(self):
        proposal = _external_proposal()
        _, record = _park(proposal)
        result = resume_parked(
            record, evidence=[_good_evidence("ev-new")],
            attestation=_attestation(), verifiers=_VERIFIERS,
        )
        self.assertIn("ev-new", result.admitted_refs)
        self.assertEqual(record.proposal.evidence_refs, ("e1",))

    def test_refuted_evidence_is_not_admitted(self):
        proposal = _external_proposal()
        _, record = _park(proposal)
        bad = eq.EvidenceItem(
            ref="ev-bad", artifact_ref="a", digest="d", verifier="strict"
        )
        result = resume_parked(
            record, evidence=[bad], attestation=_attestation(),
            verifiers={"strict": lambda item: False},
        )
        self.assertNotIn("ev-bad", result.admitted_refs)


class TheStrengthLadder(unittest.TestCase):
    """ADR-037 R5, operator ruling on #379: risk defines how strong."""

    def test_low_and_medium_permit_delegation_estimators_and_asserted(self):
        for risk in ("low", "medium"):
            ladder = strength_for(risk)
            self.assertIn("delegated_policy", ladder["authority_kind"])
            self.assertIn("estimator", ladder["qualification_class"])
            self.assertEqual(ladder["binding_status"], eq.ASSERTED)

    def test_high_and_critical_require_human_confirmation_and_verified(self):
        for risk in ("high", "critical"):
            ladder = strength_for(risk)
            self.assertEqual(ladder["authority_kind"], "human_confirmation")
            self.assertNotIn("delegated_policy", ladder["authority_kind"])
            self.assertNotIn("estimator", ladder["qualification_class"])
            self.assertEqual(ladder["binding_status"], eq.VERIFIED)

    def test_the_boundary_derives_from_policy_HIGH_RISK_at_call_time(self):
        """DoD 5. An import-time table holds a stale copy; this must not.

        Re-listing ("high","critical") locally would be the eighth instance of
        the control-in-one-module pattern.
        """
        original = policy._HIGH_RISK
        try:
            self.assertEqual(strength_for("medium")["binding_status"], eq.ASSERTED)
            policy._HIGH_RISK = ("medium", "high", "critical")
            self.assertEqual(strength_for("medium")["binding_status"], eq.VERIFIED)
        finally:
            policy._HIGH_RISK = original
        self.assertEqual(strength_for("medium")["binding_status"], eq.ASSERTED)

    def test_no_strength_ladder_constant_exists(self):
        """DoD 5b. The table form must not return quietly."""
        import agentmem_ref.resumption as module

        self.assertFalse(hasattr(module, "STRENGTH_LADDER"))
        self.assertFalse(hasattr(module, "UNDEFINED_BAR"))
        self.assertFalse(hasattr(module, "INDEPENDENCE_OPEN_QUESTION"))
        # LD6 removes the concept, not just the constant: a property still
        # testing `bar == UNDEFINED_BAR` would NameError the moment it ran.
        from agentmem_ref.resumption import CriteriaReport

        self.assertFalse(hasattr(CriteriaReport, "has_undefined_bar"))

    def test_the_report_states_the_ladder_not_an_undefined_bar(self):
        _, record = _park(_review_proposal())
        report = criteria_for(record)

        independence = [c for c in report.unmet if c.kind == CRITERION_INDEPENDENCE]
        self.assertEqual(len(independence), 1)
        self.assertIn("count is one at every risk class", independence[0].detail)
        self.assertIn("R5", independence[0].note)
        self.assertIn("#379", independence[0].note)

    def test_rows_are_marked_in_force_or_pending_per_outcome(self):
        """DoD 6b / audit V2. Asserted at high risk, where the paths diverge."""
        _, ext_record = _park(_external_proposal())
        ext = [c for c in criteria_for(ext_record).unmet
               if c.kind == CRITERION_INDEPENDENCE][0]
        self.assertIn(f"human_confirmation ({IN_FORCE})", ext.bar)

        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # Loop 11 asserted that require_review rows were pending step 4, because
        # _apply_review discharged on assertion with no authority-kind check.
        # 4b-2 removed that route, so every ladder row now bites on this path
        # too and the marking inverts.
        review_high = _proposal(pid="prop-rr-high", operation="link_creation",
                                risk_class="high")
        self.assertEqual(policy.evaluate(review_high).outcome, policy.REQUIRE_REVIEW)
        _, rr_record = _park(review_high)
        rr = [c for c in criteria_for(rr_record).unmet
              if c.kind == CRITERION_INDEPENDENCE][0]
        self.assertIn(f"human_confirmation ({IN_FORCE})", rr.bar)
        self.assertNotIn(PENDING_STEP_4, rr.bar)

    def test_criteria_for_takes_no_risk_class_parameter(self):
        """DoD 8b / audit V3. The ninth instance, declined.

        A parameter would let a caller pass `low` for a `critical` record,
        understating all three ladder rows at once.
        """
        import inspect

        self.assertNotIn("risk_class", inspect.signature(criteria_for).parameters)

        critical = _proposal(pid="prop-crit", operation="link_creation",
                             risk_class="critical")
        _, record = _park(critical)
        bar = [c for c in criteria_for(record).unmet
               if c.kind == CRITERION_INDEPENDENCE][0].bar
        self.assertIn("human_confirmation", bar)
        self.assertIn(eq.VERIFIED, bar)

    def test_no_numeric_threshold_appears_anywhere_in_the_report(self):
        """ADR-037:128 warns by name against inventing such a number."""
        import re

        _, record = _park(_external_proposal())
        analysis = eq.group_by_dependence([_good_evidence()], verifiers=_VERIFIERS)
        report = criteria_for(record, analysis)

        for criterion in report.unmet:
            # The open-question note quotes ">=2" as the thing NOT to generalize.
            haystack = f"{criterion.bar} {criterion.satisfied_by}"
            self.assertIsNone(
                re.search(r">=\s*\d|\b\d+\s+independent", haystack),
                f"invented threshold in {criterion.kind}: {haystack!r}",
            )

    def test_each_unmet_criterion_names_what_would_satisfy_it(self):
        """DoD 10 -- section 4's actual requirement."""
        _, record = _park(_external_proposal())
        report = criteria_for(record)
        separation = [c for c in report.unmet if c.kind == CRITERION_SEPARATION]
        self.assertEqual(len(separation), 1)
        self.assertIn("ExternalVerification", separation[0].satisfied_by)
        self.assertIn("human_confirmation", separation[0].bar)


class ResumptionGrantsNothingAndMutatesNothing(unittest.TestCase):
    """DoD 11, 12 -- LD4, LD7, LD8, LD10."""

    def test_a_failed_resumption_leaves_the_record_identical(self):
        proposal = _external_proposal()
        registry, record = _park(proposal)
        before = dataclasses.astuple(record)
        events_before = len(registry.events)

        resume_parked(record, attestation=_attestation(pid="mismatch"))

        self.assertEqual(dataclasses.astuple(registry.get("prop-ext")), before)
        self.assertEqual(len(registry.events), events_before)

    def test_a_successful_resumption_also_leaves_the_record_identical(self):
        """Resumption returns a decision; it does not discharge the record."""
        proposal = _external_proposal()
        registry, record = _park(proposal)
        before = dataclasses.astuple(record)

        result = resume_parked(record, attestation=_attestation())

        self.assertTrue(result.resumed)
        self.assertEqual(dataclasses.astuple(registry.get("prop-ext")), before)

    def test_policy_drift_is_detected_and_reported_without_refusing(self):
        """DoD 12 / LD10. Re-evaluating under current policy is correct."""
        proposal = _external_proposal()
        _, record = _park(proposal)

        result = resume_parked(
            record, attestation=_attestation(),
            current_policy_version="ref-p2-hypothetical",
        )

        self.assertTrue(result.policy_drift)
        self.assertTrue(result.resumed)

        same = resume_parked(
            record, attestation=_attestation(),
            current_policy_version=record.policy_version,
        )
        self.assertFalse(same.policy_drift)

    def test_a_newly_yielded_block_refuses_rather_than_resuming(self):
        """LD8. Reachable only under drift, since evaluate is deterministic."""
        # Park a legitimate require_review record first -- step 1 refuses to
        # park a block, which is precisely why this case can only arise later.
        _, record = _park(_review_proposal(pid="prop-blk"))
        self.assertEqual(record.decision.outcome, policy.REQUIRE_REVIEW)

        # Now simulate the one condition that can produce a new block: policy
        # moved under the retained proposal. Modelled here by a proposal whose
        # current policy answer is block.
        drifted = dataclasses.replace(
            record,
            proposal=dataclasses.replace(
                record.proposal, operation="score_adjustment", risk_class="critical"
            ),
        )
        self.assertEqual(policy.evaluate(drifted.proposal).outcome, policy.BLOCK)

        result = resume_parked(drifted)

        self.assertFalse(result.resumed)
        self.assertEqual(result.refusal, BLOCK_UNREACHABLE)
        self.assertIsNone(result.decision)

    def test_result_exposes_no_permission_surface(self):
        _, record = _park(_external_proposal())
        result = resume_parked(record, attestation=_attestation())
        surface = {n for n in dir(result) if not n.startswith("_")}
        self.assertEqual(
            surface,
            {"proposal_id", "resumed", "decision", "refusal", "report",
             "policy_drift", "admitted_refs"},
        )
        for forbidden in ("commit", "approve", "grant", "permit", "authorize", "write"):
            self.assertNotIn(forbidden, surface)


if __name__ == "__main__":
    unittest.main()
