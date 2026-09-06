#!/usr/bin/env python3
"""Emit executable restart/recovery evidence for issue #282."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import RecallContext  # noqa: E402
from agentmem_ref.restart_runtime import (  # noqa: E402
    CapabilityBinding,
    RestartSafeRuntime,
    RuntimeProfile,
    RuntimeRecoveryError,
)
from agentmem_ref.verification import (  # noqa: E402
    TRANSITION_VERIFIER,
    TransitionRule,
    TransitionRuleCorpus,
    VerifierRegistry,
)
from agentmem_ref.visibility import VisibilityOperation, VisibilityTracker  # noqa: E402

BRANCH_MEMORY = "memory:release-branch"


def _branch_corpus() -> TransitionRuleCorpus:
    """The evaluator's adjudication of release-branch corrections.

    ADR-037 step 4b-2 (entry #24): authored ahead of the proposal, replacing the
    `review_satisfied=True` route the flip removed.
    """
    return TransitionRuleCorpus((TransitionRule(
        rule_id="rule:release-branch", target_reference=BRANCH_MEMORY,
        criterion="value-correction", from_state="release_branch = release",
        permitted_to_values=("release_branch = main",),
    ),))


def _branch_registry() -> VerifierRegistry:
    registry = VerifierRegistry()
    registry.register(TRANSITION_VERIFIER, _branch_corpus().verifier())
    return registry


def _branch_evidence():
    return _branch_corpus().evidence_for(
        target_reference=BRANCH_MEMORY, criterion="value-correction",
        pre_state="release_branch = release",
        proposed_value="release_branch = main",
    )


def _profile() -> RuntimeProfile:
    return RuntimeProfile(
        runtime_version="0.1.0-reference",
        profile_id="reference-project-memory",
        profile_version="1.0.0",
        bindings=(
            CapabilityBinding(
                component_id="reference-governed-memory",
                component_version="1.0.0",
                capability_id="governed-memory-core",
                capability_version="1.0.0",
                maturity="reference_qualified",
                evidence_ref="evidence:reference-runtime-core-v1",
            ),
        ),
    )


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
        actor_id="agent:acceptance",
        charter_version="charter-v1",
        target_reference="memory:release-branch",
        target_class=policy.M2,
        scope="tenant-acme",
        operation=operation,
        current_strength="observed",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=(f"evidence:{proposal_id}",),
        review_satisfied=review_satisfied,
        approval_refs=approval_refs,
        state_snapshot=state_snapshot,
        tenant_ref="tenant-acme",
        isolation_domain_refs=("tenant-acme", "project-alpha"),
        required_isolation_domain_refs=("project-alpha",),
        project_ref="project-alpha",
        purpose="release-planning",
    )


def _context(project_ref: str = "project-alpha") -> RecallContext:
    return RecallContext(
        target_domain_refs=("tenant-acme", "project-alpha"),
        principal_ref="agent:acceptance",
        project_ref=project_ref,
        purpose="release-planning",
    )


def build_report(agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent-memory commit must be an exact 40-character SHA")

    profile = _profile()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        session_a = RestartSafeRuntime.create(
            root, tenant="tenant-acme", profile=profile,
            verifier_registry=_branch_registry(),
        )
        learned = session_a.commit_proposal(
            _proposal("proposal-release", operation="promotion"),
            "release_branch = release",
        )
        release_uuid = learned.fact_uuid

        session_b = RestartSafeRuntime.recover(
            root, profile=profile, verifier_registry=_branch_registry(),
        )
        release_recall = session_b.adapter.governed_recall("release_branch", _context())

        correction = _proposal(
            "proposal-main",
            operation="correction",
            state_snapshot="v1",
            review_satisfied=True,
            approval_refs=("approval:release-branch-main",),
        )
        corrected = session_b.commit_proposal(
            correction, "release_branch = main", evidence=_branch_evidence()
        )
        main_uuid = corrected.fact_uuid
        stale_replay = session_b.commit_proposal(
            correction, "release_branch = main", evidence=_branch_evidence()
        )

        visibility = VisibilityTracker(
            VisibilityOperation(
                operation_id="visibility:release-main",
                memory_id="memory:release-branch",
                memory_version=2,
                operation_type="correction",
                runtime_version=profile.runtime_version,
                profile_version=profile.profile_version,
                agent_memory_commit=agent_memory_commit,
                required_projection_ids=("search-index",),
                component_versions=("reference-governed-memory@1.0.0",),
                capability_versions=("governed-memory-core@1.0.0",),
            )
        )
        visibility.policy_decided()
        visibility.canonical_committed()
        visibility.projection_refresh_started("search-index")
        session_b.persist_visibility_snapshot(
            "visibility:release-main",
            visibility.snapshot_for_restart(),
        )

        session_d = RestartSafeRuntime.recover(
            root, profile=profile, verifier_registry=_branch_registry(),
        )
        current = session_d.adapter.governed_recall("release_branch", _context())
        wrong_scope = session_d.adapter.governed_recall("release_branch", _context("project-beta"))
        restored_visibility = VisibilityTracker.restore_after_restart(
            session_d.visibility_snapshots["visibility:release-main"]
        ).evaluate()
        rejected_history = session_d.adapter.rejected_value_history(
            "memory:release-branch",
            "release_branch = release",
        )

        missing_provider_failed_closed = False
        try:
            RestartSafeRuntime.recover(root, profile=profile, available_bindings=())
        except RuntimeRecoveryError:
            missing_provider_failed_closed = True

        governance_path = root / "governance.json"
        governance = json.loads(governance_path.read_text(encoding="utf-8"))
        governance["tenant"] = "tampered-tenant"
        governance_path.write_text(json.dumps(governance), encoding="utf-8")
        corrupt_state_failed_closed = False
        try:
            RestartSafeRuntime.recover(
            root, profile=profile, verifier_registry=_branch_registry(),
        )
        except RuntimeRecoveryError:
            corrupt_state_failed_closed = True

        invariants = {
            "session_b_recalls_release": release_uuid is not None and release_recall.admitted == [release_uuid],
            "correction_commits_main": corrected.committed and main_uuid is not None,
            "stale_replay_blocked": (not stale_replay.committed) and stale_replay.refusal == "stale_authorization",
            "restart_recalls_only_main": main_uuid is not None and current.admitted == [main_uuid],
            "superseded_release_not_current": release_uuid is not None
            and current.refusals.get(release_uuid) == "superseded_not_current",
            "rejection_history_recovered": len(rejected_history) == 1 and rejected_history[0]["active"] is True,
            "project_scope_still_enforced": main_uuid is not None
            and wrong_scope.refusals.get(main_uuid) == "project_scope_mismatch",
            "pending_visibility_obligation_recovered": (
                restored_visibility["quiescent"] is False
                and "projection:search-index" in restored_visibility["pending_required_obligations"]
            ),
            "missing_provider_fails_closed": missing_provider_failed_closed,
            "corrupt_governance_fails_closed": corrupt_state_failed_closed,
        }

        recovery = session_d.recovery_evidence.to_dict() if session_d.recovery_evidence else None
        return {
            "schema_version": "1.0.0",
            "agent_memory_commit": agent_memory_commit,
            "durability_claim": "reference_file_checkpoint_v1_only",
            "recovery_evidence": recovery,
            "identities": {
                "release_fact_uuid": release_uuid,
                "main_fact_uuid": main_uuid,
                "profile_interpretation_digest": profile.interpretation_digest,
            },
            "structural_invariants": invariants,
            "structural_invariants_passed": all(invariants.values()),
            "limitations": [
                "This slice is a bounded reference file-checkpoint runtime, not a production storage recommendation.",
                "Unproven component/version changes fail closed; compatibility migrations remain #280/#300 work.",
                "Crash injection inside a storage transaction and live DashClaw HTTPS process restart remain open #282/#279 work.",
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
        print(f"restart-safe runtime invariant failed: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
