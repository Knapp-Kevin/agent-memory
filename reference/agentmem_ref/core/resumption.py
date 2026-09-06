"""Governed resumption and criteria reporting: ADR-037 step 3 of 4, plus §4.

Step 1 gave a refusal somewhere to sit. Step 2 gave evidence a class and a
lineage. This is the first step that consumes both, and the first that
transitions rather than describes -- which is why it is graded L3. A resumption
that returns ``allow`` for a proposal that should still be parked is an
authority bypass, not a wrong shape.

The honest range of this module, measured
-----------------------------------------

``require_external_verification``  **resumable.** A bound, separated attestation
                                   discharges it through
                                   ``evaluate_with_external_verification``.

``require_review``                 **not resumable.** Evidence reaches the
                                   evaluator only as ``proposal.evidence_refs``,
                                   and M-EVID is an emptiness check -- appending
                                   qualified, independently verified evidence to
                                   a proposal that already had one reference
                                   changes the outcome not at all. Its only
                                   discharge today is ``review_satisfied`` plus
                                   ``approval_refs``: exactly the assertion path
                                   **step 4** converts.

That is not a shortfall; it is what ADR-037's ordering means. Step 2's headline
finding -- that evidence is a truthiness check -- applies to step 3's own
mechanism, and step 4 is the cycle that fixes it.

It does change what a criteria report must say. For a parked ``require_review``
the report names the assertion route as step 4's, rather than listing an
evidence criterion no evidence can currently satisfy. **Telling an agent to
collect evidence that cannot help is worse than telling it to wait.**

The strength ladder (ADR-037 R5)
-------------------------------

ADR-037 §4 requires stating "what independence bar applies at this risk class".
Step 3 reported it as ``undefined`` because no such bar existed in accepted
doctrine. The operator ruled on GH #379: **risk defines how strong.**

So the bar is not a count. **The count is one at every risk class** -- existence
of a qualifying independent dependence group, which R2's lineage grouping already
defines -- and risk varies the *strength* that one group must reach:

    low / medium    delegated_policy or human_confirmation
                    directly-satisfying class; an estimator may contribute
                    `asserted` binding status sufficient

    high / critical human_confirmation only
                    directly-satisfying class only
                    `verified` binding status required

Two of those three rows are pre-existing implemented doctrine: the authority kind
comes from ``policy.attestation_refusal`` and ``decision_overwrite._grant_refusal``,
and the estimator row is R3 verbatim. **The binding-status row is the new ruling.**

Nothing here holds a count, and nothing compares against an integer. ADR-037 line
128 describes exactly how the other choice decays.

The high/critical boundary is read from ``policy._HIGH_RISK`` **on every call**, so
a change to the risk boundary moves the ladder with it. A table built at import
would read it once and hold a copy, which is re-listing the constant with extra
steps.

What is in force today
----------------------

The ladder is what step 4 will enforce. Only one row bites now::

    require_external_verification  authority kind      IN FORCE (attestation_refusal)
                                   class, binding      pending step 4
    require_review                 every row           pending step 4

``_apply_review`` still discharges on ``review_satisfied`` plus ``approval_refs``
at any risk class, with no authority-kind check -- and ``require_review`` occupies
nine base-table cells at high or critical risk. Reporting the ladder as currently
binding there would state a bar the system does not enforce.

The evaluator boundary
----------------------

§3: "Resumption is an evaluator operation, not an actor operation." The
signature is the enforcement. Of everything ``resume_parked`` takes, only
``evidence`` is the actor's -- R1 permits an actor to produce evidence for its
own parked proposal. The attestation, the verifier registry, the current state
version and the current policy version are the evaluator's.

The current state version in particular **cannot** be read from the parked
record: the record was written before the delay that makes staleness a risk.
Reading it from there would replay a decision made under earlier conditions,
which is what §5 forbids.

Stdlib apart from the sibling reference modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from . import evidence_qualification as eq
from . import policy
from .pending_verification import ParkedProposal

#: §4 criterion kinds.
CRITERION_QUALIFICATION = "evidence_qualification"
CRITERION_SEPARATION = "authority_separation"
CRITERION_INDEPENDENCE = "independence"
CRITERION_GATE = "gate_not_yet_converted"

#: Enforcement status of a ladder row, per parked outcome.
IN_FORCE = "in force"
PENDING_STEP_4 = "pending ADR-037 step 4"

# Refusal reasons.
STALE = "stale_authorization"
NOT_PARKED = "proposal_not_parked"
BLOCK_UNREACHABLE = "resumption_would_yield_block"


@dataclass(frozen=True)
class UnmetCriterion:
    """One thing standing between a parked proposal and its discharge.

    ``bar`` is what would satisfy it. It is ``undefined`` exactly where doctrine
    defines nothing, and ``note`` then carries the open question rather than a
    number nobody ruled on.
    """

    kind: str
    detail: str
    satisfied_by: str = ""
    bar: str = ""
    note: str = ""


@dataclass(frozen=True)
class CriteriaReport:
    """ADR-037 §4: what would discharge *this* proposal."""

    proposal_id: str
    outcome: str
    unmet: tuple[UnmetCriterion, ...]


@dataclass(frozen=True)
class ResumptionResult:
    """A re-evaluation, never a permission.

    ``decision`` is what policy says now. Acting on it is the caller's business,
    exactly as with any other ``Decision``. Nothing here commits, writes to a
    substrate, or marks the parked record discharged.
    """

    proposal_id: str
    resumed: bool
    decision: policy.Decision | None
    refusal: str
    report: CriteriaReport
    policy_drift: bool = False
    admitted_refs: tuple[str, ...] = ()


def criteria_for(
    record: ParkedProposal,
    analysis: eq.DependenceAnalysis | None = None,
) -> CriteriaReport:
    """State which criteria are unmet, and what would satisfy each (§4)."""
    unmet: list[UnmetCriterion] = []
    outcome = record.decision.outcome

    if outcome == policy.REQUIRE_REVIEW:
        # ADR-037 step 4b-2 (entry #24). Before the flip this reported
        # CRITERION_GATE -- "wait for step 4" -- because evidence genuinely could
        # not move require_review while assertion discharged it. Step 4 has
        # landed, so that message is now stale and would point a caller at
        # completed work instead of at a traversable route.
        #
        # The real criterion is R5's ladder, which is now enforced.
        strength = strength_for(record.proposal.risk_class)
        unmet.append(
            UnmetCriterion(
                kind=CRITERION_QUALIFICATION,
                detail=(
                    "require_review requires qualified independent evidence; "
                    "review_satisfied plus approval_refs no longer discharges it"
                ),
                satisfied_by=(
                    "policy.evaluate_with_qualified_evidence with one qualifying "
                    "independent dependence group"
                ),
                bar=(
                    f"class: {strength['qualification_class']}; "
                    f"binding status: {strength['binding_status']}"
                ),
            )
        )
        if record.proposal.risk_class in policy._HIGH_RISK:
            unmet.append(
                UnmetCriterion(
                    kind=CRITERION_SEPARATION,
                    detail="human confirmation is also required at this risk class",
                    satisfied_by="policy.ExternalVerification",
                    bar=strength["authority_kind"],
                )
            )
    elif outcome == policy.REQUIRE_EXTERNAL_VERIFICATION:
        unmet.append(
            UnmetCriterion(
                kind=CRITERION_SEPARATION,
                detail=(
                    "an attestation bound to this proposal, whose verifier "
                    "principal is not the proposing actor"
                ),
                satisfied_by="policy.ExternalVerification",
                bar=(
                    "human_confirmation at high or critical risk; "
                    "risk ceiling at or above the proposal's"
                ),
            )
        )

    if analysis is not None and not analysis.qualifying_group_count(status=eq.VERIFIED):
        unmet.append(
            UnmetCriterion(
                kind=CRITERION_QUALIFICATION,
                detail="no independent group carries verified directly-satisfying evidence",
                satisfied_by=" or ".join(eq.DIRECTLY_SATISFYING),
                bar="at least one verified group; an estimator is never a sole basis",
            )
        )

    # §4's third requirement, resolved by ADR-037 R5. The risk class is DERIVED
    # from the record, never accepted from a caller: all three ladder rows key
    # off it, so one wrong value would understate every axis at once.
    strength = strength_for(record.proposal.risk_class)
    # ADR-037 step 4b-2 (entry #24). Before the flip only the authority row on
    # the external-verification path bit; every other row was pending step 4.
    # The flip enforces all three rows for require_review too, through
    # `evaluate_with_qualified_evidence`, so they are now in force. Leaving them
    # marked pending would point a caller at completed work.
    authority_status = IN_FORCE
    row_status = IN_FORCE
    unmet.append(
        UnmetCriterion(
            kind=CRITERION_INDEPENDENCE,
            detail=(
                "one qualifying independent dependence group. The count is one at "
                "every risk class; risk varies how strong that one must be."
            ),
            satisfied_by="a dependence group meeting the strength ladder below",
            bar=(
                f"authority: {strength['authority_kind']} ({authority_status}); "
                f"class: {strength['qualification_class']} ({row_status}); "
                f"binding status: {strength['binding_status']} ({row_status})"
            ),
            note="ADR-037 R5 (risk defines how strong), GH #379",
        )
    )
    return CriteriaReport(record.proposal_id, outcome, tuple(unmet))


def strength_for(risk_class: str) -> dict[str, str]:
    """The strength ladder for a risk class. ADR-037 R5.

    A pure lookup. It reports what would satisfy each axis and carries no
    authority of its own -- comparing supplied evidence against this is step 4's
    work, and no function here does it.

    **Delegates to** ``policy.strength_ladder_for``. The ladder is defined once,
    in the lower-level module, and read here: two copies of doctrine are two
    things that can diverge. ``policy._HIGH_RISK`` is still read on every call,
    so the ladder tracks the risk boundary rather than holding a stale copy.
    """
    return policy.strength_ladder_for(risk_class)


def resume_parked(
    record: ParkedProposal,
    *,
    evidence: Sequence[eq.EvidenceItem] = (),
    attestation: policy.ExternalVerification | None = None,
    verifiers: Mapping[str, Callable[[eq.EvidenceItem], bool]] | None = None,
    current_state_version: str = "",
    current_policy_version: str = "",
) -> ResumptionResult:
    """Re-evaluate a parked proposal against current policy and current state.

    Only ``evidence`` is the actor's contribution. Everything else is the
    evaluator's, which is what makes this an evaluator operation.
    """
    analysis = eq.group_by_dependence(evidence, verifiers=verifiers) if evidence else None

    # Staleness refuses BEFORE policy is re-evaluated (ADR-037 section 5, entry
    # #14). If the world moved, the proposal's authority no longer binds, and
    # evaluating would produce a decision against state it was never assessed
    # for. Refuse first, evaluate never.
    if current_state_version and record.proposal.state_snapshot:
        if current_state_version != record.proposal.state_snapshot:
            return ResumptionResult(
                proposal_id=record.proposal_id,
                resumed=False,
                decision=None,
                refusal=STALE,
                report=criteria_for(record, analysis),
            )

    drift = bool(current_policy_version) and current_policy_version != record.policy_version

    # Admitted evidence amends evidence_refs and NOTHING else. A resumption that
    # could rewrite risk_class or actor_id would be a proposal-rewriting
    # primitive, which at this risk grade is an authority bypass rather than a
    # wrong shape.
    admitted = _admitted_refs(analysis)
    proposal = record.proposal
    if admitted:
        merged = tuple(dict.fromkeys(tuple(proposal.evidence_refs) + admitted))
        proposal = _with_evidence_refs(proposal, merged)

    # Route through the function that can actually discharge. attestation_refusal
    # is NOT called here: evaluate_with_external_verification calls it
    # internally and surfaces the result in decision.reasons, and a second copy
    # of a control already correctly placed in the shared evaluator is two
    # things that can diverge.
    if attestation is not None:
        decision = policy.evaluate_with_external_verification(proposal, attestation)
    else:
        decision = policy.evaluate(proposal)

    if decision.outcome == policy.BLOCK:
        # Reachable only under policy drift, since evaluate is deterministic over
        # the retained proposal. Step 1 refuses to park a block because its
        # envelope prohibits enter_pending_verification; manufacturing one here
        # would defeat that guard from the other side.
        return ResumptionResult(
            proposal_id=record.proposal_id,
            resumed=False,
            decision=None,
            refusal=BLOCK_UNREACHABLE,
            report=criteria_for(record, analysis),
            policy_drift=drift,
            admitted_refs=admitted,
        )

    resumed = decision.outcome in (policy.ALLOW, policy.ALLOW_WITH_LEDGER)
    return ResumptionResult(
        proposal_id=record.proposal_id,
        resumed=resumed,
        decision=decision,
        refusal="" if resumed else decision.outcome,
        report=criteria_for(record, analysis),
        policy_drift=drift,
        admitted_refs=admitted,
    )


def _admitted_refs(analysis: eq.DependenceAnalysis | None) -> tuple[str, ...]:
    """Refs from groups that qualified. Unqualified opinion is not admitted."""
    if analysis is None:
        return ()
    admitted: list[str] = []
    for group in analysis.groups:
        if group in analysis.refuted_groups:
            continue
        admitted.extend(group)
    return tuple(dict.fromkeys(admitted))


def _with_evidence_refs(
    proposal: policy.Proposal, evidence_refs: tuple[str, ...]
) -> policy.Proposal:
    """Copy a proposal changing only ``evidence_refs`` (LD12, amend-only)."""
    import dataclasses

    return dataclasses.replace(proposal, evidence_refs=evidence_refs)
