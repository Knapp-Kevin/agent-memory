from __future__ import annotations

import json
import tempfile
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule
from pathlib import Path

from agentmem_ref import policy, projections
from agentmem_ref.adapter import RecallContext
from agentmem_ref.runtime_composition import ConfiguredCompositionRuntime
from agentmem_ref.runtime_config import validate_runtime_configuration


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "reference" / "fixtures" / "runtime-configuration" / "reference-composed-runtime.json"
TENANT = "tenant-acme"
MEMORY_ID = "memory:deploy-window"
PROJECT = "project-alpha"


def _plan():
    return validate_runtime_configuration(json.loads(CONFIG.read_text(encoding="utf-8")))


def _proposal(
    proposal_id: str,
    *,
    operation: str,
    state_snapshot: str = "",
    review_satisfied: bool = False,
    approval_refs: tuple[str, ...] = (),
    project_ref: str = PROJECT,
) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="agent:composition-test",
        charter_version="charter-v1",
        target_reference=MEMORY_ID,
        target_class=policy.M2,
        scope=TENANT,
        operation=operation,
        current_strength="observed",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="irreversible" if operation == "permanent_deletion" else "reversible",
        risk_class="low",
        evidence_refs=(f"evidence:{proposal_id}",),
        review_satisfied=review_satisfied,
        approval_refs=approval_refs,
        state_snapshot=state_snapshot,
        tenant_ref=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(PROJECT,),
        project_ref=project_ref,
        purpose="deployment-planning",
    )


def _context(project_ref: str = PROJECT) -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:composition-test",
        project_ref=project_ref,
        purpose="deployment-planning",
    )


def _deletion_corpus():
    return corpus_for(rule(
        rule_id="rule:deploy-window-deletion", target=MEMORY_ID,
        criterion="permanent-deletion", from_state="current",
        to_values=("deleted",),
    ))


class ConfiguredRuntimeCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # The host configures verifier trust at construction; a caller making a
        # correction cannot reach it.
        self.corpus = corpus_for(
            rule(rule_id="rule:deploy-window-correction", target=MEMORY_ID,
                 criterion="value-correction", from_state="deploy window is Thursday",
                 to_values=("deploy window is Friday",)),
            rule(rule_id="rule:deploy-window-deletion", target=MEMORY_ID,
                 criterion="permanent-deletion", from_state="current",
                 to_values=("deleted",)),
        )
        self.runtime = ConfiguredCompositionRuntime.create(
            Path(self.temp.name),
            tenant=TENANT,
            plan=_plan(),
            verifier_registry=registry_for(self.corpus),
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _retain_initial(self):
        retained = self.runtime.retain(
            _proposal("proposal-initial", operation="promotion"),
            "deploy window is Thursday",
        )
        self.assertTrue(retained.committed)
        self.assertIsNotNone(retained.fact_uuid)
        return retained

    def test_canonical_write_and_derived_projection_compose(self) -> None:
        retained = self._retain_initial()
        self.assertEqual(self.runtime.adapter.state_version(MEMORY_ID), 1)
        self.assertEqual(self.runtime.adapter.current_fact_uuid(MEMORY_ID), retained.fact_uuid)
        self.assertEqual(
            self.runtime.projections.freshness(self.runtime.projection_id),
            projections.CURRENT,
        )
        admission = self.runtime.projection_admission()
        self.assertTrue(admission.admitted)
        self.assertEqual(admission.authority_effect, "none")

    def test_governed_retrieval_keeps_project_isolation(self) -> None:
        retained = self._retain_initial()
        same_project = self.runtime.recall("deploy window", _context())
        self.assertEqual(same_project.admitted, [retained.fact_uuid])

        foreign = self.runtime.recall("deploy window", _context("project-beta"))
        self.assertNotIn(retained.fact_uuid, foreign.admitted)
        self.assertEqual(foreign.refusals[retained.fact_uuid], "project_scope_mismatch")

    def test_correction_stales_projection_without_automatic_rebuild(self) -> None:
        initial = self._retain_initial()
        correction = self.runtime.correct(
            _proposal(
                "proposal-correct",
                operation="correction",
                state_snapshot="v1",
                review_satisfied=True,
                approval_refs=("approval:memory-owner",),
            ),
            "deploy window is Friday",
            evidence=self.corpus.evidence_for(
                target_reference=MEMORY_ID, criterion="value-correction",
                pre_state="deploy window is Thursday",
                proposed_value="deploy window is Friday"),
        )
        self.assertTrue(correction.committed)
        self.assertNotEqual(correction.fact_uuid, initial.fact_uuid)
        self.assertEqual(self.runtime.adapter.state_version(MEMORY_ID), 2)
        self.assertEqual(
            self.runtime.projections.freshness(self.runtime.projection_id),
            projections.STALE,
        )
        admission = self.runtime.projection_admission()
        self.assertFalse(admission.admitted)
        self.assertEqual(admission.refusal, "projection_stale")
        # Staleness alone did not mutate the projection basis/version.
        self.assertEqual(self.runtime.projections.store.get(self.runtime.projection_id).version, 1)

    def test_categorical_projection_rebuild_does_not_mutate_canonical_identity(self) -> None:
        self._retain_initial()
        corrected = self.runtime.correct(
            _proposal(
                "proposal-correct",
                operation="correction",
                state_snapshot="v1",
                review_satisfied=True,
                approval_refs=("approval:memory-owner",),
            ),
            "deploy window is Friday",
            evidence=self.corpus.evidence_for(
                target_reference=MEMORY_ID, criterion="value-correction",
                pre_state="deploy window is Thursday",
                proposed_value="deploy window is Friday"),
        )
        fact_before = self.runtime.adapter.current_fact_uuid(MEMORY_ID)
        version_before = self.runtime.adapter.state_version(MEMORY_ID)

        rebuilt = self.runtime.rebuild_projection()

        self.assertTrue(rebuilt.committed)
        self.assertTrue(rebuilt.categorical)
        self.assertEqual(self.runtime.adapter.current_fact_uuid(MEMORY_ID), fact_before)
        self.assertEqual(self.runtime.adapter.state_version(MEMORY_ID), version_before)
        self.assertEqual(
            self.runtime.projections.freshness(self.runtime.projection_id),
            projections.CURRENT,
        )
        self.assertEqual(corrected.fact_uuid, fact_before)

    def test_disable_remove_restore_rebuild_preserve_canonical_identity(self) -> None:
        retained = self._retain_initial()
        fact_before = retained.fact_uuid
        version_before = self.runtime.adapter.state_version(MEMORY_ID)

        disabled = self.runtime.disable_projection_component(MEMORY_ID)
        self.assertTrue(disabled.canonical_identity_unchanged)
        self.assertTrue(disabled.projection_present)
        self.assertFalse(self.runtime.projection_admission().admitted)
        self.assertEqual(self.runtime.projection_admission().refusal, "component_disabled")

        removed = self.runtime.remove_projection_component(MEMORY_ID)
        self.assertTrue(removed.canonical_identity_unchanged)
        self.assertFalse(removed.projection_present)
        self.assertEqual(self.runtime.adapter.current_fact_uuid(MEMORY_ID), fact_before)
        self.assertEqual(self.runtime.adapter.state_version(MEMORY_ID), version_before)

        restored = self.runtime.restore_and_rebuild_projection_component(
            MEMORY_ID,
            scope=TENANT,
        )
        self.assertTrue(restored.canonical_identity_unchanged)
        self.assertTrue(restored.projection_present)
        self.assertEqual(restored.projection_freshness, projections.CURRENT)
        self.assertTrue(self.runtime.projection_admission().admitted)
        self.assertEqual(self.runtime.adapter.current_fact_uuid(MEMORY_ID), fact_before)
        self.assertEqual(self.runtime.adapter.state_version(MEMORY_ID), version_before)

    def test_deletion_turns_remaining_projection_into_residual_not_current(self) -> None:
        retained = self._retain_initial()
        deleted = self.runtime.delete_current(
            _proposal(
                "proposal-delete",
                operation="permanent_deletion",
                review_satisfied=True,
                approval_refs=("approval:data-protection-officer",),
            ),
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_deletion_corpus().evidence_for(
                target_reference=MEMORY_ID, criterion="permanent-deletion",
                pre_state="current", proposed_value="deleted"),
        )
        self.assertTrue(deleted.committed)
        self.assertEqual(deleted.fact_uuid, retained.fact_uuid)
        self.assertIsNone(self.runtime.adapter.current_fact_uuid(MEMORY_ID))
        self.assertEqual(
            self.runtime.projections.freshness(self.runtime.projection_id),
            projections.RESIDUAL,
        )
        admission = self.runtime.projection_admission()
        self.assertFalse(admission.admitted)
        self.assertEqual(admission.refusal, "projection_residual")

        removed = self.runtime.remove_projection_component(MEMORY_ID)
        self.assertFalse(removed.projection_present)
        self.assertIsNone(self.runtime.adapter.current_fact_uuid(MEMORY_ID))

    def test_component_lifecycle_evidence_never_creates_authority(self) -> None:
        self._retain_initial()
        disabled = self.runtime.disable_projection_component(MEMORY_ID)
        self.assertEqual(disabled.authority_effect, "none")
        removed = self.runtime.remove_projection_component(MEMORY_ID)
        self.assertEqual(removed.authority_effect, "none")
        restored = self.runtime.restore_and_rebuild_projection_component(MEMORY_ID, scope=TENANT)
        self.assertEqual(restored.authority_effect, "none")
        self.assertEqual(self.runtime.projection_admission().authority_effect, "none")


if __name__ == "__main__":
    unittest.main()
