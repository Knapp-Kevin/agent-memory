"""ADR-037 step 2: evidence gets a class it cannot claim, and a lineage it cannot escape.

Written against the plausible wrong implementation. That one reads a
``qualification_class`` field off the item, treats a failing verifier as merely
unverified, groups by a declared label, and reports one flattering total. Each
has a test here that fails.
"""

from __future__ import annotations

import unittest

from agentmem_ref.evidence_qualification import (
    ARTIFACT_BOUND,
    ASSERTED,
    CALIBRATED_ESTIMATOR,
    REFUTED,
    REPRODUCIBLE_PROCEDURE,
    UNQUALIFIED,
    VERIFIED,
    DependenceAnalysis,
    EvidenceItem,
    group_by_dependence,
    qualify,
)


def _artifact(ref="a", **kw):
    base = dict(artifact_ref="art://x", digest="sha256:abc", verifier="digest-check")
    base.update(kw)
    return EvidenceItem(ref=ref, **base)


def _procedure(ref="p", **kw):
    base = dict(
        inputs="in-1", method="pytest", method_version="8.0", result="pass",
        verifier="rerun",
    )
    base.update(kw)
    return EvidenceItem(ref=ref, **base)


def _estimator(ref="e", **kw):
    base = dict(
        estimator_id="model-x", estimator_version="v1", calibration_ref="cal://2026-09"
    )
    base.update(kw)
    return EvidenceItem(ref=ref, **base)


class ClassIsDerivedFromBindings(unittest.TestCase):
    """DoD 1-4 -- R3's ranking, computed from what an item carries."""

    def test_artifact_bound_requires_all_three_bindings(self):
        self.assertEqual(qualify(_artifact()).qualification_class, ARTIFACT_BOUND)
        for dropped in ("artifact_ref", "digest", "verifier"):
            item = _artifact(**{dropped: ""})
            q = qualify(item)
            self.assertNotEqual(
                q.qualification_class, ARTIFACT_BOUND, f"{dropped} must be required"
            )
            self.assertIn(dropped, q.missing_bindings)

    def test_reproducible_procedure_requires_all_five_bindings(self):
        self.assertEqual(
            qualify(_procedure()).qualification_class, REPRODUCIBLE_PROCEDURE
        )
        for dropped in ("inputs", "method", "method_version", "result", "verifier"):
            q = qualify(_procedure(**{dropped: ""}))
            self.assertNotEqual(q.qualification_class, REPRODUCIBLE_PROCEDURE)
            self.assertIn(dropped, q.missing_bindings)

    def test_calibrated_estimator_requires_its_three_bindings(self):
        self.assertEqual(
            qualify(_estimator()).qualification_class, CALIBRATED_ESTIMATOR
        )
        for dropped in ("estimator_id", "estimator_version", "calibration_ref"):
            q = qualify(_estimator(**{dropped: ""}))
            self.assertNotEqual(q.qualification_class, CALIBRATED_ESTIMATOR)

    def test_a_caller_cannot_declare_its_own_class(self):
        """DoD 4. This is the test that separates this cycle from six prior defects.

        ``EvidenceItem`` has no ``qualification_class`` field at all, so the
        claim cannot even be expressed -- the strongest form of the guarantee.
        """
        self.assertNotIn("qualification_class", EvidenceItem.__dataclass_fields__)
        with self.assertRaises(TypeError):
            EvidenceItem(ref="x", qualification_class=ARTIFACT_BOUND)
        # And the empty claim, made the only way it can be, still fails.
        self.assertEqual(
            qualify(EvidenceItem(ref=ARTIFACT_BOUND)).qualification_class, UNQUALIFIED
        )

    def test_bare_strings_are_unqualified_not_an_error(self):
        """DoD 5, LD3. The corpus is full of these; step 4 must be able to count them."""
        for ref in ("i-said-so", " ", "receipt-ish"):
            q = qualify(EvidenceItem(ref=ref))
            self.assertEqual(q.qualification_class, UNQUALIFIED)
            self.assertFalse(q.directly_satisfying)


