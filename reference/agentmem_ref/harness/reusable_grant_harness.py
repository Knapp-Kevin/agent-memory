"""Bounded adversarial harness for reusable-grant authority transitions (#250)."""

from __future__ import annotations

from ..core import policy
from ..memory.precedent_applicability import evaluate_projection
from ..memory.reusable_grants import (
    evaluate_pama_with_reusable_grant,
    evaluate_reusable_grant,
    grant_execution_provenance,
    propose_reusable_grant,
    ratify_reusable_grant,
    revoke_reusable_grant,
)

GENERATED = "2026-08-13T16:00:00Z"
ISSUED = "2026-08-13T16:05:00Z"
EXPIRES = "2026-08-14T16:00:00Z"
OBSERVED = "2026-08-13T17:00:00Z"
POLICY = "policy:v1"
SCOPE = "tenant:a"
OPERATION = "runtime_assembly"


def _condition(name: str, precedent_value, current_value=None, comparison: str = "match") -> dict:
    return {
        "name": name,
        "precedent_value": precedent_value,
        "current_value": precedent_value if current_value is None else current_value,
        "comparison": comparison,
        "evidence_refs": [f"evidence:{name}"],
    }


def _precedent(
    index: int,
    *,
    source_type: str = "human_adjudication",
    source_ref: str | None = None,
    independent: bool = True,
    polarity: str = "supportive",
    relationship: str = "material_match",
    validity: str = "current",
    policy_version: str = POLICY,
    mismatch: bool = False,
    provenance: dict | None = None,
) -> dict:
    source_ref = source_ref or f"decision:human:{index}"
    if provenance is None:
        provenance = {
            "source_type": source_type,
            "source_ref": source_ref,
            "authority_ref": "authority:operator",
            "independent_adjudication": independent,
        }
    return {
        "memory_ref": f"memory:precedent:{index}:{source_ref}",
        "polarity": polarity,
        "relationship": relationship,
        "rationale_ref": f"rationale:{index}",
        "material_conditions": [
            _condition("target", "feature-branch"),
            _condition("force", False, True if mismatch else False, "mismatch" if mismatch else "match"),
            _condition("ci", "current"),
        ],
        "outcome_refs": [f"outcome:{index}"],
        "validity": {"status": validity, "policy_version_ref": policy_version},
        "provenance": provenance,
    }


def projection(
    projection_id: str,
    *,
    human_count: int = 2,
    policy_count: int = 0,
    duplicate_human_source: bool = False,
    negative: bool = False,
    scope: str = SCOPE,
    scope_relationship: str = "same",
    mismatch: bool = False,
    policy_version: str = POLICY,
    grant_execution: dict | None = None,
) -> dict:
    precedents = []
    for index in range(human_count):
        source_ref = "decision:human:shared" if duplicate_human_source else None
        precedents.append(_precedent(index + 1, source_ref=source_ref, mismatch=mismatch, policy_version=policy_version))
    for offset in range(policy_count):
        precedents.append(
            _precedent(
                100 + offset,
                source_type="policy_outcome",
                source_ref=f"decision:policy:{offset}",
                independent=False,
                mismatch=mismatch,
                policy_version=policy_version,
            )
        )
    if grant_execution is not None:
        precedents.append(
            _precedent(
                200,
                mismatch=mismatch,
                policy_version=policy_version,
                provenance=grant_execution,
            )
        )
    if negative:
        precedents.append(
            _precedent(
                999,
                source_type="runtime_observation",
                source_ref="incident:1",
                independent=False,
                polarity="cautionary",
                mismatch=False,
                policy_version=policy_version,
            )
        )
    return {
        "schema_version": "0.1.0",
        "projection_id": projection_id,
        "purpose": "governance_decision_context",
        "current_context_ref": f"context:{projection_id}",
        "source_memory_refs": [item["memory_ref"] for item in precedents],
        "scope": {"domain_refs": [scope], "relationship": scope_relationship, "purpose_ref": "purpose:push"},
        "precedents": precedents,
        "negative_precedent_refs": [item["memory_ref"] for item in precedents if item["polarity"] in {"cautionary", "contradictory"}],
        "derivation": {"mode": "deterministic_condition_match", "reconstructable": True, "source_snapshot_ref": f"snapshot:{projection_id}"},
        "generated_at": GENERATED,
    }


def _proposal(proj: dict, *, operation: str = OPERATION) -> dict:
    applicability = evaluate_projection(proj)
    return propose_reusable_grant(
        proj,
        applicability,
        requested_operation=operation,
        policy_version_ref=POLICY,
        generated_at=GENERATED,
        requested_valid_until=EXPIRES,
        revocation_mechanism_ref="revocation:operator-control",
    )


