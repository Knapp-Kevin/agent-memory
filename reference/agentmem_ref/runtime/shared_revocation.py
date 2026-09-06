"""Shared-memory membership revocation propagation.

A shared-space membership change is current authority state, not a command to
mutate every downstream store. This reference seam updates the shared-domain
recall membership and recomputes the authority inherited by derived state.
"""

from __future__ import annotations

from dataclasses import dataclass

from .scope_governance import DerivedScope, ScopeReconciliation, SourceScope, reconcile_derived_scope


@dataclass(frozen=True)
class SharedRevocationResult:
    domain_ref: str
    revoked_principal: str
    affected_source_refs: tuple[str, ...]
    reconciliation: ScopeReconciliation


def propagate_shared_membership_revocation(
    adapter,
    *,
    domain_ref: str,
    revoked_principal: str,
    remaining_members: tuple[str, ...],
    current_derived_scope: DerivedScope,
    source_scopes: tuple[SourceScope, ...],
) -> SharedRevocationResult:
    """Apply current membership and recompute downstream derived authority.

    Only sources actually bound to ``domain_ref`` lose the revoked principal
    from their allowed audience. Other source authority remains unchanged.
    The result reports whether the existing derived scope is still current; it
    does not silently rewrite, delete, or re-authorize the downstream object.
    """
    if not domain_ref or not revoked_principal:
        raise ValueError("shared revocation requires a domain and principal")
    if revoked_principal in remaining_members:
        raise ValueError("revoked principal cannot remain a member")

    adapter.set_shared_domain_members(domain_ref, remaining_members)

    updated: list[SourceScope] = []
    affected: list[str] = []
    for source in source_scopes:
        if domain_ref not in source.domain_refs:
            updated.append(source)
            continue
        affected.append(source.source_ref)
        updated.append(
            SourceScope(
                source_ref=source.source_ref,
                domain_refs=source.domain_refs,
                allowed_audiences=frozenset(
                    audience for audience in source.allowed_audiences if audience != revoked_principal
                ),
                allowed_purposes=source.allowed_purposes,
                restrictions=source.restrictions,
            )
        )

    reconciliation = reconcile_derived_scope(current_derived_scope, tuple(updated))
    return SharedRevocationResult(
        domain_ref=domain_ref,
        revoked_principal=revoked_principal,
        affected_source_refs=tuple(affected),
        reconciliation=reconciliation,
    )
