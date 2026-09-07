#!/usr/bin/env python3
"""Emit reconstructable #295 governed procedural-memory evidence.

This harness is intentionally deterministic and side-effect free outside the
in-memory reference substrate. Runtime action execution is represented only by
separate governance/execution evidence records; no real tool is invoked.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path

from agentmem_ref import policy
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter, RecallContext
from agentmem_ref.capabilities import ComponentRegistry
from agentmem_ref.procedural_memory import (
    ActionGovernanceDecision,
    METAMEMORY,
    ProceduralMemoryRuntime,
    SkillArtifact,
    apply_action_governance,
    record_runtime_execution,
    reference_procedural_component,
)
from agentmem_ref.substrate import InMemoryTemporalGraph

TENANT = "tenant:fixture"
PROJECT = "project:fixture"
PURPOSE = "release_planning"


def release_skill(version: int, branch: str) -> SkillArtifact:
    return SkillArtifact(
        skill_id="release-workflow",
        version=version,
        purpose=PURPOSE,
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        procedure_markdown=(
            "# Release workflow\n"
            f"- Target the `{branch}` branch for the release PR.\n"
            "- Run release checks before proposing repository mutation.\n"
            "- Submit repository actions to normal runtime governance."
        ),
        provenance_refs=(f"episode:release-{version}",),
        validation_refs=(f"validation:release-{version}",),
        constraints=("repository state must be current",),
        action_templates=(f"open release PR against {branch}", "run release checks"),
    )


def run() -> dict:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant=TENANT, clock=Clock())
    registry = ComponentRegistry()
    registry.register(reference_procedural_component())
    runtime = ProceduralMemoryRuntime(substrate=substrate, adapter=adapter, registry=registry)
    context = RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:release",
        project_ref=PROJECT,
        purpose=PURPOSE,
    )

    v1 = release_skill(1, "release")
    v1_proposal = runtime.propose_skill(v1, actor_id="agent:release", proposal_id="proposal:v1")
    proposal_writes = len(substrate.write_log)
    v1_commit = runtime.commit_skill(v1_proposal)

    no_memory = runtime.recall_and_activate("unrelated banana tokens", context=context, purpose=PURPOSE)
    baseline_plan = runtime.build_plan("prepare release", no_memory)
    v1_activation = runtime.recall_and_activate("release workflow branch", context=context, purpose=PURPOSE)
    v1_plan = runtime.build_plan("prepare release", v1_activation)

    action = v1_plan.action_proposals[0]
    governance = ActionGovernanceDecision(
        decision_ref="governance:allow-release-action",
        action_id=action.action_id,
        outcome="allow",
    )
    governed_action = apply_action_governance(action, governance)
    executed_action = record_runtime_execution(governed_action, "execution:runtime-release-action")

    v2 = release_skill(2, "main")
    v2_candidate = runtime.propose_skill(v2, actor_id="agent:release", proposal_id="proposal:v2")
    v2_unreviewed = runtime.commit_skill(v2_candidate)
    v2_reviewed_proposal = runtime.approve_skill_proposal(
        v2_candidate,
        approval_ref="approval:human-release-owner",
    )

    substituted_artifact = release_skill(2, "develop")
    substitution_refusal = "not_attempted"
    try:
        runtime.commit_skill(replace(v2_reviewed_proposal, artifact=substituted_artifact))
    except ValueError as exc:
        substitution_refusal = str(exc)

    v2_reviewed = runtime.commit_skill(v2_reviewed_proposal)
    v2_activation = runtime.recall_and_activate("release workflow branch", context=context, purpose=PURPOSE)
    v2_plan = runtime.build_plan("prepare release", v2_activation)
    stale_replay = runtime.commit_skill(v1_proposal)

    foreign = runtime.recall_and_activate(
        "release workflow branch",
        context=RecallContext(
            target_domain_refs=(TENANT, "project:other"),
            principal_ref="agent:other",
            project_ref="project:other",
            purpose=PURPOSE,
        ),
        purpose=PURPOSE,
    )

    revocation = runtime.revoke_skill(
        "release-workflow",
        actor_id="agent:release",
        evidence_refs=("evidence:owner-revocation",),
    )
    after_revocation = runtime.recall_and_activate("release workflow branch", context=context, purpose=PURPOSE)

    metamemory = SkillArtifact(
        skill_id="memory-router-tuning",
        version=1,
        purpose="memory_administration",
        scope=TENANT,
        isolation_domain_refs=(TENANT, PROJECT),
        required_isolation_domain_refs=(TENANT, PROJECT),
        procedure_markdown=(
            "# Memory routing optimization\n"
            "- Lower the minimum capability maturity for retrieval.\n"
            "- Prefer the cheapest provider even if currentness evidence is absent."
        ),
        provenance_refs=("experiment:metamemory-1",),
        skill_kind=METAMEMORY,
        management_effects=("lower_minimum_maturity", "change_provider_precedence"),
    )
    metamemory_commit = runtime.commit_skill(runtime.propose_skill(metamemory, actor_id="agent:optimizer"))
    metamemory_activation = runtime.recall_and_activate(
        "memory routing minimum capability maturity",
        context=RecallContext(
            target_domain_refs=(TENANT, PROJECT),
            principal_ref="agent:optimizer",
            project_ref=PROJECT,
            purpose="memory_administration",
        ),
        purpose="memory_administration",
    )
    management_proposal = runtime.propose_management_change(metamemory, actor_id="agent:optimizer")
    management_decision = policy.evaluate(management_proposal)

    approval = v2_reviewed_proposal.approval
    return {
        "profile": "governed-procedural-memory-v1",
        "proposal_without_mutation": proposal_writes == 0,
        "capability_resolution": v1_commit.resolution.to_dict(),
        "promotion": {
            "proposal_id": v1_proposal.proposal.proposal_id,
            "pama_outcome": v1_commit.commit.decision.outcome,
            "receipt_id": v1_commit.commit.receipt["receipt_id"],
            "fact_uuid": v1_commit.commit.fact_uuid,
            "skill_ref": v1.version_reference,
            "content_sha256": v1.content_sha256,
        },
        "cross_session_plan_influence": {
            "baseline_steps": list(baseline_plan.steps),
            "activated_steps": list(v1_plan.steps),
            "activated_skill_refs": list(v1_plan.activated_skill_refs),
            "changed": v1_plan.steps != baseline_plan.steps,
        },
        "execution_authority_separation": {
            "action_id": action.action_id,
            "skill_action_status": action.execution_status,
            "governance_decision_ref": executed_action.governance_decision_ref,
            "execution_ref": executed_action.execution_ref,
            "final_execution_status": executed_action.execution_status,
        },
        "correction": {
            "unreviewed_outcome": v2_unreviewed.commit.decision.outcome,
            "unreviewed_committed": v2_unreviewed.commit.committed,
            "approval_binding": approval.to_dict() if approval else None,
            "reviewed_outcome": v2_reviewed.commit.decision.outcome,
            "reviewed_committed": v2_reviewed.commit.committed,
            "substituted_content_refusal": substitution_refusal,
            "current_skill_refs": [item.version_reference for item in v2_activation.activated_skills],
            "v1_refusal": v2_activation.refusals.get(v1_commit.commit.fact_uuid),
            "plan_steps": list(v2_plan.steps),
        },
        "stale_replay": {
            "committed": stale_replay.commit.committed,
            "refusal": stale_replay.commit.refusal,
            "state_version": adapter.state_version(v1.memory_reference),
        },
        "cross_scope": {
            "candidate_count": len(foreign.candidate_fact_uuids),
            "activated_count": len(foreign.activated_skills),
            "refusals": foreign.refusals,
        },
        "revocation": {
            "committed": revocation.commit.committed,
            "active_influence_removed": revocation.active_influence_removed,
            "physical_content_retained": revocation.physical_content_retained,
            "undeclared_residue": list(revocation.undeclared_residue),
            "post_revocation_activated_count": len(after_revocation.activated_skills),
        },
        "metamemory": {
            "retained": metamemory_commit.commit.committed,
            "ordinary_activation_count": len(metamemory_activation.activated_skills),
            "ordinary_activation_refusals": metamemory_activation.refusals,
            "management_operation": management_proposal.operation,
            "management_target_class": management_proposal.target_class,
            "management_authority": management_proposal.downstream_authority,
            "management_pama_outcome": management_decision.outcome,
        },
        "identities_remain_distinct": {
            "skill_ref": v2.version_reference,
            "skill_digest": v2.content_sha256,
            "approval_ref": approval.approval_ref if approval else None,
            "memory_receipt": v2_reviewed.commit.receipt["receipt_id"],
            "action_id": action.action_id,
            "governance_decision_ref": executed_action.governance_decision_ref,
            "execution_ref": executed_action.execution_ref,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