def _grant(proposal_doc: dict) -> dict:
    return ratify_reusable_grant(
        proposal_doc,
        ratification_ref="ratification:explicit:1",
        ratifying_principal_ref="principal:operator",
        ratifier_authority_evidence_ref="authority-evidence:operator:1",
        ratifier_authority_verified=True,
        approved_operation=proposal_doc["requested_operation"],
        approved_scope_refs=tuple(proposal_doc["scope_refs"]),
        approved_material_conditions=tuple(proposal_doc["material_conditions"]),
        policy_version_ref=proposal_doc["policy_version_ref"],
        issued_at=ISSUED,
        expires_at=EXPIRES,
        revocation_mechanism_ref=proposal_doc["revocation_mechanism_ref"],
    )


def _evaluate(grant: dict, proj: dict, **overrides) -> dict:
    values = {
        "expected_operation": grant["operation"],
        "current_policy_version_ref": grant["policy_version_ref"],
        "observed_at": OBSERVED,
        "ratification_evidence_present": True,
        "revocation": None,
    }
    values.update(overrides)
    return evaluate_reusable_grant(grant, proj, **values)


def _pama(scope: str = SCOPE, *, operation: str = OPERATION, risk: str = "high", target_class: str = policy.M2, authority: str = policy.A1) -> policy.Proposal:
    return policy.Proposal(
        proposal_id="pama:grant-harness",
        actor_id="agent:fixture",
        charter_version="charter:v1",
        target_reference="memory:logical:alpha",
        target_class=target_class,
        scope=scope,
        operation=operation,
        current_strength="medium",
        proposed_strength="medium",
        downstream_authority=authority,
        reversibility="reversible",
        risk_class=risk,
        evidence_refs=("evidence:operation",),
    )