class BindingStatusSaysWhetherAnyoneChecked(unittest.TestCase):
    """DoD 4b-4d -- audit V1 and V4."""

    def test_default_is_asserted_because_no_verifier_has_run(self):
        q = qualify(_artifact())
        self.assertEqual(q.qualification_class, ARTIFACT_BOUND)
        self.assertEqual(q.binding_status, ASSERTED)

    def test_passing_verifier_yields_verified(self):
        q = qualify(_artifact(), verifiers={"digest-check": lambda item: True})
        self.assertEqual(q.binding_status, VERIFIED)

    def test_failing_verifier_yields_refuted_never_asserted(self):
        """DoD 4c / audit V4.

        ``"verified" if passed else "asserted"`` is the implementation this
        test exists to fail. It would make "nobody checked this digest" and
        "somebody checked it and it did not match" the same state, letting a
        proposer whose artifact failed keep re-presenting it as unchecked.
        """
        q = qualify(_artifact(), verifiers={"digest-check": lambda item: False})
        self.assertEqual(q.binding_status, REFUTED)
        self.assertNotEqual(q.binding_status, ASSERTED)

    def test_naming_a_verifier_nobody_holds_stays_asserted(self):
        """DoD 4d. The registry is the evaluator's; naming is not holding."""
        q = qualify(_artifact(verifier="my-own-rubber-stamp"), verifiers={})
        self.assertEqual(q.binding_status, ASSERTED)
        q2 = qualify(
            _artifact(verifier="my-own-rubber-stamp"),
            verifiers={"digest-check": lambda item: True},
        )
        self.assertEqual(q2.binding_status, ASSERTED)

    def test_unqualified_item_cannot_be_verified_into_standing(self):
        q = qualify(
            EvidenceItem(ref="opinion", verifier="digest-check"),
            verifiers={"digest-check": lambda item: True},
        )
        self.assertEqual(q.qualification_class, UNQUALIFIED)


class DependenceIsDerivedFromLineage(unittest.TestCase):
    """DoD 6-9 -- R2's three relations."""

    def test_relation_1_derived_from_joins(self):
        root = _artifact("root")
        derived = _artifact("summary", derived_from=("root",))
        analysis = group_by_dependence([root, derived])
        self.assertEqual(analysis.independent_group_count, 1)

    def test_relation_2_shared_failure_domain_joins_distinct_roots(self):
        """The syndicated-report case: derivation cannot compute this one."""
        a = _artifact("news-a", failure_domain="syndicated-report")
        b = _artifact("news-b", failure_domain="syndicated-report")
        self.assertEqual(group_by_dependence([a, b]).independent_group_count, 1)

    def test_relation_3_identical_procedure_run_twice_is_one_item(self):
        """DoD 9 / R2's second deterministic reproduction.

        Asserted with no ``derived_from`` edge and no shared ``failure_domain``,
        so the test cannot pass through relation 1 or 2. Under the two-relation
        algorithm this reported two independent groups -- the laundering R2
        names by name.
        """
        first = _procedure("run-1")
        second = _procedure("run-2")
        self.assertEqual(first.derived_from, ())
        self.assertEqual(second.derived_from, ())
        self.assertEqual(first.failure_domain, "")
        self.assertEqual(second.failure_domain, "")
        self.assertEqual(group_by_dependence([first, second]).independent_group_count, 1)

    def test_differing_procedure_version_is_two_groups(self):
        """The negative control for relation 3: it must not over-merge."""
        first = _procedure("run-1")
        second = _procedure("run-2", method_version="9.0")
        self.assertEqual(group_by_dependence([first, second]).independent_group_count, 2)

    def test_a_declaration_cannot_split_a_lineage_connected_pair(self):
        """DoD 8, LD4. Merge-only asymmetry, tested against a hostile declaration."""
        root = _artifact("root", failure_domain="domain-a")
        derived = _artifact("summary", derived_from=("root",), failure_domain="domain-b")
        self.assertEqual(group_by_dependence([root, derived]).independent_group_count, 1)

    def test_genuinely_independent_items_stay_separate(self):
        a = _artifact("a")
        b = _procedure("b")
        self.assertEqual(group_by_dependence([a, b]).independent_group_count, 2)


