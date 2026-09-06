"""Contextual recall re-evaluation and sleeper-poisoning tests for issue #200."""

from __future__ import annotations

import unittest

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext
from agentmem_ref.contextual_recall import (
    ContextualRule,
    DeterministicContextualRecallPolicy,
    build_decision,
)
from agentmem_ref.contextual_recall_adapter import ContextualRecallAdapter
from agentmem_ref.sleeper_poisoning_harness import run_sleeper_poisoning_harness
from agentmem_ref.substrate import InMemoryTemporalGraph


class _InvalidPolicy:
    policy_ref = "contextual-policy:invalid"
    policy_version = "1.0.0"

    def evaluate(self, candidate_ref, context, *, evaluated_at):
        return {
            "candidate_ref": candidate_ref,
            "outcome": "grant_everything",
            "evaluated_at": evaluated_at,
        }


class _FailingPolicy:
    policy_ref = "contextual-policy:failing"
    policy_version = "1.0.0"

    def evaluate(self, candidate_ref, context, *, evaluated_at):
        raise RuntimeError("simulated policy backend failure")


class ContextualRecallTests(unittest.TestCase):
    def _base(self):
        substrate = InMemoryTemporalGraph()
        base = GovernedMemoryAdapter(substrate, tenant="tenant-a", clock=Clock())
        proposal = policy.Proposal(
            proposal_id="proposal:contextual-test",
            actor_id="actor:test",
            charter_version="charter:v1",
            target_reference="mem:contextual-test",
            target_class=policy.M2,
            scope="scope:tenant-a/project-a",
            operation="promotion",
            current_strength="observed",
            proposed_strength="promoted",
            downstream_authority=policy.A1,
            reversibility="reversible",
            risk_class="low",
            evidence_refs=("evidence:contextual-test",),
            tenant_ref="tenant-a",
            project_ref="project-a",
            purpose="test",
            isolation_domain_refs=("scope:tenant-a/project-a",),
        )
        committed = base.commit_proposal(proposal, "contextual recall test fact")
        self.assertTrue(committed.committed)
        self.assertIsNotNone(committed.fact_uuid)
        return substrate, base, committed.fact_uuid

    def _context(self, purpose="benign"):
        return RecallContext(
            target_domain_refs=("scope:tenant-a/project-a",),
            principal_ref="principal:test",
            project_ref="project-a",
            purpose=purpose,
        )

    def test_sleeper_behavioral_harness_matches_structural_fixture(self):
        result = run_sleeper_poisoning_harness()
        self.assertTrue(result["passed"], result)
        checks = result["checks"]
        self.assertTrue(checks["fixture_write_time_check_may_pass"])
        self.assertTrue(checks["fixture_later_trigger_rechecked"])
        self.assertTrue(checks["fixture_unsafe_activation_forbidden"])
        self.assertTrue(checks["same_candidate_discovered_after_trigger"])
        self.assertTrue(checks["triggered_candidate_not_admitted"])
        self.assertTrue(checks["triggered_candidate_absent_from_downstream_influence"])

    def test_prior_benign_admission_is_not_cached_as_permission(self):
        _substrate, base, fact_uuid = self._base()
        contextual_policy = DeterministicContextualRecallPolicy(
            policy_ref="contextual-policy:test",
            policy_version="1.0.0",
            rules=(
                ContextualRule(
                    rule_id="trigger-block",
                    candidate_ref=fact_uuid,
                    purpose="triggered",
                    outcome="block",
                    reason_code="triggered_context_block",
                ),
            ),
        )
        recall = ContextualRecallAdapter(base, policy=contextual_policy, clock=Clock(start=10))

        benign = recall.governed_recall("contextual recall", self._context("benign"))
        triggered = recall.governed_recall("contextual recall", self._context("triggered"))

        self.assertIn(fact_uuid, benign.admitted)
        self.assertIn(fact_uuid, triggered.candidates)
        self.assertNotIn(fact_uuid, triggered.admitted)
        self.assertEqual(contextual_policy.evaluation_count, 2)
        self.assertEqual(
            triggered.contextual_decisions[fact_uuid]["interpretation"]["prior_admission_authority"],
            "none",
        )

    def test_contextual_policy_cannot_widen_builtin_dispute_refusal(self):
        _substrate, base, fact_uuid = self._base()
        base.mark_disputed(fact_uuid)
        always_admit = DeterministicContextualRecallPolicy(
            policy_ref="contextual-policy:always-admit",
            policy_version="1.0.0",
            default_outcome="admit",
        )
        recall = ContextualRecallAdapter(base, policy=always_admit)
        result = recall.governed_recall("contextual recall", self._context())

        self.assertIn(fact_uuid, result.candidates)
        self.assertNotIn(fact_uuid, result.admitted)
        self.assertEqual(result.refusals[fact_uuid], "disputed")
        self.assertNotIn(fact_uuid, result.contextual_decisions)
        self.assertEqual(always_admit.evaluation_count, 0)

    def test_required_missing_policy_fails_closed(self):
        _substrate, base, fact_uuid = self._base()
        recall = ContextualRecallAdapter(
            base,
            policy=None,
            require_policy=True,
            required_policy_ref="contextual-policy:high-assurance",
            required_policy_version="current-required",
            clock=Clock(start=10),
        )
        result = recall.governed_recall("contextual recall", self._context())
        decision = result.contextual_decisions[fact_uuid]
        self.assertNotIn(fact_uuid, result.admitted)
        self.assertEqual(decision["outcome"], "block")
        self.assertEqual(decision["policy"]["status"], "unavailable")
        self.assertEqual(decision["reason_code"], "contextual_policy_unavailable")

    def test_failing_policy_fails_closed(self):
        _substrate, base, fact_uuid = self._base()
        result = ContextualRecallAdapter(base, policy=_FailingPolicy(), clock=Clock(start=10)).governed_recall(
            "contextual recall", self._context()
        )
        decision = result.contextual_decisions[fact_uuid]
        self.assertEqual(decision["outcome"], "block")
        self.assertEqual(decision["policy"]["status"], "error")
        self.assertNotIn(fact_uuid, result.context_surface)

    def test_invalid_policy_outcome_fails_closed(self):
        _substrate, base, fact_uuid = self._base()
        result = ContextualRecallAdapter(base, policy=_InvalidPolicy(), clock=Clock(start=10)).governed_recall(
            "contextual recall", self._context()
        )
        decision = result.contextual_decisions[fact_uuid]
        self.assertEqual(decision["outcome"], "block")
        self.assertEqual(decision["policy"]["status"], "invalid")
        self.assertEqual(decision["reason_code"], "contextual_policy_invalid_decision")

    def test_policy_version_change_is_reconstructable_without_memory_mutation(self):
        substrate, base, fact_uuid = self._base()
        first_stored = substrate.get_fact(fact_uuid)
        first_policy = DeterministicContextualRecallPolicy(
            policy_ref="contextual-policy:versioned",
            policy_version="1.0.0",
            default_outcome="admit",
        )
        recall = ContextualRecallAdapter(base, policy=first_policy, clock=Clock(start=10))
        first = recall.governed_recall("contextual recall", self._context("same-purpose"))
        self.assertEqual(first.contextual_decisions[fact_uuid]["policy"]["policy_version"], "1.0.0")
        self.assertIn(fact_uuid, first.admitted)

        second_policy = DeterministicContextualRecallPolicy(
            policy_ref="contextual-policy:versioned",
            policy_version="2.0.0",
            rules=(
                ContextualRule(
                    rule_id="new-risk-rule",
                    candidate_ref=fact_uuid,
                    purpose="same-purpose",
                    outcome="require_review",
                    reason_code="new_policy_requires_review",
                ),
            ),
        )
        recall.set_policy(second_policy)
        second = recall.governed_recall("contextual recall", self._context("same-purpose"))
        second_stored = substrate.get_fact(fact_uuid)

        self.assertEqual(second.contextual_decisions[fact_uuid]["policy"]["policy_version"], "2.0.0")
        self.assertEqual(second.contextual_decisions[fact_uuid]["outcome"], "require_review")
        self.assertNotIn(fact_uuid, second.admitted)
        self.assertEqual(first_stored, second_stored)

    def test_risk_signal_can_inform_decision_but_is_not_authority(self):
        _substrate, base, fact_uuid = self._base()
        risk = {
            "signal_ref": "risk:learned:1",
            "signal_semantics": "probabilistic_contextual_risk",
            "estimator_ref": "estimator:risk-model",
            "estimator_version": "v7",
            "signal_value": 0.91,
            "uncertainty_summary": "model-estimated risk; not authority",
        }
        contextual_policy = DeterministicContextualRecallPolicy(
            policy_ref="contextual-policy:risk-informed",
            policy_version="1.0.0",
            rules=(
                ContextualRule(
                    rule_id="risk-informed-quarantine",
                    candidate_ref=fact_uuid,
                    purpose="risky",
                    outcome="quarantine",
                    reason_code="risk_requires_quarantine",
                    evidence_refs=("evidence:risk-review",),
                    risk_evidence=risk,
                ),
            ),
        )
        result = ContextualRecallAdapter(base, policy=contextual_policy, clock=Clock(start=10)).governed_recall(
            "contextual recall", self._context("risky")
        )
        decision = result.contextual_decisions[fact_uuid]
        self.assertEqual(decision["risk_evidence"]["signal_value"], 0.91)
        self.assertEqual(decision["interpretation"]["risk_signal_authority"], "none")
        self.assertEqual(decision["interpretation"]["authority_effect"], "current_recall_only")
        self.assertNotIn(fact_uuid, result.admitted)

    def test_decision_contains_only_bounded_context_not_query_or_memory_content(self):
        _substrate, base, fact_uuid = self._base()
        contextual_policy = DeterministicContextualRecallPolicy(
            policy_ref="contextual-policy:minimized",
            policy_version="1.0.0",
        )
        query = "contextual recall raw query should not be copied"
        result = ContextualRecallAdapter(base, policy=contextual_policy, clock=Clock(start=10)).governed_recall(
            query, self._context("benign")
        )
        decision = result.contextual_decisions[fact_uuid]
        rendered = str(decision)
        self.assertNotIn(query, rendered)
        self.assertNotIn("contextual recall test fact", rendered)
        self.assertEqual(decision["candidate_ref"], fact_uuid)

    def test_build_decision_rejects_unknown_outcome(self):
        with self.assertRaisesRegex(ValueError, "unsupported contextual recall outcome"):
            build_decision(
                candidate_ref="fact:1",
                context=self._context(),
                policy_ref="policy:test",
                policy_version="1",
                policy_status="evaluated",
                outcome="permit_forever",
                reason_code="bad",
                evaluated_at="2026-08-12T22:59:00Z",
            )


if __name__ == "__main__":
    unittest.main()
