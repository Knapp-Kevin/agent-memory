"""P4: canonical memory versus derived projections.

Executes the seven-item evidence bar stated in
`docs/programs/runtime-evidence/canonical-and-derived-state.md`, which exists
to discharge ADR-020 validation item 12, *derived-memory deletion residue is
tested*.

The spike names items 4, 5, and 6 as the ones a persuasive demonstration would
skip: transitive purge, an independent sweep, and refusal of automatic
estimator-mediated rebuild. Each has a dedicated test here, and each is paired
with a negative case proving the check can fail.

Run: python -m unittest discover -s reference/tests -t reference
"""

from __future__ import annotations

import sys
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy, projections, residue  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.projection_governance import ProjectionGovernor  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

TENANT = "tenant-a"
SOURCE = "mem:alpha"


def make_proposal(**overrides) -> policy.Proposal:
    base = dict(
        proposal_id="prop-1",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference=SOURCE,
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("ev:1",),
        tenant_ref=TENANT,
    )
    base.update(overrides)
    return policy.Proposal(**base)


def purge_corpus():
    """The evaluator's adjudication of permitted purges (ADR-037 step 4b-2).

    Authored ahead of any proposal: this source may be purged once declared for
    deletion. The caller presents a purge against it and cannot author it.
    """
    return corpus_for(rule(
        rule_id="rule:approved-purge", target=SOURCE, criterion="permanent-deletion",
        from_state="current", to_values=("purged",),
    ))


def purge_evidence():
    return purge_corpus().evidence_for(
        target_reference=SOURCE, criterion="permanent-deletion",
        pre_state="current", proposed_value="purged",
    )


def approved_purge(**overrides) -> policy.Proposal:
    """A purge an external authority has actually approved."""
    return make_proposal(
        proposal_id="prop-purge",
        operation="permanent_deletion",
        reversibility="irreversible",
        risk_class="low",
        approval_refs=("approval:data-protection-officer",),
        review_satisfied=True,
        **overrides,
    )


class ProjectionDeclarationTests(unittest.TestCase):
    """Item 1: a declaration exists, with basis recorded at build time."""

    def setUp(self) -> None:
        self.adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), TENANT, Clock(),
            verifier_registry=registry_for(purge_corpus()))
        self.gov = ProjectionGovernor(self.adapter)
        self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")

    def test_declaration_records_the_versions_actually_read(self):
        declared = self.gov.declare(
            "idx:1", (SOURCE,), projections.DETERMINISTIC,
            projections.REFERENCE_ONLY, projections.REPRODUCIBLE, TENANT,
        )
        self.assertEqual(declared.basis_map, {SOURCE: self.adapter.state_version(SOURCE)})
        self.assertEqual(self.gov.freshness("idx:1"), projections.CURRENT)


class FreshnessRelationTests(unittest.TestCase):
    """Item 2: stale and residual are computed, never asserted by a flag."""

    def setUp(self) -> None:
        self.adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), TENANT, Clock(),
            verifier_registry=registry_for(purge_corpus()))
        self.gov = ProjectionGovernor(self.adapter)
        self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")
        self.gov.declare(
            "sum:1", (SOURCE,), projections.ESTIMATOR_MEDIATED,
            projections.RECOVERABLE_CONTENT, projections.APPROXIMABLE, TENANT,
        )

    def test_version_drift_makes_a_projection_stale(self):
        self.assertEqual(self.gov.freshness("sum:1"), projections.CURRENT)
        self.adapter.record_correction(SOURCE)
        self.assertEqual(self.gov.freshness("sum:1"), projections.STALE)

    def test_residual_dominates_stale(self):
        """A tombstoned basis is a governance problem, not a correctness one."""
        self.adapter.record_correction(SOURCE)
        self.gov._purged.add(SOURCE)
        self.assertEqual(self.gov.freshness("sum:1"), projections.RESIDUAL)


