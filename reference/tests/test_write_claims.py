"""Executable evidence for proposed ADR-024 pre-write claims.

Run: python -m unittest discover -s reference/tests -t reference
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy, receipts  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402
from agentmem_ref.write_claims import (  # noqa: E402
    ACQUIRED,
    COMMITTED,
    EXPIRED,
    REJECTED,
    SharedWriteCoordinator,
    WriteClaim,
)


class ManualClock:
    def __init__(self, value: str = "2026-08-12T17:10:00Z") -> None:
        self.value = value

    def now(self) -> str:
        return self.value


class SharedWriteClaimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant="shared:test", clock=Clock())
        self.claim_clock = ManualClock()
        self.authorized_refs = {"authority:shared-write"}
        self.coordinator = SharedWriteCoordinator(
            self.adapter,
            authority_resolver=lambda claim: claim.authority_ref in self.authorized_refs,
            now=self.claim_clock.now,
        )

    def _claim(self, claim_id: str = "claim:a", **changes) -> WriteClaim:
        values = {
            "claim_id": claim_id,
            "actor_id": "agent:a",
            "task_id": "task:shared",
            "scope": "shared:test",
            "target_reference": "memory:shared",
            "mutation_class": "promotion",
            "authority_ref": "authority:shared-write",
            "state_snapshot": f"v{self.adapter.state_version('memory:shared')}",
            "issued_at": "2026-08-12T17:00:00Z",
            "expires_at": "2026-08-12T18:00:00Z",
        }
        values.update(changes)
        return WriteClaim(**values)

    def _proposal(self, **changes) -> policy.Proposal:
        values = {
            "proposal_id": "proposal:shared",
            "actor_id": "agent:a",
            "charter_version": "charter:1",
            "target_reference": "memory:shared",
            "target_class": policy.M2,
            "scope": "shared:test",
            "operation": "promotion",
            "current_strength": "reinforced",
            "proposed_strength": "promoted",
            "downstream_authority": policy.A1,
            "reversibility": "reversible",
            "risk_class": "low",
            "evidence_refs": ("evidence:shared",),
            "state_snapshot": f"v{self.adapter.state_version('memory:shared')}",
            "tenant_ref": "shared:test",
            "purpose": "shared-write-test",
            "task_ref": "task:shared",
        }
        values.update(changes)
        return policy.Proposal(**values)

    def _writes(self) -> list[tuple]:
        return [entry for entry in self.substrate.write_log if entry[0] == "write_fact"]

    def test_valid_claim_commits_only_after_pama_and_emits_audit_evidence(self):
        acquired = self.coordinator.acquire(self._claim())
        self.assertEqual(acquired.status, ACQUIRED)
        self.assertEqual(acquired.events[0]["event_type"], "memory.write_claim_acquired")
        receipts.validate("memory-audit-event.schema.json", acquired.events[0])

        result = self.coordinator.commit("claim:a", self._proposal(), "shared fact")
        self.assertEqual(result.status, COMMITTED)
        self.assertTrue(result.commit_result and result.commit_result.committed)
        self.assertEqual(result.commit_result.decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(len(self._writes()), 1)
        self.assertEqual(result.events[-1]["event_type"], "memory.write_claim_committed")
        self.assertEqual(result.events[-1]["receipt_ref"], result.commit_result.receipt["receipt_id"])
        self.assertIsNone(self.coordinator.active_claim_id("shared:test", "memory:shared"))

    def test_conflicting_claim_is_rejected_before_durable_write(self):
        first = self.coordinator.acquire(self._claim("claim:a"))
        second = self.coordinator.acquire(self._claim("claim:b", actor_id="agent:b"))

        self.assertEqual(first.status, ACQUIRED)
        self.assertEqual(second.status, REJECTED)
        self.assertEqual(second.reason, "claim_conflict")
        self.assertEqual(len(self._writes()), 0)
        self.assertEqual(self.coordinator.active_claim_id("shared:test", "memory:shared"), "claim:a")
        self.assertEqual(second.events[-1]["payload"]["reason"], "claim_conflict")

    def test_expired_claim_cannot_be_acquired(self):
        self.claim_clock.value = "2026-08-12T18:00:00Z"
        record = self.coordinator.acquire(self._claim())

        self.assertEqual(record.status, EXPIRED)
        self.assertEqual(record.reason, "claim_expired")
        self.assertEqual(len(self._writes()), 0)
        self.assertEqual(record.events[-1]["event_type"], "memory.write_claim_expired")

    def test_stale_claim_is_rejected_at_acquisition(self):
        self.adapter.record_correction("memory:shared")
        record = self.coordinator.acquire(self._claim(state_snapshot="v0"))

        self.assertEqual(record.status, REJECTED)
        self.assertEqual(record.reason, "stale_claim")
        self.assertEqual(len(self._writes()), 0)

    def test_claim_that_becomes_stale_is_rejected_before_adapter_commit(self):
        record = self.coordinator.acquire(self._claim())
        self.assertEqual(record.status, ACQUIRED)
        self.adapter.record_correction("memory:shared")

        result = self.coordinator.commit("claim:a", self._proposal(state_snapshot="v0"), "stale fact")
        self.assertEqual(result.status, REJECTED)
        self.assertEqual(result.reason, "stale_claim")
        self.assertIsNone(result.commit_result)
        self.assertEqual(len(self._writes()), 0)

    def test_unauthorized_claim_fails_closed(self):
        record = self.coordinator.acquire(self._claim(authority_ref="authority:not-granted"))

        self.assertEqual(record.status, REJECTED)
        self.assertEqual(record.reason, "unauthorized_claim")
        self.assertEqual(len(self._writes()), 0)
        self.assertEqual(record.events[-1]["authority"]["authority_refs"], ["authority:not-granted"])

    def test_claim_and_proposal_must_bind_same_actor_scope_target_task_and_mutation(self):
        mutations = {
            "actor_id": "agent:b",
            "scope": "shared:other",
            "target_reference": "memory:other",
            "task_ref": "task:other",
            "operation": "pruning",
        }
        expected = {
            "actor_id": "claim_actor_mismatch",
            "scope": "claim_scope_mismatch",
            "target_reference": "claim_target_mismatch",
            "task_ref": "claim_task_mismatch",
            "operation": "claim_mutation_mismatch",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                substrate = InMemoryTemporalGraph()
                adapter = GovernedMemoryAdapter(substrate, tenant="shared:test", clock=Clock())
                coordinator = SharedWriteCoordinator(adapter, lambda _claim: True, self.claim_clock.now)
                claim = self._claim()
                coordinator._adapter = adapter
                acquired = coordinator.acquire(claim)
                self.assertEqual(acquired.status, ACQUIRED)
                proposal = replace(self._proposal(), **{field: value})
                result = coordinator.commit("claim:a", proposal, "mismatch")
                self.assertEqual(result.status, REJECTED)
                self.assertEqual(result.reason, expected[field])
                self.assertEqual(
                    [entry for entry in substrate.write_log if entry[0] == "write_fact"],
                    [],
                )

    def test_valid_claim_never_overrides_pama(self):
        acquired = self.coordinator.acquire(self._claim())
        self.assertEqual(acquired.status, ACQUIRED)

        blocked = self._proposal(actor_authority_resolved=False)
        result = self.coordinator.commit("claim:a", blocked, "must not commit")

        self.assertEqual(result.status, REJECTED)
        self.assertEqual(result.reason, "pama_not_committed")
        self.assertIsNotNone(result.commit_result)
        self.assertEqual(result.commit_result.decision.outcome, policy.BLOCK)
        self.assertFalse(result.commit_result.committed)
        self.assertEqual(len(self._writes()), 0)
        self.assertEqual(result.events[-1]["payload"]["pama_outcome"], policy.BLOCK)


if __name__ == "__main__":
    unittest.main()
