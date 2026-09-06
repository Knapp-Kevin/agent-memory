"""Adjudicated transition fixtures. ADR-037 step 4b-2, operator ruling 2026-09-05.

The flip removed the asserted discharge for `require_review`. Tests that used
`review_satisfied=True` as *scaffolding* — to reach behaviour that has nothing to
do with review discharge — need an honest route.

The pattern that was rejected
-----------------------------

A first attempt built a **change record**: "A became B, under authority X, for
commit Y", with a verifier proving the record described commit Y. That
establishes binding and integrity, and nothing more::

    proposal says B
      -> record says the proposal changes A to B
        -> verifier confirms it really does
          -> therefore changing A to B is justified

Circular. Neatly hashed, still circular. It was rejected.

The pattern that is sound
-------------------------

A `TransitionRule` **pre-exists the proposal** and adjudicates it. The evaluator
holds a corpus of rules; a test presents a proposal *against* one. The verifier
re-runs the rule, so a different proposed value, a stale pre-state, a wrong
target, or a rule the corpus does not hold all **refute**.

That is R3's `reproducible_procedure` — inputs, method, method version, result,
verifier — which R3 recognises as directly satisfying.

The decisive property, and there is a test for it
-------------------------------------------------

    Can a caller create both the proposal and a matching rule, after deciding
    what it wants, and satisfy the verifier?

No. `corpus_for` is the *evaluator's* construction. A caller building its own
`TransitionRuleCorpus` is not the evaluator, and the adapter under test resolves
verifiers from the registry its host configured — not from anything the caller
passes. See `test_fail_closed_review.py::TheLaunderingTest`.

Authority is deliberately absent here. Who authorised a change belongs in the
receipt and `discharge_authority`, or in a separate attestation. Letting it
elevate the evidential class would merge authority back into evidence.

Where no rule honestly covers a transition, `evidence_for` returns empty and the
proposal **parks**. That is the correct outcome, not a gap to paper over.
"""

from __future__ import annotations

from agentmem_ref import policy
from agentmem_ref.verification import (
    TRANSITION_VERIFIER,
    TransitionRule,
    TransitionRuleCorpus,
    VerifierRegistry,
)


def rule(*, rule_id: str, target: str, criterion: str, from_state: str,
         to_values: tuple[str, ...]) -> TransitionRule:
    """An adjudication authored ahead of the proposal it will judge."""
    return TransitionRule(
        rule_id=rule_id,
        target_reference=target,
        criterion=criterion,
        from_state=from_state,
        permitted_to_values=to_values,
    )


def corpus_for(*rules: TransitionRule) -> TransitionRuleCorpus:
    """The evaluator's corpus. A caller cannot write into this."""
    return TransitionRuleCorpus(rules)


def registry_for(corpus: TransitionRuleCorpus) -> VerifierRegistry:
    """The evaluator's verifier registry, trusting the corpus's adjudicator."""
    registry = VerifierRegistry()
    registry.register(TRANSITION_VERIFIER, corpus.verifier())
    return registry


def governed_adapter(substrate, tenant, clock, corpus, **kw):
    """An adapter whose host has configured verifier trust.

    The registry is supplied at construction, which is the whole point: a caller
    making a proposal cannot reach it.
    """
    from agentmem_ref.adapter import GovernedMemoryAdapter

    return GovernedMemoryAdapter(
        substrate, tenant, clock, verifier_registry=registry_for(corpus), **kw
    )


def commit_adjudicated(adapter, corpus, proposal, fact_text, *, pre_state,
                       criterion="value-correction", episode=None):
    """Commit with evidence from a rule the evaluator already held.

    Returns the commit result. When no rule covers the transition the evidence
    is empty and the proposal parks — deliberately, rather than being given
    something that looks like evidence.
    """
    evidence = corpus.evidence_for(
        target_reference=proposal.target_reference,
        criterion=criterion,
        pre_state=pre_state,
        proposed_value=fact_text,
    )
    return adapter.commit_proposal(proposal, fact_text, episode, evidence=evidence)


def attestation_for(proposal: policy.Proposal, *, principal: str = "human:reviewer"):
    """A separated human-confirmation attestation, for high/critical fixtures."""
    return policy.ExternalVerification(
        bound_proposal_id=proposal.proposal_id,
        verifier_principal_id=principal,
        authority_kind=policy.HUMAN_CONFIRMATION,
        max_risk_class="critical",
    )