class CorrectionPropagationTests(unittest.TestCase):
    """Item 3: correction marks dependents stale and supersedes without erasing."""

    def setUp(self) -> None:
        self.adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), TENANT, Clock(),
            verifier_registry=registry_for(purge_corpus()))
        self.gov = ProjectionGovernor(self.adapter)
        self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")
        self.gov.declare(
            "sum:1", (SOURCE,), projections.ESTIMATOR_MEDIATED,
            projections.RECOVERABLE_CONTENT, projections.APPROXIMABLE, TENANT,
        )
        self.gov.declare(
            "idx:1", (SOURCE,), projections.DETERMINISTIC,
            projections.REFERENCE_ONLY, projections.REPRODUCIBLE, TENANT,
        )

    def test_correction_supersedes_content_bearing_without_erasing(self):
        result = self.gov.correct(SOURCE)

        self.assertIn("sum:1", result.now_stale)
        self.assertIn("sum:1", result.superseded)
        # The superseded version survives for decisions that used it.
        retained = self.gov.store.superseded("sum:1")
        self.assertEqual(len(retained), 1)
        self.assertEqual(retained[0].version, 1)
        self.assertEqual(self.gov.store.get("sum:1").version, 2)

    def test_reference_only_projections_are_not_superseded(self):
        result = self.gov.correct(SOURCE)

        self.assertIn("idx:1", result.now_stale)
        self.assertNotIn("idx:1", result.superseded)


class TransitivePurgeTests(unittest.TestCase):
    """Items 4 and 5: transitive closure, and an independent sweep that can fail."""

    def setUp(self) -> None:
        self.adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), TENANT, Clock(),
            verifier_registry=registry_for(purge_corpus()))
        self.gov = ProjectionGovernor(self.adapter)
        self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")
        # A chain: canonical -> summary -> summary-of-summary.
        self.gov.declare(
            "sum:1", (SOURCE,), projections.ESTIMATOR_MEDIATED,
            projections.RECOVERABLE_CONTENT, projections.APPROXIMABLE, TENANT,
        )
        self.gov.declare(
            "sum:2", ("sum:1",), projections.ESTIMATOR_MEDIATED,
            projections.RECOVERABLE_CONTENT, projections.APPROXIMABLE, TENANT,
        )

    def test_closure_is_transitive_not_one_hop(self):
        closure = self.gov.store.derivation_closure(SOURCE)
        self.assertEqual(set(closure), {"sum:1", "sum:2"})

    def test_purge_reaches_the_whole_closure_and_sweeps_clean(self):
        result = self.gov.purge(approved_purge(), SOURCE,
            evidence=purge_evidence(), verifier_registry=registry_for(purge_corpus()))

        self.assertTrue(result.committed)
        self.assertEqual(set(result.buckets[residue.PURGED]), {"sum:1", "sum:2"})
        self.assertEqual(result.undeclared, [])
        self.assertTrue(result.hard_gate_passed)
        self.assertIsNone(self.gov.store.get("sum:2"))

    def test_a_one_hop_purge_is_caught_by_the_sweep(self):
        """The sweep must be able to fail, or item 5 proves nothing."""
        one_hop = residue.ResiduePlan(purged=["sum:1"])
        residue.apply_purge(self.gov.store, one_hop, self.gov._purged)
        self.gov._purged.add(SOURCE)

        undeclared = self.gov.sweep(one_hop.declared)

        self.assertEqual(undeclared, ["sum:2"], "a one-hop purge must not sweep clean")

    def test_superseded_versions_are_in_purge_scope(self):
        """Deletion dominates correction: retained versions are recoverable residue."""
        self.gov.correct(SOURCE)
        self.assertTrue(self.gov.store.superseded("sum:1"))

        self.gov.purge(approved_purge(), SOURCE,
            evidence=purge_evidence(), verifier_registry=registry_for(purge_corpus()))

        self.assertEqual(self.gov.store.superseded("sum:1"), ())

    def test_unreachable_projections_are_declared_not_omitted(self):
        self.gov.declare(
            "export:1", (SOURCE,), projections.DETERMINISTIC,
            projections.RECOVERABLE_CONTENT, projections.IRREPRODUCIBLE, TENANT,
            reachable=False, note="third-party export",
        )

        result = self.gov.purge(approved_purge(), SOURCE,
            evidence=purge_evidence(), verifier_registry=registry_for(purge_corpus()))

        self.assertIn("export:1", result.buckets[residue.DECLARED_UNCONTROLLABLE])
        self.assertEqual(result.undeclared, [], "declared residue is not undeclared residue")

    def test_unauthorized_purge_does_not_run(self):
        result = self.gov.purge(make_proposal(operation="permanent_deletion"), SOURCE)

        self.assertFalse(result.committed)
        self.assertIsNotNone(self.gov.store.get("sum:1"))


