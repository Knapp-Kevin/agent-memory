#!/usr/bin/env python3
"""Emit exact-head ADR-032 structural mutation classification evidence."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref import domain_schema_mutation as dsm, policy  # noqa: E402
from agentmem_ref.structural_mutation import (  # noqa: E402

    S0,
    S1,
    S2,
    S3,
    StructuralMutationError,
    StructuralProposal,
    SchemaRef,
    activate,
    authorize_lifecycle,
    classify,
    evaluate_pama_v13,
    retire,
    rollback,
    supersede,
)
from agentmem_ref.structural_pama import build_pama_decision_v13  # noqa: E402
from agentmem_ref.verification import (  # noqa: E402
    TRANSITION_VERIFIER,
    TransitionRule,
    TransitionRuleCorpus,
    VerifierRegistry,
)


def digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def structural(**overrides) -> StructuralProposal:
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


def pama(s: StructuralProposal, **overrides) -> policy.Proposal:
    values = dict(
        proposal_id=s.proposal_id,
        actor_id="agent:schema-observer",
        charter_version="charter:1",
        target_reference="domain-model:project-a",
        target_class=policy.M3,
        scope="tenant-a/project-a",
        operation=dsm.DOMAIN_SCHEMA_MUTATION,
        current_strength="promoted",
        proposed_strength="canonical",
        downstream_authority=policy.A3,
        reversibility=s.reversibility,
        risk_class="low",
        evidence_refs=s.evidence_refs,
        estimator_refs=s.estimator_refs,
        estimator_versions=s.estimator_versions,
        confidence=s.confidence,
        state_snapshot=s.state_digest,
        tenant_ref=s.tenant_ref,
        purpose="domain ontology evolution",
        isolation_domain_refs=s.isolation_domain_refs,
        required_isolation_domain_refs=s.isolation_domain_refs,
        project_ref="project-a",
    )
    values.update(overrides)
    return policy.Proposal(**values)


def build_report(agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent-memory commit must be an exact 40-character SHA")

    s0 = structural(
        proposal_id="projection:rebuild",
        current_schema=SchemaRef("projection:graph", "2", "project"),
        proposed_schema=SchemaRef("projection:graph", "3", "project"),
        layer="derived",
        change_kind="rebuild_only",
        semantic_diff=("replace graph projection layout without semantic change",),
        optional_additive=False,
        affected_memory_count=5000,
        rollback_ref="rollback:projection:graph:2",
    )
    s0_impact = classify(s0)

    s1 = structural()
    s1_impact = classify(s1)
    s1_pama = pama(s1)
    s1_decision = evaluate_pama_v13(
        s1_pama,
        s1_impact,
        current_state_digest=s1.state_digest,
        current_dependency_digest=s1.dependency_digest,
    )
    s1_document = build_pama_decision_v13(
        s1_pama,
        s1_decision,
        s1_impact,
        selected_action=dsm.DOMAIN_SCHEMA_MUTATION,
        receipt_ref="receipt:s1",
    )
    s1_lifecycle = authorize_lifecycle(
        s1_impact,
        s1_decision,
        current_state_digest=s1.state_digest,
        current_dependency_digest=s1.dependency_digest,
        decision_ref="decision:s1",
    )
    s1_active = activate(s1_lifecycle)
    s1_superseded = supersede(s1_active)
    s1_retired = retire(s1_superseded)
    s1_rollback = rollback(
        s1_active,
        rollback_ref=s1.rollback_ref,
        execution_ref="execution:rollback:s1",
    )

    s2 = structural(
        proposal_id="schema:semantic-migration",
        proposed_schema=SchemaRef("domain:project", "5.0.0", "project"),
        change_kind="semantic_change",
        semantic_diff=("change status enum into lifecycle state object",),
        preserves_semantics=False,
        optional_additive=False,
        migration_required=True,
        information_loss="possible",
        historical_interpretation_preserved=False,
        reversibility="compensatable",
        rollback_ref="rollback:migration:5",
    )
    s2_impact = classify(s2)
    s2_pending = evaluate_pama_v13(
        pama(s2), s2_impact,
        current_state_digest=s2.state_digest,
        current_dependency_digest=s2.dependency_digest,
    )
    s2_reviewed_pama = pama(s2, review_satisfied=True, approval_refs=("approval:human:42",))
    # ADR-037 step 4b-2 (entry #24). The S2 human-review requirement is
    # unchanged; only the discharge route is. The evaluator holds an
    # adjudication of this schema migration, authored ahead of the proposal.
    _s2_corpus = TransitionRuleCorpus((TransitionRule(
        rule_id="rule:s2-schema-migration",
        target_reference=s2_reviewed_pama.target_reference,
        criterion="schema-migration", from_state="v1",
        permitted_to_values=("v2",),
    ),))
    _s2_registry = VerifierRegistry()
    _s2_registry.register(TRANSITION_VERIFIER, _s2_corpus.verifier())
    s2_reviewed = evaluate_pama_v13(
        s2_reviewed_pama, s2_impact,
        current_state_digest=s2.state_digest,
        current_dependency_digest=s2.dependency_digest,
        evidence=_s2_corpus.evidence_for(
            target_reference=s2_reviewed_pama.target_reference,
            criterion="schema-migration", pre_state="v1", proposed_value="v2",
        ),
        verifier_registry=_s2_registry,
    )
    s2_document = build_pama_decision_v13(
        s2_reviewed_pama,
        s2_reviewed,
        s2_impact,
        selected_action=dsm.DOMAIN_SCHEMA_MUTATION,
        receipt_ref="receipt:s2",
        selection_mode="human",
        approval_refs=("approval:human:42",),
    )

    disputed = structural(
        proposal_id="schema:disputed-semantic-migration",
        proposed_schema=SchemaRef("domain:project", "5.0.0", "project"),
        change_kind="semantic_change",
        semantic_diff=("reinterpret status as lifecycle state despite estimator disagreement",),
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
    disputed_impact = classify(disputed)
    disputed_decision = evaluate_pama_v13(
        pama(disputed), disputed_impact,
        current_state_digest=disputed.state_digest,
        current_dependency_digest=disputed.dependency_digest,
    )

    s3 = structural(
        proposal_id="schema:destructive-widening",
        proposed_schema=SchemaRef("domain:project", "5.0.0", "tenant"),
        change_kind="destructive_retirement",
        semantic_diff=("retire project field and reinterpret it as tenant governance state",),
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
    s3_impact = classify(s3)
    s3_decision = evaluate_pama_v13(
        pama(
            s3,
            risk_class="critical",
            downstream_authority=policy.A5,
            requested_scope_change="project -> tenant",
            confidence=1.0,
        ),
        s3_impact,
        current_state_digest=s3.state_digest,
        current_dependency_digest=s3.dependency_digest,
    )

    low_conf = structural(confidence=0.01)
    high_conf = replace(low_conf, confidence=0.999999)
    low_impact = classify(low_conf)
    high_impact = classify(high_conf)
    low_decision = evaluate_pama_v13(
        pama(low_conf, confidence=0.01), low_impact,
        current_state_digest=low_conf.state_digest,
        current_dependency_digest=low_conf.dependency_digest,
    )
    high_decision = evaluate_pama_v13(
        pama(high_conf, confidence=0.999999), high_impact,
        current_state_digest=high_conf.state_digest,
        current_dependency_digest=high_conf.dependency_digest,
    )

    repeated_impact = classify(s1)
    repeated_decision = evaluate_pama_v13(
        pama(s1), repeated_impact,
        current_state_digest=s1.state_digest,
        current_dependency_digest=s1.dependency_digest,
    )

    stale_state_blocked = stale_dependency_blocked = False
    try:
        evaluate_pama_v13(
            s1_pama, s1_impact,
            current_state_digest=digest("state:v5"),
            current_dependency_digest=s1.dependency_digest,
        )
    except StructuralMutationError:
        stale_state_blocked = True
    try:
        evaluate_pama_v13(
            s1_pama, s1_impact,
            current_state_digest=s1.state_digest,
            current_dependency_digest=digest("deps:v5"),
        )
    except StructuralMutationError:
        stale_dependency_blocked = True

    live_dependency_retirement_blocked = residue_retirement_blocked = False
    try:
        retire(s1_superseded, live_dependency_refs=("consumer:still-live",))
    except StructuralMutationError:
        live_dependency_retirement_blocked = True
    try:
        retire(s1_superseded, pending_residue_refs=("projection:old-schema",))
    except StructuralMutationError:
        residue_retirement_blocked = True

    invariants = {
        "derived_rebuild_is_s0_not_domain_mutation": s0_impact.classification.structural_class == S0,
        "bounded_additive_domain_extension_is_s1": s1_impact.classification.structural_class == S1,
        "structural_record_preserves_semantic_diff_and_isolation_scope": (
            s1_impact.to_dict()["impact"]["semantic_diff"] == list(s1.semantic_diff)
            and s1_impact.to_dict()["impact"]["tenant_ref"] == s1.tenant_ref
            and s1_impact.to_dict()["impact"]["isolation_domain_refs"] == list(s1.isolation_domain_refs)
        ),
        "s1_autonomy_is_deterministic_and_ledgered": (
            s1_impact.classification.autonomous_eligible
            and s1_decision.outcome == policy.ALLOW_WITH_LEDGER
            and s1_document["decision"]["selection_mode"] == "deterministic"
            and "required_review_refs" not in s1_document["policy"]
        ),
        "s1_lifecycle_reaches_retired_only_through_governed_states": s1_retired.lifecycle_state == "retired",
        "declared_s1_rollback_is_reconstructable": (
            s1_rollback.lifecycle_state == "superseded"
            and s1_rollback.rollback_ref == s1.rollback_ref
            and s1_rollback.rollback_execution_ref == "execution:rollback:s1"
        ),
        "semantic_migration_is_s2_review_required": (
            s2_impact.classification.structural_class == S2
            and s2_pending.outcome == policy.REQUIRE_REVIEW
        ),
        "s2_human_review_can_authorize_without_becoming_autonomous": (
            not s2_impact.classification.autonomous_eligible
            and s2_reviewed.outcome == policy.ALLOW_WITH_LEDGER
            and s2_document["decision"]["selection_mode"] == "human"
            and s2_document["policy"]["required_review_refs"] == ["approval:human:42"]
        ),
        "probabilistic_classifier_disagreement_cannot_implicit_allow": (
            disputed_impact.classification.structural_class == S2
            and disputed_decision.outcome == policy.REQUIRE_REVIEW
        ),
        "destructive_scope_authority_change_is_s3_and_blocked": (
            s3_impact.classification.structural_class == S3
            and s3_decision.outcome == policy.BLOCK
        ),
        "estimator_confidence_cannot_lower_structural_authority": (
            low_impact.classification.structural_class == high_impact.classification.structural_class == S1
            and low_decision.outcome == high_decision.outcome == policy.ALLOW_WITH_LEDGER
        ),
        "repeated_proposal_does_not_accumulate_authority": (
            repeated_impact.impact_digest == s1_impact.impact_digest
            and repeated_decision.outcome == s1_decision.outcome
            and repeated_decision.permitted_actions == s1_decision.permitted_actions
        ),
        "stale_state_snapshot_invalidates_structural_authorization": stale_state_blocked,
        "dependency_drift_invalidates_structural_authorization": stale_dependency_blocked,
        "live_dependencies_block_retirement": live_dependency_retirement_blocked,
        "residue_obligations_block_retirement": residue_retirement_blocked,
        "structural_evidence_grants_no_authority": (
            s1_impact.authority_effect == "none"
            and s2_impact.authority_effect == "none"
            and disputed_impact.authority_effect == "none"
            and s3_impact.authority_effect == "none"
        ),
    }
    invariants = {name: bool(value) for name, value in invariants.items()}

    return {
        "schema_version": "1.0.0",
        "agent_memory_commit": agent_memory_commit,
        "structural_policy": {
            "policy_id": s1_impact.structural_policy.policy_id,
            "policy_version": s1_impact.structural_policy.policy_version,
            "classifier_id": s1_impact.structural_policy.classifier_id,
            "classifier_version": s1_impact.structural_policy.classifier_version,
        },
        "cases": {
            "s0_derived_rebuild": s0_impact.to_dict(),
            "s1_autonomous_additive": {
                "impact": s1_impact.to_dict(),
                "pama_decision": s1_document,
                "retired_lifecycle_state": s1_retired.lifecycle_state,
                "rollback_lifecycle_state": s1_rollback.lifecycle_state,
                "rollback_execution_ref": s1_rollback.rollback_execution_ref,
            },
            "s2_semantic_migration": {
                "impact": s2_impact.to_dict(),
                "pending_outcome": s2_pending.outcome,
                "reviewed_pama_decision": s2_document,
            },
            "disputed_probabilistic_classification": {
                "impact": disputed_impact.to_dict(),
                "outcome": disputed_decision.outcome,
            },
            "s3_destructive_scope_authority": {
                "impact": s3_impact.to_dict(),
                "outcome": s3_decision.outcome,
            },
        },
        "structural_invariants": invariants,
        "structural_invariants_passed": all(invariants.values()),
        "authority_effect": "none",
        "limitations": [
            "PAMA 1.3 proves one bounded S1 autonomous profile; it does not make arbitrary additive changes autonomous.",
            "S0 is classified here but remains a derived maintenance path, not domain_schema_mutation.",
            "S2/S3 remain explicitly human-authorized or blocked; no estimator confidence, disagreement, or repetition can lower their floor.",
            "Rollback records the authorized rollback reference and execution evidence; provider-specific physical restoration remains a component/runtime responsibility.",
            "The reference lifecycle demonstrates authority and retirement gates; provider-specific migration execution remains a component/runtime responsibility.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    report = build_report(args.agent_memory_commit)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    if not report["structural_invariants_passed"]:
        failed = [name for name, passed in report["structural_invariants"].items() if not passed]
        print(f"structural mutation invariants failed: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
