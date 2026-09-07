"""Isolation-domain scope propagation for derived memory.

Executable evidence for ADR-022. A transform may change representation but does
not erase source authority constraints.

The safe default is:

    derived audience <= intersection(source audiences)
    derived purpose  <= intersection(source purposes)
    derived restrictions >= union(source restrictions)

An empty compatible audience or purpose is not silently widened. It is a hard
failure that requires a separate governed scope-promotion decision.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core import policy


class ScopeConflict(ValueError):
    """Raised when source scopes have no compatible derived authority."""


@dataclass(frozen=True)
class SourceScope:
    source_ref: str
    domain_refs: frozenset[str]
    allowed_audiences: frozenset[str]
    allowed_purposes: frozenset[str]
    restrictions: frozenset[str] = frozenset()


@dataclass(frozen=True)
class DerivedScope:
    source_refs: tuple[str, ...]
    domain_refs: frozenset[str]
    allowed_audiences: frozenset[str]
    allowed_purposes: frozenset[str]
    restrictions: frozenset[str]


@dataclass(frozen=True)
class ScopeReconciliation:
    """Result of re-evaluating derived authority after source scope changes."""

    inherited_scope: DerivedScope | None
    current_scope: DerivedScope
    current_for_use: bool
    requires_narrowing: bool
    incompatible: bool = False
    reason: str = ""


def derive_scope(sources: tuple[SourceScope, ...]) -> DerivedScope:
    """Compute the default scope a derivation may inherit without promotion."""
    if not sources:
        raise ScopeConflict("derived scope requires at least one source")

    domains = set(sources[0].domain_refs)
    audiences = set(sources[0].allowed_audiences)
    purposes = set(sources[0].allowed_purposes)
    restrictions: set[str] = set()

    for source in sources:
        domains.intersection_update(source.domain_refs)
        audiences.intersection_update(source.allowed_audiences)
        purposes.intersection_update(source.allowed_purposes)
        restrictions.update(source.restrictions)

    if not domains:
        raise ScopeConflict("source isolation domains have no compatible intersection")
    if not audiences:
        raise ScopeConflict("source audiences have no compatible intersection")
    if not purposes:
        raise ScopeConflict("source purposes have no compatible intersection")

    return DerivedScope(
        source_refs=tuple(source.source_ref for source in sources),
        domain_refs=frozenset(domains),
        allowed_audiences=frozenset(audiences),
        allowed_purposes=frozenset(purposes),
        restrictions=frozenset(restrictions),
    )


def scope_broadens(inherited: DerivedScope, requested: DerivedScope) -> bool:
    """Return True when requested scope would weaken any inherited constraint."""
    return (
        not requested.domain_refs.issubset(inherited.domain_refs)
        or not requested.allowed_audiences.issubset(inherited.allowed_audiences)
        or not requested.allowed_purposes.issubset(inherited.allowed_purposes)
        or not requested.restrictions.issuperset(inherited.restrictions)
    )


def reconcile_derived_scope(
    current: DerivedScope,
    current_sources: tuple[SourceScope, ...],
) -> ScopeReconciliation:
    """Recompute inherited authority after a source scope change.

    A derived object that remains broader than the newly inherited scope is not
    current for use until it is narrowed or rebuilt through a governed path.
    If the sources no longer have any compatible scope at all, the derivation
    fails closed rather than retaining its historical authority envelope.
    """
    expected_refs = tuple(source.source_ref for source in current_sources)
    if current.source_refs != expected_refs:
        return ScopeReconciliation(
            inherited_scope=None,
            current_scope=current,
            current_for_use=False,
            requires_narrowing=False,
            incompatible=True,
            reason="source_basis_changed",
        )

    try:
        inherited = derive_scope(current_sources)
    except ScopeConflict as exc:
        return ScopeReconciliation(
            inherited_scope=None,
            current_scope=current,
            current_for_use=False,
            requires_narrowing=False,
            incompatible=True,
            reason=str(exc),
        )

    broader = scope_broadens(inherited, current)
    return ScopeReconciliation(
        inherited_scope=inherited,
        current_scope=current,
        current_for_use=not broader,
        requires_narrowing=broader,
        reason="derived_scope_exceeds_current_source_authority" if broader else "",
    )


def evaluate_scope_promotion(proposal: policy.Proposal, inherited: DerivedScope, requested: DerivedScope) -> policy.Decision:
    """Evaluate intentional broadening through PAMA rather than derivation logic.

    A non-broadening request needs no scope-expansion authority. A broadening
    request must be represented as `scope_expansion`; callers cannot relabel it
    as a harmless transform to obtain a weaker envelope.
    """
    if not scope_broadens(inherited, requested):
        return policy.Decision(
            outcome=policy.ALLOW,
            permitted_actions=("retain_inherited_scope",),
            prohibited_actions=(),
            reasons=("requested scope does not broaden inherited constraints",),
        )

    if proposal.operation != "scope_expansion":
        return policy.Decision(
            outcome=policy.BLOCK,
            permitted_actions=(),
            prohibited_actions=(proposal.operation, "scope_expansion"),
            reasons=("scope broadening must be evaluated as scope_expansion",),
        )

    return policy.evaluate(proposal)
