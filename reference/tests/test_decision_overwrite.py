"""Executable ADR-025 durable decision overwrite authority cases."""

from __future__ import annotations

import unittest

from agentmem_ref import policy, receipts
from agentmem_ref.decision_overwrite import (
    AGENT_CONSENSUS,
    COMMITTED,
    DELEGATED_POLICY,
    HUMAN_CONFIRMATION,
    PENDING,
    REJECTED,
    AuthorityGrant,
    DurableDecision,
    DurableDecisionRegistry,
    OverwriteProposal,
)


class ManualClock:
    def __init__(self, value: str = "2026-08-12T18:20:00Z") -> None:
        self.value = value

    def now(self) -> str:
        return self.value


def _original(*, human_confirmed: bool = True) -> DurableDecision:
    return DurableDecision(
        decision_id="decision:original",
        decision_statement="Keep protected-branch changes behind reviewed pull requests.",
        rationale="Canonical changes require review and current validation evidence.",
        decision_scope="repo:agent-memory",
        owner="human:maintainer",
        approval_refs=("approval:original",),
        decided_at="2026-08-12T16:00:00Z",
        human_confirmed=human_confirmed,
    )


def _replacement(grant_ref: str = "grant:human") -> DurableDecision:
    return DurableDecision(
        decision_id="decision:replacement",
        decision_statement="Permit a bounded automation path while preserving protected merges.",
        rationale="A narrower automated path has current evidence and explicit authority.",
        decision_scope="repo:agent-memory",
        owner="human:maintainer",
        approval_refs=(grant_ref,),
        decided_at="2026-08-12T18:10:00Z",
        supersedes="decision:original",
        human_confirmed=True,
    )


def _proposal(
    registry: DurableDecisionRegistry,
    *,
    grant_ref: str = "grant:human",
    risk_class: str = "high",
    isolation_domain_refs: tuple[str, ...] = (),
    required_isolation_domain_refs: tuple[str, ...] = (),
) -> OverwriteProposal:
    return OverwriteProposal(
        proposal_id="overwrite:1",
        proposing_actor="agent:planner",
        target_decision_id="decision:original",
        replacement=_replacement(grant_ref),
        scope="repo:agent-memory",
        rationale="New evidence supports replacing the earlier durable decision.",
        evidence_refs=("evidence:overwrite",),
        conflict_notes=("prior decision remains historically valid evidence",),
        state_snapshot=registry.state_snapshot("decision:original"),
        risk_class=risk_class,
        target_class=policy.M4,
        downstream_authority=policy.A3,
        isolation_domain_refs=isolation_domain_refs,
        required_isolation_domain_refs=required_isolation_domain_refs,
    )


def _grant(
    *,
    kind: str = HUMAN_CONFIRMATION,
    grant_id: str = "grant:human",
    principal_id: str = "human:maintainer",
    max_risk_class: str = "critical",
    revoked: bool = False,
    issued_at: str = "2026-08-12T18:00:00Z",
    expires_at: str = "2026-08-12T19:00:00Z",
    proposal_id: str = "overwrite:1",
    target_decision_id: str = "decision:original",
    scope: str = "repo:agent-memory",
    mutation_class: str = "decision_overwrite",
    authorized_actor_ids: tuple[str, ...] = ("agent:planner",),
) -> AuthorityGrant:
    return AuthorityGrant(
        grant_id=grant_id,
        authority_kind=kind,
        principal_id=principal_id,
        proposal_id=proposal_id,
        target_decision_id=target_decision_id,
        scope=scope,
        mutation_class=mutation_class,
        issued_at=issued_at,
        expires_at=expires_at,
        max_risk_class=max_risk_class,
        authorized_actor_ids=authorized_actor_ids,
        revoked=revoked,
    )


def _registry(*, human_confirmed: bool = True) -> DurableDecisionRegistry:
    registry = DurableDecisionRegistry(ManualClock().now)
    registry.register(_original(human_confirmed=human_confirmed))
    return registry


