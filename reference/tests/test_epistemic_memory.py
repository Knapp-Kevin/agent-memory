from __future__ import annotations

import json
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule


BELIEF_REF = "belief:deployment-safety"


def _belief_corpus():
    return corpus_for(
        rule(rule_id="rule:belief-revision", target=BELIEF_REF,
             criterion="belief-revision", from_state="current",
             to_values=("revised", "disputed", "retracted")),
    )


def _belief_evidence():
    return _belief_corpus().evidence_for(
        target_reference=BELIEF_REF, criterion="belief-revision",
        pre_state="current", proposed_value="revised",
    )
from pathlib import Path

import jsonschema

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext
from agentmem_ref.capabilities import ComponentDeclaration
from agentmem_ref.epistemic_memory import (
    CAPABILITY_ID,
    BeliefRevision,
    EpistemicBeliefMemory,
    EpistemicRevisionError,
    EpistemicScope,
    StaleEpistemicRevision,
)
from agentmem_ref.substrate import InMemoryTemporalGraph

ROOT = Path(__file__).resolve().parents[2]
PROFILE = (
    ROOT
    / "reference"
    / "fixtures"
    / "component-capabilities"
    / "epistemic-reference-v3.json"
)
SCHEMA = ROOT / "schemas" / "component-capability-profile.schema.json"

TENANT = "tenant:epistemic"
PROJECT = "project:epistemic"


def governed_scope() -> EpistemicScope:
    return EpistemicScope(
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        project_ref=PROJECT,
        purpose="reasoning",
    )


def context() -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:epistemic-test",
        project_ref=PROJECT,
        purpose="reasoning",
    )


def revision(
    revision_ref: str,
    *,
    belief_ref: str = "belief:deployment-safety",  # noqa: matches BELIEF_REF below
    claim_text: str = "Staged deployment is likely safe for this service",
    confidence: float | None = 0.7,
    source_component: str = "EpistemicReference",
    epistemic_kind: str = "belief",
    epistemic_status: str = "active",
    supporting: tuple[str, ...] = ("evidence:canary-success",),
    contradicting: tuple[str, ...] = (),
    prior_revision_ref: str = "",
    revision_reason: str = "",
    scope: EpistemicScope | None = None,
) -> BeliefRevision:
    return BeliefRevision(
        belief_ref=belief_ref,
        revision_ref=revision_ref,
        epistemic_kind=epistemic_kind,
        claim_text=claim_text,
        confidence=confidence,
        scope=scope or governed_scope(),
        source_component=source_component,
        observed_at="2026-01-01T00:00:00Z",
        supporting_evidence_refs=supporting,
        contradicting_evidence_refs=contradicting,
        prior_revision_ref=prior_revision_ref,
        revision_reason=revision_reason,
        epistemic_status=epistemic_status,
        estimator_ref=f"estimator:{source_component}",
        estimator_version="1.0.0",
    )


def runtime(*components: str) -> tuple[
    EpistemicBeliefMemory,
    GovernedMemoryAdapter,
    InMemoryTemporalGraph,
]:
    substrate = InMemoryTemporalGraph()
    # ADR-037 step 4b-2: expected semantic change (entry #24).
    # The evaluator holds an adjudication of belief revision, authored ahead of
    # any proposal: a belief may be revised or disputed under the epistemic
    # revision policy. A caller presents a revision against it; it cannot
    # author one.
    corpus = _belief_corpus()
    adapter = GovernedMemoryAdapter(
        substrate, tenant=TENANT, clock=Clock(),
        verifier_registry=registry_for(corpus),
    )
    memory = EpistemicBeliefMemory(
        adapter=adapter,
        available_components=tuple(components),
    )
    return memory, adapter, substrate