class CountingDiscipline(unittest.TestCase):
    """DoD 10, 11, 15, 16 -- audit C1. Every edge fails toward overstating."""

    def test_ten_copies_of_one_reference_are_one_group(self):
        """DoD 11. Row count is not corroboration."""
        items = [_artifact("same", derived_from=("same",)) for _ in range(10)]
        # Same ref repeated: they are literally one item, ten times.
        self.assertEqual(group_by_dependence(items).independent_group_count, 1)

    def test_answering_step_4s_question_from_the_result_alone(self):
        """DoD 10 / audit V5.

        How many independent groups carry directly-satisfying evidence that was
        actually verified? Answered without reaching into the raw items and
        without re-deriving the grouping.
        """
        verifiers = {"digest-check": lambda item: True, "rerun": lambda item: True}
        analysis = group_by_dependence(
            [_artifact("a"), _procedure("p"), _estimator("e")], verifiers=verifiers
        )
        self.assertEqual(analysis.qualifying_group_count(status=VERIFIED), 2)
        self.assertEqual(analysis.contributing_group_count(status=VERIFIED), 0)
        self.assertEqual(analysis.independent_group_count, 3)

    def test_asserted_and_verified_groups_are_distinguishable(self):
        """The distinction LD2 introduces must survive into the counts."""
        unchecked = group_by_dependence([_artifact("a")])
        checked = group_by_dependence(
            [_artifact("a")], verifiers={"digest-check": lambda item: True}
        )
        self.assertEqual(unchecked.qualifying_group_count(status=VERIFIED), 0)
        self.assertEqual(checked.qualifying_group_count(status=VERIFIED), 1)
        self.assertEqual(unchecked.qualifying_group_count(status=ASSERTED), 1)

    def test_a_group_counts_at_its_weakest_status(self):
        """DoD 15 / audit C1.

        A group holding one verified and one refuted item is internally
        contradictory. Counting it as verified would hide the refutation --
        reintroducing at group level the collapse ``refuted`` prevents at item
        level.
        """
        good = _artifact("good", failure_domain="shared")
        bad = _artifact("bad", verifier="strict", failure_domain="shared")
        analysis = group_by_dependence(
            [good, bad],
            verifiers={"digest-check": lambda item: True, "strict": lambda item: False},
        )
        self.assertEqual(analysis.independent_group_count, 1)
        self.assertEqual(analysis.qualifying_group_count(status=VERIFIED), 0)
        self.assertEqual(len(analysis.refuted_groups), 1)

    def test_no_total_mixes_unqualified_groups_with_qualifying_ones(self):
        """DoD 16 / audit C1. Raising the count does not raise the class."""
        opinions = [EvidenceItem(ref=f"opinion-{n}") for n in range(10)]
        analysis = group_by_dependence(opinions)
        self.assertEqual(analysis.independent_group_count, 10)
        self.assertEqual(analysis.qualifying_group_count(status=ASSERTED), 0)
        self.assertEqual(analysis.contributing_group_count(status=ASSERTED), 0)

    def test_an_estimator_is_never_counted_as_directly_satisfying(self):
        """LD8, R3. It may contribute; it is never a sole basis."""
        analysis = group_by_dependence(
            [_estimator("e1"), _estimator("e2", failure_domain="d")],
            verifiers={"digest-check": lambda item: True},
        )
        self.assertEqual(analysis.qualifying_group_count(status=ASSERTED), 0)
        self.assertGreaterEqual(analysis.contributing_group_count(status=ASSERTED), 1)


class ReportsWhatEvidenceIsNeverWhatMayHappen(unittest.TestCase):
    """DoD 12, LD7. Step 4's verdict must not arrive early."""

    _FORBIDDEN = (
        "discharges", "sufficient", "sufficient_for", "decide", "decision",
        "outcome", "permit", "permitted", "authorize", "approve", "allow",
        "evaluate", "risk_class", "resume",
    )

    def test_module_exposes_no_verdict_returning_surface(self):
        import agentmem_ref.evidence_qualification as module

        public = {n for n in dir(module) if not n.startswith("_")}
        for forbidden in self._FORBIDDEN:
            self.assertNotIn(forbidden, public)

    def test_analysis_exposes_counts_not_verdicts(self):
        analysis = group_by_dependence([_artifact("a")])
        surface = {n for n in dir(analysis) if not n.startswith("_")}
        self.assertEqual(
            surface,
            {"groups", "group_counts", "refuted_groups", "independent_group_count",
             "qualifying_group_count", "contributing_group_count"},
        )
        for forbidden in self._FORBIDDEN:
            self.assertNotIn(forbidden, surface)

    def test_no_function_accepts_a_risk_class(self):
        """Accepting one invites returning a verdict against it."""
        import inspect

        for func in (qualify, group_by_dependence):
            self.assertNotIn("risk_class", inspect.signature(func).parameters)

    def test_qualification_reports_no_permission(self):
        q = qualify(_artifact())
        surface = {n for n in dir(q) if not n.startswith("_")}
        self.assertEqual(
            surface,
            {"ref", "qualification_class", "binding_status", "missing_bindings",
             "directly_satisfying"},
        )

    def test_pending_verification_is_not_imported(self):
        """Connecting qualification to parking is step 3's work.

        Checked over the module's actual import statements rather than its
        text, so the docstring may say what is deliberately absent.
        """
        import ast
        import inspect

        import agentmem_ref.evidence_qualification as module

        imported: set[str] = set()
        for node in ast.walk(ast.parse(inspect.getsource(module))):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                imported.update(alias.name for alias in node.names)

        self.assertNotIn("pending_verification", imported)
        self.assertNotIn("PendingVerificationRegistry", imported)
        self.assertNotIn("policy", imported)


class NameAxesStayDistinct(unittest.TestCase):
    """LD1 -- the collision found in research, before it was spent."""

    def test_does_not_redefine_the_existing_evidence_classes_vocabulary(self):
        from agentmem_ref import derivation_currentness, evidence_qualification

        self.assertEqual(
            derivation_currentness.EVIDENCE_CLASSES,
            {"ordinary", "negative", "adversarial", "correction", "incident"},
        )
        self.assertFalse(hasattr(evidence_qualification, "EVIDENCE_CLASSES"))
        self.assertFalse(hasattr(evidence_qualification, "evidence_class"))
        self.assertIn(
            "qualification_class", Qualification_fields()
        )


def Qualification_fields():
    from agentmem_ref.evidence_qualification import Qualification

    return Qualification.__dataclass_fields__


if __name__ == "__main__":
    unittest.main()
