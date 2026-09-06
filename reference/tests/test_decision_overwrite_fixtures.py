"""Drive the ADR-025 durable-decision fixtures through the reference boundary."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agentmem_ref.decision_overwrite import (
    AuthorityGrant,
    DurableDecision,
    DurableDecisionRegistry,
    OverwriteProposal,
)

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class FixedClock:
    def now(self) -> str:
        return "2026-08-12T18:20:00Z"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _decision(data: dict, *, default_human_confirmed: bool = True) -> DurableDecision:
    raw = data.get("decision") or {}
    return DurableDecision(
        decision_id=raw.get("decision_id", "decision:original"),
        decision_statement=raw.get(
            "decision_statement",
            "Keep protected-branch changes behind reviewed pull requests.",
        ),
        rationale=raw.get(
            "rationale",
            "Canonical changes require review and current validation evidence.",
        ),
        decision_scope=raw.get("decision_scope", data["overwrite_proposal"]["scope"]),
        owner=raw.get("owner", "human:maintainer"),
        approval_refs=tuple(raw.get("approval_refs", ["approval:original"])),
        decided_at=raw.get("decided_at", "2026-08-12T16:00:00Z"),
        human_confirmed=raw.get("human_confirmed", default_human_confirmed),
    )


def _proposal(data: dict, registry: DurableDecisionRegistry) -> OverwriteProposal:
    raw = data["overwrite_proposal"]
    grant_ref = data.get("authority_grant", {}).get("grant_id", "grant:human")
    replacement = DurableDecision(
        decision_id=raw["replacement_decision_id"],
        decision_statement="Replacement decision from conformance fixture.",
        rationale="Replacement remains append-only and authority-bound.",
        decision_scope=raw["scope"],
        owner="human:maintainer",
        approval_refs=(grant_ref,),
        decided_at="2026-08-12T18:10:00Z",
        supersedes=raw["target_decision_id"],
        human_confirmed=True,
    )
    return OverwriteProposal(
        proposal_id=raw["proposal_id"],
        proposing_actor=raw["proposing_actor"],
        target_decision_id=raw["target_decision_id"],
        replacement=replacement,
        scope=raw["scope"],
        rationale="Fixture overwrite proposal.",
        evidence_refs=(data["memory_unit"]["evidence"][0]["id"],),
        conflict_notes=("preserve prior decision historically",),
        state_snapshot=raw["state_snapshot"],
        risk_class=raw["risk_class"],
    )


def _grant(data: dict) -> AuthorityGrant:
    raw = data["authority_grant"]
    proposal = data["overwrite_proposal"]
    return AuthorityGrant(
        grant_id=raw["grant_id"],
        authority_kind=raw["authority_kind"],
        principal_id=raw["principal_id"],
        proposal_id=proposal["proposal_id"],
        target_decision_id=proposal["target_decision_id"],
        scope=proposal["scope"],
        mutation_class="decision_overwrite",
        issued_at=raw["issued_at"],
        expires_at=raw["expires_at"],
        max_risk_class=raw["max_risk_class"],
        authorized_actor_ids=(proposal["proposing_actor"],),
    )


class DurableDecisionFixtureTests(unittest.TestCase):
    def _registry(self, data: dict, *, default_human_confirmed: bool = True) -> DurableDecisionRegistry:
        registry = DurableDecisionRegistry(FixedClock().now)
        registry.register(_decision(data, default_human_confirmed=default_human_confirmed))
        return registry

    def test_agent_proposal_fixture(self):
        data = _load("durable-decision-agent-proposal.json")
        registry = self._registry(data)
        proposal = _proposal(data, registry)

        result = registry.propose(proposal)
        expected = data["expected_behavior"]
        self.assertEqual(result.status, expected["proposal_status"])
        self.assertEqual(registry.decision_status(proposal.target_decision_id), expected["target_status"])
        self.assertEqual(registry.decision(proposal.replacement.decision_id) is not None, expected["replacement_present"])
        self.assertEqual(len(registry.supersession_journal), expected["supersession_journal_count"])

        result = registry.commit(proposal.proposal_id, None)
        self.assertEqual(result.reason, expected["commit_without_authority_reason"])

    def test_human_confirmed_overwrite_fixture(self):
        data = _load("durable-decision-human-confirmed-overwrite.json")
        registry = self._registry(data)
        proposal = _proposal(data, registry)
        registry.propose(proposal)

        result = registry.commit(proposal.proposal_id, _grant(data))
        expected = data["expected_behavior"]
        self.assertEqual(result.status, expected["commit_status"])
        self.assertEqual(registry.decision_status(proposal.target_decision_id), expected["target_status"])
        self.assertEqual(registry.decision_status(proposal.replacement.decision_id), expected["replacement_status"])
        self.assertEqual(len(registry.supersession_journal), expected["supersession_journal_count"])
        self.assertEqual(result.decision.outcome, expected["pama_outcome"])
        self.assertEqual(result.supersession_evidence["authority_kind"], expected["authority_kind"])

    def test_stale_overwrite_fixture(self):
        data = _load("durable-decision-stale-overwrite.json")
        registry = self._registry(data)
        proposal = _proposal(data, registry)
        registry.propose(proposal)
        registry.record_external_state_change(proposal.target_decision_id)

        result = registry.commit(proposal.proposal_id, _grant(data))
        expected = data["expected_behavior"]
        self.assertEqual(result.status, expected["commit_status"])
        self.assertEqual(result.reason, expected["reason"])
        self.assertEqual(registry.decision_status(proposal.target_decision_id), expected["target_status"])
        self.assertEqual(registry.decision(proposal.replacement.decision_id) is not None, expected["replacement_present"])
        self.assertEqual(len(registry.supersession_journal), expected["supersession_journal_count"])

    def test_agent_collusion_fixture(self):
        data = _load("durable-decision-agent-collusion.json")
        registry = self._registry(data)
        proposal = _proposal(data, registry)
        registry.propose(proposal)

        result = registry.commit(proposal.proposal_id, _grant(data))
        expected = data["expected_behavior"]
        self.assertEqual(result.status, expected["commit_status"])
        self.assertEqual(result.reason, expected["reason"])
        self.assertEqual(registry.decision_status(proposal.target_decision_id), expected["target_status"])
        self.assertEqual(registry.decision(proposal.replacement.decision_id) is not None, expected["replacement_present"])
        self.assertEqual(len(registry.supersession_journal), expected["supersession_journal_count"])

    def test_delegated_low_risk_fixture(self):
        data = _load("durable-decision-delegated-low-risk-overwrite.json")
        registry = self._registry(data, default_human_confirmed=False)
        proposal = _proposal(data, registry)
        registry.propose(proposal)

        result = registry.commit(proposal.proposal_id, _grant(data))
        expected = data["expected_behavior"]
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # The fixture's declared behaviour changed with the flip: the grant still
        # resolves, and the overwrite now parks because authority is not
        # evidence. The assertions below read the fixture, so the change is
        # declared there rather than hidden in the test.
        self.assertEqual(result.status, expected["commit_status"])
        self.assertEqual(result.reason, expected["commit_reason"])
        self.assertEqual(registry.decision_status(proposal.target_decision_id), expected["target_status"])
        self.assertIsNone(registry.decision(proposal.replacement.decision_id))
        self.assertEqual(len(registry.supersession_journal), expected["supersession_journal_count"])
        self.assertEqual(result.decision.outcome, expected["pama_outcome"])
        self.assertEqual(result.grant.authority_kind, expected["authority_kind"])
        self.assertTrue(expected["authority_resolved"])
        self.assertEqual(len(registry.pending_verification.parked()), 1)


if __name__ == "__main__":
    unittest.main()
