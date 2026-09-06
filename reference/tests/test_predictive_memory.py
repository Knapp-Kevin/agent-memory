from __future__ import annotations

import json
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule

PREDICTION_REF = "prediction:deployment"


def _prediction_corpus():
    """The evaluator's adjudication of prediction revision, authored ahead of
    any proposal (ADR-037 step 4b-2, entry #24)."""
    return corpus_for(rule(
        rule_id="rule:prediction-revision", target=PREDICTION_REF,
        criterion="prediction-revision", from_state="current",
        to_values=("revised",),
    ))


def _prediction_evidence():
    return _prediction_corpus().evidence_for(
        target_reference=PREDICTION_REF, criterion="prediction-revision",
        pre_state="current", proposed_value="revised",
    )
from pathlib import Path

import jsonschema

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext
from agentmem_ref.capabilities import ComponentDeclaration
from agentmem_ref.predictive_memory import (
    CAPABILITY_ID,
    PredictionOutcomeComparison,
    PredictionRevision,
    PredictiveCounterfactualMemory,
    PredictiveRevisionError,
    PredictiveScope,
    StalePredictionRevision,
)
from agentmem_ref.substrate import InMemoryTemporalGraph

ROOT = Path(__file__).resolve().parents[2]
PROFILE = (
    ROOT
    / "reference"
    / "fixtures"
    / "component-capabilities"
    / "predictive-reference-v3.json"
)
SCHEMA = ROOT / "schemas" / "component-capability-profile.schema.json"

TENANT = "tenant:predictive"
PROJECT = "project:predictive"


def governed_scope() -> PredictiveScope:
    return PredictiveScope(
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        project_ref=PROJECT,
        purpose="planning",
    )


def context() -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:predictive-test",
        project_ref=PROJECT,
        purpose="planning",
    )


def prediction(
    revision_ref: str,
    *,
    prediction_ref: str = "prediction:deployment",
    prediction_kind: str = "forecast",
    expected_outcome: str = "Staged deployment completes without elevated errors",
    confidence: float | None = 0.72,
    source_component: str = "PredictorA",
    basis: tuple[str, ...] = ("evidence:canary",),
    assumptions: tuple[str, ...] = ("traffic mix remains stable",),
    prior_revision_ref: str = "",
    revision_reason: str = "",
    scope: PredictiveScope | None = None,
) -> PredictionRevision:
    return PredictionRevision(
        prediction_ref=prediction_ref,
        revision_ref=revision_ref,
        prediction_kind=prediction_kind,
        expected_outcome=expected_outcome,
        confidence=confidence,
        scope=scope or governed_scope(),
        source_component=source_component,
        created_at="2026-01-01T00:00:00Z",
        target_window="next deployment window",
        basis_evidence_refs=basis,
        assumptions=assumptions,
        prior_revision_ref=prior_revision_ref,
        revision_reason=revision_reason,
        estimator_ref=f"estimator:{source_component}",
        estimator_version="1.0.0",
    )


def comparison(
    comparison_ref: str,
    *,
    prediction_ref: str = "prediction:deployment",
    prediction_revision_ref: str = "prediction-rev:001",
    disposition: str = "matched",
    source_component: str = "ComparatorA",
    observed_summary: str = "Deployment completed without elevated errors",
    observed_refs: tuple[str, ...] = ("observation:deploy-run-42",),
) -> PredictionOutcomeComparison:
    return PredictionOutcomeComparison(
        comparison_ref=comparison_ref,
        prediction_ref=prediction_ref,
        prediction_revision_ref=prediction_revision_ref,
        observed_outcome_summary=observed_summary,
        observed_evidence_refs=observed_refs,
        observed_at="2026-01-01T01:00:00Z",
        disposition=disposition,
        source_component=source_component,
        comparison_evidence_refs=("comparison:method-v1",),
        confidence=0.9,
        estimator_ref=f"estimator:{source_component}",
        estimator_version="1.0.0",
    )