class EpistemicBeliefMemoryTests(unittest.TestCase):
    def test_v3_profile_is_honest_process_local_epistemic_capability(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        value = json.loads(PROFILE.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(value)
        component = ComponentDeclaration.from_dict(value)

        self.assertEqual("component-capability-v3", component.profile_version)
        self.assertEqual(1, len(component.capabilities))
        capability = component.capabilities[0]
        self.assertEqual(CAPABILITY_ID, capability.capability_id)
        self.assertEqual("runtime_wired", capability.maturity)
        self.assertEqual("none", capability.authority_effect)
        self.assertEqual(
            "process_local_only",
            capability.operational_contract.restart_recovery,
        )
        self.assertEqual(
            "process_local_only",
            capability.operational_contract.reconciliation,
        )

    def test_initial_belief_retains_epistemic_state_through_existing_governance(self) -> None:
        memory, adapter, substrate = runtime("EpistemicReference")
        first = revision("belief-rev:001", epistemic_kind="hypothesis")

        result = memory.apply_revision(first, actor_id="agent:epistemic-test")

        self.assertTrue(result.commit.committed)
        self.assertEqual(policy.ALLOW_WITH_LEDGER, result.commit.decision.outcome)
        self.assertEqual("current", result.lineage_state)
        self.assertEqual(first, memory.current(first.belief_ref))
        self.assertEqual(first.claim_text, memory.current_claim(first.belief_ref))
        self.assertEqual((first,), memory.history(first.belief_ref))
        self.assertEqual(result.fact_uuid, adapter.current_fact_uuid(first.belief_ref))
        self.assertEqual(first.claim_text, substrate.get_fact(result.fact_uuid).fact_text)
        self.assertEqual(0.7, result.commit.pama_decision["basis"]["confidence"])

        active = memory.recall_active(
            "staged deployment safe service",
            context=context(),
        )
        self.assertIn(first.belief_ref, active.active_object_refs)

    def test_confidence_one_cannot_bypass_review_and_refused_revision_is_not_current(self) -> None:
        memory, adapter, _ = runtime("EpistemicReference")
        first = revision("belief-rev:001")
        committed = memory.apply_revision(first, actor_id="agent:epistemic-test")
        first_fact = committed.fact_uuid

        proposed = revision(
            "belief-rev:002",
            claim_text="Staged deployment is unsafe for this service",
            confidence=1.0,
            supporting=("evidence:incident",),
            contradicting=("evidence:canary-success",),
            prior_revision_ref=first.revision_ref,
            revision_reason="new incident contradicts the earlier belief",
        )
        refused = memory.apply_revision(
            proposed,
            actor_id="agent:epistemic-test",
        )

        self.assertFalse(refused.commit.committed)
        self.assertEqual(policy.REQUIRE_REVIEW, refused.commit.decision.outcome)
        self.assertEqual("refused", refused.lineage_state)
        self.assertEqual(first, memory.current(first.belief_ref))
        self.assertEqual((first,), memory.history(first.belief_ref))
        self.assertEqual(first_fact, adapter.current_fact_uuid(first.belief_ref))
        self.assertIn("correction", refused.commit.decision.prohibited_actions)

    def test_approved_revision_is_append_only_and_preserves_directional_evidence(self) -> None:
        memory, adapter, substrate = runtime("EpistemicReference")
        first = revision("belief-rev:001")
        first_result = memory.apply_revision(first, actor_id="agent:epistemic-test")

        second = revision(
            "belief-rev:002",
            claim_text="Staged deployment is risky until the incident is explained",
            confidence=0.45,
            supporting=("evidence:incident",),
            contradicting=("evidence:canary-success", "evidence:load-test"),
            prior_revision_ref=first.revision_ref,
            revision_reason="contradictory production evidence",
        )
        second_result = memory.apply_revision(
            second,
            actor_id="agent:epistemic-test",
            review_satisfied=True,
            approval_refs=("approval:epistemic-review",),
            evidence=_belief_evidence(),
        )

        self.assertTrue(second_result.commit.committed)
        self.assertEqual(policy.ALLOW_WITH_LEDGER, second_result.commit.decision.outcome)
        self.assertEqual((first, second), memory.history(first.belief_ref))
        self.assertEqual("superseded", memory.revision_state(first.belief_ref, first.revision_ref))
        self.assertEqual("current", memory.revision_state(first.belief_ref, second.revision_ref))
        self.assertEqual(("evidence:incident",), second.supporting_evidence_refs)
        self.assertEqual(
            ("evidence:canary-success", "evidence:load-test"),
            second.contradicting_evidence_refs,
        )
        self.assertTrue(substrate.get_fact(first_result.fact_uuid).is_event_invalid)
        self.assertEqual(
            second_result.fact_uuid,
            adapter.current_fact_uuid(first.belief_ref),
        )

    def test_disputed_belief_remains_epistemic_but_is_not_active_cognition(self) -> None:
        memory, _, _ = runtime("EpistemicReference")
        first = revision("belief-rev:001")
        memory.apply_revision(first, actor_id="agent:epistemic-test")

        disputed = revision(
            "belief-rev:002",
            claim_text="Deployment safety remains unresolved",
            confidence=0.5,
            supporting=("evidence:canary-success",),
            contradicting=("evidence:incident",),
            prior_revision_ref=first.revision_ref,
            revision_reason="evidence is materially conflicting",
            epistemic_status="disputed",
        )
        result = memory.apply_revision(
            disputed,
            actor_id="agent:epistemic-test",
            review_satisfied=True,
            approval_refs=("approval:dispute-review",),
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_belief_evidence(),
        )

        self.assertTrue(result.commit.committed)
        self.assertEqual("disputed", result.lineage_state)
        self.assertEqual(disputed, memory.current(disputed.belief_ref))
        active = memory.recall_active(
            "deployment safety unresolved",
            context=context(),
        )
        self.assertIn(result.fact_uuid, active.admitted_fact_uuids)
        self.assertNotIn(disputed.belief_ref, active.active_object_refs)
        self.assertEqual("epistemic_disputed", active.refusals[result.fact_uuid])

    def test_retraction_preserves_history_and_removes_current_claim_from_recall(self) -> None:
        memory, adapter, substrate = runtime("EpistemicReference")
        first = revision("belief-rev:001")
        first_result = memory.apply_revision(first, actor_id="agent:epistemic-test")

        retracted = revision(
            "belief-rev:002",
            claim_text="",
            confidence=None,
            supporting=("evidence:withdrawal",),
            prior_revision_ref=first.revision_ref,
            revision_reason="source withdrew the underlying observation",
            epistemic_status="retracted",
        )
        result = memory.apply_revision(
            retracted,
            actor_id="agent:epistemic-test",
        )

        self.assertTrue(result.commit.committed)
        self.assertEqual("retracted", result.lineage_state)
        self.assertEqual((first, retracted), memory.history(first.belief_ref))
        self.assertEqual("superseded", memory.revision_state(first.belief_ref, first.revision_ref))
        self.assertIsNone(memory.current_claim(first.belief_ref))
        self.assertIsNone(adapter.current_fact_uuid(first.belief_ref))
        self.assertIsNotNone(substrate.get_fact(first_result.fact_uuid))
        self.assertIsNotNone(adapter.tombstone(first_result.fact_uuid))

        active = memory.recall_active(
            "staged deployment safe service",
            context=context(),
        )
        self.assertEqual([], active.active_object_refs)
        self.assertEqual(
            "tombstoned",
            active.refusals[first_result.fact_uuid],
        )

    def test_stale_revision_and_scope_change_fail_before_substrate_mutation(self) -> None:
        memory, _, substrate = runtime("EpistemicReference")
        first = revision("belief-rev:001")
        memory.apply_revision(first, actor_id="agent:epistemic-test")
        before = tuple(substrate.write_log)

        stale = revision(
            "belief-rev:002",
            prior_revision_ref="belief-rev:000",
            revision_reason="stale writer",
        )
        with self.assertRaises(StaleEpistemicRevision):
            memory.apply_revision(stale, actor_id="agent:epistemic-test")
        self.assertEqual(before, tuple(substrate.write_log))

        foreign_scope = EpistemicScope(
            scope=TENANT,
            isolation_domain_refs=(TENANT, "project:other"),
            required_isolation_domain_refs=(TENANT, "project:other"),
            project_ref="project:other",
        )
        changed_scope = revision(
            "belief-rev:003",
            prior_revision_ref=first.revision_ref,
            revision_reason="attempted scope movement",
            scope=foreign_scope,
        )
        with self.assertRaises(EpistemicRevisionError):
            memory.apply_revision(changed_scope, actor_id="agent:epistemic-test")
        self.assertEqual(before, tuple(substrate.write_log))

    def test_provider_replacement_does_not_change_belief_identity_or_authority(self) -> None:
        memory, _, _ = runtime("EstimatorA")
        first = revision(
            "belief-rev:001",
            source_component="EstimatorA",
        )
        first_result = memory.apply_revision(first, actor_id="agent:epistemic-test")
        self.assertNotIn("authority_effect", first_result.commit.pama_decision)

        memory.replace_component(
            old_component="EstimatorA",
            new_component="EstimatorB",
        )
        second = revision(
            "belief-rev:002",
            source_component="EstimatorB",
            claim_text="Staged deployment safety estimate has changed",
            supporting=("evidence:new-run",),
            prior_revision_ref=first.revision_ref,
            revision_reason="replacement estimator produced new evidence",
        )
        second_result = memory.apply_revision(
            second,
            actor_id="agent:epistemic-test",
            review_satisfied=True,
            approval_refs=("approval:provider-change-review",),
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            # The property under test -- provider replacement changes neither
            # belief identity nor authority -- is untouched.
            evidence=_belief_evidence(),
        )

        self.assertTrue(second_result.commit.committed)
        self.assertEqual(first.belief_ref, second.belief_ref)
        self.assertEqual(first.belief_ref, second_result.commit.pama_decision["target"]["reference"])
        self.assertEqual("EstimatorB", memory.current(first.belief_ref).source_component)
        self.assertNotIn("authority_effect", second_result.commit.pama_decision)

    def test_profile_declares_only_epistemic_not_semantic_fact_or_predictive_capability(self) -> None:
        value = json.loads(PROFILE.read_text(encoding="utf-8"))
        declared = {
            item["capability_id"]
            for item in value["capabilities"]
        }
        self.assertEqual({CAPABILITY_ID}, declared)
        self.assertNotIn("semantic_fact_memory", declared)
        self.assertNotIn("predictive_counterfactual_memory", declared)


if __name__ == "__main__":
    unittest.main()
