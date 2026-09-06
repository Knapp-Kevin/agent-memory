"""ADR-037 step 4b-2: require_review fails closed.

`review_satisfied=True` plus arbitrary `approval_refs` no longer discharges
`require_review`. Callers with qualifying evidence cross; callers without it
park, with a traversable remediation path.

The most important class here is `TheLaunderingTest`. It is the question the
operator posed as the one that decides whether the evidence pattern is sound:

    Can a malicious caller create both the proposal and a matching fixture,
    after deciding what it wants, and satisfy the verifier?

If that ever passes, the pattern is laundering and the cycle failed regardless
of what else is green.
"""

from __future__ import annotations

import unittest

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter
from agentmem_ref.pending_verification import PendingVerificationRegistry
from agentmem_ref.resumption import criteria_for
from agentmem_ref.substrate import InMemoryTemporalGraph
from agentmem_ref.verification import (
    TRANSITION_VERIFIER,
    TransitionRule,
    TransitionRuleCorpus,
    VerifierRegistry,
)
from tests.qualified_fixtures import corpus_for, governed_adapter, rule

TENANT = "tenant-a"
MEMORY = "mem:flip"


def _proposal(pid="prop-1", *, operation="correction", risk="low", asserted=True,
              state_snapshot="v0"):
    """Note: `state_snapshot` is the adapter's state VERSION, which is a
    different thing from a transition rule's pre-state (a value). Conflating
    them makes every commit look stale."""
    return policy.Proposal(
        proposal_id=pid, actor_id="agent:planner", charter_version="charter-1",
        target_reference=MEMORY, target_class=policy.M2, scope=TENANT,
        operation=operation, current_strength="reinforced",
        proposed_strength="promoted", downstream_authority=policy.A1,
        reversibility="reversible", risk_class=risk,
        evidence_refs=("ev:1",), tenant_ref=TENANT,
        approval_refs=("approval:owner",) if asserted else (),
        review_satisfied=asserted, state_snapshot=state_snapshot,
    )


def _corpus():
    return corpus_for(rule(
        rule_id="rule:flip", target=MEMORY, criterion="value-correction",
        from_state="value-a", to_values=("value-b",),
    ))


class AssertionNoLongerDischarges(unittest.TestCase):
    """Acceptance criterion 1."""

    def test_review_satisfied_plus_arbitrary_approval_refs_is_refused(self):
        for risk in ("low", "medium"):
            decision = policy.evaluate(_proposal(risk=risk))
            self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW, risk)
            self.assertIn(policy.REVIEW_REQUIRES_QUALIFIED_EVIDENCE, decision.reasons)

    def test_the_refusal_names_the_route_out(self):
        """Criterion 7: a refusal that names nothing is a dead end."""
        decision = policy.evaluate(_proposal())
        self.assertTrue(decision.reasons)
        record = PendingVerificationRegistry().park(_proposal(), decision)
        report = criteria_for(record)
        self.assertTrue(report.unmet)
        self.assertTrue(any("evaluate_with_qualified_evidence" in c.satisfied_by
                            for c in report.unmet))


