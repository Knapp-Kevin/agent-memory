"""The marker meta-test. ADR-037 step 4b-2, operator acceptance criterion 6.

    Every changed test is classified as either expected semantic change or
    actual regression. No mass snapshot update.

An absence of that shape is not checkable by inspection, and with 24 files going
red at once the pressure to sweep peaks exactly where a manual check is weakest.
So the classification is mechanical: every test whose expectation changed with
the flip carries a marker naming its classification and this cycle, and this
test counts them.

It also guards the flip itself. If a future change quietly restores assertion
discharge, `test_the_flip_is_still_in_place` fails — which matters more than the
counting, because that is the defect the whole cycle exists to prevent.
"""

from __future__ import annotations

import inspect
import pathlib
import unittest

from agentmem_ref import policy

TESTS = pathlib.Path(__file__).resolve().parent
SOURCE = TESTS.parent / "agentmem_ref"

MARKER = "ADR-037 step 4b-2: expected semantic change (entry #24)"
REGRESSION_MARKER = "ADR-037 step 4b-2: actual regression"

#: Files whose expectations changed with the flip. Enumerated, not globbed, so
#: adding a file to the list is a deliberate act that shows up in review.
CHANGED = {
    "test_boundary_crossing.py",
    "test_canonical_and_derived_state.py",
    "test_decision_overwrite.py",
    "test_decision_overwrite_fixtures.py",
    "test_deletion_completeness_evidence.py",
    "test_derived_authority.py",
    "test_epistemic_memory.py",
    "test_evidence_producers.py",
    "test_governed_resumption.py",
    "test_interchange.py",
    "test_interchange_propagation.py",
    "test_predictive_memory.py",
    "test_procedural_memory.py",
    "test_qualified_discharge.py",
    "test_rejected_value_readmission.py",
    "test_restart_safe_runtime.py",
    "test_reusable_grants.py",
    "test_runtime_composition.py",
    "test_semantic_readmission_adapter.py",
    "test_semantic_readmission_fixture.py",
    "test_structural_mutation_governance.py",
    "test_verified_discharge.py",
    "test_write_readable_visibility.py",
}


class EveryChangedTestIsClassified(unittest.TestCase):
    """Acceptance criterion 6."""

    def test_every_changed_file_carries_a_marker(self):
        missing = [
            name for name in sorted(CHANGED)
            if MARKER not in (TESTS / name).read_text(encoding="utf-8")
        ]
        self.assertEqual(missing, [], "changed files with no classification marker")

    def test_no_change_was_classified_as_a_regression(self):
        """A regression is a defect to fix, not an expectation to update.

        None were found. If one ever is, it is marked and this assertion is the
        place that says so out loud rather than letting it pass as expected.
        """
        regressions = [
            path.name for path in TESTS.glob("test_*.py")
            # This file defines the marker constant, so it necessarily contains
            # the string it scans for.
            if path.name != pathlib.Path(__file__).name
            and REGRESSION_MARKER in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(regressions, [])

    def test_the_marker_names_this_cycle_and_its_ledger_entry(self):
        """A bare 'expected change' comment would age into noise."""
        self.assertIn("entry #24", MARKER)
        self.assertIn("step 4b-2", MARKER)


def _governed():
    """The governed operations the operator's boundary applies to."""
    from agentmem_ref.adapter import GovernedMemoryAdapter
    from agentmem_ref.crossing import evaluate_crossing
    from agentmem_ref.interchange import evaluate_source_notice, import_bundle
    from agentmem_ref.projection_governance import ProjectionGovernor
    from agentmem_ref.structural_mutation import evaluate_pama_v13

    return (
        GovernedMemoryAdapter.commit_proposal,
        GovernedMemoryAdapter.governed_delete,
        evaluate_crossing,
        import_bundle,
        evaluate_source_notice,
        ProjectionGovernor.purge,
        ProjectionGovernor.propose_rebuild,
        evaluate_pama_v13,
    )


class TheFlipIsStillInPlace(unittest.TestCase):
    """The guard that outlives the migration bookkeeping."""

    def test_assertion_does_not_discharge_require_review(self):
        proposal = policy.Proposal(
            proposal_id="p", actor_id="a", charter_version="v1",
            target_reference="t", target_class="semantic", scope="project",
            operation="write", current_strength=0.1, proposed_strength=0.2,
            downstream_authority=False, reversibility="reversible",
            risk_class="low", evidence_refs=("e1",),
            review_satisfied=True, approval_refs=("approver-1",),
        )
        decision = policy.evaluate(proposal)
        self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW)
        self.assertIn(policy.REVIEW_REQUIRES_QUALIFIED_EVIDENCE, decision.reasons)

    def test_apply_review_has_no_path_returning_allow_for_require_review(self):
        """DoD 10: the asserted route is gone from the code, not just the tests."""
        import inspect

        source = inspect.getsource(policy._apply_review)
        self.assertNotIn("review discharged by", source)
        self.assertIn("REVIEW_REQUIRES_QUALIFIED_EVIDENCE", source)

    def test_no_governed_entry_point_accepts_a_caller_verifier_mapping(self):
        """Operator boundary: verifier trust is evaluator-held.

        Scoped to **governed operations**, which is where the ruling bites. The
        low-level `evidence_qualification` primitives take the already-resolved
        mapping by design -- that is what a registry resolves *to*, and they
        decide nothing about trust. The boundary is that no caller of a governed
        operation can hand one in.
        """
        offenders = [
            fn.__qualname__ for fn in _governed()
            if "verifiers" in inspect.signature(fn).parameters
        ]
        self.assertEqual(
            offenders, [],
            "a caller-supplied verifier mapping is review_satisfied=True with "
            "more Python",
        )

    def test_governed_entry_points_carry_the_evidence_channel(self):
        """DoD 20: forward or park, with no third category."""
        for fn in _governed():
            self.assertIn("evidence", inspect.signature(fn).parameters,
                          fn.__qualname__)

    def test_wrappers_forward_rather_than_bury_the_channel(self):
        """DoD 20, the `configured_restart` class of defect."""
        from agentmem_ref.configured_restart import ConfigBoundRestartRuntime
        from agentmem_ref.restart_runtime import RestartSafeRuntime
        from agentmem_ref.runtime_composition import ConfiguredCompositionRuntime

        for fn in (RestartSafeRuntime.commit_proposal,
                   RestartSafeRuntime.governed_delete,
                   ConfigBoundRestartRuntime.commit_proposal,
                   ConfigBoundRestartRuntime.governed_delete,
                   ConfiguredCompositionRuntime.retain,
                   ConfiguredCompositionRuntime.correct,
                   ConfiguredCompositionRuntime.delete_current):
            params = inspect.signature(fn).parameters
            self.assertIn("evidence", params, fn.__qualname__)
            self.assertNotIn("verifiers", params, fn.__qualname__)


if __name__ == "__main__":
    unittest.main()
