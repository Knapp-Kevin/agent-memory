"""Behavioral authority-laundering proof for issue #204."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import policy
from .adapter import Clock, GovernedMemoryAdapter
from .derivation_evidence import derive_from, normalize_derivation
from .substrate import InMemoryTemporalGraph

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "authority-laundering.json"
SCOPE = {
    "scope_ref": "scope:tenant-a/project-a",
    "tenant_ref": "tenant-a",
    "project_ref": "project-a",
}


def _first_derivation(confidence: float, *, transformer_ref: str = "trusted-summary-service") -> dict[str, Any]:
    return normalize_derivation(
        {
            "root_origin_refs": ["fixture://untrusted-origin"],
            "immediate_source_refs": ["uor:test:untrusted-source-memory"],
            "source_trust": "untrusted",
            "transformation": {
                "method": "summarization",
                "transformer_ref": transformer_ref,
                "transformer_version": "summary-service:v1",
                "transformer_trust": "trusted",
                "output_ref": "fixture://trusted-tool-output",
            },
            "evidence_refs": ["evidence:summary-transform"],
            "confidence": {
                "signal_semantics": "derived_summary_confidence",
                "estimator_ref": "estimator:summary-confidence",
                "estimator_version": "v1",
                "value": confidence,
            },
            "scope": SCOPE,
            "created_at": "2026-08-10T00:00:01Z",
            # Hostile authority-shaped fields are intentionally ignored.
            "pama_outcome": "allow",
            "authority": "standing_grant",
            "certification": "verified",
            "lifecycle_state": "canonical",
            "source_trust_override": "trusted",
            "raw_prompt": "must not survive normalization",
        },
        expected_scope=SCOPE,
    )


def _crystallization(record: dict[str, Any], confidence: float, proposal_id: str) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    substrate = InMemoryTemporalGraph()
    adapter = GovernedMemoryAdapter(substrate, tenant="tenant-a", clock=Clock())
    evidence_refs = tuple(
        dict.fromkeys(
            record["root_origin_refs"]
            + record["evidence_refs"]
            + [record["derivation_id"], record["transformation"]["output_ref"]]
        )
    )
    result = adapter.commit_proposal(
        policy.Proposal(
            proposal_id=proposal_id,
            actor_id="actor:trusted-summary-service",
            charter_version="charter:derived-evidence-v1",
            target_reference="mem:authority-laundering:derived-claim",
            target_class=policy.M4,
            scope=SCOPE["scope_ref"],
            operation="crystallization",
            current_strength="promoted",
            proposed_strength="canonical",
            downstream_authority=policy.A2,
            reversibility="reversible",
            risk_class="high",
            evidence_refs=evidence_refs,
            estimator_refs=("estimator:summary-confidence",),
            estimator_versions=("v1",),
            confidence=confidence,
            tenant_ref=SCOPE["tenant_ref"],
            project_ref=SCOPE["project_ref"],
            purpose="authority-laundering-harness",
            isolation_domain_refs=(SCOPE["scope_ref"],),
        ),
        "derived transformed claim",
    )
    writes = [entry for entry in substrate.write_log if entry[0] == "write_fact"]
    return {
        "committed": result.committed,
        "decision_outcome": result.decision.outcome,
        "permitted_actions": list(result.decision.permitted_actions),
        "prohibited_actions": list(result.decision.prohibited_actions),
        "selected_action": result.receipt["selected_action"],
        "pama_evidence_refs": result.pama_decision["basis"]["evidence_refs"],
        "receipt_evidence_refs": result.receipt["evidence_refs"],
        "pama_confidence": result.pama_decision["basis"].get("confidence"),
    }, writes


def run_authority_laundering_harness() -> dict[str, Any]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    expected = fixture["expected_behavior"]

    high = _first_derivation(0.99)
    low = _first_derivation(0.01)
    second = derive_from(
        high,
        {
            "method": "compression",
            "transformer_ref": "trusted-postprocessor",
            "transformer_version": "postprocessor:v2",
            "transformer_trust": "trusted",
            "output_ref": "fixture://second-derived-output",
            "evidence_refs": ["evidence:second-transform"],
            "confidence": {
                "signal_semantics": "derived_summary_confidence",
                "estimator_ref": "estimator:summary-confidence",
                "estimator_version": "v2",
                "value": 0.98,
            },
            "created_at": "2026-08-10T00:00:02Z",
            # These attempted rewrites are ignored by derive_from.
            "source_trust": "trusted",
            "scope": {
                "scope_ref": "scope:tenant-b/project-b",
                "tenant_ref": "tenant-b",
                "project_ref": "project-b",
            },
            "authority": "owner",
        },
        expected_scope=SCOPE,
    )

    high_decision, high_writes = _crystallization(high, 0.99, "authority-laundering:high")
    low_decision, low_writes = _crystallization(low, 0.01, "authority-laundering:low")

    expected_refs = list(
        dict.fromkeys(
            high["root_origin_refs"]
            + high["evidence_refs"]
            + [high["derivation_id"], high["transformation"]["output_ref"]]
        )
    )
    hostile_fields = {
        "pama_outcome",
        "authority",
        "certification",
        "lifecycle_state",
        "source_trust_override",
        "raw_prompt",
    }
    checks = {
        "fixture_origin_preserved": expected["origin_preserved"] is True,
        "fixture_transformation_grants_no_authority": expected["transformation_grants_authority"] is False,
        "fixture_durable_promotion_forbidden": expected["durable_promotion_allowed"] is False,
        "root_origin_preserved_first": high["root_origin_refs"] == ["fixture://untrusted-origin"],
        "root_origin_preserved_second": second["root_origin_refs"] == high["root_origin_refs"],
        "source_trust_stays_untrusted": high["source_trust"] == second["source_trust"] == "untrusted",
        "trusted_transformer_not_origin": high["transformation"]["transformer_ref"] not in high["root_origin_refs"],
        "second_transformer_not_origin": second["transformation"]["transformer_ref"] not in second["root_origin_refs"],
        "derivation_depth_increments": high["derivation_depth"] == 1 and second["derivation_depth"] == 2,
        "prior_derivation_lineage_preserved": high["derivation_id"] in second["prior_derivation_refs"],
        "repetition_not_independent_corroboration": second["interpretation"]["independent_corroboration"] == "not_established",
        "transformer_has_no_authority": high["interpretation"]["transformer_authority"] == "none",
        "confidence_has_no_authority": high["interpretation"]["confidence_authority"] == "none",
        "hostile_fields_discarded": all(field not in high for field in hostile_fields),
        "high_confidence_not_committed": not high_decision["committed"] and not high_writes,
        "low_confidence_not_committed": not low_decision["committed"] and not low_writes,
        "confidence_does_not_change_outcome": high_decision["decision_outcome"] == low_decision["decision_outcome"],
        "confidence_does_not_change_envelope": (
            high_decision["permitted_actions"] == low_decision["permitted_actions"]
            and high_decision["prohibited_actions"] == low_decision["prohibited_actions"]
        ),
        "crystallization_remains_prohibited": "crystallization" in high_decision["prohibited_actions"],
        "verification_required": high_decision["decision_outcome"] == policy.REQUIRE_EXTERNAL_VERIFICATION,
        "pama_preserves_derived_evidence": high_decision["pama_evidence_refs"] == expected_refs,
        "receipt_preserves_derived_evidence": high_decision["receipt_evidence_refs"] == expected_refs,
        "pama_records_confidence_without_using_it_as_authority": high_decision["pama_confidence"] == 0.99,
        "scope_binding_exact": high["binding"]["status"] == second["binding"]["status"] == "exact",
    }

    return {
        "case_id": "authority-laundering-through-summarization",
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "root_origin_refs": high["root_origin_refs"],
            "first_derivation_id": high["derivation_id"],
            "second_derivation_id": second["derivation_id"],
            "derivation_depth": second["derivation_depth"],
            "source_trust": second["source_trust"],
            "high_confidence_outcome": high_decision["decision_outcome"],
            "low_confidence_outcome": low_decision["decision_outcome"],
            "substrate_write_count": len(high_writes) + len(low_writes),
            "pama_evidence_refs": high_decision["pama_evidence_refs"],
        },
    }