class TheLaunderingTest(unittest.TestCase):
    """Criterion: the question that decides whether the pattern is sound.

    A caller that fabricates both the proposal and a matching rule, after
    choosing its desired outcome, must not satisfy the verifier.
    """

    def test_a_caller_authored_rule_does_not_verify(self):
        substrate = InMemoryTemporalGraph()
        # The evaluator's corpus knows nothing about `mem:attacker`.
        adapter = governed_adapter(substrate, TENANT, Clock(), _corpus())

        # The attacker decides what it wants, then writes a rule that permits
        # exactly that, and cites it. The evidence is perfectly well-formed.
        attacker_corpus = TransitionRuleCorpus((TransitionRule(
            rule_id="rule:attacker-authored",
            target_reference=MEMORY,
            criterion="value-correction",
            from_state="value-a",
            permitted_to_values=("whatever-i-want",),
        ),))
        forged = attacker_corpus.evidence_for(
            target_reference=MEMORY, criterion="value-correction",
            pre_state="value-a", proposed_value="whatever-i-want",
        )
        self.assertTrue(forged, "the attacker's evidence is well-formed")

        result = adapter.commit_proposal(
            _proposal("prop-attack"), "whatever-i-want", evidence=forged
        )

        # The adapter resolves verifiers from the registry ITS HOST configured.
        # The attacker's rule is not in that corpus, so the adjudicator refutes
        # it and the proposal parks.
        self.assertFalse(result.committed)

    def test_a_rule_the_evaluator_does_not_hold_verifies_nothing(self):
        corpus = _corpus()
        registry = VerifierRegistry()
        registry.register(TRANSITION_VERIFIER, corpus.verifier())

        foreign = TransitionRuleCorpus((TransitionRule(
            rule_id="rule:not-held", target_reference=MEMORY,
            criterion="value-correction", from_state="value-a",
            permitted_to_values=("value-b",),
        ),))
        (item,) = foreign.evidence_for(
            target_reference=MEMORY, criterion="value-correction",
            pre_state="value-a", proposed_value="value-b",
        )

        from agentmem_ref import evidence_qualification as eq

        self.assertEqual(
            eq.qualify(item, verifiers=registry.as_mapping()).binding_status,
            eq.REFUTED,
        )

    def test_a_forged_result_field_does_not_verify(self):
        """The adjudicator RE-RUNS the rule; it does not trust the claim.

        Found by adversarial pass A3: removing the `rule.admits(...)` re-check
        left the suite green, because every other test produced its `result`
        field honestly. That made the re-check the only thing standing between a
        forged `result="admitted"` and a verified item -- with nothing asserting
        it. This is that assertion.

        The item below cites a rule the evaluator genuinely holds, is
        well-formed, and claims a transition the rule does not admit.
        """
        from agentmem_ref import evidence_qualification as eq

        corpus = _corpus()
        registry = VerifierRegistry()
        registry.register(TRANSITION_VERIFIER, corpus.verifier())

        forged = eq.EvidenceItem(
            ref="rule:flip",
            inputs=f"{MEMORY}@value-a->value-i-want",
            method="rule:flip",              # a rule the evaluator DOES hold
            method_version="1",
            result="admitted",               # ...and a claim it does not support
            verifier=TRANSITION_VERIFIER,
            failure_domain="transition-rule:rule:flip",
        )

        self.assertEqual(
            eq.qualify(forged, verifiers=registry.as_mapping()).binding_status,
            eq.REFUTED,
        )

    def test_a_forged_pre_state_does_not_verify(self):
        """Same shape, on the other input the rule binds."""
        from agentmem_ref import evidence_qualification as eq

        corpus = _corpus()
        registry = VerifierRegistry()
        registry.register(TRANSITION_VERIFIER, corpus.verifier())

        forged = eq.EvidenceItem(
            ref="rule:flip",
            inputs=f"{MEMORY}@value-whatever->value-b",
            method="rule:flip", method_version="1", result="admitted",
            verifier=TRANSITION_VERIFIER,
            failure_domain="transition-rule:rule:flip",
        )

        self.assertEqual(
            eq.qualify(forged, verifiers=registry.as_mapping()).binding_status,
            eq.REFUTED,
        )

    def test_the_evaluators_own_rule_does_verify(self):
        """The control: the mechanism works when the rule is genuinely held."""
        corpus = _corpus()
        registry = VerifierRegistry()
        registry.register(TRANSITION_VERIFIER, corpus.verifier())
        (item,) = corpus.evidence_for(
            target_reference=MEMORY, criterion="value-correction",
            pre_state="value-a", proposed_value="value-b",
        )

        from agentmem_ref import evidence_qualification as eq

        self.assertEqual(
            eq.qualify(item, verifiers=registry.as_mapping()).binding_status,
            eq.VERIFIED,
        )


