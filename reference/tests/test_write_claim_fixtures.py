"""Drive the ADR-024 shared-write claim fixtures through the reference coordinator.

Run: python -m unittest discover -s reference/tests -t reference
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402
from agentmem_ref.write_claims import SharedWriteCoordinator, WriteClaim  # noqa: E402

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class ManualClock:
    def __init__(self, value: str = "2026-08-12T17:10:00Z") -> None:
        self.value = value

    def now(self) -> str:
        return self.value


def _claim(data: dict) -> WriteClaim:
    fields = {
        key: value
        for key, value in data.items()
        if key in WriteClaim.__dataclass_fields__
    }
    return WriteClaim(**fields)


def _proposal(claim: WriteClaim, *, actor_authority_resolved: bool = True) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=f"proposal:{claim.claim_id}",
        actor_id=claim.actor_id,
        charter_version="charter:fixture",
        target_reference=claim.target_reference,
        target_class=policy.M2,
        scope=claim.scope,
        operation=claim.mutation_class,
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:shared-write-fixture",),
        actor_authority_resolved=actor_authority_resolved,
        state_snapshot=claim.state_snapshot,
        tenant_ref=claim.scope,
        purpose="shared-write-fixture",
        task_ref=claim.task_id,
    )


def _writes(substrate: InMemoryTemporalGraph) -> list[tuple]:
    return [entry for entry in substrate.write_log if entry[0] == "write_fact"]


class SharedWriteFixtureTests(unittest.TestCase):
    def _load(self, name: str) -> dict:
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))

    def test_valid_claim_fixture(self):
        fixture = self._load("shared-write-valid-claim.json")
        data = fixture["write_claim"]
        claim = _claim(data)
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant=claim.scope, clock=Clock())
        coordinator = SharedWriteCoordinator(adapter, lambda _claim: data["authorized"], ManualClock().now)

        acquired = coordinator.acquire(claim)
        acquire_status = acquired.status
        committed = coordinator.commit(claim.claim_id, _proposal(claim), "fixture fact")
        expected = fixture["expected_behavior"]

        self.assertEqual(acquire_status, expected["claim_status"])
        self.assertEqual(committed.status, expected["commit_status"])
        self.assertEqual(len(_writes(substrate)), expected["substrate_write_count"])
        self.assertEqual(committed.commit_result.decision.outcome, expected["pama_outcome"])

    def test_conflicting_claim_fixture(self):
        fixture = self._load("shared-write-conflicting-claim.json")
        claims = [_claim(item) for item in fixture["write_claims"]]
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant=claims[0].scope, clock=Clock())
        coordinator = SharedWriteCoordinator(adapter, lambda _claim: True, ManualClock().now)

        first = coordinator.acquire(claims[0])
        second = coordinator.acquire(claims[1])
        expected = fixture["expected_behavior"]

        self.assertEqual(first.status, expected["first_claim_status"])
        self.assertEqual(second.status, expected["second_claim_status"])
        self.assertEqual(second.reason, expected["second_reason"])
        self.assertEqual(len(_writes(substrate)), expected["substrate_write_count_before_commit"])

    def test_stale_claim_fixture(self):
        fixture = self._load("shared-write-stale-claim.json")
        data = fixture["write_claim"]
        claim = _claim(data)
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant=claim.scope, clock=Clock())
        while f"v{adapter.state_version(claim.target_reference)}" != data["current_state"]:
            adapter.record_correction(claim.target_reference)
        coordinator = SharedWriteCoordinator(adapter, lambda _claim: data["authorized"], ManualClock().now)

        result = coordinator.acquire(claim)
        expected = fixture["expected_behavior"]

        self.assertEqual(result.status, expected["claim_status"])
        self.assertEqual(result.reason, expected["reason"])
        self.assertEqual(len(_writes(substrate)), expected["substrate_write_count"])

    def test_unauthorized_claim_fixture(self):
        fixture = self._load("shared-write-unauthorized-claim.json")
        data = fixture["write_claim"]
        claim = _claim(data)
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant=claim.scope, clock=Clock())
        coordinator = SharedWriteCoordinator(adapter, lambda _claim: data["authorized"], ManualClock().now)

        result = coordinator.acquire(claim)
        expected = fixture["expected_behavior"]

        self.assertEqual(result.status, expected["claim_status"])
        self.assertEqual(result.reason, expected["reason"])
        self.assertEqual(len(_writes(substrate)), expected["substrate_write_count"])

    def test_acquired_lease_that_expires_before_commit_fails_closed(self):
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant="shared:test", clock=Clock())
        clock = ManualClock("2026-08-12T17:10:00Z")
        claim = WriteClaim(
            claim_id="claim:expiring",
            actor_id="agent:a",
            task_id="task:shared",
            scope="shared:test",
            target_reference="memory:shared",
            mutation_class="promotion",
            authority_ref="authority:shared-write",
            state_snapshot="v0",
            issued_at="2026-08-12T17:00:00Z",
            expires_at="2026-08-12T17:30:00Z",
        )
        coordinator = SharedWriteCoordinator(adapter, lambda _claim: True, clock.now)
        acquired = coordinator.acquire(claim)
        self.assertEqual(acquired.status, "acquired")

        clock.value = "2026-08-12T17:30:00Z"
        result = coordinator.commit(claim.claim_id, _proposal(claim), "must not commit")
        self.assertEqual(result.status, "expired")
        self.assertEqual(result.reason, "claim_expired")
        self.assertEqual(_writes(substrate), [])
        self.assertEqual(result.events[-1]["event_type"], "memory.write_claim_expired")

    def test_valid_claim_cannot_launder_blocked_pama_authority(self):
        fixture = self._load("shared-write-valid-claim.json")
        claim = _claim(fixture["write_claim"])
        substrate = InMemoryTemporalGraph()
        adapter = GovernedMemoryAdapter(substrate, tenant=claim.scope, clock=Clock())
        coordinator = SharedWriteCoordinator(adapter, lambda _claim: True, ManualClock().now)
        coordinator.acquire(claim)

        result = coordinator.commit(
            claim.claim_id,
            _proposal(claim, actor_authority_resolved=False),
            "must not commit",
        )
        self.assertEqual(result.status, "rejected")
        self.assertEqual(result.reason, "pama_not_committed")
        self.assertEqual(result.commit_result.decision.outcome, policy.BLOCK)
        self.assertEqual(_writes(substrate), [])


if __name__ == "__main__":
    unittest.main()
