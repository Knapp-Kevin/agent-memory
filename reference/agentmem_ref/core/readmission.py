"""Rejected-value history and governed semantic re-admission signals.

Exact/structured rejected identity and semantic similarity deliberately have
different authority properties:

- deterministic normalized identity may enforce the already-proven exact-value
  write guard;
- semantic similarity is estimator evidence only. It may trigger a governed
  reconciliation/review lane, but the estimator cannot emit allow/block or
  authorize durable re-admission.

Raw rejected memory content is not retained here. Rejection history stores a
scoped SHA-256 fingerprint plus provenance, authority, and lifecycle metadata.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

REJECTED = "rejected"
READMITTED = "readmitted"
PURGED = "purged"

NO_SEMANTIC_SIGNAL = "no_semantic_reconciliation_signal"
REQUIRE_RECONCILIATION = "require_reconciliation"


def normalize_value(value: str) -> str:
    """Canonicalize only deterministic presentation differences.

    Case and repeated whitespace are normalized. Punctuation, word order, and
    semantic paraphrase are intentionally untouched so this helper cannot
    quietly become a probabilistic equivalence oracle.
    """

    return " ".join(value.casefold().split())


def value_fingerprint(value: str) -> str:
    normalized = normalize_value(value)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def rejection_id(memory_id: str, fingerprint: str, correction_proposal_id: str) -> str:
    material = f"{memory_id}\n{fingerprint}\n{correction_proposal_id}".encode("utf-8")
    return f"rejection:sha256:{hashlib.sha256(material).hexdigest()}"


@dataclass
class RejectionRecord:
    memory_id: str
    value_fingerprint: str
    superseded_fact_uuid: str
    correction_proposal_id: str
    evidence_refs: tuple[str, ...]
    authority_refs: tuple[str, ...]
    scope: str
    rejected_at: str
    active: bool = True
    lifecycle_state: str = REJECTED
    readmitted_at: str | None = None
    readmission_proposal_id: str | None = None

    @property
    def rejection_id(self) -> str:
        return rejection_id(self.memory_id, self.value_fingerprint, self.correction_proposal_id)

    def as_dict(self) -> dict:
        return {
            "rejection_id": self.rejection_id,
            "memory_id": self.memory_id,
            "value_fingerprint": self.value_fingerprint,
            "superseded_fact_uuid": self.superseded_fact_uuid,
            "correction_proposal_id": self.correction_proposal_id,
            "evidence_refs": list(self.evidence_refs),
            "authority_refs": list(self.authority_refs),
            "scope": self.scope,
            "rejected_at": self.rejected_at,
            "active": self.active,
            "lifecycle_state": self.lifecycle_state,
            "readmitted_at": self.readmitted_at,
            "readmission_proposal_id": self.readmission_proposal_id,
        }


@dataclass(frozen=True)
class SemanticSimilaritySignal:
    """Estimator evidence that a proposal may resemble an active rejection.

    The signal has no authority/result field by design. Consumers may route it
    through a deterministic policy, but cannot honestly interpret the object as
    an allow, block, approval, or readmission decision.
    """

    memory_id: str
    rejection_ref: str
    estimator_id: str
    estimator_version: str
    candidate_match: bool
    confidence: float | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("memory_id", "rejection_ref", "estimator_id", "estimator_version"):
            if not getattr(self, name):
                raise ValueError(f"semantic similarity signal requires {name}")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("semantic similarity confidence must be between 0 and 1")

    def as_evidence(self) -> dict:
        evidence = {
            "signal_type": "semantic_rejected_value_similarity",
            "signal_semantics": "candidate_match_for_reconciliation_not_authority",
            "signal_value": self.candidate_match,
            "estimator_id": self.estimator_id,
            "estimator_version": self.estimator_version,
            "rejection_ref": self.rejection_ref,
            "evidence_refs": list(self.evidence_refs),
        }
        if self.confidence is not None:
            evidence["confidence"] = self.confidence
        return evidence


@dataclass(frozen=True)
class SemanticReadmissionRouting:
    """Deterministic consequence of an estimator signal.

    The only restrictive outcome is reconciliation/review. There is no `allow`
    or permanent `block` result in this type. Durable permission still belongs
    to the ordinary PAMA/approval path.
    """

    consequence: str
    review_required: bool
    signal: SemanticSimilaritySignal


def route_semantic_similarity(signal: SemanticSimilaritySignal) -> SemanticReadmissionRouting:
    consequence = REQUIRE_RECONCILIATION if signal.candidate_match else NO_SEMANTIC_SIGNAL
    return SemanticReadmissionRouting(
        consequence=consequence,
        review_required=signal.candidate_match,
        signal=signal,
    )


class RejectedValueRegistry:
    """Append-oriented rejection history keyed by memory and exact value identity."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], list[RejectionRecord]] = {}

    def _key(self, memory_id: str, value: str) -> tuple[str, str]:
        return memory_id, value_fingerprint(value)

    def active(self, memory_id: str, value: str) -> RejectionRecord | None:
        records = self._records.get(self._key(memory_id, value), ())
        for record in reversed(records):
            if record.active:
                return record
        return None

    def active_records(self, memory_id: str) -> tuple[dict, ...]:
        """Return active rejection metadata without raw rejected content."""
        return tuple(
            record.as_dict()
            for (record_memory_id, _fingerprint), records in self._records.items()
            if record_memory_id == memory_id
            for record in records
            if record.active
        )

    def find_active_by_ref(self, memory_id: str, rejection_ref: str) -> RejectionRecord | None:
        for record in self.active_records(memory_id):
            if record["rejection_id"] == rejection_ref:
                fingerprint = record["value_fingerprint"]
                for candidate in reversed(self._records.get((memory_id, fingerprint), ())):
                    if candidate.active and candidate.rejection_id == rejection_ref:
                        return candidate
        return None

    def reject(
        self,
        *,
        memory_id: str,
        value: str,
        superseded_fact_uuid: str,
        correction_proposal_id: str,
        evidence_refs: tuple[str, ...],
        authority_refs: tuple[str, ...] = (),
        scope: str,
        rejected_at: str,
    ) -> RejectionRecord:
        record = RejectionRecord(
            memory_id=memory_id,
            value_fingerprint=value_fingerprint(value),
            superseded_fact_uuid=superseded_fact_uuid,
            correction_proposal_id=correction_proposal_id,
            evidence_refs=tuple(evidence_refs),
            authority_refs=tuple(authority_refs),
            scope=scope,
            rejected_at=rejected_at,
        )
        self._records.setdefault(self._key(memory_id, value), []).append(record)
        return record

    def readmit(
        self,
        *,
        memory_id: str,
        value: str,
        proposal_id: str,
        readmitted_at: str,
    ) -> RejectionRecord | None:
        record = self.active(memory_id, value)
        if record is None:
            return None
        record.active = False
        record.lifecycle_state = READMITTED
        record.readmitted_at = readmitted_at
        record.readmission_proposal_id = proposal_id
        return record

    def history(self, memory_id: str, value: str) -> tuple[dict, ...]:
        return tuple(record.as_dict() for record in self._records.get(self._key(memory_id, value), ()))

    def purge_memory(self, memory_id: str) -> int:
        """Remove rejection fingerprints/history for a permanently deleted memory.

        Rejection history is governed state, not an excuse to retain a sensitive
        fingerprint forever. The caller is responsible for preserving whatever
        deletion receipt/audit evidence policy requires outside this registry.
        """
        keys = [key for key in self._records if key[0] == memory_id]
        count = sum(len(self._records[key]) for key in keys)
        for key in keys:
            del self._records[key]
        return count