class TheRuleAdjudicatesRatherThanDescribes(unittest.TestCase):
    """DoD 18. The properties that separate adjudication from description."""

    def setUp(self):
        self.corpus = _corpus()
        self.registry = VerifierRegistry()
        self.registry.register(TRANSITION_VERIFIER, self.corpus.verifier())

    def _qualify(self, **kw):
        from agentmem_ref import evidence_qualification as eq

        items = self.corpus.evidence_for(**kw)
        if not items:
            return None
        return eq.qualify(items[0], verifiers=self.registry.as_mapping())

    def test_a_different_proposed_value_refutes(self):
        from agentmem_ref import evidence_qualification as eq

        q = self._qualify(target_reference=MEMORY, criterion="value-correction",
                          pre_state="value-a", proposed_value="value-c")
        self.assertEqual(q.binding_status, eq.REFUTED)

    def test_a_stale_pre_state_refutes(self):
        from agentmem_ref import evidence_qualification as eq

        q = self._qualify(target_reference=MEMORY, criterion="value-correction",
                          pre_state="value-stale", proposed_value="value-b")
        self.assertEqual(q.binding_status, eq.REFUTED)

    def test_a_wrong_target_yields_no_rule_at_all(self):
        self.assertIsNone(self._qualify(
            target_reference="mem:somewhere-else", criterion="value-correction",
            pre_state="value-a", proposed_value="value-b"))

    def test_an_uncovered_criterion_yields_no_evidence(self):
        """No rule covers it, so nothing is manufactured and the proposal parks."""
        self.assertIsNone(self._qualify(
            target_reference=MEMORY, criterion="something-nobody-adjudicated",
            pre_state="value-a", proposed_value="value-b"))


class VerifierTrustIsEvaluatorHeld(unittest.TestCase):
    """DoD 15, 16 -- operator ruling on the boundary."""

    def test_no_entry_point_accepts_a_caller_supplied_verifier_mapping(self):
        import inspect

        from agentmem_ref.crossing import evaluate_crossing
        from agentmem_ref.interchange import evaluate_source_notice, import_bundle

        for fn in (GovernedMemoryAdapter.commit_proposal, evaluate_crossing,
                   import_bundle, evaluate_source_notice):
            params = inspect.signature(fn).parameters
            self.assertNotIn("verifiers", params, fn.__qualname__)

    def test_the_adapter_takes_its_registry_at_construction(self):
        import inspect

        params = inspect.signature(GovernedMemoryAdapter.__init__).parameters
        self.assertIn("verifier_registry", params)

    def test_an_empty_registry_leaves_evidence_asserted(self):
        """The safe default: naming a verifier nobody holds is not holding one."""
        from agentmem_ref import evidence_qualification as eq

        (item,) = _corpus().evidence_for(
            target_reference=MEMORY, criterion="value-correction",
            pre_state="value-a", proposed_value="value-b",
        )
        self.assertEqual(
            eq.qualify(item, verifiers=VerifierRegistry().as_mapping()).binding_status,
            eq.ASSERTED,
        )


class EvidenceDoesNotTouchLegacyState(unittest.TestCase):
    """DoD 19 -- operator ruling. Legacy fields stay legacy."""

    def test_a_qualified_commit_does_not_rewrite_review_satisfied(self):
        substrate = InMemoryTemporalGraph()
        corpus = _corpus()
        adapter = governed_adapter(substrate, TENANT, Clock(), corpus)
        proposal = _proposal("prop-legacy", asserted=False)
        before = (proposal.review_satisfied, proposal.approval_refs)

        evidence = corpus.evidence_for(
            target_reference=MEMORY, criterion="value-correction",
            pre_state="value-a", proposed_value="value-b",
        )
        adapter.commit_proposal(proposal, "value-b", evidence=evidence)

        self.assertEqual((proposal.review_satisfied, proposal.approval_refs), before)
        self.assertFalse(proposal.review_satisfied)


class QualifiedEvidenceCrosses(unittest.TestCase):
    """Criterion 2, at the adapter."""

    def test_an_adjudicated_transition_commits(self):
        substrate = InMemoryTemporalGraph()
        corpus = _corpus()
        adapter = governed_adapter(substrate, TENANT, Clock(), corpus)

        evidence = corpus.evidence_for(
            target_reference=MEMORY, criterion="value-correction",
            pre_state="value-a", proposed_value="value-b",
        )
        result = adapter.commit_proposal(
            _proposal("prop-ok", asserted=False), "value-b", evidence=evidence
        )

        self.assertTrue(result.committed)

    def test_no_evidence_parks_rather_than_failing(self):
        substrate = InMemoryTemporalGraph()
        adapter = governed_adapter(substrate, TENANT, Clock(), _corpus())

        result = adapter.commit_proposal(_proposal("prop-bare"), "value-b")

        self.assertFalse(result.committed)
        self.assertIsNone(adapter.current_fact_uuid(MEMORY))


if __name__ == "__main__":
    unittest.main()
