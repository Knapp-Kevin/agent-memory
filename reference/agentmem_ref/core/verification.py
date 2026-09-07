"""Evaluator-owned verifier trust and adjudicated transition rules.

ADR-037 step 4b-2, under the operator ruling of 2026-09-05.

Two things live here, and the reason they are together is that both answer the
same question: *who decides whether a claim has been checked?*

VerifierRegistry — trust is held, not passed
--------------------------------------------

PR #383 established that a module may supply a verifier *implementation* while
the evaluator owns the *registry*. A governed entry point that accepted a raw
mapping would hand registration back to the caller::

    commit_proposal(..., verifiers={"thing": lambda item: True})

which is ``review_satisfied=True`` rebuilt with more Python. So verifier trust
is a `VerifierRegistry` **configured on the adapter or runtime by its host**,
never a per-operation argument, and registering into one is not reachable from a
proposal or from its evidence.

TransitionRuleCorpus — the fixture must adjudicate, not describe
----------------------------------------------------------------

The tempting evidence shape is a record saying *"A became B, under authority X,
for commit Y"*, with a verifier proving the record describes commit Y. That
establishes **binding and integrity** and nothing else. It does not establish
that A *should* become B::

    proposal says B
      -> record says the proposal changes A to B
        -> verifier confirms it really does
          -> therefore changing A to B is justified

Circular. Neatly hashed, still circular.

A `TransitionRule` instead **pre-exists the proposal** and adjudicates it. It
binds a canonical pre-state, the permissible resulting state, and the criterion
being evaluated. The verifier re-runs the rule against the actual proposed
transition, so a different proposed value, a stale pre-state, a wrong target, or
a mismatched transition all **refute**.

That is R3's `reproducible_procedure` -- inputs, method, method version, result,
verifier -- which R3 already recognises as directly satisfying.

The test that decides the pattern
---------------------------------

    Can a caller create both the proposal and a matching rule, after deciding
    what it wants, and satisfy the verifier?

If yes, it is laundering. Here the answer is no: rules are resolved from a
corpus the evaluator holds, and a caller can only present a proposal against
one. A rule the corpus does not contain verifies nothing.

**Authority is deliberately absent from this module.** Who authorised a change
belongs in the receipt, in `discharge_authority`, or in a separate attestation.
Letting it elevate the evidential class would merge authority back into evidence
two cycles after they were separated.

Stdlib only.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Callable, Mapping

from .evidence_qualification import EvidenceItem

TRANSITION_VERIFIER = "evaluator:adjudicated-transition"

#: Bumped when the adjudication method changes, so evidence records which
#: version of the procedure produced its result (R3 requires method_version).
TRANSITION_METHOD_VERSION = "1"


class VerifierRegistry:
    """Which verifier implementations this evaluator trusts.

    Held by the host that constructs the adapter or runtime. A caller may
    present evidence *naming* a verifier; only the evaluator decides whether
    that name resolves to anything. An unresolved name leaves the item
    ``asserted``, which is step 2's behaviour and remains correct.
    """

    def __init__(self) -> None:
        self._verifiers: dict[str, Callable[[EvidenceItem], bool]] = {}

    def register(self, name: str, verifier: Callable[[EvidenceItem], bool]) -> None:
        """Trust a verifier implementation under this name.

        Deliberately not reachable from a proposal or its evidence: registering
        your own verifier is certifying your own evidence.
        """
        if not name or not callable(verifier):
            raise ValueError("a verifier registration needs a name and a callable")
        self._verifiers[name] = verifier

    def as_mapping(self) -> Mapping[str, Callable[[EvidenceItem], bool]]:
        """The resolved verifiers, for `qualify`/`group_by_dependence`."""
        return dict(self._verifiers)

    def __contains__(self, name: object) -> bool:
        return name in self._verifiers


@dataclass(frozen=True)
class TransitionRule:
    """An adjudication that pre-exists the proposal it will be applied to.

    ``permitted_to_values`` is the set of resulting states this rule allows from
    ``from_state``. The rule is authored ahead of time and held by the evaluator;
    a proposal is checked *against* it and cannot author it.
    """

    rule_id: str
    target_reference: str
    criterion: str
    from_state: str
    permitted_to_values: tuple[str, ...]

    def admits(self, *, pre_state: str, proposed_value: str, target: str) -> bool:
        """Re-run the rule against an actual proposed transition."""
        return (
            target == self.target_reference
            and pre_state == self.from_state
            and proposed_value in self.permitted_to_values
        )

    def digest(self) -> str:
        body = {
            "rule_id": self.rule_id,
            "target_reference": self.target_reference,
            "criterion": self.criterion,
            "from_state": self.from_state,
            "permitted_to_values": list(self.permitted_to_values),
        }
        canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class TransitionRuleCorpus:
    """Adjudicated rules the evaluator holds. Callers read; they do not write.

    A caller presents a proposal; the evaluator resolves whether a rule already
    covers that target and criterion. A rule the corpus does not contain cannot
    be conjured by presenting evidence that cites it.
    """

    def __init__(self, rules: tuple[TransitionRule, ...] = ()) -> None:
        self._rules = {(r.target_reference, r.criterion): r for r in rules}

    def resolve(self, *, target_reference: str, criterion: str) -> TransitionRule | None:
        return self._rules.get((target_reference, criterion))

    def evidence_for(
        self, *, target_reference: str, criterion: str, pre_state: str, proposed_value: str
    ) -> tuple[EvidenceItem, ...]:
        """Evidence citing a rule that already exists, applied to this transition.

        Returns empty when no rule covers the transition -- which is the correct
        outcome, and the one that makes the proposal park. Evidence is not
        manufactured to fit a proposal that no adjudication covers.
        """
        rule = self.resolve(target_reference=target_reference, criterion=criterion)
        if rule is None:
            return ()
        return (
            EvidenceItem(
                ref=rule.rule_id,
                inputs=f"{target_reference}@{pre_state}->{proposed_value}",
                method=rule.rule_id,
                method_version=TRANSITION_METHOD_VERSION,
                result="admitted" if rule.admits(
                    pre_state=pre_state, proposed_value=proposed_value,
                    target=target_reference) else "refused",
                verifier=TRANSITION_VERIFIER,
                failure_domain=f"transition-rule:{rule.rule_id}",
            ),
        )

    def verifier(self):
        """The adjudicating verifier, for the evaluator to register.

        Re-derives the rule from the corpus and re-runs it against the inputs the
        evidence carries. Refutes a stale pre-state, a wrong target, a mismatched
        transition, or a rule this corpus does not hold.
        """

        def verify(item: EvidenceItem) -> bool:
            rule = next(
                (r for r in self._rules.values() if r.rule_id == item.method), None
            )
            if rule is None:
                # A rule this evaluator does not hold verifies nothing, however
                # well-formed the evidence citing it looks.
                return False
            if item.method_version != TRANSITION_METHOD_VERSION:
                return False
            try:
                target_and_pre, proposed = item.inputs.split("->", 1)
                target, pre_state = target_and_pre.rsplit("@", 1)
            except ValueError:
                return False
            if not rule.admits(
                pre_state=pre_state, proposed_value=proposed, target=target
            ):
                return False
            return item.result == "admitted"

        return verify
