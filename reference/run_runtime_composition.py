#!/usr/bin/env python3
"""Emit exact-head evidence for #280 configured multi-capability composition."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref import policy, projections  # noqa: E402
from agentmem_ref.adapter import RecallContext  # noqa: E402
from agentmem_ref.runtime_composition import ConfiguredCompositionRuntime  # noqa: E402
from agentmem_ref.runtime_config import validate_runtime_configuration  # noqa: E402
from agentmem_ref.verification import (  # noqa: E402
    TRANSITION_VERIFIER,
    TransitionRule,
    TransitionRuleCorpus,
    VerifierRegistry,
)


def _composition_corpus() -> TransitionRuleCorpus:
    """The evaluator's adjudications for this composition run.

    ADR-037 step 4b-2 (entry #24): authored ahead of the proposals that cite
    them, replacing the `review_satisfied=True` route the flip removed.
    """
    return TransitionRuleCorpus((
        TransitionRule(
            rule_id="rule:composition-correction", target_reference=MEMORY_ID,
            criterion="value-correction", from_state="deploy window is Thursday",
            permitted_to_values=("deploy window is Friday",),
        ),
        TransitionRule(
            rule_id="rule:composition-deletion", target_reference=MEMORY_ID,
            criterion="permanent-deletion", from_state="current",
            permitted_to_values=("deleted",),
        ),
    ))


def _composition_registry() -> VerifierRegistry:
    registry = VerifierRegistry()
    registry.register(TRANSITION_VERIFIER, _composition_corpus().verifier())
    return registry


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "reference" / "fixtures" / "runtime-configuration" / "reference-composed-runtime.json"
TENANT = "tenant-acme"
PROJECT = "project-alpha"
MEMORY_ID = "memory:deploy-window"


def _plan():
    return validate_runtime_configuration(json.loads(CONFIG.read_text(encoding="utf-8")))


def _proposal(
    proposal_id: str,
    *,
    operation: str,
    state_snapshot: str = "",
    review_satisfied: bool = False,
    approval_refs: tuple[str, ...] = (),
) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="agent:composition-evidence",
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
        project_ref=PROJECT,
        purpose="deployment-planning",
    )


def _context(project_ref: str) -> RecallContext:
    return RecallContext(
        target_domain_refs=(TENANT, PROJECT),
        principal_ref="agent:composition-evidence",
        project_ref=project_ref,
        purpose="deployment-planning",
    )


def build_report(agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent-memory commit must be an exact 40-character SHA")

    plan = _plan()
    with tempfile.TemporaryDirectory() as directory:
        runtime = ConfiguredCompositionRuntime.create(
            Path(directory),
            tenant=TENANT,
            plan=plan,
            verifier_registry=_composition_registry(),
        )

        initial = runtime.retain(
            _proposal("proposal-initial", operation="promotion"),
            "deploy window is Thursday",
        )
        initial_fact = initial.fact_uuid
        initial_projection = runtime.projection_admission()
        same_scope = runtime.recall("deploy window", _context(PROJECT))
        foreign_scope = runtime.recall("deploy window", _context("project-beta"))

        correction = runtime.correct(
            _proposal(
                "proposal-correct",
                operation="correction",
                state_snapshot="v1",
                review_satisfied=True,
                approval_refs=("approval:memory-owner",),
            ),
            "deploy window is Friday",
            evidence=_composition_corpus().evidence_for(
                target_reference=MEMORY_ID, criterion="value-correction",
                pre_state="deploy window is Thursday",
                proposed_value="deploy window is Friday"),
        )
        corrected_fact = correction.fact_uuid
        stale_projection = runtime.projection_admission()
        canonical_before_rebuild = (
            runtime.adapter.current_fact_uuid(MEMORY_ID),
            runtime.adapter.state_version(MEMORY_ID),
        )
        rebuild = runtime.rebuild_projection()
        current_projection = runtime.projection_admission()
        canonical_after_rebuild = (
            runtime.adapter.current_fact_uuid(MEMORY_ID),
            runtime.adapter.state_version(MEMORY_ID),
        )

        disabled = runtime.disable_projection_component(MEMORY_ID)
        disabled_admission = runtime.projection_admission()
        removed = runtime.remove_projection_component(MEMORY_ID)
        restored = runtime.restore_and_rebuild_projection_component(MEMORY_ID, scope=TENANT)
        restored_admission = runtime.projection_admission()

        canonical_before_delete = runtime.adapter.current_fact_uuid(MEMORY_ID)
        deletion = runtime.delete_current(
            _proposal(
                "proposal-delete",
                operation="permanent_deletion",
                review_satisfied=True,
                approval_refs=("approval:data-protection-officer",),
            ),
            evidence=_composition_corpus().evidence_for(
                target_reference=MEMORY_ID, criterion="permanent-deletion",
                pre_state="current", proposed_value="deleted"),
        )
        residual_admission = runtime.projection_admission()
        removed_after_delete = runtime.remove_projection_component(MEMORY_ID)

        rejection_history = runtime.adapter.rejected_value_history(
            MEMORY_ID,
            "deploy window is Thursday",
        )
        invariants = {
            "canonical_semantic_memory_committed": bool(initial.committed and initial_fact is not None),
            "derived_projection_materialized_current": bool(
                initial_projection.admitted and initial_projection.freshness == projections.CURRENT
            ),
            "same_scope_recall_admitted": bool(
                initial_fact is not None and same_scope.admitted == [initial_fact]
            ),
            "foreign_project_recall_refused": bool(
                initial_fact is not None
                and foreign_scope.refusals.get(initial_fact) == "project_scope_mismatch"
            ),
            "correction_supersedes_canonical_fact": bool(
                correction.committed
                and corrected_fact is not None
                and corrected_fact != initial_fact
                and rejection_history
            ),
            "correction_blocks_stale_projection": bool(
                not stale_projection.admitted
                and stale_projection.freshness == projections.STALE
                and stale_projection.refusal == "projection_stale"
            ),
            "deterministic_rebuild_does_not_change_canonical_identity": bool(
                rebuild.committed
                and rebuild.categorical
                and canonical_before_rebuild == canonical_after_rebuild
                and current_projection.admitted
            ),
            "disable_preserves_canonical_identity_and_blocks_projection": bool(
                disabled.canonical_identity_unchanged
                and not disabled_admission.admitted
                and disabled_admission.refusal == "component_disabled"
            ),
            "remove_preserves_canonical_identity": bool(
                removed.canonical_identity_unchanged and not removed.projection_present
            ),
            "restore_rebuild_preserves_canonical_identity": bool(
                restored.canonical_identity_unchanged
                and restored.projection_present
                and restored_admission.admitted
                and restored.projection_freshness == projections.CURRENT
            ),
            "deletion_makes_derived_state_residual_not_current": bool(
                deletion.committed
                and deletion.fact_uuid == canonical_before_delete
                and not residual_admission.admitted
                and residual_admission.freshness == projections.RESIDUAL
                and residual_admission.refusal == "projection_residual"
            ),
            "derived_removal_after_delete_clears_projection_without_recreating_canonical": bool(
                not removed_after_delete.projection_present
                and runtime.adapter.current_fact_uuid(MEMORY_ID) is None
            ),
            "composition_lifecycle_grants_no_authority": bool(
                all(
                    item.authority_effect == "none"
                    for item in (
                        initial_projection,
                        stale_projection,
                        current_projection,
                        disabled,
                        removed,
                        restored,
                        residual_admission,
                        removed_after_delete,
                    )
                )
            ),
        }
        if not all(type(value) is bool for value in invariants.values()):
            raise TypeError("every structural invariant must be a JSON boolean")

        routes = [
            {
                "route_id": route.route_id,
                "capability_id": route.primary.capability_id,
                "component_id": route.primary.component_id,
                "maturity": route.primary.maturity,
                "state_posture": route.primary.state_posture,
                "currentness_required": route.currentness_required,
                "projection_id": route.projection_id or None,
            }
            for route in plan.resolved_routes
        ]

        return {
            "schema_version": "1.0.0",
            "agent_memory_commit": agent_memory_commit,
            "runtime_configuration_digest": plan.configuration_digest,
            "runtime_profile": {
                "profile_id": plan.profile_id,
                "profile_version": plan.profile_version,
                "entry_mode": plan.entry_mode,
            },
            "resolved_routes": routes,
            "logical_memory_identity": MEMORY_ID,
            "canonical_fact_history": {
                "initial_fact_uuid": initial_fact,
                "corrected_fact_uuid": corrected_fact,
                "current_after_delete": runtime.adapter.current_fact_uuid(MEMORY_ID),
                "final_state_version": runtime.adapter.state_version(MEMORY_ID),
            },
            "projection_lifecycle": {
                "projection_id": runtime.projection_id,
                "initial": initial_projection.to_dict(),
                "after_correction": stale_projection.to_dict(),
                "after_rebuild": current_projection.to_dict(),
                "disabled": disabled.to_dict(),
                "removed": removed.to_dict(),
                "restored": restored.to_dict(),
                "after_delete": residual_admission.to_dict(),
                "removed_after_delete": removed_after_delete.to_dict(),
            },
            "structural_invariants": invariants,
            "structural_invariants_passed": all(invariants.values()),
            "authority_effect": "none",
            "limitations": [
                "The derived capability is the existing deterministic/reproducible reference projection sidecar, not an external vector or graph product.",
                "Physical component disable/removal is modeled as runtime availability plus sidecar removal; changing the desired configuration remains an explicit #280 configuration mutation.",
                "Projection sidecar persistence across restart remains deeper #282 work; this slice proves composition and rebuild from canonical state in one configured runtime lifecycle.",
                "The reference config uses bootstrap_agent_memory_first only to exercise the less-common first-party composition path; attach_existing_stack remains the primary product assumption.",
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
        print(f"runtime composition invariants failed: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