class RebuildAuthorityTests(unittest.TestCase):
    """Item 6: invalidation must not become a write channel."""

    def setUp(self) -> None:
        self.adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), TENANT, Clock(),
            verifier_registry=registry_for(purge_corpus()))
        self.gov = ProjectionGovernor(self.adapter)
        self.adapter.commit_proposal(make_proposal(), "deploy window is Thursday")
        self.gov.declare(
            "sum:1", (SOURCE,), projections.ESTIMATOR_MEDIATED,
            projections.RECOVERABLE_CONTENT, projections.APPROXIMABLE, TENANT,
        )
        self.gov.declare(
            "idx:1", (SOURCE,), projections.DETERMINISTIC,
            projections.REFERENCE_ONLY, projections.REPRODUCIBLE, TENANT,
        )

    def test_estimator_mediated_rebuild_is_refused_without_authority(self):
        self.adapter.record_correction(SOURCE)
        self.assertEqual(self.gov.freshness("sum:1"), projections.STALE)

        result = self.gov.propose_rebuild("sum:1")

        self.assertFalse(result.committed)
        self.assertIn("authority decision", result.refusal)
        # Staleness alone did not commit new estimator content.
        self.assertEqual(self.gov.store.get("sum:1").version, 1)

    def test_estimator_mediated_rebuild_proceeds_under_authority(self):
        self.adapter.record_correction(SOURCE)
        authorized = make_proposal(
            proposal_id="prop-rebuild",
            operation="correction",
            approval_refs=("approval:owner",),
            review_satisfied=True,
        )

        # ADR-037 step 4b-2: expected semantic change (entry #24).
        result = self.gov.propose_rebuild(
            "sum:1", authorized,
            evidence=purge_corpus().evidence_for(
                target_reference=SOURCE, criterion="permanent-deletion",
                pre_state="current", proposed_value="purged"),
            verifier_registry=registry_for(purge_corpus()),
        )

        self.assertTrue(result.committed)
        self.assertEqual(self.gov.store.get("sum:1").version, 2)

    def test_deterministic_reproducible_rebuild_is_categorically_authorized(self):
        self.adapter.record_correction(SOURCE)

        result = self.gov.propose_rebuild("idx:1")

        self.assertTrue(result.committed)
        self.assertTrue(result.categorical)


class ClosureSafetyTests(unittest.TestCase):
    """The spike asks whether the derivation graph is well-founded. Assume not."""

    def test_cyclic_derivation_terminates(self):
        adapter = GovernedMemoryAdapter(InMemoryTemporalGraph(), TENANT, Clock(),
            verifier_registry=registry_for(purge_corpus()))
        gov = ProjectionGovernor(adapter)
        adapter.commit_proposal(make_proposal(), "a claim")
        gov.declare("a", (SOURCE,), projections.DETERMINISTIC,
                    projections.REFERENCE_ONLY, projections.REPRODUCIBLE, TENANT)
        gov.declare("b", ("a",), projections.DETERMINISTIC,
                    projections.REFERENCE_ONLY, projections.REPRODUCIBLE, TENANT)
        # Close the cycle: a is rebuilt from b.
        gov.store.declare(
            projections.Projection(
                projection_id="a", basis=(("b", 1),), transform=projections.DETERMINISTIC,
                content_class=projections.REFERENCE_ONLY, rebuild=projections.REPRODUCIBLE,
                scope=TENANT,
            )
        )

        closure = gov.store.derivation_closure("b")

        self.assertEqual(set(closure), {"a", "b"})


if __name__ == "__main__":
    unittest.main()
