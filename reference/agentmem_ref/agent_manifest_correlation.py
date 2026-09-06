"""P4.5b correlation with the Agent Manifest memory checkpoint protocol.

Agent Manifest owns checkpoint construction, RFC 9162 consistency proofs, TTL,
sequence, and delta-budget verification. This module does not reimplement that
protocol. It content-addresses the checkpoint tuple, proves that the canonical
Agent Memory receipt references that checkpoint, and preserves the external
checkpoint verdict beside Agent Memory governance and lifecycle outcomes.

A checkpoint root proves the bound log state; it does not, by itself, disclose
or independently prove the semantic class of a newly appended operation. Agent
Memory action semantics therefore remain in the signed Agent Memory evidence.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from .portable_evidence import TrustKey, sha256_ref, verify_evidence

CORRELATION_TYPE = "agent-memory-agent-manifest-correlation"
CORRELATION_VERSION = "1.0.0"
AGENT_MANIFEST_SPEC_VERSION = "0.2"
AGENT_MANIFEST_SDK_VERSION = "0.11.2"
AGENT_MANIFEST_UPSTREAM_COMMIT = "9d26ac84461e829dba8ff97ca35748eeb874debe"

DELTA_REASONS = {"accepted", "drift", "rollback", "expired", "budget"}
REPRESENTATIONS = {"kv", "vector", "graph"}
_HASH_ALGORITHMS = {"sha256", "shake256"}


def _value(checkpoint: object, name: str) -> object:
    if isinstance(checkpoint, Mapping):
        if name not in checkpoint:
            raise ValueError(f"checkpoint missing {name}")
        return checkpoint[name]
    try:
        return getattr(checkpoint, name)
    except AttributeError as exc:
        raise ValueError(f"checkpoint missing {name}") from exc


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("checkpoint approved_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def _timestamp(value: object) -> str:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("checkpoint approved_at must include a timezone")
        parsed = value.astimezone(timezone.utc)
    elif isinstance(value, str) and value:
        try:
            parsed = _parse_timestamp(value)
        except ValueError as exc:
            raise ValueError("checkpoint approved_at must be a valid timezone-aware datetime") from exc
    else:
        raise ValueError("checkpoint approved_at must be a datetime or non-empty string")
    return parsed.isoformat().replace("+00:00", "Z")


def _validate_hashvalue(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("checkpoint memory_root must be a HashValue")
    algorithm, sep, digest = value.partition(":")
    if (
        not sep
        or algorithm not in _HASH_ALGORITHMS
        or len(digest) != 64
        or digest != digest.lower()
        or any(char not in "0123456789abcdef" for char in digest)
    ):
        raise ValueError("checkpoint memory_root must be sha256/shake256 plus 64 lowercase hex characters")
    return value


def checkpoint_payload(checkpoint: object) -> dict:
    """Project only fields Agent Manifest v0.2 binds into a checkpoint.

    The upstream protocol defines the bound tuple as
    ``{memory_root, tree_size, seq, approved_at, ttl_seconds}``. We preserve
    exactly that tuple here and intentionally omit operation content and the
    upstream verifier's internal proof representation.
    """
    memory_root = _validate_hashvalue(_value(checkpoint, "memory_root"))
    tree_size = _value(checkpoint, "tree_size")
    seq = _value(checkpoint, "seq")
    ttl_seconds = _value(checkpoint, "ttl_seconds")
    approved_at = _timestamp(_value(checkpoint, "approved_at"))

    if not isinstance(tree_size, int) or isinstance(tree_size, bool) or tree_size < 0:
        raise ValueError("checkpoint tree_size must be a non-negative integer")
    if not isinstance(seq, int) or isinstance(seq, bool) or seq < 0:
        raise ValueError("checkpoint seq must be a non-negative integer")
    if not isinstance(ttl_seconds, int) or isinstance(ttl_seconds, bool) or ttl_seconds <= 0:
        raise ValueError("checkpoint ttl_seconds must be a positive integer")

    return {
        "memory_root": memory_root,
        "tree_size": tree_size,
        "seq": seq,
        "approved_at": approved_at,
        "ttl_seconds": ttl_seconds,
    }


def checkpoint_reference(checkpoint: object) -> str:
    """Return a content-addressed reference suitable for receipt.evidence_refs."""
    return sha256_ref(checkpoint_payload(checkpoint))


def correlate_agent_manifest_delta(
    portable_evidence: Mapping[str, object],
    canonical_receipt: Mapping[str, object],
    trust_keys: Mapping[tuple[str, str], TrustKey],
    *,
    previous_checkpoint: object,
    new_checkpoint: object,
    delta_accepted: bool,
    delta_reason: str,
    representation: str,
) -> dict:
    """Bind an externally verified Agent Manifest delta to Agent Memory evidence.

    ``delta_accepted`` and ``delta_reason`` MUST come from the pinned Agent
    Manifest verifier (or another conforming implementation). This function
    never recomputes a consistency proof, TTL verdict, sequence verdict, delta
    budget, or operation semantics; those remain owned by their source systems.

    A rejected delta still yields a valid correlation artifact when the records
    are correctly bound. Likewise, an accepted checkpoint advance never upgrades
    Agent Memory lifecycle satisfaction from ``residual`` to ``satisfied``.
    """
    if delta_reason not in DELTA_REASONS:
        raise ValueError(f"unsupported Agent Manifest delta reason: {delta_reason}")
    if delta_accepted != (delta_reason == "accepted"):
        raise ValueError("delta_accepted and delta_reason disagree")
    if representation not in REPRESENTATIONS:
        raise ValueError(f"unsupported memory representation: {representation}")

    previous = checkpoint_payload(previous_checkpoint)
    new = checkpoint_payload(new_checkpoint)
    previous_ref = checkpoint_reference(previous_checkpoint)
    checkpoint_ref = checkpoint_reference(new_checkpoint)

    failures: list[str] = []
    portable_result = verify_evidence(
        portable_evidence,
        trust_keys,
        canonical_receipt=canonical_receipt,
    )
    if portable_result["evidence_integrity"] != "valid":
        failures.append("portable_evidence_invalid")
    if portable_result["receipt_resolution"] != "resolved":
        failures.append("canonical_receipt_not_resolved")

    memory_action = portable_evidence.get("memory_action")
    if canonical_receipt.get("selected_action") != memory_action:
        failures.append("receipt_memory_action_mismatch")

    evidence_refs = canonical_receipt.get("evidence_refs", [])
    if not isinstance(evidence_refs, list) or checkpoint_ref not in evidence_refs:
        failures.append("receipt_missing_checkpoint_ref")

    state = portable_evidence.get("state")
    if not isinstance(state, Mapping):
        failures.append("portable_state_binding_missing")
    else:
        if state.get("before_ref") != previous_ref:
            failures.append("before_checkpoint_ref_mismatch")
        if state.get("after_ref") != checkpoint_ref:
            failures.append("after_checkpoint_ref_mismatch")

    governance = portable_evidence.get("governance")
    if not isinstance(governance, Mapping):
        governance = {}

    return {
        "correlation_type": CORRELATION_TYPE,
        "version": CORRELATION_VERSION,
        "correlation_integrity": "valid" if not failures else "invalid",
        "binding_failures": failures,
        "agent_memory": {
            "portable_evidence_ref": sha256_ref(dict(portable_evidence)),
            "canonical_receipt_ref": portable_evidence.get("canonical_receipt_ref", ""),
            "action_ref": portable_evidence.get("action_ref", ""),
            "memory_action": memory_action or "",
            "governance_disposition": governance.get("disposition", "unverifiable"),
            "lifecycle_satisfaction": portable_evidence.get("lifecycle_result", "unverifiable"),
        },
        "agent_manifest": {
            "spec_version": AGENT_MANIFEST_SPEC_VERSION,
            "sdk_version": AGENT_MANIFEST_SDK_VERSION,
            "upstream_commit": AGENT_MANIFEST_UPSTREAM_COMMIT,
            "representation": representation,
            "checkpoint_ref": checkpoint_ref,
            "previous_checkpoint": previous,
            "new_checkpoint": new,
            "delta_verification": "accepted" if delta_accepted else "rejected",
            "delta_reason": delta_reason,
        },
    }
