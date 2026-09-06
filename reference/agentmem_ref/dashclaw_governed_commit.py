"""Stateful commit seam for DashClaw-governed Agent Memory mutations.

The pure external-verdict adapter can resolve authority over the *requested*
scope, but a correction also needs authority over the scope already bound to the
logical target. ``GovernedMemoryAdapter`` intentionally keeps that scope metadata
private to its current reference runtime, so this #279 integration seam records
the scope of successful mutations it commits and fails closed when an existing
target cannot be reconstructed.

The stored binding contains scope facts, not the identity of the actor who
created them. On every later mutation, authority over the current target scope
is re-resolved for the *current acting identity*. This prevents an actor who is
authorized in Project A from correcting a Project B memory merely by naming its
logical target reference and proposing a Project A replacement.

This #279 profile is intentionally project-scoped. Authenticated organization
identity is not organization-wide memory mutation authority. The pure
``ProjectScopedAuthorityResolver`` is defined separately so provider transports
can reuse that boundary without importing the stateful commit runtime.

This registry is process-local by design in the current slice. Its restart-safe
persistence/reconstruction becomes part of #282 rather than being mistaken for
durable governance merely because the underlying memory substrate persists.
"""

from __future__ import annotations

from dataclasses import dataclass

from .adapter import GovernedMemoryAdapter
from .dashclaw_authority import ProjectScopedAuthorityResolver
from .dashclaw_external_verdict import (
    AuthorityRequest,
    AuthorityResolution,
    AuthorityResolver,
    BoundCommitResult,
    BoundMutation,
    commit_bound_mutation,
)


@dataclass(frozen=True)
class TargetScopeBinding:
    """Process-local scope facts bound to one current logical memory target."""

    memory_id: str
    org_id: str
    scope: str
    project_ref: str
    task_ref: str
    isolation_domain_refs: tuple[str, ...]
    authority_evidence_ref: str


class DashClawGovernedCommitter:
    """Revalidate requested and current-target scope before ordinary commit."""

    def __init__(self, memory: GovernedMemoryAdapter, authority_resolver: AuthorityResolver) -> None:
        self._memory = memory
        self._authority_resolver = authority_resolver
        self._target_scopes: dict[str, TargetScopeBinding] = {}

    @staticmethod
    def _requested_scope(mutation: BoundMutation) -> AuthorityRequest:
        proposal = mutation.proposal
        return AuthorityRequest(
            org_id=mutation.org_id,
            agent_id=mutation.agent_id,
            scope=proposal.scope,
            project_ref=proposal.project_ref,
            task_ref=proposal.task_ref,
            isolation_domain_refs=tuple(proposal.isolation_domain_refs),
            target_reference=proposal.target_reference,
        )

    @staticmethod
    def _current_scope_for_actor(mutation: BoundMutation, binding: TargetScopeBinding) -> AuthorityRequest:
        """Ask whether the current actor controls the target's existing scope."""
        return AuthorityRequest(
            org_id=mutation.org_id,
            agent_id=mutation.agent_id,
            scope=binding.scope,
            project_ref=binding.project_ref,
            task_ref=binding.task_ref,
            isolation_domain_refs=binding.isolation_domain_refs,
            target_reference=binding.memory_id,
        )

    @staticmethod
    def _same_scope(binding: TargetScopeBinding, requested: AuthorityRequest) -> bool:
        return (
            binding.org_id == requested.org_id
            and binding.scope == requested.scope
            and binding.project_ref == requested.project_ref
            and binding.task_ref == requested.task_ref
            and set(binding.isolation_domain_refs) == set(requested.isolation_domain_refs)
            and binding.memory_id == requested.target_reference
        )

    def _refusal(self, mutation: BoundMutation, code: str) -> BoundCommitResult:
        return BoundCommitResult(
            committed=False,
            refusal=code,
            input_identity=mutation.input_identity,
            proposal_digest=mutation.proposal_digest,
        )

    def commit(
        self,
        mutation: BoundMutation,
        *,
        approval_ref: str | None = None,
        approval_actor_id: str | None = None,
        approved_input_identity: str | None = None,
    ) -> BoundCommitResult:
        requested = self._requested_scope(mutation)
        requested_resolution = self._authority_resolver(requested)
        if not requested_resolution.authorized or not requested_resolution.evidence_ref:
            return self._refusal(mutation, "requested_scope_authority_unresolved")

        memory_id = mutation.proposal.target_reference
        current_uuid = self._memory.current_fact_uuid(memory_id)
        current_binding = self._target_scopes.get(memory_id)

        if current_uuid is not None and current_binding is None:
            # Existing governed state without a reconstructable target-scope
            # binding must not be corrected merely because the new requested
            # scope is authorized. #282 will make this state durable/replayable.
            return self._refusal(mutation, "target_scope_unresolved")

        if current_binding is not None:
            current_request = self._current_scope_for_actor(mutation, current_binding)
            current_resolution = self._authority_resolver(current_request)
            if not current_resolution.authorized or not current_resolution.evidence_ref:
                return self._refusal(mutation, "target_scope_authority_unresolved")

            # Ordinary correction/promotion cannot silently move an existing
            # logical target across isolation boundaries. Explicit scope
            # expansion remains visible to PAMA and still requires authority
            # over both the old and requested scopes before it can proceed.
            if mutation.proposal.operation != "scope_expansion" and not self._same_scope(
                current_binding,
                requested,
            ):
                return self._refusal(mutation, "target_scope_mismatch")

        result = commit_bound_mutation(
            self._memory,
            mutation,
            approval_ref=approval_ref,
            approval_actor_id=approval_actor_id,
            approved_input_identity=approved_input_identity,
        )
        if result.committed:
            self._target_scopes[memory_id] = TargetScopeBinding(
                memory_id=memory_id,
                org_id=mutation.org_id,
                scope=requested.scope,
                project_ref=requested.project_ref,
                task_ref=requested.task_ref,
                isolation_domain_refs=requested.isolation_domain_refs,
                authority_evidence_ref=requested_resolution.evidence_ref,
            )
        return result

    def target_scope_binding(self, memory_id: str) -> TargetScopeBinding | None:
        """Return the current process-local binding for evidence/tests only."""
        return self._target_scopes.get(memory_id)