class DurableDecisionOverwriteTests(unittest.TestCase):
    def test_agent_proposal_is_evidence_not_mutation(self):
        registry = _registry()
        proposal = _proposal(registry)

        result = registry.propose(proposal)

        self.assertEqual(result.status, PENDING)
        self.assertEqual(registry.decision_status("decision:original"), "active")
        self.assertIsNone(registry.decision("decision:replacement"))
        self.assertEqual(registry.supersession_journal, [])
        self.assertEqual(result.events[-1]["event_type"], "memory.decision_overwrite_proposed")

        rejected = registry.commit(proposal.proposal_id, None)
        self.assertEqual(rejected.status, REJECTED)
        self.assertEqual(rejected.reason, "authority_required")
        self.assertEqual(registry.decision_status("decision:original"), "active")
        self.assertIsNone(registry.decision("decision:replacement"))

    def test_human_confirmed_overwrite_appends_supersession_evidence(self):
        registry = _registry()
        original = registry.decision("decision:original")
        proposal = _proposal(registry)
        registry.propose(proposal)

        result = registry.commit(proposal.proposal_id, _grant())

        self.assertEqual(result.status, COMMITTED)
        self.assertIs(registry.decision("decision:original"), original)
        self.assertEqual(registry.decision_status("decision:original"), "superseded")
        self.assertEqual(registry.superseded_by("decision:original"), "decision:replacement")
        self.assertEqual(registry.decision_status("decision:replacement"), "active")
        self.assertEqual(len(registry.supersession_journal), 1)
        self.assertEqual(
            registry.supersession_journal[0]["prior_decision_id"],
            "decision:original",
        )
        self.assertEqual(
            registry.supersession_journal[0]["replacement_decision_id"],
            "decision:replacement",
        )
        self.assertEqual(result.decision.outcome, policy.ALLOW_WITH_LEDGER)
        receipts.verify_receipt_decision_pair(result.receipt, result.pama_decision)
        self.assertEqual(result.events[-1]["event_type"], "memory.decision_overwrite_committed")

    def test_agent_consensus_cannot_replace_human_confirmed_decision(self):
        registry = _registry()
        proposal = _proposal(registry, grant_ref="grant:agents")
        registry.propose(proposal)

        result = registry.commit(
            proposal.proposal_id,
            _grant(kind=AGENT_CONSENSUS, grant_id="grant:agents", principal_id="agent:reviewer"),
        )

        self.assertEqual(result.status, REJECTED)
        self.assertEqual(result.reason, "human_confirmation_required")
        self.assertEqual(registry.decision_status("decision:original"), "active")
        self.assertIsNone(registry.decision("decision:replacement"))
        self.assertEqual(registry.supersession_journal, [])

    def test_stale_overwrite_proposal_fails_before_authority_use(self):
        registry = _registry()
        proposal = _proposal(registry)
        registry.propose(proposal)
        registry.record_external_state_change("decision:original")

        result = registry.commit(proposal.proposal_id, _grant())

        self.assertEqual(result.status, REJECTED)
        self.assertEqual(result.reason, "stale_overwrite_proposal")
        self.assertIsNone(registry.decision("decision:replacement"))

    def test_delegated_policy_can_cover_bounded_low_risk_nonhuman_decision(self):
        registry = _registry(human_confirmed=False)
        proposal = _proposal(registry, grant_ref="grant:delegated", risk_class="low")
        registry.propose(proposal)

        result = registry.commit(
            proposal.proposal_id,
            _grant(
                kind=DELEGATED_POLICY,
                grant_id="grant:delegated",
                principal_id="policy:maintainer-delegation",
                max_risk_class="medium",
            ),
        )

        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # Operator ruling: decision_overwrite parks its low/medium require_review
        # path unless genuine proposal evidence is available, and the
        # AuthorityGrant must NOT be used as that evidence -- it answers the
        # authority question, not the evidence question. A valid grant can
        # authorise review of a bad proposal.
        #
        # The property this test was written for is unchanged and still asserted
        # below: delegated_policy IS a valid non-human authority at low risk, and
        # the grant resolves. What changed is that resolving authority no longer
        # commits on its own.
        self.assertEqual(result.status, PENDING)
        self.assertEqual(result.reason, "parked_pending_verification")
        self.assertIsNotNone(result.grant)
        self.assertEqual(result.grant.authority_kind, DELEGATED_POLICY)

        # And it parks durably: the record outlives the call and names what is
        # missing, so the caller has a traversable route rather than a refusal.
        parked = registry.pending_verification.parked()
        self.assertEqual(len(parked), 1)
        from agentmem_ref.resumption import criteria_for
        self.assertTrue(criteria_for(parked[0]).unmet)
        self.assertEqual(result.decision.outcome, policy.REQUIRE_REVIEW)
        self.assertIsNone(result.supersession_evidence)

    def test_high_risk_overwrite_requires_human_even_when_prior_decision_was_not_human_confirmed(self):
        registry = _registry(human_confirmed=False)
        proposal = _proposal(registry, grant_ref="grant:delegated", risk_class="high")
        registry.propose(proposal)

        result = registry.commit(
            proposal.proposal_id,
            _grant(kind=DELEGATED_POLICY, grant_id="grant:delegated", principal_id="policy:delegation"),
        )

        self.assertEqual(result.status, REJECTED)
        self.assertEqual(result.reason, "human_confirmation_required")

    def test_authority_grant_failures_do_not_mutate(self):
        cases = (
            ("authority_grant_revoked", {"revoked": True}),
            ("authority_grant_expired", {"expires_at": "2026-08-12T18:20:00Z"}),
            ("authority_grant_not_yet_valid", {"issued_at": "2026-08-12T18:30:00Z", "expires_at": "2026-08-12T19:00:00Z"}),
            ("authority_proposal_mismatch", {"proposal_id": "overwrite:other"}),
            ("authority_target_mismatch", {"target_decision_id": "decision:other"}),
            ("authority_scope_mismatch", {"scope": "repo:other"}),
            ("authority_mutation_mismatch", {"mutation_class": "correction"}),
            ("actor_not_delegated", {"authorized_actor_ids": ("agent:other",)}),
            ("self_approval_prohibited", {"principal_id": "agent:planner"}),
            ("authority_risk_ceiling_exceeded", {"max_risk_class": "medium"}),
        )
        for expected_reason, overrides in cases:
            with self.subTest(expected_reason=expected_reason):
                registry = _registry()
                proposal = _proposal(registry)
                registry.propose(proposal)
                result = registry.commit(proposal.proposal_id, _grant(**overrides))
                self.assertEqual(result.status, REJECTED)
                self.assertEqual(result.reason, expected_reason)
                self.assertIsNone(registry.decision("decision:replacement"))
                self.assertEqual(registry.supersession_journal, [])

    def test_replacement_must_record_exact_authority_and_supersession(self):
        registry = _registry()
        proposal = OverwriteProposal(
            proposal_id="overwrite:1",
            proposing_actor="agent:planner",
            target_decision_id="decision:original",
            replacement=DurableDecision(
                decision_id="decision:replacement",
                decision_statement="Replacement",
                rationale="Rationale",
                decision_scope="repo:agent-memory",
                owner="human:maintainer",
                approval_refs=("approval:unrelated",),
                decided_at="2026-08-12T18:10:00Z",
                supersedes="decision:original",
                human_confirmed=True,
            ),
            scope="repo:agent-memory",
            rationale="Proposal rationale",
            evidence_refs=("evidence:overwrite",),
            conflict_notes=(),
            state_snapshot=registry.state_snapshot("decision:original"),
            risk_class="high",
        )
        registry.propose(proposal)
        result = registry.commit(proposal.proposal_id, _grant())
        self.assertEqual(result.reason, "authority_not_recorded_on_replacement")

        registry = _registry()
        bad_link = OverwriteProposal(
            proposal_id="overwrite:1",
            proposing_actor="agent:planner",
            target_decision_id="decision:original",
            replacement=DurableDecision(
                decision_id="decision:replacement",
                decision_statement="Replacement",
                rationale="Rationale",
                decision_scope="repo:agent-memory",
                owner="human:maintainer",
                approval_refs=("grant:human",),
                decided_at="2026-08-12T18:10:00Z",
                supersedes=None,
                human_confirmed=True,
            ),
            scope="repo:agent-memory",
            rationale="Proposal rationale",
            evidence_refs=("evidence:overwrite",),
            conflict_notes=(),
            state_snapshot=registry.state_snapshot("decision:original"),
            risk_class="high",
        )
        registry.propose(bad_link)
        result = registry.commit(bad_link.proposal_id, _grant())
        self.assertEqual(result.reason, "replacement_supersession_mismatch")

    def test_valid_human_grant_still_cannot_override_pama_block(self):
        registry = _registry()
        proposal = _proposal(
            registry,
            isolation_domain_refs=("scope:visible",),
            required_isolation_domain_refs=("scope:required",),
        )
        registry.propose(proposal)

        result = registry.commit(proposal.proposal_id, _grant())

        self.assertEqual(result.status, REJECTED)
        self.assertEqual(result.reason, "pama_not_permitted")
        self.assertEqual(result.decision.outcome, policy.BLOCK)
        self.assertIsNone(registry.decision("decision:replacement"))
        self.assertEqual(registry.supersession_journal, [])
        receipts.verify_receipt_decision_pair(result.receipt, result.pama_decision)


if __name__ == "__main__":
    unittest.main()
