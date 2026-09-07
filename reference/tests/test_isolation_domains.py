"""Executable isolation-domain recall evidence for accepted ADR-022.

These tests deliberately use one adapter, one agent identity, one tenant, and
one physical substrate. The only changing boundary is logical memory scope.
That is the property #68 needs to make load-bearing.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

TENANT = "tenant-a"
AGENT = "agent:planner"
DOMAIN_A = "domain:project-a"
DOMAIN_B = "domain:project-b"
COMPARTMENT_EXPORT = "compartment:export-controlled"
COMPARTMENT_LEGAL = "compartment:legal"


def proposal(
    reference: str,
    domain: str,
    project: str,
    task: str,
    *,
    additional_domains: tuple[str, ...] = (),
    required_domains: tuple[str, ...] = (),
) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=f"proposal:{reference}",
        actor_id=AGENT,
        charter_version="charter-1",
        target_reference=reference,
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("evidence:source",),
        tenant_ref=TENANT,
        purpose="assistance",
        isolation_domain_refs=(domain, *additional_domains),
        required_isolation_domain_refs=required_domains,
        project_ref=project,
        task_ref=task,
    )


class IsolationDomainRecallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.substrate = InMemoryTemporalGraph()
        self.adapter = GovernedMemoryAdapter(self.substrate, tenant=TENANT, clock=Clock())

    def _commit(
        self,
        reference: str,
        domain: str,
        project: str,
        task: str,
        *,
        additional_domains: tuple[str, ...] = (),
        required_domains: tuple[str, ...] = (),
    ):
        result = self.adapter.commit_proposal(
            proposal(
                reference,
                domain,
                project,
                task,
                additional_domains=additional_domains,
                required_domains=required_domains,
            ),
            "deployment credential rotation procedure",
        )
        self.assertTrue(result.committed)
        return result.fact_uuid

    def test_matching_domain_project_and_task_is_admitted(self):
        fact_uuid = self._commit("mem:a1", DOMAIN_A, "project-a", "task-1")

        recall = self.adapter.governed_recall(
            "deployment credential rotation procedure",
            RecallContext(
                target_domain_refs=(DOMAIN_A,),
                project_ref="project-a",
                task_ref="task-1",
                purpose="assistance",
            ),
        )

        self.assertIn(fact_uuid, recall.candidates)
        self.assertIn(fact_uuid, recall.admitted)

    def test_same_agent_same_tenant_wrong_project_is_blocked(self):
        fact_uuid = self._commit("mem:a2", DOMAIN_A, "project-a", "task-1")

        # Same adapter == same agent/runtime identity; same tenant and same
        # physical store. Semantic match remains exact enough to be a candidate.
        recall = self.adapter.governed_recall(
            "deployment credential rotation procedure",
            RecallContext(
                target_domain_refs=(DOMAIN_B,),
                project_ref="project-b",
                task_ref="task-1",
                purpose="assistance",
            ),
        )

        self.assertIn(fact_uuid, recall.candidates)
        self.assertNotIn(fact_uuid, recall.admitted)
        self.assertEqual(recall.refusals[fact_uuid], "isolation_domain_mismatch")

    def test_same_agent_same_project_wrong_task_is_blocked(self):
        fact_uuid = self._commit("mem:a3", DOMAIN_A, "project-a", "task-1")

        recall = self.adapter.governed_recall(
            "deployment credential rotation procedure",
            RecallContext(
                target_domain_refs=(DOMAIN_A,),
                project_ref="project-a",
                task_ref="task-2",
                purpose="assistance",
            ),
        )

        self.assertIn(fact_uuid, recall.candidates)
        self.assertNotIn(fact_uuid, recall.admitted)
        self.assertEqual(recall.refusals[fact_uuid], "task_scope_mismatch")

    def test_task_switch_does_not_carry_prior_context_authority(self):
        fact_uuid = self._commit("mem:a4", DOMAIN_A, "project-a", "task-1")

        first = self.adapter.governed_recall(
            "deployment credential rotation procedure",
            RecallContext((DOMAIN_A,), project_ref="project-a", task_ref="task-1"),
        )
        self.assertIn(fact_uuid, first.admitted)

        switched = self.adapter.governed_recall(
            "deployment credential rotation procedure",
            RecallContext((DOMAIN_B,), project_ref="project-b", task_ref="task-9"),
        )

        self.assertIn(fact_uuid, switched.candidates)
        self.assertNotIn(fact_uuid, switched.admitted)
        self.assertEqual(switched.refusals[fact_uuid], "isolation_domain_mismatch")

    def test_unresolved_target_domain_fails_closed_for_scoped_memory(self):
        fact_uuid = self._commit("mem:a5", DOMAIN_A, "project-a", "task-1")

        recall = self.adapter.governed_recall(
            "deployment credential rotation procedure",
            RecallContext(target_domain_refs=(), project_ref="project-a", task_ref="task-1"),
        )

        self.assertIn(fact_uuid, recall.candidates)
        self.assertNotIn(fact_uuid, recall.admitted)
        self.assertEqual(recall.refusals[fact_uuid], "isolation_domain_mismatch")

    def test_same_tenant_missing_required_compartment_is_blocked(self):
        fact_uuid = self._commit(
            "mem:a6",
            DOMAIN_A,
            "project-a",
            "task-1",
            additional_domains=(COMPARTMENT_EXPORT, COMPARTMENT_LEGAL),
            required_domains=(COMPARTMENT_EXPORT, COMPARTMENT_LEGAL),
        )

        recall = self.adapter.governed_recall(
            "deployment credential rotation procedure",
            RecallContext(
                target_domain_refs=(DOMAIN_A, COMPARTMENT_EXPORT),
                project_ref="project-a",
                task_ref="task-1",
                purpose="assistance",
            ),
        )

        self.assertIn(fact_uuid, recall.candidates)
        self.assertNotIn(fact_uuid, recall.admitted)
        self.assertEqual(recall.refusals[fact_uuid], "required_isolation_domain_missing")

    def test_all_required_compartments_allow_admission_when_other_gates_match(self):
        fact_uuid = self._commit(
            "mem:a7",
            DOMAIN_A,
            "project-a",
            "task-1",
            additional_domains=(COMPARTMENT_EXPORT, COMPARTMENT_LEGAL),
            required_domains=(COMPARTMENT_EXPORT, COMPARTMENT_LEGAL),
        )

        recall = self.adapter.governed_recall(
            "deployment credential rotation procedure",
            RecallContext(
                target_domain_refs=(DOMAIN_A, COMPARTMENT_EXPORT, COMPARTMENT_LEGAL),
                project_ref="project-a",
                task_ref="task-1",
                purpose="assistance",
            ),
        )

        self.assertIn(fact_uuid, recall.admitted)

    def test_ordinary_multiple_domain_refs_remain_alternative_routes(self):
        fact_uuid = self._commit(
            "mem:a8",
            DOMAIN_A,
            "project-a",
            "task-1",
            additional_domains=("domain:shared-route",),
        )

        recall = self.adapter.governed_recall(
            "deployment credential rotation procedure",
            RecallContext(
                target_domain_refs=(DOMAIN_A,),
                project_ref="project-a",
                task_ref="task-1",
            ),
        )

        self.assertIn(fact_uuid, recall.admitted)


if __name__ == "__main__":
    unittest.main()
