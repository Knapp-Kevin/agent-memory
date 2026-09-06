"""Emit composed P4 -> P4.5 deletion-completeness evidence for CI/audit.

The output contains only public, content-free evidence chains. Internal memory
content and projection identifiers are used to execute the residue model but are
never serialized.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref import policy, projections, receipts, residue  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.deletion_completeness import (  # noqa: E402
    build_deletion_completeness_chain,
    measure_deletion_completeness,
)
from agentmem_ref.portable_evidence import IssuerKey  # noqa: E402
from agentmem_ref.projection_governance import ProjectionGovernor  # noqa: E402
from agentmem_ref.evidence_qualification import group_by_dependence  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402
from agentmem_ref.verification import (  # noqa: E402
    TRANSITION_VERIFIER,
    TransitionRule,
    TransitionRuleCorpus,
    VerifierRegistry,
)

TENANT = "tenant:opaque:deletion-evidence"
SOURCE = "memory:internal:alpha"
ISSUER = "issuer:deletion-completeness-reference"
KEY = IssuerKey(
    issuer_id=ISSUER,
    key_id="key-p45-lifecycle-report",
    private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(97, 129))),
    valid_from="2026-08-01T00:00:00Z",
    valid_until="2026-08-31T23:59:59Z",
)


def _seed_proposal() -> policy.Proposal:
    return policy.Proposal(
        proposal_id="prop-seed-report",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference=SOURCE,
        target_class=policy.M2,
        scope=TENANT,
        operation="promotion",
        current_strength="reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=("ev:seed",),
        tenant_ref=TENANT,
    )


def _delete_proposal(proposal_id: str) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference=SOURCE,
        target_class=policy.M2,
        scope=TENANT,
        operation="permanent_deletion",
        current_strength="reinforced",
        proposed_strength="removed",
        downstream_authority=policy.A1,
        reversibility="irreversible",
        risk_class="low",
        evidence_refs=("ev:deletion-request",),
        tenant_ref=TENANT,
        approval_refs=("approval:data-protection-officer",),
        review_satisfied=True,
    )


def _deletion_corpus() -> TransitionRuleCorpus:
    """The evaluator's adjudication of this purge (ADR-037 step 4b-2, entry #24).

    Authored ahead of the proposal: this source may be purged. The runner
    presents a purge against it and cannot author one. Replaces the
    `review_satisfied=True` route the flip removed.
    """
    return TransitionRuleCorpus((TransitionRule(
        rule_id="rule:deletion-completeness", target_reference=SOURCE,
        criterion="permanent-deletion", from_state="current",
        permitted_to_values=("purged",),
    ),))


def _deletion_registry() -> VerifierRegistry:
    registry = VerifierRegistry()
    registry.register(TRANSITION_VERIFIER, _deletion_corpus().verifier())
    return registry


def _deletion_evidence():
    return _deletion_corpus().evidence_for(
        target_reference=SOURCE, criterion="permanent-deletion",
        pre_state="current", proposed_value="purged",
    )


def _governor() -> ProjectionGovernor:
    adapter = GovernedMemoryAdapter(
        InMemoryTemporalGraph(), TENANT, Clock(),
        verifier_registry=_deletion_registry(),
    )
    gov = ProjectionGovernor(adapter)
    adapter.commit_proposal(_seed_proposal(), "private memory content not emitted")
    gov.declare(
        "internal:summary:one",
        (SOURCE,),
        projections.ESTIMATOR_MEDIATED,
        projections.RECOVERABLE_CONTENT,
        projections.APPROXIMABLE,
        TENANT,
    )
    gov.declare(
        "internal:summary:two",
        ("internal:summary:one",),
        projections.ESTIMATOR_MEDIATED,
        projections.RECOVERABLE_CONTENT,
        projections.APPROXIMABLE,
        TENANT,
    )
    return gov


def _chain(receipt: dict, measurement, commit: str, action_ref: str) -> dict:
    return build_deletion_completeness_chain(
        receipt,
        measurement,
        agent_memory_commit=commit,
        issuer_id=ISSUER,
        issuer_key=KEY,
        issued_at="2026-08-11T21:40:02Z",
        action_ref=action_ref,
        policy_ref="policy:pama-2026-08",
        authority_state_ref="authority:rev-41",
        decision_time="2026-08-11T21:40:01Z",
        scope_ref="scope:opaque:deletion-report",
        before_state_ref="sha256:" + "6" * 64,
        source_domain_ref="domain:opaque:source",
        destination_domain_ref="domain:opaque:deleted",
        domain_authorization_state_ref="domain-auth:deletion-report:41",
    )


def _declared_residual(commit: str) -> dict:
    gov = _governor()
    result = gov.purge(
        _delete_proposal("prop-report-declared"),
        SOURCE,
        retained_by_policy={"internal:summary:two"},
        evidence=_deletion_evidence(),
        verifier_registry=_deletion_registry(),
    )
    measurement = measure_deletion_completeness(result.buckets, gov.sweep(set()))
    return _chain(result.receipt, measurement, commit, "action:delete:declared-residual")


def _undeclared_residual(commit: str) -> dict:
    gov = _governor()
    delete = _delete_proposal("prop-report-undeclared")
    # ADR-037 step 4b-2 (entry #24). This scenario reports how an
    # undeclared-residue gate failure is *measured*; it still needs a decision
    # that permits the deletion, which now comes from the evaluator's
    # adjudication rather than from `review_satisfied=True`.
    decision = policy.evaluate_with_qualified_evidence(
        delete,
        group_by_dependence(
            _deletion_evidence(), verifiers=_deletion_registry().as_mapping()
        ),
    )
    receipt = receipts.build_receipt(
        receipt_id="receipt:delete:undeclared-report",
        proposal=delete,
        decision=decision,
        selected_action="permanent_deletion",
        selection_mode="deterministic",
        timestamp="2026-08-11T21:40:01Z",
        before_state="v1",
        after_state="v1",
    )
    one_hop = residue.ResiduePlan(purged=["internal:summary:one"])
    residue.apply_purge(gov.store, one_hop, gov._purged)
    gov._purged.add(SOURCE)
    buckets = residue.partition(gov.store, gov.view(), one_hop)
    measurement = measure_deletion_completeness(buckets, gov.sweep(set()))
    return _chain(receipt, measurement, commit, "action:delete:undeclared-residual")


def _satisfied(commit: str) -> dict:
    gov = _governor()
    result = gov.purge(
        _delete_proposal("prop-report-clean"), SOURCE,
        evidence=_deletion_evidence(),
        verifier_registry=_deletion_registry(),
    )
    measurement = measure_deletion_completeness(result.buckets, gov.sweep(set()))
    return _chain(result.receipt, measurement, commit, "action:delete:zero-residue")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = {
        "report_type": "agent-memory-deletion-completeness-report",
        "version": "1.0.0",
        "agent_memory_commit": args.agent_memory_commit,
        "scenarios": {
            "declared_residual": _declared_residual(args.agent_memory_commit),
            "undeclared_residual": _undeclared_residual(args.agent_memory_commit),
            "zero_residue": _satisfied(args.agent_memory_commit),
        },
    }

    if report["scenarios"]["declared_residual"]["measurement"]["lifecycle_satisfaction"] != "residual":
        raise AssertionError("declared residual scenario did not remain residual")
    if report["scenarios"]["undeclared_residual"]["measurement"]["hard_gate_passed"]:
        raise AssertionError("undeclared residue scenario did not fail the hard gate")
    if report["scenarios"]["zero_residue"]["measurement"]["lifecycle_satisfaction"] != "satisfied":
        raise AssertionError("zero-residue scenario did not satisfy lifecycle")

    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if any(secret in rendered for secret in (
        "private memory content",
        "internal:summary:one",
        "internal:summary:two",
        SOURCE,
    )):
        raise AssertionError("public deletion-completeness report leaked internal identifiers/content")

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
