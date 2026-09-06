"""Local reference evidence for governed cross-system memory interchange.

This module does not define a transport standard and does not import another
project's authority semantics. It exercises Agent Memory's own Profile 6 seam:

- sender export requires a committed governed boundary crossing;
- memory identity, provenance, lifecycle, sensitivity, ownership, and source
  domain scope survive export;
- sender authority travels as evidence, never as receiver permission;
- the receiver evaluates its own PAMA authority before admitting an import;
- ownership conflicts fail closed;
- successful imports bind a receiving isolation domain while retaining source
  domain provenance;
- later source correction/deletion notices remain evidence until receiver-local
  governance authorizes a local consequence.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

from ..core import policy, receipts

NOTICE_CORRECTION = "correction"
NOTICE_SUPERSESSION = "supersession"
NOTICE_REVOCATION = "revocation"
NOTICE_DELETION = "deletion"
NOTICE_KINDS = frozenset({NOTICE_CORRECTION, NOTICE_SUPERSESSION, NOTICE_REVOCATION, NOTICE_DELETION})


@dataclass(frozen=True)
class ExportBundle:
    sender_system: str
    receiver_system: str
    memory: dict
    crossing_receipt: dict
    sender_authority_evidence: tuple[str, ...]


@dataclass(frozen=True)
class InterchangeLink:
    memory_id: str
    source_system: str
    receiver_system: str
    source_crossing_receipt_ref: str
    source_domain_refs: tuple[str, ...]
    receiver_domain_ref: str


@dataclass(frozen=True)
class ImportResult:
    decision: policy.Decision
    admitted: bool
    memory: dict | None
    refusal: str | None = None
    link: InterchangeLink | None = None


@dataclass(frozen=True)
class SourceLifecycleNotice:
    notice_id: str
    source_system: str
    memory_id: str
    kind: str
    evidence_refs: tuple[str, ...]
    source_state: str = ""
    source_receipt_ref: str = ""


@dataclass(frozen=True)
class NoticeResult:
    decision: policy.Decision
    recognized: bool
    local_action: str
    refusal: str | None = None


def build_export_bundle(
    memory: dict,
    *,
    sender_system: str,
    receiver_system: str,
    crossing_receipt: dict,
) -> ExportBundle:
    """Build an export only from a schema-valid memory and committed crossing."""
    receipts.validate("memory-unit.schema.json", memory)
    receipts.validate("boundary-crossing-receipt.schema.json", crossing_receipt)

    if crossing_receipt.get("outcome") != "committed":
        raise ValueError("memory export requires a committed governed crossing")
    if memory["id"] not in crossing_receipt.get("source_refs", ()):
        raise ValueError("crossing receipt does not bind the exported memory")

    scope = memory.get("scope") or {}
    if not scope.get("owner_principal"):
        raise ValueError("cross-system export requires an explicit owner_principal")
    if not scope.get("isolation_domain_refs"):
        raise ValueError("cross-system export requires explicit source isolation domains")

    evidence = []
    for key in ("decision_receipt_ref", "ledger_ref"):
        value = crossing_receipt.get(key)
        if value:
            evidence.append(value)
    evidence.append(crossing_receipt["receipt_id"])

    return ExportBundle(
        sender_system=sender_system,
        receiver_system=receiver_system,
        memory=deepcopy(memory),
        crossing_receipt=deepcopy(crossing_receipt),
        sender_authority_evidence=tuple(evidence),
    )


def _evaluate(proposal, evidence, attestation, verifier_registry):
    """Route through the qualified path when evidence is supplied.

    ADR-037 step 4b-2. Same shape as `crossing._evaluate`.
    """
    if evidence:
        from ..core.evidence_qualification import group_by_dependence

        return policy.evaluate_with_qualified_evidence(
            proposal,
            group_by_dependence(
                evidence,
                verifiers=(verifier_registry.as_mapping() if verifier_registry else None),
            ),
            attestation=attestation,
        )
    return policy.evaluate(proposal)


def import_bundle(
    bundle: ExportBundle,
    *,
    receiver_domain_ref: str,
    receiver_proposal: policy.Proposal,
    expected_owner_principal: str | None = None,
    evidence=None,
    attestation: policy.ExternalVerification | None = None,
    verifier_registry=None,
) -> ImportResult:
    """Evaluate one import under receiver-local authority.

    SCOPE ADDITION, disclosed (ADR-037 step 4b-2, entry #24): `evidence`, with
    the same shape and reasoning as the adapter's and crossing's. Note that this
    is a case where the distinction matters especially: the sender's crossing
    receipt records the sender's authority, and reusing it as the receiver's
    evidence would be exactly the authority/evidence collapse the operator ruled
    against. The receiver supplies its own.

    The sender's crossing receipt is evidence that the sender authorized an
    export. It is never reused as the receiver's allow decision.
    """
    source = deepcopy(bundle.memory)
    receipts.validate("memory-unit.schema.json", source)

    source_scope = source.get("scope") or {}
    owner = source_scope.get("owner_principal")
    if expected_owner_principal is not None and owner != expected_owner_principal:
        decision = policy.Decision(
            outcome=policy.BLOCK,
            permitted_actions=(),
            prohibited_actions=("scope_expansion",),
            reasons=("cross-system ownership conflict",),
        )
        return ImportResult(decision, False, None, "ownership_conflict")

    if receiver_proposal.target_reference != source["id"]:
        raise ValueError("receiver proposal must bind the imported memory id")
    if receiver_proposal.operation != "scope_expansion":
        decision = policy.Decision(
            outcome=policy.BLOCK,
            permitted_actions=(),
            prohibited_actions=(receiver_proposal.operation, "scope_expansion"),
            reasons=("cross-system import must be evaluated as scope_expansion",),
        )
        return ImportResult(decision, False, None, "receiver_reauthorization_required")

    decision = _evaluate(receiver_proposal, evidence, attestation, verifier_registry)
    if decision.outcome not in (policy.ALLOW, policy.ALLOW_WITH_LEDGER):
        return ImportResult(decision, False, None, f"receiver_{decision.outcome}")

    source_domains = tuple(source_scope.get("isolation_domain_refs", ()))
    inherited_sources = tuple(source_scope.get("source_isolation_domain_refs", ()))
    all_sources = list(dict.fromkeys((*source_domains, *inherited_sources)))

    imported = deepcopy(source)
    imported["acquisition_mode"] = "imported"
    imported_scope = deepcopy(source_scope)
    imported_scope["primary_isolation_domain_ref"] = receiver_domain_ref
    imported_scope["isolation_domain_refs"] = [receiver_domain_ref]
    imported_scope["source_isolation_domain_refs"] = all_sources
    imported["scope"] = imported_scope
    imported["authority"] = {
        "pama_outcome": decision.outcome,
        "risk_class": receiver_proposal.risk_class,
        "policy_version": decision.policy_version,
        "authority_refs": list(receiver_proposal.approval_refs),
        "permitted_actions": list(decision.permitted_actions),
        "prohibited_actions": list(decision.prohibited_actions),
        "selection_mode": "deterministic",
    }

    receipts.validate("memory-unit.schema.json", imported)
    link = InterchangeLink(
        memory_id=source["id"],
        source_system=bundle.sender_system,
        receiver_system=bundle.receiver_system,
        source_crossing_receipt_ref=bundle.crossing_receipt["receipt_id"],
        source_domain_refs=tuple(all_sources),
        receiver_domain_ref=receiver_domain_ref,
    )
    return ImportResult(decision, True, imported, link=link)


def evaluate_source_notice(
    imported_memory: dict,
    link: InterchangeLink,
    notice: SourceLifecycleNotice,
    *,
    receiver_proposal: policy.Proposal,
    evidence=None,
    attestation: policy.ExternalVerification | None = None,
    verifier_registry=None,
) -> NoticeResult:
    """Recognize a source lifecycle change without importing remote authority.

    A notice may make a local correction/deletion obligation visible. It never
    directly changes or deletes receiver state. The receiver evaluates the
    corresponding local consequence under its own current policy and authority.
    """
    receipts.validate("memory-unit.schema.json", imported_memory)
    if notice.kind not in NOTICE_KINDS:
        raise ValueError(f"unsupported lifecycle notice: {notice.kind}")
    if not notice.evidence_refs:
        raise ValueError("source lifecycle notice requires evidence refs")
    if imported_memory["id"] != link.memory_id or notice.memory_id != link.memory_id:
        return NoticeResult(
            policy.Decision(policy.BLOCK, (), ("correction", "permanent_deletion"), ("notice memory identity mismatch",)),
            False,
            "none",
            "identity_mismatch",
        )
    if notice.source_system != link.source_system:
        return NoticeResult(
            policy.Decision(policy.BLOCK, (), ("correction", "permanent_deletion"), ("notice source system mismatch",)),
            False,
            "none",
            "source_system_mismatch",
        )

    expected_operation = "permanent_deletion" if notice.kind == NOTICE_DELETION else "correction"
    if receiver_proposal.target_reference != link.memory_id:
        raise ValueError("receiver notice proposal must bind the imported memory id")
    if receiver_proposal.operation != expected_operation:
        decision = policy.Decision(
            outcome=policy.BLOCK,
            permitted_actions=(),
            prohibited_actions=(receiver_proposal.operation, expected_operation),
            reasons=("source lifecycle notice mapped to wrong local consequence",),
        )
        return NoticeResult(decision, True, "none", "wrong_local_consequence")

    decision = _evaluate(receiver_proposal, evidence, attestation, verifier_registry)
    if decision.outcome not in (policy.ALLOW, policy.ALLOW_WITH_LEDGER):
        return NoticeResult(decision, True, "pending_local_governance", f"receiver_{decision.outcome}")

    action = "schedule_local_deletion" if notice.kind == NOTICE_DELETION else "schedule_local_correction"
    return NoticeResult(decision, True, action)
