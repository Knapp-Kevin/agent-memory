"""Deterministic structural-mutation governance under ADR-032.

Probabilistic systems may propose structural changes and contribute evidence.
They never choose their structural consequence class or durable authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json
from typing import Iterable

from ..core import policy, receipts


STRUCTURAL_IMPACT_SCHEMA_VERSION = "1.0.0"
CLASSIFIER_ID = "agent-memory-structural-impact"
CLASSIFIER_VERSION = "1.0.0"
POLICY_ID = "agent-memory-structural-autonomy"
POLICY_VERSION = "1.0.0"

S0 = "S0"
S1 = "S1"
S2 = "S2"
S3 = "S3"

PROPOSED = "proposed"
AUTHORIZED = "authorized"
ACTIVE = "active"
SUPERSEDED = "superseded"
RETIRED = "retired"


class StructuralMutationError(ValueError):
    """A structural mutation cannot be classified or transitioned safely."""


@dataclass(frozen=True)
class StructuralPolicy:
    policy_id: str = POLICY_ID
    policy_version: str = POLICY_VERSION
    classifier_id: str = CLASSIFIER_ID
    classifier_version: str = CLASSIFIER_VERSION
    s1_allowed_scopes: tuple[str, ...] = ("project", "application", "local")
    s1_max_affected_memories: int = 1000


@dataclass(frozen=True)
class SchemaRef:
    schema_id: str
    schema_version: str
    scope: str


@dataclass(frozen=True)
class StructuralProposal:
    proposal_id: str
    current_schema: SchemaRef
    proposed_schema: SchemaRef
    layer: str
    change_kind: str
    semantic_diff: tuple[str, ...]
    tenant_ref: str
    isolation_domain_refs: tuple[str, ...]
    preserves_semantics: bool
    optional_additive: bool
    migration_required: bool
    information_loss: str
    historical_interpretation_preserved: bool
    scope_posture: str
    authority_posture: str
    isolation_posture: str
    affected_memory_count: int
    dependent_refs: tuple[str, ...]
    incompatible_dependency_refs: tuple[str, ...]
    live_dependency_refs: tuple[str, ...]
    reversibility: str
    rollback_ref: str
    rebuild_obligations: tuple[str, ...]
    residue_obligations: tuple[str, ...]
    state_digest: str
    dependency_digest: str
    evidence_refs: tuple[str, ...]
    estimator_refs: tuple[str, ...] = ()
    estimator_versions: tuple[str, ...] = ()
    confidence: float | None = None


@dataclass(frozen=True)
class StructuralClassification:
    structural_class: str
    autonomous_eligible: bool
    required_authority: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class StructuralImpact:
    proposal: StructuralProposal
    classification: StructuralClassification
    structural_policy: StructuralPolicy

    @property
    def authority_effect(self) -> str:
        return "none"

    @property
    def impact_digest(self) -> str:
        rendered = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return "sha256:" + hashlib.sha256(rendered).hexdigest()

    def to_dict(self) -> dict[str, object]:
        proposal = self.proposal
        classification = self.classification
        structural_policy = self.structural_policy
        value = {
            "schema_version": STRUCTURAL_IMPACT_SCHEMA_VERSION,
            "proposal_id": proposal.proposal_id,
            "current_schema": asdict(proposal.current_schema),
            "proposed_schema": asdict(proposal.proposed_schema),
            "impact": {
                "layer": proposal.layer,
                "change_kind": proposal.change_kind,
                "semantic_diff": list(proposal.semantic_diff),
                "tenant_ref": proposal.tenant_ref or None,
                "isolation_domain_refs": list(proposal.isolation_domain_refs),
                "preserves_semantics": proposal.preserves_semantics,
                "optional_additive": proposal.optional_additive,
                "migration_required": proposal.migration_required,
                "information_loss": proposal.information_loss,
                "historical_interpretation_preserved": proposal.historical_interpretation_preserved,
                "scope_posture": proposal.scope_posture,
                "authority_posture": proposal.authority_posture,
                "isolation_posture": proposal.isolation_posture,
                "affected_memory_count": proposal.affected_memory_count,
                "dependent_refs": list(proposal.dependent_refs),
                "incompatible_dependency_refs": list(proposal.incompatible_dependency_refs),
                "live_dependency_refs": list(proposal.live_dependency_refs),
                "reversibility": proposal.reversibility,
                "rollback_ref": proposal.rollback_ref or None,
                "rebuild_obligations": list(proposal.rebuild_obligations),
                "residue_obligations": list(proposal.residue_obligations),
            },
            "snapshot": {
                "state_digest": proposal.state_digest,
                "dependency_digest": proposal.dependency_digest,
            },
            "evidence": {
                "evidence_refs": list(proposal.evidence_refs),
                "estimator_refs": list(proposal.estimator_refs),
                "estimator_versions": list(proposal.estimator_versions),
                "confidence": proposal.confidence,
            },
            "classifier": {
                "classifier_id": structural_policy.classifier_id,
                "classifier_version": structural_policy.classifier_version,
                "policy_id": structural_policy.policy_id,
                "policy_version": structural_policy.policy_version,
                "s1_allowed_scopes": list(structural_policy.s1_allowed_scopes),
                "s1_max_affected_memories": structural_policy.s1_max_affected_memories,
            },
            "classification": {
                "structural_class": classification.structural_class,
                "autonomous_eligible": classification.autonomous_eligible,
                "required_authority": classification.required_authority,
                "reasons": list(classification.reasons),
            },
            "authority_effect": "none",
        }
        receipts.validate("structural-mutation-impact.schema.json", value)
        return value


@dataclass(frozen=True)
class SchemaLifecycle:
    proposal_id: str
    current_schema: SchemaRef
    proposed_schema: SchemaRef
    impact_digest: str
    state_digest: str
    dependency_digest: str
    structural_class: str
    lifecycle_state: str = PROPOSED
    authorization_ref: str = ""
    approval_refs: tuple[str, ...] = ()
    rollback_ref: str = ""
    rollback_execution_ref: str = ""
    live_dependency_refs: tuple[str, ...] = ()
    pending_residue_refs: tuple[str, ...] = ()


_ALLOWED_LAYERS = {"derived", "domain", "canonical"}
_ALLOWED_CHANGE_KINDS = {"rebuild_only", "additive_extension", "semantic_change", "destructive_retirement"}
_ALLOWED_INFORMATION_LOSS = {"none", "possible", "certain", "unknown"}
_ALLOWED_SCOPE = {"unchanged", "narrowed", "widened", "unknown"}
_ALLOWED_AUTHORITY = {"unchanged", "widened", "governance_bearing", "unknown"}
_ALLOWED_ISOLATION = {"preserved", "changed", "unknown"}
_ALLOWED_REVERSIBILITY = {"reversible", "versioned_revocable", "compensatable", "irreversible", "unknown"}


def _validate_digest(value: str, name: str) -> None:
    if not value.startswith("sha256:") or len(value) != 71:
        raise StructuralMutationError(f"{name} must be a sha256:<64 lowercase hex> digest")
    try:
        int(value.removeprefix("sha256:"), 16)
    except ValueError as exc:
        raise StructuralMutationError(f"{name} must be a sha256:<64 lowercase hex> digest") from exc
    if value != value.lower():
        raise StructuralMutationError(f"{name} must be lowercase")


def _validate_proposal(proposal: StructuralProposal) -> None:
    if proposal.layer not in _ALLOWED_LAYERS:
        raise StructuralMutationError(f"unsupported structural layer {proposal.layer!r}")
    if proposal.change_kind not in _ALLOWED_CHANGE_KINDS:
        raise StructuralMutationError(f"unsupported structural change kind {proposal.change_kind!r}")
    if not proposal.semantic_diff:
        raise StructuralMutationError("structural proposal requires an explicit semantic diff")
    if not proposal.isolation_domain_refs:
        raise StructuralMutationError("structural proposal requires explicit isolation-domain bindings")
    if proposal.information_loss not in _ALLOWED_INFORMATION_LOSS:
        raise StructuralMutationError(f"unsupported information-loss posture {proposal.information_loss!r}")
    if proposal.scope_posture not in _ALLOWED_SCOPE:
        raise StructuralMutationError(f"unsupported scope posture {proposal.scope_posture!r}")
    if proposal.authority_posture not in _ALLOWED_AUTHORITY:
        raise StructuralMutationError(f"unsupported authority posture {proposal.authority_posture!r}")
    if proposal.isolation_posture not in _ALLOWED_ISOLATION:
        raise StructuralMutationError(f"unsupported isolation posture {proposal.isolation_posture!r}")
    if proposal.reversibility not in _ALLOWED_REVERSIBILITY:
        raise StructuralMutationError(f"unsupported reversibility {proposal.reversibility!r}")
    if proposal.affected_memory_count < 0:
        raise StructuralMutationError("affected_memory_count cannot be negative")
    if not proposal.evidence_refs:
        raise StructuralMutationError("structural classification requires at least one evidence reference")
    if proposal.confidence is not None and not 0 <= proposal.confidence <= 1:
        raise StructuralMutationError("confidence must be between 0 and 1")
    _validate_digest(proposal.state_digest, "state_digest")
    _validate_digest(proposal.dependency_digest, "dependency_digest")


def _s3_reasons(proposal: StructuralProposal) -> list[str]:
    reasons: list[str] = []
    if proposal.scope_posture in {"widened", "unknown"}:
        reasons.append(f"scope posture is {proposal.scope_posture}")
    if proposal.authority_posture in {"widened", "governance_bearing", "unknown"}:
        reasons.append(f"authority posture is {proposal.authority_posture}")
    if proposal.isolation_posture in {"changed", "unknown"}:
        reasons.append(f"isolation posture is {proposal.isolation_posture}")
    if proposal.reversibility == "irreversible":
        reasons.append("change is irreversible")
    if proposal.information_loss == "certain":
        reasons.append("information loss is certain")
    if proposal.change_kind == "destructive_retirement" and proposal.live_dependency_refs:
        reasons.append("destructive retirement has live dependencies")
    if proposal.layer == "canonical" and proposal.change_kind == "destructive_retirement":
        reasons.append("destructive canonical retirement")
    return reasons


def _s2_reasons(proposal: StructuralProposal) -> list[str]:
    reasons: list[str] = []
    if proposal.layer == "canonical":
        reasons.append("canonical semantic layer changes require review")
    if proposal.change_kind == "semantic_change":
        reasons.append("existing semantics change")
    if proposal.migration_required:
        reasons.append("durable migration is required")
    if not proposal.preserves_semantics:
        reasons.append("semantic preservation is not proven")
    if not proposal.historical_interpretation_preserved:
        reasons.append("historical interpretation is not preserved")
    if proposal.information_loss in {"possible", "unknown"}:
        reasons.append(f"information loss is {proposal.information_loss}")
    if proposal.reversibility == "unknown":
        reasons.append("reversibility is unknown")
    if proposal.incompatible_dependency_refs:
        reasons.append("incompatible dependencies exist")
    if proposal.change_kind == "destructive_retirement":
        reasons.append("retirement is destructive")
    return reasons


def _s0_eligible(proposal: StructuralProposal) -> bool:
    return (
        proposal.layer == "derived"
        and proposal.change_kind == "rebuild_only"
        and proposal.preserves_semantics
        and not proposal.migration_required
        and proposal.information_loss == "none"
        and proposal.historical_interpretation_preserved
        and proposal.scope_posture in {"unchanged", "narrowed"}
        and proposal.authority_posture == "unchanged"
        and proposal.isolation_posture == "preserved"
        and not proposal.incompatible_dependency_refs
        and proposal.reversibility in {"reversible", "versioned_revocable", "compensatable"}
    )


def _s1_eligible(proposal: StructuralProposal, structural_policy: StructuralPolicy) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if proposal.layer != "domain":
        reasons.append("S1 requires application/domain layer")
    if proposal.change_kind != "additive_extension" or not proposal.optional_additive:
        reasons.append("S1 requires a bounded optional additive extension")
    if not proposal.preserves_semantics or not proposal.historical_interpretation_preserved:
        reasons.append("S1 requires preserved existing and historical interpretation")
    if proposal.migration_required:
        reasons.append("S1 cannot require migration")
    if proposal.information_loss != "none":
        reasons.append("S1 cannot carry information-loss risk")
    if proposal.scope_posture not in {"unchanged", "narrowed"}:
        reasons.append("S1 cannot widen or leave scope unknown")
    if proposal.current_schema.scope not in structural_policy.s1_allowed_scopes:
        reasons.append("schema scope is outside the delegated S1 policy")
    if proposal.proposed_schema.scope != proposal.current_schema.scope:
        reasons.append("S1 autonomous extension must preserve the schema scope identity")
    if proposal.authority_posture != "unchanged":
        reasons.append("S1 cannot widen authority")
    if proposal.isolation_posture != "preserved":
        reasons.append("S1 must preserve isolation")
    if proposal.affected_memory_count > structural_policy.s1_max_affected_memories:
        reasons.append("affected-memory count exceeds the delegated S1 bound")
    if proposal.incompatible_dependency_refs:
        reasons.append("S1 cannot have incompatible dependencies")
    if proposal.reversibility not in {"reversible", "versioned_revocable"}:
        reasons.append("S1 requires reversible or versioned-revocable posture")
    if not proposal.rollback_ref:
        reasons.append("S1 requires an explicit rollback reference")
    return not reasons, reasons


def classify(
    proposal: StructuralProposal,
    *,
    structural_policy: StructuralPolicy = StructuralPolicy(),
) -> StructuralImpact:
    """Deterministically classify structural consequence without estimator authority."""
    _validate_proposal(proposal)

    s3 = _s3_reasons(proposal)
    if s3:
        classification = StructuralClassification(
            structural_class=S3,
            autonomous_eligible=False,
            required_authority="external_human_verification",
            reasons=tuple(s3),
        )
    else:
        s2 = _s2_reasons(proposal)
        if s2:
            classification = StructuralClassification(
                structural_class=S2,
                autonomous_eligible=False,
                required_authority="human_review",
                reasons=tuple(s2),
            )
        elif _s0_eligible(proposal):
            classification = StructuralClassification(
                structural_class=S0,
                autonomous_eligible=True,
                required_authority="deterministic_policy",
                reasons=("derived rebuild-only change preserves higher-layer semantics",),
            )
        else:
            s1_eligible, s1_reasons = _s1_eligible(proposal, structural_policy)
            if s1_eligible:
                classification = StructuralClassification(
                    structural_class=S1,
                    autonomous_eligible=True,
                    required_authority="deterministic_policy",
                    reasons=("bounded additive domain extension satisfies delegated S1 policy",),
                )
            else:
                classification = StructuralClassification(
                    structural_class=S2,
                    autonomous_eligible=False,
                    required_authority="human_review",
                    reasons=tuple(s1_reasons or ["change is not proven inside an S0/S1 autonomous envelope"]),
                )

    impact = StructuralImpact(proposal=proposal, classification=classification, structural_policy=structural_policy)
    impact.to_dict()
    return impact


def assert_snapshot_current(
    impact: StructuralImpact,
    *,
    current_state_digest: str,
    current_dependency_digest: str,
) -> None:
    """Reject authorization when impact analysis no longer describes current state."""
    _validate_digest(current_state_digest, "current_state_digest")
    _validate_digest(current_dependency_digest, "current_dependency_digest")
    if impact.proposal.state_digest != current_state_digest:
        raise StructuralMutationError("stale structural impact: state snapshot digest changed")
    if impact.proposal.dependency_digest != current_dependency_digest:
        raise StructuralMutationError("stale structural impact: dependency snapshot digest changed")


def evaluate_pama_v13(
    pama_proposal: policy.Proposal,
    impact: StructuralImpact,
    *,
    current_state_digest: str,
    current_dependency_digest: str,
    external_verification: "policy.ExternalVerification | None" = None,
    evidence=None,
    verifier_registry=None,
) -> policy.Decision:
    """Evaluate PAMA 1.3 structural delegation without weakening existing floors.

    ADR-037 step 4b-2, DoD 20: `evidence` forwards the qualified-evidence
    channel, so a structural mutation that resolves to `require_review` has a
    reachable route rather than a dead end. Verifier trust is the evaluator's
    typed registry, not a caller-supplied mapping.
    """
    if pama_proposal.operation != "domain_schema_mutation":
        raise StructuralMutationError("structural PAMA evaluator requires domain_schema_mutation")
    if pama_proposal.proposal_id != impact.proposal.proposal_id:
        raise StructuralMutationError("PAMA proposal and structural impact proposal ids differ")
    assert_snapshot_current(
        impact,
        current_state_digest=current_state_digest,
        current_dependency_digest=current_dependency_digest,
    )

    structural_class = impact.classification.structural_class
    if structural_class == S0:
        raise StructuralMutationError(
            "S0 derived rebuild-only work is not a domain_schema_mutation; use the maintenance path"
        )

    if structural_class == S1 and impact.classification.autonomous_eligible:
        base = policy.ALLOW_WITH_LEDGER
        allow_review_discharge = False
    elif structural_class == S3:
        base = policy.REQUIRE_EXTERNAL_VERIFICATION
        allow_review_discharge = True
    else:
        base = policy.REQUIRE_EXTERNAL_VERIFICATION if pama_proposal.risk_class in {"high", "critical"} else policy.REQUIRE_REVIEW
        allow_review_discharge = True

    if external_verification is not None:
        # GAP-ARCH-04 (LD6). This path passes base_outcome=REQUIRE_EXTERNAL_
        # VERIFICATION for high/critical risk, so the LD1 cap applies here too.
        # Before this cycle no test reached the discharge, so the behaviour
        # change would have been invisible to a green suite.
        decision = policy.evaluate_with_external_verification(
            pama_proposal, external_verification, base_outcome=base
        )
    elif evidence:
        from ..core.evidence_qualification import group_by_dependence

        decision = policy.evaluate_with_qualified_evidence(
            pama_proposal,
            group_by_dependence(
                evidence,
                verifiers=(verifier_registry.as_mapping() if verifier_registry else None),
            ),
            base_outcome=base,
        )
    else:
        decision = policy.evaluate_with_base_outcome(
            pama_proposal,
            base_outcome=base,
            allow_review_discharge=allow_review_discharge,
        )
    return replace(
        decision,
        reasons=decision.reasons
        + (
            f"ADR-032 structural class {structural_class}",
            f"structural classifier {impact.structural_policy.classifier_id}@{impact.structural_policy.classifier_version}",
            f"structural policy {impact.structural_policy.policy_id}@{impact.structural_policy.policy_version}",
        ),
    )


def authorize_lifecycle(
    impact: StructuralImpact,
    decision: policy.Decision,
    *,
    current_state_digest: str,
    current_dependency_digest: str,
    decision_ref: str,
    approval_refs: Iterable[str] = (),
) -> SchemaLifecycle:
    assert_snapshot_current(
        impact,
        current_state_digest=current_state_digest,
        current_dependency_digest=current_dependency_digest,
    )
    approvals = tuple(approval_refs)
    structural_class = impact.classification.structural_class
    if decision.outcome not in {policy.ALLOW, policy.ALLOW_WITH_LEDGER}:
        raise StructuralMutationError("structural mutation has not been authorized by PAMA")
    if structural_class in {S2, S3} and not approvals:
        raise StructuralMutationError("S2/S3 activation requires an explicit external approval reference")
    if structural_class == S1 and not impact.classification.autonomous_eligible and not approvals:
        raise StructuralMutationError("non-delegable S1 mutation requires explicit approval")
    return SchemaLifecycle(
        proposal_id=impact.proposal.proposal_id,
        current_schema=impact.proposal.current_schema,
        proposed_schema=impact.proposal.proposed_schema,
        impact_digest=impact.impact_digest,
        state_digest=current_state_digest,
        dependency_digest=current_dependency_digest,
        structural_class=structural_class,
        lifecycle_state=AUTHORIZED,
        authorization_ref=decision_ref,
        approval_refs=approvals,
        rollback_ref=impact.proposal.rollback_ref,
        live_dependency_refs=impact.proposal.live_dependency_refs,
        pending_residue_refs=impact.proposal.residue_obligations,
    )


def activate(lifecycle: SchemaLifecycle) -> SchemaLifecycle:
    if lifecycle.lifecycle_state != AUTHORIZED:
        raise StructuralMutationError("schema can activate only from authorized state")
    return replace(lifecycle, lifecycle_state=ACTIVE)


def rollback(
    lifecycle: SchemaLifecycle,
    *,
    rollback_ref: str,
    execution_ref: str,
) -> SchemaLifecycle:
    """Represent governed rollback of an authorized/active successor.

    The successor becomes superseded; restoring provider-specific physical state
    remains outside this reference authority/lifecycle model.
    """
    if lifecycle.lifecycle_state not in {AUTHORIZED, ACTIVE}:
        raise StructuralMutationError("schema rollback is only valid before or during active successor state")
    if not lifecycle.rollback_ref:
        raise StructuralMutationError("schema lifecycle has no declared rollback reference")
    if rollback_ref != lifecycle.rollback_ref:
        raise StructuralMutationError("rollback reference does not match the authorized structural proposal")
    if not execution_ref:
        raise StructuralMutationError("rollback requires an execution evidence reference")
    return replace(
        lifecycle,
        lifecycle_state=SUPERSEDED,
        rollback_execution_ref=execution_ref,
    )


def supersede(lifecycle: SchemaLifecycle) -> SchemaLifecycle:
    if lifecycle.lifecycle_state != ACTIVE:
        raise StructuralMutationError("schema can be superseded only from active state")
    return replace(lifecycle, lifecycle_state=SUPERSEDED)


def retire(
    lifecycle: SchemaLifecycle,
    *,
    live_dependency_refs: Iterable[str] = (),
    pending_residue_refs: Iterable[str] = (),
) -> SchemaLifecycle:
    if lifecycle.lifecycle_state != SUPERSEDED:
        raise StructuralMutationError("schema can retire only after supersession")
    live = tuple(live_dependency_refs)
    residue = tuple(pending_residue_refs)
    if live:
        raise StructuralMutationError(f"schema retirement blocked by live dependencies: {list(live)}")
    if residue:
        raise StructuralMutationError(f"schema retirement blocked by residue obligations: {list(residue)}")
    return replace(
        lifecycle,
        lifecycle_state=RETIRED,
        live_dependency_refs=(),
        pending_residue_refs=(),
    )
