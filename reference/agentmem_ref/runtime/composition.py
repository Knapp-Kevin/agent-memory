"""Explicit policy gate for composing individually admitted memories.

Candidate-level recall admission and set-level context composition are distinct
capabilities. This module exercises the latter without inventing a universal
rule that different domains may never compose. A caller supplies explicit
policy constraints describing domain combinations that are prohibited in the
current context.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompositionCandidate:
    memory_ref: str
    domain_refs: tuple[str, ...]


@dataclass(frozen=True)
class CompositionConstraint:
    """One explicit set-level policy constraint.

    Every domain in ``prohibited_domain_set`` must be present in the proposed
    composition before the constraint is violated. The tuple is a set in
    semantic meaning; tuple order carries no hierarchy.
    """

    constraint_ref: str
    prohibited_domain_set: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class CompositionResult:
    allowed: bool
    memory_refs: tuple[str, ...]
    domain_refs: tuple[str, ...]
    violated_constraint_refs: tuple[str, ...] = ()
    reason: str = ""


def evaluate_composition(
    candidates: tuple[CompositionCandidate, ...],
    *,
    admitted_memory_refs: tuple[str, ...],
    constraints: tuple[CompositionConstraint, ...],
) -> CompositionResult:
    """Evaluate a proposed context composition after candidate-level admission.

    The caller must provide the memory references actually admitted by the
    governed recall step. A composition cannot use a candidate that was not
    admitted, and explicit set-level constraints are evaluated over the union
    of domain provenance carried by the proposed context.
    """
    admitted = set(admitted_memory_refs)
    requested_refs = tuple(candidate.memory_ref for candidate in candidates)

    if len(set(requested_refs)) != len(requested_refs):
        return CompositionResult(
            allowed=False,
            memory_refs=requested_refs,
            domain_refs=(),
            reason="duplicate_memory_reference",
        )

    for candidate in candidates:
        if not candidate.memory_ref or not candidate.domain_refs:
            return CompositionResult(
                allowed=False,
                memory_refs=requested_refs,
                domain_refs=(),
                reason="composition_candidate_scope_unresolved",
            )
        if candidate.memory_ref not in admitted:
            return CompositionResult(
                allowed=False,
                memory_refs=requested_refs,
                domain_refs=(),
                reason="composition_candidate_not_admitted",
            )

    domain_union = tuple(sorted({domain for candidate in candidates for domain in candidate.domain_refs}))
    present = set(domain_union)
    violated: list[str] = []

    for constraint in constraints:
        prohibited = set(constraint.prohibited_domain_set)
        if not constraint.constraint_ref or not prohibited:
            raise ValueError("composition constraints require a reference and prohibited domain set")
        if prohibited.issubset(present):
            violated.append(constraint.constraint_ref)

    if violated:
        return CompositionResult(
            allowed=False,
            memory_refs=requested_refs,
            domain_refs=domain_union,
            violated_constraint_refs=tuple(violated),
            reason="cross_domain_composition_prohibited",
        )

    return CompositionResult(
        allowed=True,
        memory_refs=requested_refs,
        domain_refs=domain_union,
    )