def runtime(*components: str) -> tuple[
    PredictiveCounterfactualMemory,
    GovernedMemoryAdapter,
    InMemoryTemporalGraph,
]:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(
        substrate, tenant=TENANT, clock=Clock(),
        verifier_registry=registry_for(_prediction_corpus()),
    )
    memory = PredictiveCounterfactualMemory(
        adapter=adapter,
        available_components=tuple(components),
    )
    return memory, adapter, substrate


class PredictiveCounterfactualMemoryTests(unittest.TestCase):
    def test_v3_profile_is_honest_process_local_predictive_capability(self) -> None:
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

    def test_forecast_simulation_and_counterfactual_remain_independently_typed(self) -> None:
        memory, _, _ = runtime("PredictorA")
        for index, kind in enumerate(
            ("forecast", "simulation", "counterfactual"),
            start=1,
        ):
            item = prediction(
                f"prediction-rev:{index:03d}",
                prediction_ref=f"prediction:{kind}",
                prediction_kind=kind,
            )
            result = memory.apply_revision(
                item,
                actor_id="agent:predictive-test",
            )
            self.assertTrue(result.commit.committed)
            self.assertEqual(kind, memory.current(item.prediction_ref).prediction_kind)
            self.assertEqual("tentative", result.commit.pama_decision["mutation"]["proposed_strength"])

    def test_initial_forecast_is_retained_as_predictive_not_observed_history(self) -> None:
        memory, adapter, substrate = runtime("PredictorA")
        first = prediction("prediction-rev:001")

        result = memory.apply_revision(first, actor_id="agent:predictive-test")

        self.assertTrue(result.commit.committed)
        self.assertEqual(policy.ALLOW_WITH_LEDGER, result.commit.decision.outcome)
        self.assertEqual("current", result.lineage_state)
        self.assertEqual(first, memory.current(first.prediction_ref))
        fact = substrate.get_fact(result.fact_uuid)
        self.assertTrue(fact.fact_text.startswith("PREDICTIVE[forecast]"))
        self.assertEqual(result.fact_uuid, adapter.current_fact_uuid(first.prediction_ref))
        self.assertEqual(0.72, result.commit.pama_decision["basis"]["confidence"])

        active = memory.recall_active(
            "staged deployment elevated errors",
            context=context(),
        )
        self.assertIn(first.prediction_ref, active.active_object_refs)

    def test_confidence_one_cannot_grant_external_action_authority(self) -> None:
        memory, adapter, substrate = runtime("PredictorA")
        high_confidence = prediction(
            "prediction-rev:001",
            confidence=1.0,
        )

        result = memory.apply_revision(
            high_confidence,
            actor_id="agent:predictive-test",
            downstream_authority=policy.A4,
        )

        self.assertFalse(result.commit.committed)
        self.assertEqual(policy.REQUIRE_REVIEW, result.commit.decision.outcome)
        self.assertEqual("refused", result.lineage_state)
        self.assertEqual((), memory.history(high_confidence.prediction_ref))
        self.assertIsNone(adapter.current_fact_uuid(high_confidence.prediction_ref))
        self.assertNotIn("write_fact", [entry[0] for entry in substrate.write_log])
        self.assertIn("promotion", result.commit.decision.prohibited_actions)

    def test_prediction_revision_is_append_only_and_refused_revision_is_not_current(self) -> None:
        memory, adapter, substrate = runtime("PredictorA")
        first = prediction("prediction-rev:001")
        first_result = memory.apply_revision(first, actor_id="agent:predictive-test")

        second = prediction(
            "prediction-rev:002",
            expected_outcome="Staged deployment causes a transient error increase",
            confidence=0.55,
            basis=("evidence:new-load-test",),
            prior_revision_ref=first.revision_ref,
            revision_reason="new load test changes expected outcome",
        )
        refused = memory.apply_revision(second, actor_id="agent:predictive-test")
        self.assertFalse(refused.commit.committed)
        self.assertEqual(first, memory.current(first.prediction_ref))
        self.assertEqual((first,), memory.history(first.prediction_ref))
        self.assertEqual(first_result.fact_uuid, adapter.current_fact_uuid(first.prediction_ref))

        approved = memory.apply_revision(
            second,
            actor_id="agent:predictive-test",
            review_satisfied=True,
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_prediction_evidence(),
            approval_refs=("approval:prediction-revision",),
        )
        self.assertTrue(approved.commit.committed)
        self.assertEqual((first, second), memory.history(first.prediction_ref))
        self.assertEqual("superseded", memory.revision_state(first.prediction_ref, first.revision_ref))
        self.assertEqual("current", memory.revision_state(first.prediction_ref, second.revision_ref))
        self.assertTrue(substrate.get_fact(first_result.fact_uuid).is_event_invalid)

    def test_outcome_comparison_is_separate_and_does_not_rewrite_prediction(self) -> None:
        memory, _, substrate = runtime("PredictorA", "ComparatorA")
        first = prediction("prediction-rev:001")
        first_result = memory.apply_revision(first, actor_id="agent:predictive-test")
        observed = comparison("comparison:001")

        result = memory.record_outcome_comparison(
            observed,
            actor_id="agent:predictive-test",
        )

        self.assertTrue(result.commit.committed)
        self.assertEqual(first, memory.current(first.prediction_ref))
        self.assertEqual((first,), memory.history(first.prediction_ref))
        self.assertEqual(observed, memory.comparison(observed.comparison_ref))
        self.assertEqual((observed,), memory.comparisons_for(first.prediction_ref))
        self.assertEqual(first.revision_ref, observed.prediction_revision_ref)
        self.assertEqual(("observation:deploy-run-42",), observed.observed_evidence_refs)
        self.assertEqual("forecast", memory.current(first.prediction_ref).prediction_kind)
        prediction_fact = substrate.get_fact(first_result.fact_uuid)
        comparison_fact = substrate.get_fact(result.fact_uuid)
        self.assertTrue(prediction_fact.fact_text.startswith("PREDICTIVE[forecast]"))
        self.assertTrue(comparison_fact.fact_text.startswith("PREDICTION_COMPARISON[matched]"))
        self.assertNotEqual(first_result.fact_uuid, result.fact_uuid)

    def test_comparison_disposition_is_descriptive_not_authority(self) -> None:
        memory, _, _ = runtime("PredictorA", "ComparatorA")
        first = prediction("prediction-rev:001")
        memory.apply_revision(first, actor_id="agent:predictive-test")

        outcomes = []
        for disposition in ("matched", "contradicted", "partial", "unresolved"):
            item = comparison(
                f"comparison:{disposition}",
                disposition=disposition,
                observed_summary=f"Observed outcome for {disposition}",
                observed_refs=(f"observation:{disposition}",),
            )
            result = memory.record_outcome_comparison(
                item,
                actor_id="agent:predictive-test",
            )
            self.assertTrue(result.commit.committed)
            self.assertEqual(disposition, result.comparison.disposition)
            self.assertEqual(disposition, result.commit.pama_decision.get("provider_verdict", disposition))
            outcomes.append(result.commit.decision.outcome)

        self.assertEqual([policy.ALLOW_WITH_LEDGER] * 4, outcomes)

    def test_counterfactual_remains_counterfactual_after_actual_outcome_comparison(self) -> None:
        memory, _, _ = runtime("PredictorA", "ComparatorA")
        counterfactual = prediction(
            "prediction-rev:001",
            prediction_ref="prediction:counterfactual-no-cache",
            prediction_kind="counterfactual",
            expected_outcome="Without caching, latency would exceed the target",
        )
        memory.apply_revision(counterfactual, actor_id="agent:predictive-test")
        outcome = comparison(
            "comparison:counterfactual",
            prediction_ref=counterfactual.prediction_ref,
            prediction_revision_ref=counterfactual.revision_ref,
            disposition="partial",
            observed_summary="Actual cached deployment met latency target",
            observed_refs=("observation:cached-deployment",),
        )
        memory.record_outcome_comparison(
            outcome,
            actor_id="agent:predictive-test",
        )

        current = memory.current(counterfactual.prediction_ref)
        self.assertEqual("counterfactual", current.prediction_kind)
        self.assertEqual(counterfactual.expected_outcome, current.expected_outcome)
        self.assertEqual(
            counterfactual.revision_ref,
            memory.comparison(outcome.comparison_ref).prediction_revision_ref,
        )

    def test_stale_revision_scope_change_and_kind_change_fail_before_mutation(self) -> None:
        memory, _, substrate = runtime("PredictorA")
        first = prediction("prediction-rev:001")
        memory.apply_revision(first, actor_id="agent:predictive-test")
        before = tuple(substrate.write_log)

        stale = prediction(
            "prediction-rev:002",
            prior_revision_ref="prediction-rev:000",
            revision_reason="stale writer",
        )
        with self.assertRaises(StalePredictionRevision):
            memory.apply_revision(stale, actor_id="agent:predictive-test")
        self.assertEqual(before, tuple(substrate.write_log))

        foreign_scope = PredictiveScope(
            scope=TENANT,
            isolation_domain_refs=(TENANT, "project:other"),
            required_isolation_domain_refs=(TENANT, "project:other"),
            project_ref="project:other",
        )
        changed_scope = prediction(
            "prediction-rev:003",
            prior_revision_ref=first.revision_ref,
            revision_reason="attempted scope movement",
            scope=foreign_scope,
        )
        with self.assertRaises(PredictiveRevisionError):
            memory.apply_revision(changed_scope, actor_id="agent:predictive-test")
        self.assertEqual(before, tuple(substrate.write_log))

        changed_kind = prediction(
            "prediction-rev:004",
            prediction_kind="simulation",
            prior_revision_ref=first.revision_ref,
            revision_reason="attempted type mutation",
        )
        with self.assertRaises(PredictiveRevisionError):
            memory.apply_revision(changed_kind, actor_id="agent:predictive-test")
        self.assertEqual(before, tuple(substrate.write_log))

    def test_provider_replacement_preserves_prediction_identity_and_authority_boundary(self) -> None:
        memory, _, _ = runtime("PredictorA", "ComparatorA")
        first = prediction("prediction-rev:001", source_component="PredictorA")
        memory.apply_revision(first, actor_id="agent:predictive-test")

        memory.replace_component(old_component="PredictorA", new_component="PredictorB")
        second = prediction(
            "prediction-rev:002",
            source_component="PredictorB",
            expected_outcome="Replacement predictor expects a small error increase",
            basis=("evidence:replacement-model",),
            prior_revision_ref=first.revision_ref,
            revision_reason="replacement provider produced revised forecast",
        )
        result = memory.apply_revision(
            second,
            actor_id="agent:predictive-test",
            review_satisfied=True,
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=_prediction_evidence(),
            approval_refs=("approval:provider-revision",),
        )

        self.assertTrue(result.commit.committed)
        self.assertEqual(first.prediction_ref, second.prediction_ref)
        self.assertEqual(
            first.prediction_ref,
            result.commit.pama_decision["target"]["reference"],
        )
        self.assertEqual("PredictorB", memory.current(first.prediction_ref).source_component)
        self.assertNotIn("authority_effect", result.commit.pama_decision)

    def test_profile_declares_only_predictive_capability(self) -> None:
        value = json.loads(PROFILE.read_text(encoding="utf-8"))
        declared = {item["capability_id"] for item in value["capabilities"]}
        self.assertEqual({CAPABILITY_ID}, declared)
        self.assertNotIn("semantic_fact_memory", declared)
        self.assertNotIn("episodic_event_memory", declared)
        self.assertNotIn("epistemic_belief_memory", declared)


if __name__ == "__main__":
    unittest.main()
