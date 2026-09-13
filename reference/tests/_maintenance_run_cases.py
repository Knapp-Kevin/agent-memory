"""Shared builders for maintenance-run evidence tests."""

from __future__ import annotations

from tests.qualified_fixtures import corpus_for, registry_for, rule

from agentmem_ref import domain_schema_mutation as dsm
from agentmem_ref import policy, receipts
from agentmem_ref.maintenance_run_state import seal


def selected(decision: policy.Decision, operation: str) -> str:
    if decision.outcome == policy.REQUIRE_REVIEW:
        return "enter_pending_verification"
    if decision.outcome == policy.REQUIRE_EXTERNAL_VERIFICATION:
        return "request_external_verification"
    if decision.outcome == policy.BLOCK:
        return receipts.NO_ACTION
    return operation


def pama_decision(
    operation: str = "promotion",
    *,
    risk: str = "low",
    target_class: str = policy.M3,
    downstream_authority: str = policy.A3,
    tenant: str = "tenant-a",
    purpose: str = "memory maintenance",
    reviewed: bool = False,
):
    # `reviewed` predates ADR-037. For the PAMA 1.2 domain-schema positive
    # fixture it now means "the evaluator has qualifying transition evidence",
    # not "the caller set review_satisfied plus an approval string". Other
    # historical operation fixtures retain their existing shape.
    legacy_review_assertion = reviewed and operation != dsm.DOMAIN_SCHEMA_MUTATION
    proposal = policy.Proposal(
        proposal_id=f"maintenance:{operation}:{risk}:{tenant}",
        actor_id="agent:maintenance",
        charter_version="charter:maintenance:1",
        target_reference=f"memory:{operation}",
        target_class=target_class,
        scope=f"{tenant}/project-a",
        operation=operation,
        current_strength="promoted",
        proposed_strength="canonical",
        downstream_authority=downstream_authority,
        reversibility="versioned_revocable",
        risk_class=risk,
        evidence_refs=("evidence:source-a",),
        approval_refs=("approval:independent",) if legacy_review_assertion else (),
        review_satisfied=legacy_review_assertion,
        tenant_ref=tenant,
        purpose=purpose,
        isolation_domain_refs=(f"{tenant}/project-a",),
        required_isolation_domain_refs=(f"{tenant}/project-a",),
        project_ref="project-a",
    )
    if operation == dsm.DOMAIN_SCHEMA_MUTATION:
        if reviewed:
            corpus = corpus_for(rule(
                rule_id="rule:maintenance-domain-schema",
                target=proposal.target_reference,
                criterion="maintenance-domain-schema-transition",
                from_state="v1",
                to_values=("v2",),
            ))
            evidence = corpus.evidence_for(
                target_reference=proposal.target_reference,
                criterion="maintenance-domain-schema-transition",
                pre_state="v1",
                proposed_value="v2",
            )
            decision = dsm.evaluate(
                proposal,
                evidence=evidence,
                verifier_registry=registry_for(corpus),
            )
        else:
            decision = dsm.evaluate(proposal)
        document = dsm.build_pama_decision(
            proposal,
            decision,
            selected_action=selected(decision, operation),
            selection_mode="deterministic",
            receipt_ref=f"receipt:{proposal.proposal_id}",
        )
    else:
        decision = policy.evaluate(proposal)
        document = receipts.build_pama_decision(
            proposal,
            decision,
            selected_action=selected(decision, operation),
            selection_mode="deterministic",
            receipt_ref=f"receipt:{proposal.proposal_id}",
        )
    ref = receipts.decision_ref_for(proposal.proposal_id)
    item = {"decision_ref": ref, "operation": operation, "outcome": decision.outcome}
    return ref, document, item


def run_record(
    *,
    run_id: str = "run:1",
    cursor_before=10,
    cursor_after=11,
    planned_operations=("promotion",),
    constituent_decisions=(),
    transaction_status="committed",
    commit_status="succeeded",
    validation_status="passed",
    source_currentness="current",
    policy_version="policy:1",
    commit_policy_version="policy:1",
    policy_revalidation_ref=None,
    rollback_ref=None,
    quarantine_ref=None,
    housekeeping_only=False,
    semantic_memory_changed=True,
    tenant="tenant-a",
    purpose="memory maintenance",
):
    record = {
        "schema_version": "1.0.0",
        "profile_version": "0.1.0",
        "run_id": run_id,
        "maintenance_actor": {
            "id": "agent:maintenance",
            "charter_ref": "charter:maintenance:1",
            "authority_refs": ["authority:maintenance"],
        },
        "policy_version": policy_version,
        "commit_policy_version": commit_policy_version,
        "scope": {
            "tenant_ref": tenant,
            "project_ref": "project-a",
            "purpose": purpose,
            "isolation_domain_refs": [f"{tenant}/project-a"],
        },
        "cursor_before": cursor_before,
        "cursor_after": cursor_after,
        "input_snapshot_ref": "snapshot:maintenance:1",
        "source_currentness": source_currentness,
        "source_evidence_refs": ["evidence:source-a"],
        "proposal_refs": ["proposal:maintenance:1"],
        "constituent_decisions": list(constituent_decisions),
        "planned_operations": list(planned_operations),
        "transaction_ref": f"tx:{run_id}",
        "atomicity_mode": "atomic",
        "transaction_status": transaction_status,
        "commit_status": commit_status,
        "validation_status": validation_status,
        "validation_refs": ["validation:1"] if validation_status != "not_run" else [],
        "output_refs": ["output:1"] if transaction_status == "committed" else [],
        "supersession_refs": [],
        "tombstone_refs": [],
        "estimator_evidence_refs": [],
        "semantic_memory_changed": semantic_memory_changed,
        "housekeeping_only": housekeeping_only,
        "started_at": "2026-08-13T12:00:00Z",
        "completed_at": "2026-08-13T12:01:00Z",
        "evidence_id": f"evidence:{run_id}",
        "evidence_digest": "sha256:" + "0" * 64,
    }
    if policy_revalidation_ref:
        record["policy_revalidation_ref"] = policy_revalidation_ref
    if rollback_ref:
        record["rollback_ref"] = rollback_ref
    if quarantine_ref:
        record["quarantine_ref"] = quarantine_ref
    return seal(record)