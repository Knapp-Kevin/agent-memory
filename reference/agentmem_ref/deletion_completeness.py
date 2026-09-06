"""Compose P4 deletion-residue measurements into P4.5 portable evidence.

P4 proves whether derived state survived a governed deletion. P4.5 proves that a
content-free third party can distinguish those lifecycle outcomes without
receiving the deleted memory. This module is the explicit seam between them.

The public measurement intentionally carries counts and cryptographic references,
not projection identifiers or memory content. Internal residue identifiers remain
available to the local sweep and receipt-generation path but are not serialized
into the portable chain.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from . import residue
from .portable_evidence import IssuerKey, sha256_ref, issue_evidence

PROFILE = "agent-memory-deletion-completeness-chain"
VERSION = "1.0.0"


@dataclass(frozen=True)
class DeletionCompletenessMeasurement:
    """Content-free lifecycle measurement derived from the P4 residue partition."""

    purged_count: int
    declared_residual_controlled_count: int
    declared_residual_uncontrollable_count: int
    undeclared_residual_count: int
    independently_observed_residual_count: int

    @property
    def lifecycle_satisfaction(self) -> str:
        return "satisfied" if self.total_residual_count == 0 else "residual"

    @property
    def hard_gate_passed(self) -> bool:
        return self.undeclared_residual_count == 0

    @property
    def total_residual_count(self) -> int:
        return (
            self.declared_residual_controlled_count
            + self.declared_residual_uncontrollable_count
            + self.undeclared_residual_count
        )

    def as_public_summary(self) -> dict:
        return {
            "purged_count": self.purged_count,
            "declared_residual_controlled_count": self.declared_residual_controlled_count,
            "declared_residual_uncontrollable_count": self.declared_residual_uncontrollable_count,
            "undeclared_residual_count": self.undeclared_residual_count,
            "independently_observed_residual_count": self.independently_observed_residual_count,
            "total_residual_count": self.total_residual_count,
            "hard_gate_passed": self.hard_gate_passed,
            "lifecycle_satisfaction": self.lifecycle_satisfaction,
        }


def measure_deletion_completeness(
    buckets: Mapping[str, Sequence[str]],
    independently_observed_residual: Sequence[str],
) -> DeletionCompletenessMeasurement:
    """Derive a public lifecycle measurement from actual P4 residue evidence.

    `independently_observed_residual` is intentionally supplied from an
    independent sweep that ignores the purge's own declaration list. This makes
    it possible to prove that surviving content existed even when the deletion
    receipt correctly declared that residue.
    """
    required = {
        residue.PURGED,
        residue.DECLARED_CONTROLLED,
        residue.DECLARED_UNCONTROLLABLE,
        residue.UNDECLARED,
    }
    missing = required.difference(buckets)
    if missing:
        raise ValueError(f"residue partition missing buckets: {sorted(missing)}")

    values: dict[str, tuple[str, ...]] = {}
    for name in required:
        items = tuple(buckets[name])
        if any(not isinstance(item, str) or not item for item in items):
            raise ValueError(f"residue bucket {name} contains a non-string identifier")
        if len(items) != len(set(items)):
            raise ValueError(f"residue bucket {name} contains duplicate identifiers")
        values[name] = items

    observed = tuple(independently_observed_residual)
    if any(not isinstance(item, str) or not item for item in observed):
        raise ValueError("independent residue sweep contains a non-string identifier")
    if len(observed) != len(set(observed)):
        raise ValueError("independent residue sweep contains duplicate identifiers")

    declared_or_undeclared = (
        set(values[residue.DECLARED_CONTROLLED])
        | set(values[residue.DECLARED_UNCONTROLLABLE])
        | set(values[residue.UNDECLARED])
    )
    if not declared_or_undeclared.issubset(set(observed)):
        raise ValueError("public residue partition claims survivors the independent sweep did not observe")

    return DeletionCompletenessMeasurement(
        purged_count=len(values[residue.PURGED]),
        declared_residual_controlled_count=len(values[residue.DECLARED_CONTROLLED]),
        declared_residual_uncontrollable_count=len(values[residue.DECLARED_UNCONTROLLABLE]),
        undeclared_residual_count=len(values[residue.UNDECLARED]),
        independently_observed_residual_count=len(observed),
    )


def build_deletion_completeness_chain(
    canonical_receipt: Mapping[str, object],
    measurement: DeletionCompletenessMeasurement,
    *,
    agent_memory_commit: str,
    issuer_id: str,
    issuer_key: IssuerKey,
    issued_at: str,
    action_ref: str,
    policy_ref: str,
    authority_state_ref: str,
    decision_time: str,
    scope_ref: str,
    before_state_ref: str,
    source_domain_ref: str | None = None,
    destination_domain_ref: str | None = None,
    domain_authorization_state_ref: str | None = None,
) -> dict:
    """Bind an actual residue measurement to signed P4.5 portable evidence."""
    if len(agent_memory_commit) != 40 or any(c not in "0123456789abcdef" for c in agent_memory_commit):
        raise ValueError("agent_memory_commit must be an exact lowercase 40-hex commit SHA")

    selected_action = canonical_receipt.get("selected_action")
    if selected_action != "permanent_deletion":
        raise ValueError("deletion completeness requires a canonical permanent_deletion receipt")

    summary = measurement.as_public_summary()
    summary_ref = sha256_ref(summary)
    portable = issue_evidence(
        canonical_receipt,
        issuer_id=issuer_id,
        key=issuer_key,
        issued_at=issued_at,
        action_ref=action_ref,
        memory_action="permanent_deletion",
        governance_disposition="committed",
        policy_ref=policy_ref,
        authority_state_ref=authority_state_ref,
        decision_time=decision_time,
        scope_ref=scope_ref,
        before_state_ref=before_state_ref,
        after_state_ref=summary_ref,
        lifecycle_result=measurement.lifecycle_satisfaction,
        source_domain_ref=source_domain_ref,
        destination_domain_ref=destination_domain_ref,
        domain_authorization_state_ref=domain_authorization_state_ref,
    )

    return {
        "profile": PROFILE,
        "version": VERSION,
        "agent_memory_commit": agent_memory_commit,
        "canonical_receipt_ref": portable["canonical_receipt_ref"],
        "action_ref": action_ref,
        "measurement_ref": summary_ref,
        "measurement": summary,
        "portable_evidence_ref": sha256_ref(portable),
        "portable_evidence": portable,
    }
