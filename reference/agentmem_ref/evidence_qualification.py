"""Evidence qualification and dependence lineage: ADR-037 step 2 of 4.

The shared evaluator's entire treatment of evidence today is one truthiness
check (``policy._apply_modifiers``)::

    if not proposal.evidence_refs:
        outcome = _strictest(outcome, REQUIRE_REVIEW)

So ``(" ",)`` clears the evidence modifier exactly as a content-addressed
receipt does, and ten copies of one reference are "evidence supplied". ADR-037
R2 and R3 say what evidence must actually be; this module makes that
computable. Nothing consumes it yet.

Out of scope, because ADR-037 fixes the order:

  step 3  governed resumption -- ``PendingVerificationRegistry`` is not imported
  step 4  fail-closed ``require_review`` -- ``policy.py`` is not modified

The temptation here is not resumption. It is wiring ``qualify`` into
``_apply_modifiers`` to fix that truthiness check, which is genuinely two lines.
**Those two lines are step 4**: they convert all 51 assertion sites at once,
with no resumption path built.

What this module does NOT claim
-------------------------------

Bindings are caller-supplied strings. ``digest="deadbeef"`` with
``verifier="trust-me"`` classifies as ``ARTIFACT_BOUND`` with nothing checked.
Presence of a binding raises the cost and names a verifier, so the claim becomes
checkable *by someone later*; it does not make the claim true.

That is why a class is always paired with a **binding status**, on the
precedent this repository already set twice -- ``ratification_evidence_verified``
vs ``_asserted`` (Loop 6) and ``review_discharge`` recording ``asserted`` vs
``verified`` (Loop 7):

    asserted  bindings present, no verifier has run       (the default)
    verified  a verifier ran against this item and passed
    refuted   a verifier ran and FAILED

``refuted`` is not bookkeeping. Without it the obvious implementation is
``"verified" if passed else "asserted"``, which makes "nobody checked this
digest" and "somebody checked it and it did not match" the same state. The
second is a refutation, and collapsing it lets a proposer whose artifact failed
keep re-presenting it as merely unchecked.

The honest claim for this module is therefore narrow and real: **evidence stops
being an opaque string and becomes a typed, ranked claim that names its own
verifier.** The caller-asserted pattern is not closed here.

Naming
------

``EVIDENCE_CLASSES`` is already taken. ``derivation_currentness`` uses it for
polarity and role -- ordinary, negative, adversarial, correction, incident --
with two schema consumers. R3 ranks *checkability*, an orthogonal axis, so this
module says ``qualification_class``. Merging the two axes is exactly what
ADR-037's "four variables, kept distinct" section exists to prevent.

Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, Mapping

# --- R3: qualification classes, ranked by checkability ----------------------

ARTIFACT_BOUND = "artifact_bound"
REPRODUCIBLE_PROCEDURE = "reproducible_procedure"
CALIBRATED_ESTIMATOR = "calibrated_estimator"
UNQUALIFIED = "unqualified"

#: Classes that satisfy an evidence criterion directly (R3).
DIRECTLY_SATISFYING = (ARTIFACT_BOUND, REPRODUCIBLE_PROCEDURE)

#: May contribute under explicit policy; never authority, never a sole basis.
CONTRIBUTING = (CALIBRATED_ESTIMATOR,)

# --- Binding status ---------------------------------------------------------

ASSERTED = "asserted"
VERIFIED = "verified"
REFUTED = "refuted"

#: Ordered weakest-first. A dependence group counts at the weakest disposition
#: it carries, so a group holding a refuted item is never counted as verified.
_STATUS_RANK = {REFUTED: 0, ASSERTED: 1, VERIFIED: 2}

#: Bindings each class requires. A class is derived from what is present.
_REQUIRED_BINDINGS: dict[str, tuple[str, ...]] = {
    ARTIFACT_BOUND: ("artifact_ref", "digest", "verifier"),
    REPRODUCIBLE_PROCEDURE: ("inputs", "method", "method_version", "result", "verifier"),
    CALIBRATED_ESTIMATOR: ("estimator_id", "estimator_version", "calibration_ref"),
}

#: Checked in rank order so the strongest satisfied class wins.
_CLASS_ORDER = (ARTIFACT_BOUND, REPRODUCIBLE_PROCEDURE, CALIBRATED_ESTIMATOR)


@dataclass(frozen=True)
class EvidenceItem:
    """One evidence reference and whatever it binds.

    Every binding is optional and every binding is caller-supplied. The class
    is derived from which are present; it is never read from the item.
    """

    ref: str

    # artifact-bound
    artifact_ref: str = ""
    digest: str = ""

    # reproducible procedure
    inputs: str = ""
    method: str = ""
    method_version: str = ""
    result: str = ""

    # either of the above
    verifier: str = ""

    # calibrated estimator
    estimator_id: str = ""
    estimator_version: str = ""
    calibration_ref: str = ""

    # lineage
    derived_from: tuple[str, ...] = ()
    failure_domain: str = ""

    def _binds(self, name: str) -> bool:
        return bool(str(getattr(self, name, "")).strip())


@dataclass(frozen=True)
class Qualification:
    """What an item is, and whether anyone checked."""

    ref: str
    qualification_class: str
    binding_status: str
    missing_bindings: tuple[str, ...] = ()

    @property
    def directly_satisfying(self) -> bool:
        return self.qualification_class in DIRECTLY_SATISFYING


def qualify(
    item: EvidenceItem,
    *,
    verifiers: Mapping[str, Callable[[EvidenceItem], bool]] | None = None,
) -> Qualification:
    """Derive an item's class from its bindings, and its status from a verifier.

    ``verifiers`` is the evaluator's registry, on the ``RatificationRegistry``
    precedent: a proposal *names* a verifier, it does not supply one. With no
    registry -- or with a name absent from it -- the status is ``asserted``.
    An item cannot reach ``verified`` by naming a verifier nobody holds.
    """
    qualification_class = UNQUALIFIED
    missing: tuple[str, ...] = ()
    for candidate in _CLASS_ORDER:
        required = _REQUIRED_BINDINGS[candidate]
        absent = tuple(name for name in required if not item._binds(name))
        if not absent:
            qualification_class = candidate
            missing = ()
            break
        if not missing or len(absent) < len(missing):
            missing = absent

    if qualification_class == UNQUALIFIED:
        # Nothing qualifying was bound: an opinion held at arm's length. Not an
        # error -- the corpus is full of these today, and step 4 needs to be
        # able to count them rather than crash on them.
        return Qualification(item.ref, UNQUALIFIED, ASSERTED, missing)

    status = ASSERTED
    if verifiers and item.verifier and item.verifier in verifiers:
        status = VERIFIED if verifiers[item.verifier](item) else REFUTED
    return Qualification(item.ref, qualification_class, status)


# --- R2: dependence lineage -------------------------------------------------


@dataclass(frozen=True)
class DependenceAnalysis:
    """Groups, counted by class rank and binding status together.

    Counts, never verdicts. Step 4 decides what is sufficient; this reports
    what there is, in the shape that decision needs, so step 4 need not reach
    past this result and re-derive the grouping.
    """

    groups: tuple[tuple[str, ...], ...]
    #: (qualification_class, binding_status) -> number of groups
    group_counts: Mapping[tuple[str, str], int]
    refuted_groups: tuple[tuple[str, ...], ...]

    @property
    def independent_group_count(self) -> int:
        """Total groups, INCLUDING unqualified ones.

        Deliberately not a measure of strength: ten distinct bare strings make
        ten groups and qualify nothing. Use :meth:`qualifying_group_count`,
        which is the number this is repeatedly mistaken for.
        """
        return len(self.groups)

    def qualifying_group_count(self, *, status: str = VERIFIED) -> int:
        """Groups whose evidence directly satisfies, at ``status`` or better.

        This answers step 4's actual question -- how many independent groups
        carry directly-satisfying evidence that was actually verified -- from
        the result alone.
        """
        floor = _STATUS_RANK[status]
        return sum(
            count
            for (klass, group_status), count in self.group_counts.items()
            if klass in DIRECTLY_SATISFYING and _STATUS_RANK[group_status] >= floor
        )

    def contributing_group_count(self, *, status: str = VERIFIED) -> int:
        """Estimator-only groups. R3: may contribute, never a sole basis."""
        floor = _STATUS_RANK[status]
        return sum(
            count
            for (klass, group_status), count in self.group_counts.items()
            if klass in CONTRIBUTING and _STATUS_RANK[group_status] >= floor
        )


class _Union:
    def __init__(self) -> None:
        self._parent: dict[str, str] = {}

    def add(self, key: str) -> None:
        self._parent.setdefault(key, key)

    def find(self, key: str) -> str:
        self.add(key)
        while self._parent[key] != key:
            self._parent[key] = self._parent[self._parent[key]]
            key = self._parent[key]
        return key

    def union(self, left: str, right: str) -> None:
        a, b = self.find(left), self.find(right)
        if a != b:
            self._parent[b] = a


def group_by_dependence(
    items: Iterable[EvidenceItem],
    *,
    verifiers: Mapping[str, Callable[[EvidenceItem], bool]] | None = None,
) -> DependenceAnalysis:
    """Collapse correlated items into dependence groups, derived from lineage.

    Three relations, jointly necessary -- dropping any one leaves a laundering
    route open:

    1. ``derived_from`` -- an item derived from another shares its group.
    2. Shared declared ``failure_domain`` -- distinct roots that fail together
       (the syndicated-report case), which derivation cannot compute.
    3. Identical ``(method, method_version, inputs)`` -- the same deterministic
       procedure run twice. R2: "a second deterministic reproduction of the
       same test is validation of one evidence item, not a second evidence
       item." Such a pair shares no derivation edge and need declare no failure
       domain, so relations 1 and 2 would report it as two independent groups.

    A declared ``failure_domain`` may only ever **merge** groups, never split
    one. That asymmetry is what makes accepting the declaration safe: the party
    being constrained can weaken its own independence claim and never
    strengthen it.
    """
    items = list(items)
    union = _Union()
    by_ref: dict[str, EvidenceItem] = {}
    for item in items:
        union.add(item.ref)
        by_ref[item.ref] = item

    domains: dict[str, str] = {}
    procedures: dict[tuple[str, str, str], str] = {}
    for item in items:
        for parent in item.derived_from:  # relation 1
            if parent in by_ref:
                union.union(parent, item.ref)
        if item.failure_domain:  # relation 2 -- merge only
            key = item.failure_domain
            if key in domains:
                union.union(domains[key], item.ref)
            else:
                domains[key] = item.ref
        if item.method and item.method_version and item.inputs:  # relation 3
            signature = (item.method, item.method_version, item.inputs)
            if signature in procedures:
                union.union(procedures[signature], item.ref)
            else:
                procedures[signature] = item.ref

    clustered: dict[str, list[str]] = {}
    for item in items:
        clustered.setdefault(union.find(item.ref), []).append(item.ref)

    qualifications = {item.ref: qualify(item, verifiers=verifiers) for item in items}

    groups: list[tuple[str, ...]] = []
    refuted: list[tuple[str, ...]] = []
    counts: dict[tuple[str, str], int] = {}
    for refs in clustered.values():
        group = tuple(refs)
        groups.append(group)
        members = [qualifications[ref] for ref in refs]
        # The group's class is the strongest evidence it holds; its status is
        # the WEAKEST disposition it carries. A group holding one verified and
        # one refuted item is internally contradictory -- counting it as
        # verified would hide the refutation, reintroducing at group level the
        # collapse `refuted` exists to prevent at item level. This module does
        # not adjudicate the contradiction; it must not conceal it.
        best_class = UNQUALIFIED
        for candidate in _CLASS_ORDER:
            if any(m.qualification_class == candidate for m in members):
                best_class = candidate
                break
        weakest = min(members, key=lambda m: _STATUS_RANK[m.binding_status]).binding_status
        counts[(best_class, weakest)] = counts.get((best_class, weakest), 0) + 1
        if any(m.binding_status == REFUTED for m in members):
            refuted.append(group)

    return DependenceAnalysis(
        groups=tuple(groups),
        group_counts=counts,
        refuted_groups=tuple(refuted),
    )
