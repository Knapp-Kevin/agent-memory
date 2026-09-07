"""ADR-032 / #281 structural mutation classification and PAMA 1.3 tests."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule

from agentmem_ref import domain_schema_mutation as dsm
from agentmem_ref import policy, receipts
from agentmem_ref.structural_mutation import (
    ACTIVE,
    RETIRED,
    SUPERSEDED,
    S0,
    S1,
    S2,
    S3,
    StructuralMutationError,
    StructuralProposal,
    StructuralPolicy,
    SchemaRef,
    activate,
    authorize_lifecycle,
    classify,
    evaluate_pama_v13,
    retire,
    rollback,
    supersede,
)
from agentmem_ref.structural_pama import build_pama_decision_v13, enforce_v13_impact_binding


def digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def make_structural_proposal(**overrides) -> StructuralProposal:
    values = dict(
        proposal_id="schema:add-project-relation",
        current_schema=SchemaRef("domain:project", "4.0.0", "project"),
        proposed_schema=SchemaRef("domain:project", "4.1.0", "project"),
        layer="domain",
        change_kind="additive_extension",
        semantic_diff=("add optional project:depends_on:project relation",),
        tenant_ref="tenant-a",
        isolation_domain_refs=("tenant-a/project-a",),
        preserves_semantics=True,
        optional_additive=True,
        migration_required=False,
        information_loss="none",
        historical_interpretation_preserved=True,
        scope_posture="unchanged",
        authority_posture="unchanged",
        isolation_posture="preserved",
        affected_memory_count=120,
        dependent_refs=("consumer:project-index",),
        incompatible_dependency_refs=(),
        live_dependency_refs=(),
        reversibility="versioned_revocable",
        rollback_ref="rollback:domain-project:4.0.0",
        rebuild_obligations=("projection:project-graph",),
        residue_obligations=(),
        state_digest=digest("state:v4"),
        dependency_digest=digest("deps:v4"),
        evidence_refs=("evidence:semantic-diff", "evidence:dependency-scan"),
        estimator_refs=("estimator:ontology",),
        estimator_versions=("ontology:7",),
        confidence=0.97,
    )
    values.update(overrides)
    return StructuralProposal(**values)


def make_pama(structural: StructuralProposal, **overrides) -> policy.Proposal:
    values = dict(
        proposal_id=structural.proposal_id,
        actor_id="agent:schema-observer",
        charter_version="charter:1",
        target_reference="domain-model:project-a",
        target_class=policy.M3,
        scope="tenant-a/project-a",
        operation=dsm.DOMAIN_SCHEMA_MUTATION,
        current_strength="promoted",
        proposed_strength="canonical",
        downstream_authority=policy.A3,
        reversibility=structural.reversibility,
        risk_class="low",
        evidence_refs=structural.evidence_refs,
        estimator_refs=structural.estimator_refs,
        estimator_versions=structural.estimator_versions,
        confidence=structural.confidence,
        state_snapshot=structural.state_digest,
        tenant_ref=structural.tenant_ref,
        purpose="domain ontology evolution",
        isolation_domain_refs=structural.isolation_domain_refs,
        required_isolation_domain_refs=structural.isolation_domain_refs,
        project_ref="project-a",
    )
    values.update(overrides)
    return policy.Proposal(**values)


class StructuralMutationGovernanceTests(unittest.TestCase):
    def test_s0_is_autonomous_but_not_domain_schema_mutation(self):
        proposal = make_structural_proposal(
            proposal_id="projection:rebuild",
            current_schema=SchemaRef("projection:graph", "2", "project"),
            proposed_schema=SchemaRef("projection:graph", "3", "project"),
            layer="derived",
            change_kind="rebuild_only",
            semantic_diff=("replace graph projection layout without semantic change",),
            optional_additive=False,
            affected_memory_count=5000,
            rollback_ref="rollback:projection:graph:2",
            rebuild_obligations=("projection:graph",),
        )
        impact = classify(proposal)
        self.assertEqual(impact.classification.structural_class, S0)
        self.assertTrue(impact.classification.autonomous_eligible)
        with self.assertRaisesRegex(StructuralMutationError, "not a domain_schema_mutation"):
            evaluate_pama_v13(
                make_pama(proposal),
                impact,
                current_state_digest=proposal.state_digest,
                current_dependency_digest=proposal.dependency_digest,
            )

    def test_bounded_s1_is_deterministically_autonomous(self):
        structural = make_structural_proposal()
        impact = classify(structural)
        self.assertEqual(impact.classification.structural_class, S1)
        self.assertTrue(impact.classification.autonomous_eligible)
        self.assertEqual(impact.classification.required_authority, "deterministic_policy")
        self.assertEqual(impact.to_dict()["impact"]["semantic_diff"], list(structural.semantic_diff))
        self.assertEqual(impact.to_dict()["impact"]["isolation_domain_refs"], list(structural.isolation_domain_refs))

        pama = make_pama(structural)
        decision = evaluate_pama_v13(
            pama,
            impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
        )
        self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertIn(dsm.DOMAIN_SCHEMA_MUTATION, decision.permitted_actions)

        document = build_pama_decision_v13(
            pama,
            decision,
            impact,
            selected_action=dsm.DOMAIN_SCHEMA_MUTATION,
            receipt_ref="receipt:s1",
        )
        self.assertEqual(document["schema_version"], "1.3.0")
        self.assertEqual(document["basis"]["structural_class"], S1)
        self.assertEqual(document["decision"]["selection_mode"], "deterministic")
        self.assertNotIn("required_review_refs", document["policy"])
        enforce_v13_impact_binding(document, impact)

        lifecycle = authorize_lifecycle(
            impact,
            decision,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
            decision_ref="decision:s1",
        )
        lifecycle = activate(lifecycle)
        self.assertEqual(lifecycle.lifecycle_state, ACTIVE)
        lifecycle = supersede(lifecycle)
        lifecycle = retire(lifecycle)
        self.assertEqual(lifecycle.lifecycle_state, RETIRED)

    def test_estimator_confidence_cannot_change_s1_class_or_authority(self):
        low = make_structural_proposal(confidence=0.01)
        high = replace(low, confidence=0.999999)
        low_impact = classify(low)
        high_impact = classify(high)
        self.assertEqual(low_impact.classification.structural_class, S1)
        self.assertEqual(high_impact.classification.structural_class, S1)

        low_decision = evaluate_pama_v13(
            make_pama(low, confidence=0.01), low_impact,
            current_state_digest=low.state_digest,
            current_dependency_digest=low.dependency_digest,
        )
        high_decision = evaluate_pama_v13(
            make_pama(high, confidence=0.999999), high_impact,
            current_state_digest=high.state_digest,
            current_dependency_digest=high.dependency_digest,
        )
        self.assertEqual(low_decision.outcome, high_decision.outcome)
        self.assertEqual(low_decision.permitted_actions, high_decision.permitted_actions)

    def test_repeated_proposals_do_not_accumulate_authority(self):
        structural = make_structural_proposal()
        first_impact = classify(structural)
        second_impact = classify(structural)
        self.assertEqual(first_impact.impact_digest, second_impact.impact_digest)

        first = evaluate_pama_v13(
            make_pama(structural), first_impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
        )
        second = evaluate_pama_v13(
            make_pama(structural), second_impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
        )
        self.assertEqual(first.outcome, second.outcome)
        self.assertEqual(first.permitted_actions, second.permitted_actions)
        self.assertEqual(first.reasons, second.reasons)

    def test_probabilistic_classifier_disagreement_cannot_create_implicit_allow(self):
        structural = make_structural_proposal(
            proposal_id="schema:disputed-meaning-change",
            proposed_schema=SchemaRef("domain:project", "5.0.0", "project"),
            change_kind="semantic_change",
            semantic_diff=("reinterpret status field as lifecycle state object",),
            preserves_semantics=False,
            optional_additive=False,
            migration_required=True,
            information_loss="possible",
            historical_interpretation_preserved=False,
            reversibility="compensatable",
            rollback_ref="rollback:disputed:5",
            estimator_refs=("estimator:a:claims-S1", "estimator:b:claims-S3"),
            estimator_versions=("a:4", "b:11"),
            confidence=0.999999,
        )
        impact = classify(structural)
        self.assertEqual(impact.classification.structural_class, S2)
        decision = evaluate_pama_v13(
            make_pama(structural), impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
        )
        self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW)
        self.assertNotIn(dsm.DOMAIN_SCHEMA_MUTATION, decision.permitted_actions)

    def test_s1_bound_failure_escalates_to_s2(self):
        policy_profile = StructuralPolicy(s1_max_affected_memories=100)
        impact = classify(make_structural_proposal(affected_memory_count=101), structural_policy=policy_profile)
        self.assertEqual(impact.classification.structural_class, S2)
        self.assertFalse(impact.classification.autonomous_eligible)
        self.assertTrue(any("affected-memory" in reason for reason in impact.classification.reasons))

    def test_semantic_or_migration_change_is_s2_and_requires_human_review(self):
        structural = make_structural_proposal(
            proposal_id="schema:meaning-change",
            proposed_schema=SchemaRef("domain:project", "5.0.0", "project"),
            change_kind="semantic_change",
            semantic_diff=("change status from enum value to lifecycle state object",),
            preserves_semantics=False,
            optional_additive=False,
            migration_required=True,
            information_loss="possible",
            historical_interpretation_preserved=False,
            reversibility="compensatable",
            rollback_ref="rollback:migration:5",
        )
        impact = classify(structural)
        self.assertEqual(impact.classification.structural_class, S2)
        self.assertEqual(impact.classification.required_authority, "human_review")

        undecided = evaluate_pama_v13(
            make_pama(structural), impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
        )
        self.assertEqual(undecided.outcome, policy.REQUIRE_REVIEW)
        with self.assertRaisesRegex(StructuralMutationError, "has not been authorized"):
            authorize_lifecycle(
                impact, undecided,
                current_state_digest=structural.state_digest,
                current_dependency_digest=structural.dependency_digest,
                decision_ref="decision:s2:pending",
            )

        reviewed_pama = make_pama(
            structural,
            review_satisfied=True,
            approval_refs=("approval:human:42",),
        )
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # The S2 human-review requirement is unchanged and still asserted; only
        # the discharge route moved. The evaluator holds an adjudication of this
        # schema transition, authored ahead of the proposal.
        _corpus = corpus_for(rule(
            rule_id="rule:schema-s2-migration", target=reviewed_pama.target_reference,
            criterion="schema-migration", from_state="v1", to_values=("v2",),
        ))
        reviewed = evaluate_pama_v13(
            reviewed_pama, impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
            evidence=_corpus.evidence_for(
                target_reference=reviewed_pama.target_reference,
                criterion="schema-migration", pre_state="v1", proposed_value="v2",
            ),
            verifier_registry=registry_for(_corpus),
        )
        self.assertEqual(reviewed.outcome, policy.ALLOW_WITH_LEDGER)
        document = build_pama_decision_v13(
            reviewed_pama,
            reviewed,
            impact,
            selected_action=dsm.DOMAIN_SCHEMA_MUTATION,
            receipt_ref="receipt:s2",
            selection_mode="human",
            approval_refs=("approval:human:42",),
        )
        self.assertEqual(document["policy"]["required_review_refs"], ["approval:human:42"])
        lifecycle = authorize_lifecycle(
            impact,
            reviewed,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
            decision_ref="decision:s2",
            approval_refs=("approval:human:42",),
        )
        self.assertEqual(lifecycle.lifecycle_state, "authorized")

    def test_scope_authority_and_destructive_change_escalate_to_s3(self):
        structural = make_structural_proposal(
            proposal_id="schema:widen-and-retire",
            proposed_schema=SchemaRef("domain:project", "5.0.0", "tenant"),
            change_kind="destructive_retirement",
            semantic_diff=("retire legacy project field and reinterpret it as tenant governance state",),
            optional_additive=False,
            scope_posture="widened",
            authority_posture="governance_bearing",
            isolation_posture="changed",
            information_loss="certain",
            historical_interpretation_preserved=False,
            reversibility="irreversible",
            live_dependency_refs=("consumer:legacy",),
            confidence=1.0,
        )
        impact = classify(structural)
        self.assertEqual(impact.classification.structural_class, S3)
        self.assertFalse(impact.classification.autonomous_eligible)
        pama = make_pama(
            structural,
            risk_class="critical",
            downstream_authority=policy.A5,
            requested_scope_change="project -> tenant",
            confidence=1.0,
        )
        decision = evaluate_pama_v13(
            pama, impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
        )
        self.assertEqual(decision.outcome, policy.BLOCK)

    def test_stale_state_or_dependency_snapshot_invalidates_authorization(self):
        structural = make_structural_proposal()
        impact = classify(structural)
        pama = make_pama(structural)
        with self.assertRaisesRegex(StructuralMutationError, "state snapshot digest changed"):
            evaluate_pama_v13(
                pama, impact,
                current_state_digest=digest("state:v5"),
                current_dependency_digest=structural.dependency_digest,
            )
        with self.assertRaisesRegex(StructuralMutationError, "dependency snapshot digest changed"):
            evaluate_pama_v13(
                pama, impact,
                current_state_digest=structural.state_digest,
                current_dependency_digest=digest("deps:v5"),
            )

    def test_declared_rollback_is_governed_and_reconstructable(self):
        structural = make_structural_proposal()
        impact = classify(structural)
        decision = evaluate_pama_v13(
            make_pama(structural), impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
        )
        lifecycle = activate(authorize_lifecycle(
            impact,
            decision,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
            decision_ref="decision:s1:rollback",
        ))
        with self.assertRaisesRegex(StructuralMutationError, "does not match"):
            rollback(lifecycle, rollback_ref="rollback:wrong", execution_ref="execution:rollback:1")
        rolled_back = rollback(
            lifecycle,
            rollback_ref=structural.rollback_ref,
            execution_ref="execution:rollback:1",
        )
        self.assertEqual(rolled_back.lifecycle_state, SUPERSEDED)
        self.assertEqual(rolled_back.rollback_ref, structural.rollback_ref)
        self.assertEqual(rolled_back.rollback_execution_ref, "execution:rollback:1")

    def test_retirement_waits_for_live_dependencies_and_residue(self):
        structural = make_structural_proposal()
        impact = classify(structural)
        decision = evaluate_pama_v13(
            make_pama(structural), impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
        )
        lifecycle = supersede(activate(authorize_lifecycle(
            impact,
            decision,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
            decision_ref="decision:s1",
        )))
        with self.assertRaisesRegex(StructuralMutationError, "live dependencies"):
            retire(lifecycle, live_dependency_refs=("consumer:still-live",))
        with self.assertRaisesRegex(StructuralMutationError, "residue obligations"):
            retire(lifecycle, pending_residue_refs=("projection:old-schema",))
        self.assertEqual(retire(lifecycle).lifecycle_state, RETIRED)

    def test_historical_pama_12_remains_valid_and_old_consumer_rejects_13(self):
        structural = make_structural_proposal()
        pama = make_pama(structural)
        legacy_decision = dsm.evaluate(pama)
        legacy = dsm.build_pama_decision(
            pama,
            legacy_decision,
            selected_action=receipts.NO_ACTION,
            selection_mode=None,
            receipt_ref="receipt:legacy",
        )
        self.assertEqual(legacy["schema_version"], "1.2.0")
        dsm.enforce_consumer_compatibility(
            legacy,
            supported_schema_versions=("1.2.0",),
            supported_operations=(dsm.DOMAIN_SCHEMA_MUTATION,),
        )

        impact = classify(structural)
        decision = evaluate_pama_v13(
            pama, impact,
            current_state_digest=structural.state_digest,
            current_dependency_digest=structural.dependency_digest,
        )
        current = build_pama_decision_v13(
            pama,
            decision,
            impact,
            selected_action=dsm.DOMAIN_SCHEMA_MUTATION,
            receipt_ref="receipt:current",
        )
        with self.assertRaisesRegex(ValueError, "unsupported PAMA schema version"):
            dsm.enforce_consumer_compatibility(
                current,
                supported_schema_versions=("1.2.0",),
                supported_operations=(dsm.DOMAIN_SCHEMA_MUTATION,),
            )
        dsm.enforce_consumer_compatibility(
            current,
            supported_schema_versions=("1.2.0", "1.3.0"),
            supported_operations=(dsm.DOMAIN_SCHEMA_MUTATION,),
        )


if __name__ == "__main__":
    unittest.main()