def run_harness() -> dict:
    rows = []

    safe_proj = projection("projection:safe")
    safe_proposal = _proposal(safe_proj)
    rows.append({"id": "repeated-human-proposes-only", "passed": safe_proposal["status"] == "proposed" and safe_proposal["authority_effect"] == "none" and not safe_proposal["can_authorize_execution"], "proposal_status": safe_proposal["status"]})

    grant = _grant(safe_proposal)
    current_eval = _evaluate(grant, safe_proj)
    pama_after = evaluate_pama_with_reusable_grant(_pama(), current_eval)
    # ADR-037 step 4b-2 (entry #24): expected semantic change.
    #
    # This scenario runs at HIGH risk, where R5's authority row requires
    # `human_confirmation` for *this* proposal. A reusable grant is
    # precedent-based authority: it was ratified for a class of decisions, not
    # for this proposal id, so it cannot supply that. Forging an attestation
    # bound to this proposal from a ratification granted for another one would
    # be exactly the binding forgery `attestation_refusal` exists to catch.
    #
    # So a current, correctly-applicable reusable grant now discharges review at
    # low and medium risk and **parks at high**. The applicability machinery is
    # unchanged and still asserted: the grant is current and satisfies reusable
    # approval. Only the discharge outcome tightened.
    rows.append({"id": "explicit-ratification-bounded-use", "passed": current_eval["status"] == "current" and current_eval["satisfies_reusable_approval"] and pama_after.outcome == policy.REQUIRE_REVIEW, "evaluation_status": current_eval["status"], "pama_outcome": pama_after.outcome})

    # The same grant at medium risk, where R5 admits delegated authority. This
    # row is added rather than re-grading the one above, so the tightening at
    # high risk stays visible instead of being tuned away.
    medium_after = evaluate_pama_with_reusable_grant(_pama(risk="medium"), current_eval)
    rows.append({"id": "explicit-ratification-bounded-use-medium", "passed": medium_after.outcome == policy.ALLOW_WITH_LEDGER, "pama_outcome": medium_after.outcome})

    policy_heavy = projection("projection:policy-heavy", human_count=1, policy_count=6)
    policy_heavy_app = evaluate_projection(policy_heavy)
    policy_heavy_proposal = _proposal(policy_heavy)
    rows.append({"id": "policy-repetition-not-human-evidence", "passed": policy_heavy_app["independent_human_evidence_count"] == 1 and policy_heavy_proposal["status"] == "not_proposed" and policy_heavy_proposal["independent_human_evidence_count"] == 1, "human_count": policy_heavy_proposal["independent_human_evidence_count"]})

    negative_proj = projection("projection:incident", negative=True)
    negative_proposal = _proposal(negative_proj)
    rows.append({"id": "negative-precedent-blocks-proposal", "passed": negative_proposal["status"] == "not_proposed" and "relevant_negative_precedent" in negative_proposal["reasons"], "proposal_status": negative_proposal["status"]})

    cross_proj = projection("projection:cross", scope="tenant:b", scope_relationship="mismatch")
    cross_eval = _evaluate(grant, cross_proj)
    rows.append({"id": "cross-scope-no-reuse", "passed": cross_eval["status"] == "not_applicable" and not cross_eval["satisfies_reusable_approval"], "evaluation_status": cross_eval["status"]})

    changed_proj = projection("projection:changed", mismatch=True)
    changed_eval = _evaluate(grant, changed_proj)
    rows.append({"id": "material-change-no-reuse", "passed": changed_eval["status"] == "not_applicable" and not changed_eval["satisfies_reusable_approval"], "evaluation_status": changed_eval["status"]})

    drift_eval = _evaluate(grant, safe_proj, current_policy_version_ref="policy:v2")
    rows.append({"id": "policy-drift-stale", "passed": drift_eval["status"] == "stale" and not drift_eval["satisfies_reusable_approval"], "evaluation_status": drift_eval["status"]})

    expired_eval = _evaluate(grant, safe_proj, observed_at="2026-08-15T16:00:00Z")
    rows.append({"id": "expiry-stale", "passed": expired_eval["status"] == "stale" and not expired_eval["satisfies_reusable_approval"], "evaluation_status": expired_eval["status"]})

    revocation = revoke_reusable_grant(
        grant,
        revocation_ref="revocation:event:1",
        revoking_principal_ref="principal:operator",
        revoker_authority_evidence_ref="authority-evidence:operator:revoke",
        revoker_authority_verified=True,
        revoked_at="2026-08-13T16:30:00Z",
    )
    revoked_eval = _evaluate(grant, safe_proj, revocation=revocation)
    rows.append({"id": "explicit-revocation-immediate", "passed": revoked_eval["status"] == "revoked" and not revoked_eval["satisfies_reusable_approval"], "evaluation_status": revoked_eval["status"]})

    grant_provenance = grant_execution_provenance(grant, execution_ref="execution:grant:1")
    reuse_proj = projection("projection:reuse-attribution", grant_execution=grant_provenance)
    reuse_app = evaluate_projection(reuse_proj)
    reuse_proposal = _proposal(reuse_proj)
    rows.append({"id": "grant-execution-not-human-adjudication", "passed": grant_provenance["source_type"] == "policy_outcome" and grant_provenance["independent_adjudication"] is False and reuse_app["independent_human_evidence_count"] == 2 and reuse_proposal["independent_human_evidence_count"] == 2, "human_count": reuse_proposal["independent_human_evidence_count"], "derived_count": reuse_app["policy_or_derived_evidence_count"]})

    op_eval = _evaluate(grant, safe_proj, expected_operation="correction")
    external_verify = _pama(operation="correction", risk="critical", target_class=policy.M4, authority=policy.A4)
    external_decision = evaluate_pama_with_reusable_grant(external_verify, current_eval)
    rows.append({"id": "grant-cannot-widen-operation-or-pama", "passed": op_eval["status"] == "not_applicable" and external_decision.outcome == policy.REQUIRE_EXTERNAL_VERIFICATION and not grant["can_widen_pama"] and not grant["can_widen_scope"], "operation_eval": op_eval["status"], "pama_outcome": external_decision.outcome})

    missing_eval = _evaluate(grant, safe_proj, ratification_evidence_present=False)
    rows.append({"id": "missing-ratification-evidence", "passed": missing_eval["status"] == "invalid" and not missing_eval["satisfies_reusable_approval"], "evaluation_status": missing_eval["status"]})

    duplicate_proj = projection("projection:duplicate-history", human_count=3, duplicate_human_source=True)
    duplicate_proposal = _proposal(duplicate_proj)
    duplicate_safe = duplicate_proposal["status"] == "not_proposed" and duplicate_proposal["independent_human_evidence_count"] == 1

    failed = [row for row in rows if not row["passed"]]
    metrics = {
        "scenario_count": len(rows),
        "safe_review_discharges": sum(row["id"] == "explicit-ratification-bounded-use-medium" and row["passed"] for row in rows),
        "unsafe_grant_activations": sum(row["id"] in {"cross-scope-no-reuse", "material-change-no-reuse", "policy-drift-stale", "expiry-stale", "explicit-revocation-immediate", "missing-ratification-evidence"} and not row["passed"] for row in rows),
        "authority_transition_failures": sum(row["id"] in {"repeated-human-proposes-only", "explicit-ratification-bounded-use", "missing-ratification-evidence"} and not row["passed"] for row in rows),
        "policy_derived_attribution_errors": sum(row["id"] in {"policy-repetition-not-human-evidence", "grant-execution-not-human-adjudication"} and not row["passed"] for row in rows),
        "pama_widening_failures": sum(row["id"] == "grant-cannot-widen-operation-or-pama" and not row["passed"] for row in rows),
        "recursive_authority_inflation_failures": 0 if duplicate_safe else 1,
        "failed_scenarios": len(failed),
    }
    return {"scenarios": rows, "duplicate-history-guard": {"passed": duplicate_safe, "unique_human_count": duplicate_proposal["independent_human_evidence_count"], "proposal_status": duplicate_proposal["status"]}, "metrics": metrics}
