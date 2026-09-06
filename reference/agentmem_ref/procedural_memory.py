"""Governed procedural/skill memory reference vertical slice.

This module proves the ADR-034 boundary without inventing a specialized skill
store. A skill is serialized as bounded JSON metadata plus human-readable
Markdown, committed through the existing GovernedMemoryAdapter, recalled through
its admission path, and allowed to influence a plan only after skill-specific
currentness/applicability checks.

Crucially:

    retained skill != activated skill != authorized action != execution

The reference action gate records that separation but performs no real external
side effect. Runtime/Agent-Governance systems remain authoritative for actions.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from typing import Iterable

from . import policy
from .adapter import CommitResult, GovernedMemoryAdapter, RecallContext
from .capabilities import (
    CapabilityDeclaration,
    CapabilityRequirement,
    ComponentDeclaration,
    ComponentRegistry,
    ResolvedCapability,
)
from .substrate import TemporalGraphPort

PROCEDURAL_CAPABILITY = "procedural_skill_memory"
PROCEDURAL_CAPABILITY_VERSION = "1.0"
PROCEDURAL_MINIMUM_MATURITY = "runtime_wired"
SKILL_FORMAT = "agent-memory-skill/v1"
SKILL_HEADER = f"--- {SKILL_FORMAT}\n"
SKILL_SEPARATOR = "\n--- procedure\n"
PLAN_INFLUENCE_ONLY = "plan_influence_only"
TASK_PROCEDURE = "task_procedure"
METAMEMORY = "metamemory"


@dataclass(frozen=True)
class SkillArtifact:
    skill_id: str
    version: int
    purpose: str
    scope: str
    isolation_domain_refs: tuple[str, ...]
    required_isolation_domain_refs: tuple[str, ...]
    procedure_markdown: str
    provenance_refs: tuple[str, ...]
    validation_refs: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    action_templates: tuple[str, ...] = ()
    activation_posture: str = PLAN_INFLUENCE_ONLY
    skill_kind: str = TASK_PROCEDURE
    management_effects: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.skill_id or self.version < 1:
            raise ValueError("skill identity and positive version are required")
        if not self.procedure_markdown.strip():
            raise ValueError("procedure Markdown is required")
        if not self.scope or not self.isolation_domain_refs:
            raise ValueError("procedural memory requires explicit scope and isolation domain")
        if not set(self.required_isolation_domain_refs).issubset(set(self.isolation_domain_refs)):
            raise ValueError("required isolation domains must be included in bound isolation domains")
        if self.skill_kind not in {TASK_PROCEDURE, METAMEMORY}:
            raise ValueError(f"unsupported skill_kind: {self.skill_kind}")
        if self.skill_kind == METAMEMORY and not self.management_effects:
            raise ValueError("metamemory artifacts must declare management_effects")

    @property
    def memory_reference(self) -> str:
        return f"skill:{self.skill_id}"

    @property
    def version_reference(self) -> str:
        return f"{self.memory_reference}@v{self.version}"

    def _payload(self) -> dict:
        return {
            "format": SKILL_FORMAT,
            "skill_id": self.skill_id,
            "version": self.version,
            "purpose": self.purpose,
            "scope": self.scope,
            "isolation_domain_refs": list(self.isolation_domain_refs),
            "required_isolation_domain_refs": list(self.required_isolation_domain_refs),
            "procedure_markdown": self.procedure_markdown.strip(),
            "provenance_refs": list(self.provenance_refs),
            "validation_refs": list(self.validation_refs),
            "constraints": list(self.constraints),
            "action_templates": list(self.action_templates),
            "activation_posture": self.activation_posture,
            "skill_kind": self.skill_kind,
            "management_effects": list(self.management_effects),
        }

    @property
    def content_sha256(self) -> str:
        canonical = json.dumps(self._payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def serialize(self) -> str:
        payload = self._payload()
        procedure = payload.pop("procedure_markdown")
        payload["content_sha256"] = self.content_sha256
        metadata = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return f"{SKILL_HEADER}{metadata}{SKILL_SEPARATOR}{procedure}"

    @classmethod
    def from_text(cls, text: str) -> "SkillArtifact":
        if not text.startswith(SKILL_HEADER) or SKILL_SEPARATOR not in text:
            raise ValueError("not an Agent Memory procedural skill artifact")
        metadata_text, procedure = text[len(SKILL_HEADER) :].split(SKILL_SEPARATOR, 1)
        metadata = json.loads(metadata_text)
        expected_digest = str(metadata.pop("content_sha256"))
        if metadata.pop("format", None) != SKILL_FORMAT:
            raise ValueError("unsupported procedural skill format")
        artifact = cls(
            skill_id=str(metadata["skill_id"]),
            version=int(metadata["version"]),
            purpose=str(metadata["purpose"]),
            scope=str(metadata["scope"]),
            isolation_domain_refs=tuple(str(item) for item in metadata["isolation_domain_refs"]),
            required_isolation_domain_refs=tuple(
                str(item) for item in metadata.get("required_isolation_domain_refs", ())
            ),
            procedure_markdown=procedure.strip(),
            provenance_refs=tuple(str(item) for item in metadata.get("provenance_refs", ())),
            validation_refs=tuple(str(item) for item in metadata.get("validation_refs", ())),
            constraints=tuple(str(item) for item in metadata.get("constraints", ())),
            action_templates=tuple(str(item) for item in metadata.get("action_templates", ())),
            activation_posture=str(metadata.get("activation_posture", PLAN_INFLUENCE_ONLY)),
            skill_kind=str(metadata.get("skill_kind", TASK_PROCEDURE)),
            management_effects=tuple(str(item) for item in metadata.get("management_effects", ())),
        )
        if artifact.content_sha256 != expected_digest:
            raise ValueError("procedural skill content digest mismatch")
        return artifact


@dataclass(frozen=True)
class SkillApproval:
    """Exact approval binding for a review-required procedural mutation."""

    approval_ref: str
    proposal_id: str
    skill_version_ref: str
    content_sha256: str
    state_snapshot: str

    def to_dict(self) -> dict:
        return {
            "approval_ref": self.approval_ref,
            "proposal_id": self.proposal_id,
            "skill_version_ref": self.skill_version_ref,
            "content_sha256": self.content_sha256,
            "state_snapshot": self.state_snapshot,
        }


@dataclass(frozen=True)
class SkillProposal:
    artifact: SkillArtifact
    proposal: policy.Proposal
    content_sha256: str
    approval: SkillApproval | None = None


@dataclass(frozen=True)
class SkillCommitResult:
    artifact: SkillArtifact
    resolution: ResolvedCapability
    commit: CommitResult


@dataclass(frozen=True)
class SkillActivationResult:
    query: str
    purpose: str
    resolution: ResolvedCapability
    candidate_fact_uuids: tuple[str, ...]
    memory_admitted_fact_uuids: tuple[str, ...]
    activated_skills: tuple[SkillArtifact, ...]
    refusals: dict[str, str]
    evidence: dict


@dataclass(frozen=True)
class ActionProposal:
    action_id: str
    description: str
    skill_version_ref: str
    requires_governance: bool = True
    governance_decision_ref: str = ""
    execution_status: str = "not_executed"
    execution_ref: str = ""


@dataclass(frozen=True)
class ActionGovernanceDecision:
    decision_ref: str
    action_id: str
    outcome: str

    def __post_init__(self) -> None:
        if self.outcome not in {"allow", "deny"}:
            raise ValueError("action governance outcome must be allow or deny")


@dataclass(frozen=True)
class PlanResult:
    goal: str
    steps: tuple[str, ...]
    activated_skill_refs: tuple[str, ...]
    action_proposals: tuple[ActionProposal, ...]
    execution_status: str = "not_executed"


@dataclass(frozen=True)
class RevocationResult:
    skill_id: str
    fact_uuid: str
    commit: CommitResult
    active_influence_removed: bool
    physical_content_retained: bool
    undeclared_residue: tuple[str, ...]


class ProceduralMemoryRuntime:
    """Narrow reference runtime for one governed procedural-memory capability."""

    def __init__(
        self,
        *,
        substrate: TemporalGraphPort,
        adapter: GovernedMemoryAdapter,
        registry: ComponentRegistry,
    ) -> None:
        self.substrate = substrate
        self.adapter = adapter
        self.registry = registry

    def resolve_capability(self) -> ResolvedCapability:
        return self.registry.resolve(
            CapabilityRequirement(
                capability_id=PROCEDURAL_CAPABILITY,
                minimum_maturity=PROCEDURAL_MINIMUM_MATURITY,
                required_scope_postures=("enforces_agent_memory_scope",),
            )
        )

    def propose_skill(
        self,
        artifact: SkillArtifact,
        *,
        actor_id: str,
        proposal_id: str | None = None,
    ) -> SkillProposal:
        current_version = self.adapter.state_version(artifact.memory_reference)
        if artifact.version != current_version + 1:
            raise ValueError(
                f"skill version must advance current state exactly once: current=v{current_version}, "
                f"proposed=v{artifact.version}"
            )
        operation = "promotion" if current_version == 0 else "correction"
        digest_ref = f"skill-content:{artifact.content_sha256}"
        evidence_refs = _unique(artifact.provenance_refs + artifact.validation_refs + (digest_ref,))
        proposal = policy.Proposal(
            proposal_id=proposal_id or f"proposal:{artifact.version_reference}",
            actor_id=actor_id,
            charter_version="procedural-memory-v1",
            target_reference=artifact.memory_reference,
            target_class=policy.M3,
            scope=artifact.scope,
            operation=operation,
            current_strength="reinforced" if current_version == 0 else "promoted",
            proposed_strength="promoted",
            downstream_authority=policy.A2,
            reversibility="reversible",
            risk_class="low" if operation == "promotion" else "medium",
            evidence_refs=evidence_refs,
            state_snapshot=f"v{current_version}",
            tenant_ref=artifact.scope,
            purpose=artifact.purpose,
            isolation_domain_refs=artifact.isolation_domain_refs,
            required_isolation_domain_refs=artifact.required_isolation_domain_refs,
            project_ref=_project_ref(artifact.isolation_domain_refs),
        )
        return SkillProposal(
            artifact=artifact,
            proposal=proposal,
            content_sha256=artifact.content_sha256,
        )

    def approve_skill_proposal(self, skill_proposal: SkillProposal, *, approval_ref: str) -> SkillProposal:
        """Bind a human/external approval to one exact skill payload and state."""
        if not approval_ref:
            raise ValueError("approval reference is required")
        self._validate_skill_proposal_binding(skill_proposal, require_approval=False)
        approval = SkillApproval(
            approval_ref=approval_ref,
            proposal_id=skill_proposal.proposal.proposal_id,
            skill_version_ref=skill_proposal.artifact.version_reference,
            content_sha256=skill_proposal.content_sha256,
            state_snapshot=skill_proposal.proposal.state_snapshot,
        )
        approved_proposal = replace(
            skill_proposal.proposal,
            approval_refs=(approval_ref,),
            review_satisfied=True,
        )
        return replace(skill_proposal, proposal=approved_proposal, approval=approval)

    def commit_skill(self, skill_proposal: SkillProposal, *, evidence=None) -> SkillCommitResult:
        resolution = self.resolve_capability()
        self._validate_skill_proposal_binding(skill_proposal, require_approval=None)
        serialized = skill_proposal.artifact.serialize()
        SkillArtifact.from_text(serialized)
        # ADR-037 step 4b-2 (entry #24). Evidence is deliberately NOT attached
        # here, and the reason is worth keeping.
        #
        # 4b-1 established that this module can produce genuine artifact-bound
        # evidence: `content_sha256` with `payload_verifier` re-deriving it. That
        # evidence establishes **payload integrity** -- this artifact is what it
        # claims to be.
        #
        # It does not establish the proposition a *correction* puts under review,
        # which is that v2 should supersede v1. Attaching it here made an
        # unapproved v2 commit, which is the same circularity the operator
        # rejected in the change-record pattern: the artifact describing itself
        # is not an argument for adopting it.
        #
        # `validation_refs` would be the semantically relevant material, but it
        # is a bare tuple of strings -- `unqualified` under R3, with no digest
        # and no verifier. So a skill correction parks until a genuine
        # adjudication exists. The caller receives the criteria report.
        #
        # `evidence` is forwarded (DoD 20) so an evaluator that DOES hold a
        # relevant adjudication -- a skill-version-advance policy, say -- can
        # supply it. This module does not author one.
        result = self.adapter.commit_proposal(
            skill_proposal.proposal, serialized, evidence=evidence
        )
        if result.committed and self.adapter.state_version(skill_proposal.artifact.memory_reference) != skill_proposal.artifact.version:
            raise RuntimeError("committed procedural skill version diverged from governed state version")
        return SkillCommitResult(skill_proposal.artifact, resolution, result)

    def _validate_skill_proposal_binding(
        self,
        skill_proposal: SkillProposal,
        *,
        require_approval: bool | None,
    ) -> None:
        artifact_digest = skill_proposal.artifact.content_sha256
        if artifact_digest != skill_proposal.content_sha256:
            raise ValueError("skill_proposal_content_mismatch")
        digest_ref = f"skill-content:{artifact_digest}"
        if digest_ref not in skill_proposal.proposal.evidence_refs:
            raise ValueError("skill_proposal_digest_not_bound_to_pama_evidence")
        if skill_proposal.proposal.target_reference != skill_proposal.artifact.memory_reference:
            raise ValueError("skill_proposal_target_mismatch")

        approval_present = bool(
            skill_proposal.approval
            or skill_proposal.proposal.approval_refs
            or skill_proposal.proposal.review_satisfied
        )
        if require_approval is True and not approval_present:
            raise ValueError("skill_approval_required")
        if require_approval is False and approval_present:
            raise ValueError("unexpected_skill_approval")
        if not approval_present:
            return

        approval = skill_proposal.approval
        if approval is None:
            raise ValueError("skill_approval_binding_missing")
        if not skill_proposal.proposal.review_satisfied:
            raise ValueError("skill_approval_review_not_satisfied")
        if tuple(skill_proposal.proposal.approval_refs) != (approval.approval_ref,):
            raise ValueError("skill_approval_reference_mismatch")
        if approval.proposal_id != skill_proposal.proposal.proposal_id:
            raise ValueError("skill_approval_proposal_mismatch")
        if approval.skill_version_ref != skill_proposal.artifact.version_reference:
            raise ValueError("skill_approval_version_mismatch")
        if approval.content_sha256 != artifact_digest:
            raise ValueError("skill_approval_content_mismatch")
        if approval.state_snapshot != skill_proposal.proposal.state_snapshot:
            raise ValueError("skill_approval_state_mismatch")

    def recall_and_activate(
        self,
        query: str,
        *,
        context: RecallContext,
        purpose: str,
    ) -> SkillActivationResult:
        resolution = self.resolve_capability()
        admission = self.adapter.governed_recall(query, context)
        refusals = dict(admission.refusals)
        activated: list[SkillArtifact] = []
        memory_admitted: list[str] = []

        for fact_uuid in admission.candidates:
            fact = self.substrate.get_fact(fact_uuid)
            if fact is None:
                refusals[fact_uuid] = "candidate_missing"
                continue
            try:
                artifact = SkillArtifact.from_text(fact.fact_text)
            except (ValueError, KeyError, TypeError, json.JSONDecodeError):
                refusals.setdefault(fact_uuid, "not_valid_procedural_skill")
                continue

            if fact_uuid not in admission.admitted:
                continue
            memory_admitted.append(fact_uuid)

            if artifact.purpose and artifact.purpose != purpose:
                refusals[fact_uuid] = "purpose_mismatch"
                continue
            if artifact.activation_posture != PLAN_INFLUENCE_ONLY:
                refusals[fact_uuid] = "activation_posture_not_supported"
                continue
            if artifact.skill_kind == METAMEMORY or artifact.management_effects:
                refusals[fact_uuid] = "metamemory_requires_configuration_governance"
                continue
            activated.append(artifact)

        evidence = {
            "capability_resolution": resolution.to_dict(),
            "candidate_fact_uuids": list(admission.candidates),
            "memory_admitted_fact_uuids": memory_admitted,
            "activated_skill_refs": [artifact.version_reference for artifact in activated],
            "refusals": dict(sorted(refusals.items())),
            "authority_effect": "plan_context_influence_only",
            "execution_status": "not_executed",
        }
        return SkillActivationResult(
            query=query,
            purpose=purpose,
            resolution=resolution,
            candidate_fact_uuids=tuple(admission.candidates),
            memory_admitted_fact_uuids=tuple(memory_admitted),
            activated_skills=tuple(activated),
            refusals=refusals,
            evidence=evidence,
        )

    def build_plan(self, goal: str, activation: SkillActivationResult) -> PlanResult:
        steps: list[str] = [f"Inspect current state for: {goal}"]
        actions: list[ActionProposal] = []
        active_refs: list[str] = []
        for artifact in activation.activated_skills:
            active_refs.append(artifact.version_reference)
            steps.append(f"Apply admitted procedure {artifact.version_reference}")
            steps.extend(_procedure_steps(artifact.procedure_markdown))
            for index, description in enumerate(artifact.action_templates, start=1):
                action_id = _stable_id("action", artifact.version_reference, str(index), description)
                actions.append(
                    ActionProposal(
                        action_id=action_id,
                        description=description,
                        skill_version_ref=artifact.version_reference,
                    )
                )
        return PlanResult(
            goal=goal,
            steps=tuple(steps),
            activated_skill_refs=tuple(active_refs),
            action_proposals=tuple(actions),
        )

    def revoke_skill(
        self,
        skill_id: str,
        *,
        actor_id: str,
        evidence_refs: tuple[str, ...],
        proposal_id: str | None = None,
    ) -> RevocationResult:
        self.resolve_capability()
        memory_ref = f"skill:{skill_id}"
        fact_uuid = self.adapter.current_fact_uuid(memory_ref)
        if not fact_uuid:
            raise ValueError(f"no current procedural skill exists for {skill_id!r}")
        current_version = self.adapter.state_version(memory_ref)
        proposal = policy.Proposal(
            proposal_id=proposal_id or f"proposal:revoke:{skill_id}:v{current_version}",
            actor_id=actor_id,
            charter_version="procedural-memory-v1",
            target_reference=memory_ref,
            target_class=policy.M3,
            scope="procedural-memory",
            operation="pruning",
            current_strength="promoted",
            proposed_strength="archived",
            downstream_authority=policy.A1,
            reversibility="reversible",
            risk_class="low",
            evidence_refs=evidence_refs,
            state_snapshot=f"v{current_version}",
        )
        result = self.adapter.governed_delete(proposal, fact_uuid)
        residue = tuple(self.adapter.undeclared_residue(fact_uuid))
        return RevocationResult(
            skill_id=skill_id,
            fact_uuid=fact_uuid,
            commit=result,
            active_influence_removed=result.committed,
            physical_content_retained=self.substrate.get_fact(fact_uuid) is not None,
            undeclared_residue=residue,
        )

    def propose_management_change(
        self,
        artifact: SkillArtifact,
        *,
        actor_id: str,
        proposal_id: str | None = None,
    ) -> policy.Proposal:
        if artifact.skill_kind != METAMEMORY or not artifact.management_effects:
            raise ValueError("management change proposals require a metamemory artifact")
        return policy.Proposal(
            proposal_id=proposal_id or f"proposal:metamemory:{artifact.version_reference}",
            actor_id=actor_id,
            charter_version="procedural-memory-v1",
            target_reference=f"memory-profile:{artifact.skill_id}",
            target_class=policy.M5,
            scope=artifact.scope,
            operation="policy_mutation",
            current_strength="reinforced",
            proposed_strength="promoted",
            downstream_authority=policy.A5,
            reversibility="reversible",
            risk_class="high",
            evidence_refs=_unique(artifact.provenance_refs + artifact.validation_refs),
            purpose="memory-management-profile-change",
            isolation_domain_refs=artifact.isolation_domain_refs,
            required_isolation_domain_refs=artifact.required_isolation_domain_refs,
        )


def reference_procedural_component() -> ComponentDeclaration:
    return ComponentDeclaration(
        component_id="agent-memory-reference-procedural",
        component_version="0.1.0",
        profile_version="component-capability-v1",
        failure_posture="fail_closed",
        runtime_ref="reference/agentmem_ref/procedural_memory.py",
        provenance_refs=("issue:#295", "adr:ADR-034"),
        capabilities=(
            CapabilityDeclaration(
                capability_id=PROCEDURAL_CAPABILITY,
                capability_version=PROCEDURAL_CAPABILITY_VERSION,
                maturity="runtime_wired",
                state_posture="canonical",
                scope_posture="enforces_agent_memory_scope",
                failure_posture="fail_closed",
                authority_effect="none",
                evidence_refs=("reference:test_procedural_memory",),
            ),
        ),
    )


def apply_action_governance(action: ActionProposal, decision: ActionGovernanceDecision) -> ActionProposal:
    """Apply a separate governance decision to a proposed runtime action.

    This is intentionally not a skill-memory method. A skill cannot manufacture
    this decision; the caller must supply it from the Runtime/Governance path.
    """
    if decision.action_id != action.action_id:
        raise ValueError("governance decision does not bind the proposed action")
    if decision.outcome == "deny":
        return replace(
            action,
            governance_decision_ref=decision.decision_ref,
            execution_status="blocked_by_governance",
        )
    return replace(
        action,
        governance_decision_ref=decision.decision_ref,
        execution_status="authorized_not_executed",
    )


def record_runtime_execution(action: ActionProposal, execution_ref: str) -> ActionProposal:
    """Record execution evidence only after a separate allow decision exists."""
    if action.execution_status != "authorized_not_executed" or not action.governance_decision_ref:
        raise ValueError("runtime execution requires a bound external governance allow decision")
    if not execution_ref:
        raise ValueError("runtime execution evidence reference is required")
    return replace(action, execution_status="executed_by_runtime", execution_ref=execution_ref)


def _procedure_steps(markdown: str) -> tuple[str, ...]:
    bullets = tuple(line.strip()[2:].strip() for line in markdown.splitlines() if line.strip().startswith("- "))
    if bullets:
        return bullets
    return (markdown.strip(),)


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _project_ref(domain_refs: tuple[str, ...]) -> str:
    for value in domain_refs:
        if value.startswith("project:"):
            return value
    return ""


#: Name a proposal may cite. Naming is not holding: an evaluator that has not
#: registered this leaves the item `asserted` (step 2).
PAYLOAD_VERIFIER = "procedural-memory:skill-payload-sha256"


def evidence_for(artifact: "SkillArtifact") -> tuple:
    """Evidence for a skill artifact, built from material already held.

    ADR-037 step 4b-1. Nothing here is minted to satisfy the classifier:
    `content_sha256` and `version_reference` predate this cycle, and the digest
    is recomputed from the payload on every access.

    A module-level function taking the artifact, because that is all it needs --
    the same shape as `reusable_grants.evidence_for` and
    `dashclaw_external_verdict.evidence_for`. It *produces*; it does not
    certify. There is no discharge here and no verifier registry -- see
    `payload_verifier`, which the evaluator may register or decline (R1:
    producing evidence and certifying it are different acts).
    """
    from .evidence_qualification import EvidenceItem

    return (
        EvidenceItem(
            ref=artifact.version_reference,
            artifact_ref=artifact.version_reference,
            digest=artifact.content_sha256,
            verifier=PAYLOAD_VERIFIER,
            failure_domain="procedural-memory-skill-payload",
        ),
    )


def payload_verifier(artifact: "SkillArtifact"):
    """A real verifier the evaluator may register, bound to one artifact.

    Recomputes `content_sha256` from the payload and compares it to the digest
    the evidence item carries -- the same comparison this module already makes
    at `_verify_skill_binding`. Supplying the implementation is not holding the
    registry: the evaluator still decides whether to trust it, and an
    unregistered verifier leaves the item `asserted`.

    Returns False for a tampered payload, so the item classifies `refuted`
    rather than merely unverified.
    """

    def verify(item) -> bool:
        return bool(item.digest) and item.digest == artifact.content_sha256

    return verify
