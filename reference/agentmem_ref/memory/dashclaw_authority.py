"""Pure project-scoped authority wrapper for DashClaw provider integration.

This module keeps the provider-side scope profile independent from the stateful
Agent Memory commit path. It is intentionally tiny: authenticated DashClaw
identity is not organization-wide mutation authority, and an exact project
binding is required before a trusted resolver may authorize the request.
"""

from __future__ import annotations

from .dashclaw_external_verdict import (
    AuthorityRequest,
    AuthorityResolution,
    AuthorityResolver,
)


class ProjectScopedAuthorityResolver:
    """Constrain any trusted resolver to the bounded DashClaw project profile."""

    def __init__(self, delegate: AuthorityResolver) -> None:
        self._delegate = delegate

    def __call__(self, request: AuthorityRequest) -> AuthorityResolution:
        if not request.project_ref:
            return AuthorityResolution(authorized=False, reason_code="project_scope_required")
        if request.scope != request.project_ref:
            return AuthorityResolution(authorized=False, reason_code="scope_project_mismatch")
        domains = set(request.isolation_domain_refs)
        if request.project_ref not in domains:
            return AuthorityResolution(authorized=False, reason_code="project_isolation_not_bound")
        if request.task_ref and request.task_ref not in domains:
            return AuthorityResolution(authorized=False, reason_code="task_isolation_not_bound")
        return self._delegate(request)
