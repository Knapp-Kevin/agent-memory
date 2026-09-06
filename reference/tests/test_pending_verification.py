"""ADR-037 step 1: a refusal is parked with its route, and nothing more.

These tests are written against the plausible *wrong* implementation as much as
the intended one. The wrong implementation parks anything that is not an allow,
hardcodes ``enter_pending_verification`` as "the" remediation route, and grows a
``resume`` stub because the lifecycle felt incomplete without one. Each of those
has a test here that fails.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from agentmem_ref import policy, receipts
from agentmem_ref.pending_verification import (
    EVENT_TYPE,
    PARKABLE,
    ParkedProposal,
    PendingVerificationRegistry,
)

_BASE = dict(
    charter_version="v1",
    target_class="semantic",
    scope="project",
    operation="write",
    current_strength=0.1,
    proposed_strength=0.2,
    downstream_authority=False,
    evidence_refs=("evidence-1",),
)


def _proposal(proposal_id: str, **overrides) -> policy.Proposal:
    kwargs = dict(
        _BASE,
        proposal_id=proposal_id,
        actor_id="actor-1",
        target_reference="memory-1",
        reversibility="reversible",
        risk_class="low",
    )
    kwargs.update(overrides)
    return policy.Proposal(**kwargs)


def _review_proposal(proposal_id: str = "prop-review", **overrides) -> policy.Proposal:
    """semantic/write/low/reversible -> require_review (measured, not assumed)."""
    return _proposal(proposal_id, **overrides)


def _external_proposal(proposal_id: str = "prop-external") -> policy.Proposal:
    """semantic/write/high/irreversible -> require_external_verification."""
    return _proposal(proposal_id, risk_class="high", reversibility="irreversible")


def _fixed_clock():
    return lambda: datetime(2026, 9, 4, 23, 59, 0, tzinfo=timezone.utc)


class ParkedRecordShape(unittest.TestCase):
    """DoD 1, 1b, 1c -- the record must be able to carry step 3."""

    def test_park_records_the_decision_and_its_identity(self):
        proposal = _review_proposal()
        decision = policy.evaluate(proposal)
        registry = PendingVerificationRegistry(now=_fixed_clock())

        record = registry.park(proposal, decision, correlation_id="corr-1")

        self.assertEqual(record.proposal, proposal)
        self.assertEqual(record.decision, decision)
        self.assertEqual(record.correlation_id, "corr-1")
        self.assertEqual(record.policy_version, decision.policy_version)
        self.assertEqual(record.parked_at, "2026-09-04T23:59:00Z")
        self.assertEqual(registry.get("prop-review"), record)

    def test_retained_proposal_is_sufficient_to_re_evaluate(self):
        """DoD 1b. This is the whole reason the record holds a Proposal.

        An identity-summary record -- proposal_id, actor_id, target_reference,
        operation, risk_class -- cannot reach ``policy.evaluate`` at all, so
        step 3 would have had to reshape the record. Asserting re-evaluation
        here is what stops that from being discovered two cycles later.
        """
        proposal = _review_proposal()
        decision = policy.evaluate(proposal)
        registry = PendingVerificationRegistry()

        record = registry.park(proposal, decision)

        self.assertEqual(policy.evaluate(record.proposal), record.decision)

    def test_retained_proposal_carries_the_staleness_anchor(self):
        """DoD 1c. Resumption must be able to tell whether the world moved."""
        proposal = _review_proposal(state_snapshot="state-v7")
        registry = PendingVerificationRegistry()

        record = registry.park(proposal, policy.evaluate(proposal))

        self.assertEqual(record.proposal.state_snapshot, "state-v7")


class RemediationRouteIsTakenNotRestated(unittest.TestCase):
    """DoD 2 and 6 -- the route differs by outcome and comes from the decision."""

    def test_review_route_is_enter_pending_verification(self):
        proposal = _review_proposal()
        decision = policy.evaluate(proposal)
        self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW)

        record = PendingVerificationRegistry().park(proposal, decision)

        self.assertEqual(record.permitted_actions, decision.permitted_actions)
        self.assertEqual(
            record.permitted_actions,
            ("enter_pending_verification", "collect_more_evidence", "defer"),
        )

    def test_external_verification_route_is_a_different_route(self):
        """The route is ``request_external_verification``, NOT parking's own name.

        An implementation that hardcodes ``enter_pending_verification`` to make
        the review case pass fails here. That hardcoding is the caller-asserted
        input defect this program has now found four times.
        """
        proposal = _external_proposal()
        decision = policy.evaluate(proposal)
        self.assertEqual(decision.outcome, policy.REQUIRE_EXTERNAL_VERIFICATION)

        record = PendingVerificationRegistry().park(proposal, decision)

        self.assertEqual(record.permitted_actions, decision.permitted_actions)
        self.assertEqual(
            record.permitted_actions,
            ("request_external_verification", "collect_more_evidence", "defer"),
        )
        self.assertNotIn("enter_pending_verification", record.permitted_actions)

    def test_both_parkable_outcomes_park(self):
        registry = PendingVerificationRegistry()
        for proposal in (_review_proposal(), _external_proposal()):
            decision = policy.evaluate(proposal)
            self.assertIn(decision.outcome, PARKABLE)
            registry.park(proposal, decision)
        self.assertEqual(len(registry.parked()), 2)


class ParkingEmitsEvidence(unittest.TestCase):
    """DoD 3 -- schema-valid, and the modeled fields get their modeled home."""

    def test_exactly_one_schema_valid_event_per_park(self):
        proposal = _review_proposal()
        registry = PendingVerificationRegistry(now=_fixed_clock())

        registry.park(proposal, policy.evaluate(proposal), correlation_id="corr-9")

        self.assertEqual(len(registry.events), 1)
        event = registry.events[0]
        receipts.validate("memory-audit-event.schema.json", event)
        self.assertEqual(event["event_type"], EVENT_TYPE)
        self.assertEqual(event["event_type"], "memory.pending_verification")

    def test_modeled_governance_fields_are_top_level_not_payload(self):
        """Audit condition C1.

        Putting ``correlation_id`` in ``payload`` validates against the schema
        and is still wrong: it becomes invisible to any consumer joining on the
        modeled field, defeating the reason the record carries it. Asserting
        absence from ``payload`` is what makes a regression fail rather than
        silently degrade the evidence.
        """
        proposal = _review_proposal(state_snapshot="state-v3")
        registry = PendingVerificationRegistry()

        registry.park(proposal, policy.evaluate(proposal), correlation_id="corr-3")
        event = registry.events[0]

        self.assertEqual(event["correlation_id"], "corr-3")
        self.assertEqual(event["policy_version"], policy.evaluate(proposal).policy_version)
        self.assertEqual(event["state_snapshot"], "state-v3")
        self.assertEqual(event["actor"], "actor-1")
        self.assertEqual(event["memory_id"], "memory-1")

        for modeled in ("correlation_id", "policy_version", "state_snapshot", "actor"):
            self.assertNotIn(modeled, event["payload"], f"{modeled} belongs top-level")

    def test_payload_carries_the_detail_the_schema_does_not_model(self):
        proposal = _review_proposal()
        registry = PendingVerificationRegistry()
        decision = policy.evaluate(proposal)

        registry.park(proposal, decision)
        payload = registry.events[0]["payload"]

        self.assertEqual(payload["proposal_id"], "prop-review")
        self.assertEqual(payload["outcome"], policy.REQUIRE_REVIEW)
        self.assertEqual(payload["permitted_actions"], list(decision.permitted_actions))
        self.assertEqual(payload["prohibited_actions"], list(decision.prohibited_actions))
        self.assertIn("parked_at", payload)

    def test_correlation_id_defaults_to_the_proposal_id(self):
        proposal = _review_proposal()
        registry = PendingVerificationRegistry()

        record = registry.park(proposal, policy.evaluate(proposal))

        self.assertEqual(record.correlation_id, "prop-review")


class ParkRefusals(unittest.TestCase):
    """DoD 4, 5, 7 -- what must not be parked, and why."""

    def test_duplicate_park_raises_and_leaves_the_first_record_intact(self):
        proposal = _review_proposal()
        decision = policy.evaluate(proposal)
        registry = PendingVerificationRegistry(now=_fixed_clock())
        first = registry.park(proposal, decision, correlation_id="first")

        with self.assertRaises(ValueError) as ctx:
            registry.park(proposal, decision, correlation_id="second")

        self.assertIn("already parked", str(ctx.exception))
        self.assertEqual(registry.get("prop-review"), first)
        self.assertEqual(registry.get("prop-review").correlation_id, "first")
        self.assertEqual(len(registry.events), 1)

    def test_permitted_outcomes_cannot_be_parked(self):
        """A permitted proposal has nothing to remediate."""
        proposal = _proposal("prop-allow", operation="score_adjustment")
        decision = policy.evaluate(proposal)
        self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)
        registry = PendingVerificationRegistry()

        with self.assertRaises(ValueError) as ctx:
            registry.park(proposal, decision)

        self.assertIn("permitted the operation", str(ctx.exception))
        self.assertEqual(registry.parked(), ())
        self.assertEqual(registry.events, [])

    def test_plain_allow_cannot_be_parked(self):
        proposal = _review_proposal("prop-plain-allow")
        allowed = policy.Decision(
            outcome=policy.ALLOW,
            permitted_actions=("write", "collect_more_evidence", "defer"),
            prohibited_actions=(),
            reasons=(),
            policy_version="ref-p1",
        )
        registry = PendingVerificationRegistry()

        with self.assertRaises(ValueError):
            registry.park(proposal, allowed)

        self.assertEqual(registry.parked(), ())

    def test_block_cannot_be_parked_because_its_envelope_prohibits_it(self):
        """DoD 7 / audit V2.

        ``_envelope`` names ``enter_pending_verification`` in the *prohibited*
        set for ``block``. Parking one would contradict the very envelope the
        record preserves, and would create a record that can never resume,
        because no evidence discharges an absorbing block -- permanent parked
        residue charged against retention (#363).
        """
        proposal = _proposal(
            "prop-block", operation="score_adjustment", risk_class="critical"
        )
        decision = policy.evaluate(proposal)
        self.assertEqual(decision.outcome, policy.BLOCK)
        self.assertIn("enter_pending_verification", decision.prohibited_actions)
        self.assertEqual(decision.permitted_actions, ())
        registry = PendingVerificationRegistry()

        with self.assertRaises(ValueError) as ctx:
            registry.park(proposal, decision)

        message = str(ctx.exception)
        self.assertIn("prohibited", message)
        self.assertIn("can never be resumed", message)
        self.assertEqual(registry.parked(), ())
        self.assertEqual(registry.events, [])

    def test_parkable_set_matches_the_outcomes_with_a_route(self):
        self.assertEqual(
            PARKABLE, (policy.REQUIRE_REVIEW, policy.REQUIRE_EXTERNAL_VERIFICATION)
        )


class ParkedProposalCarriesNoAuthority(unittest.TestCase):
    """DoD 8, 9 -- LD6. Step 3 must not arrive by accident."""

    _FORBIDDEN = (
        "resume",
        "discharge",
        "approve",
        "commit",
        "unpark",
        "release",
        "grant",
        "permit",
        "authorize",
        "satisfy",
        "verify",
    )

    def test_registry_surface_is_park_get_parked_resume_events(self):
        """DECLARED AMENDMENT (Loop 10, entry #20).

        Loop 8 asserted `resume` was absent, which was correct then: step 3 was
        gated on step 2 existing. Step 3 has landed, so `resume` is now part of
        the surface and the assertion inverts. Everything else in the forbidden
        list still holds -- resumption returns a re-evaluation, not a
        permission, so no `discharge`, `approve` or `permit` appears.
        """
        surface = {n for n in dir(PendingVerificationRegistry()) if not n.startswith("_")}
        self.assertEqual(surface, {"park", "get", "parked", "resume", "events"})
        for forbidden in self._FORBIDDEN:
            if forbidden == "resume":
                continue
            self.assertNotIn(forbidden, surface)

    def test_resume_exists_on_the_registry_and_never_on_the_record(self):
        """DECLARED AMENDMENT (Loop 10, entry #20).

        Loop 8 asserted `resume` was absent entirely. Step 3 has landed, so the
        registry now has it -- and the half of the original assertion that
        still matters holds unchanged: **`ParkedProposal` must never grow one.**
        Resumption is an evaluator operation (ADR-037 section 3); a `resume` on
        the record itself would put the transition in the hands of whoever holds
        the record, which is how a parked proposal becomes a standing authority.
        """
        self.assertTrue(hasattr(PendingVerificationRegistry, "resume"))
        self.assertFalse(hasattr(ParkedProposal, "resume"))

    def test_resuming_an_unparked_proposal_refuses(self):
        from agentmem_ref.resumption import NOT_PARKED

        result = PendingVerificationRegistry().resume("never-parked")
        self.assertFalse(result.resumed)
        self.assertEqual(result.refusal, NOT_PARKED)

    def test_parked_record_exposes_no_mutator(self):
        proposal = _review_proposal()
        record = PendingVerificationRegistry().park(proposal, policy.evaluate(proposal))
        surface = {n for n in dir(record) if not n.startswith("_")}
        self.assertEqual(
            surface,
            {"proposal", "decision", "correlation_id", "parked_at",
             "policy_version", "proposal_id", "permitted_actions"},
        )
        for forbidden in self._FORBIDDEN:
            self.assertNotIn(forbidden, surface)

    def test_parked_record_is_frozen(self):
        proposal = _review_proposal()
        record = PendingVerificationRegistry().park(proposal, policy.evaluate(proposal))
        with self.assertRaises(Exception):
            record.decision = policy.evaluate(_external_proposal())

    def test_reading_a_parked_record_does_not_discharge_it(self):
        proposal = _review_proposal()
        registry = PendingVerificationRegistry()
        registry.park(proposal, policy.evaluate(proposal))

        registry.get("prop-review")
        registry.parked()

        self.assertEqual(len(registry.parked()), 1)
        self.assertEqual(len(registry.events), 1)
        self.assertEqual(
            registry.get("prop-review").decision.outcome, policy.REQUIRE_REVIEW
        )


if __name__ == "__main__":
    unittest.main()
