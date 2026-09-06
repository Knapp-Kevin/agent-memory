from __future__ import annotations

import unittest

from agentmem_ref.dashclaw_external_verdict import (
    AuthorityRequest,
    StaticAuthorityGrant,
    StaticAuthorityResolver,
)
from agentmem_ref.dashclaw_governed_commit import ProjectScopedAuthorityResolver


ORG = "fixture-org"
AGENT = "release-agent"
PROJECT = "project:fixture"
TASK = "task:release"


class ProjectScopedAuthorityResolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = ProjectScopedAuthorityResolver(
            StaticAuthorityResolver(
                (
                    StaticAuthorityGrant(
                        org_id=ORG,
                        agent_id=AGENT,
                        isolation_domain_refs=(PROJECT, TASK),
                        evidence_ref="authority-grant:fixture",
                    ),
                )
            )
        )

    def request(
        self,
        *,
        scope: str = PROJECT,
        project_ref: str = PROJECT,
        task_ref: str = "",
        domains: tuple[str, ...] = (f"org:{ORG}", PROJECT),
    ) -> AuthorityRequest:
        return AuthorityRequest(
            org_id=ORG,
            agent_id=AGENT,
            scope=scope,
            project_ref=project_ref,
            task_ref=task_ref,
            isolation_domain_refs=domains,
            target_reference="repo:fixture:release-branch",
        )

    def test_exact_project_scope_can_resolve(self) -> None:
        result = self.resolver(self.request())
        self.assertTrue(result.authorized)
        self.assertEqual(result.evidence_ref, "authority-grant:fixture")

    def test_authenticated_org_identity_is_not_org_wide_mutation_authority(self) -> None:
        result = self.resolver(
            self.request(
                scope=f"org:{ORG}",
                project_ref="",
                domains=(f"org:{ORG}",),
            )
        )
        self.assertFalse(result.authorized)
        self.assertEqual(result.reason_code, "project_scope_required")

    def test_scope_must_equal_project(self) -> None:
        result = self.resolver(self.request(scope="project:other"))
        self.assertFalse(result.authorized)
        self.assertEqual(result.reason_code, "scope_project_mismatch")

    def test_project_must_be_bound_isolation_domain(self) -> None:
        result = self.resolver(self.request(domains=(f"org:{ORG}",)))
        self.assertFalse(result.authorized)
        self.assertEqual(result.reason_code, "project_isolation_not_bound")

    def test_task_must_be_bound_when_present(self) -> None:
        result = self.resolver(self.request(task_ref=TASK))
        self.assertFalse(result.authorized)
        self.assertEqual(result.reason_code, "task_isolation_not_bound")

    def test_bound_task_can_resolve(self) -> None:
        result = self.resolver(
            self.request(
                task_ref=TASK,
                domains=(f"org:{ORG}", PROJECT, TASK),
            )
        )
        self.assertTrue(result.authorized)


if __name__ == "__main__":
    unittest.main()
