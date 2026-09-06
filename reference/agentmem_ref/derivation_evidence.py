"""Non-authoritative derivation/provenance envelope for issues #204, #210, and #212.

A summary, restatement, compression, or other transformation may create useful
new evidence. It may not create a new origin, independent corroboration, or
memory authority merely because the transformer is trusted or confident.

Historical derivation evidence remains immutable. Current applicability is
handled separately by ``derivation_currentness`` rather than by rewriting this
record after source state changes.
"""

from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from typing import Any

from . import receipts

PROFILE_VERSION = "0.1.0"
TRUST_STATES = {"untrusted", "unknown", "bounded_trusted", "trusted"}
SCOPE_RELATIONS = {"preserved", "narrowed"}
TRANSFORMATION_MODES = {"deterministic", "probabilistic"}
TRANSFORMATION_STATUSES = {"complete", "partial", "failed"}
OUTPUT_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _refs(values: Any, field: str, *, required: bool = False) -> list[str]:
    if values is None:
        values = []
    if not isinstance(values, (list, tuple)):
        raise ValueError(f"{field} must be an array")
    refs = list(dict.fromkeys(values))
    if required and not refs:
        raise ValueError(f"{field} must contain at least one reference")
    if not all(isinstance(value, str) and value for value in refs):
        raise ValueError(f"{field} references must be non-empty strings")
    return refs


def _required_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def _trust(value: Any, field: str) -> str:
    trust = _required_string(value, field)
    if trust not in TRUST_STATES:
        raise ValueError(f"unsupported {field}: {trust!r}")
    return trust


def _optional_enum(value: Any, field: str, allowed: set[str]) -> str | None:
    if value is None:
        return None
    normalized = _required_string(value, field)
    if normalized not in allowed:
        raise ValueError(f"unsupported {field}: {normalized!r}")
    return normalized


def _output_custody(transform: dict[str, Any]) -> dict[str, str]:
    """Normalize optional typed/digested output custody without raw payloads.

    ``output_ref`` remains the legacy minimum. If either type or digest is
    supplied, both are required so the record never presents a partial custody
    claim. Digest integrity is evidence about referenced bytes only; it does not
    establish semantic correctness or authority.
    """
    output_type = transform.get("output_type")
    output_digest = transform.get("output_digest")
    if output_type is None and output_digest is None:
        return {}
    if output_type is None or output_digest is None:
        raise ValueError(
            "transformation.output_type and transformation.output_digest must be supplied together"
        )
    normalized_type = _required_string(output_type, "transformation.output_type")
    normalized_digest = _required_string(output_digest, "transformation.output_digest")
    if OUTPUT_DIGEST_RE.fullmatch(normalized_digest) is None:
        raise ValueError("transformation.output_digest must be sha256:<64 lowercase hex>")
    return {
        "output_type": normalized_type,
        "output_digest": normalized_digest,
    }


def _confidence(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("confidence must be an object")
    score = value.get("value")
    if not isinstance(score, (int, float)) or isinstance(score, bool) or not 0 <= score <= 1:
        raise ValueError("confidence.value must be between 0 and 1")
    return {
        "signal_semantics": _required_string(value.get("signal_semantics"), "confidence.signal_semantics"),
        "estimator_ref": _required_string(value.get("estimator_ref"), "confidence.estimator_ref"),
        "estimator_version": _required_string(value.get("estimator_version"), "confidence.estimator_version"),
        "value": float(score),
    }


def _scope(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("scope must be an object")
    result: dict[str, Any] = {
        "scope_ref": _required_string(value.get("scope_ref"), "scope.scope_ref"),
        "tenant_ref": _required_string(value.get("tenant_ref"), "scope.tenant_ref"),
        "project_ref": _required_string(value.get("project_ref"), "scope.project_ref"),
    }
    relation = value.get("relation")
    if relation is not None:
        if relation not in SCOPE_RELATIONS:
            raise ValueError(f"unsupported scope.relation: {relation!r}")
        result["relation"] = relation
        basis_refs = _refs(value.get("basis_refs"), "scope.basis_refs", required=relation == "narrowed")
        if basis_refs:
            result["basis_refs"] = basis_refs
    elif value.get("basis_refs") is not None:
        raise ValueError("scope.basis_refs requires scope.relation")
    return result


def _binding(scope: dict[str, Any], expected_scope: dict[str, Any] | None) -> dict[str, Any]:
    if expected_scope is None:
        return {"status": "not_evaluated", "reasons": []}
    expected = _scope(expected_scope)
    reasons = [
        f"{field}_mismatch"
        for field in ("scope_ref", "tenant_ref", "project_ref")
        if scope[field] != expected[field]
    ]
    return {"status": "mismatch" if reasons else "exact", "reasons": reasons}


def _interpretation() -> dict[str, Any]:
    return {
        "authority_effect": "none",
        "memory_admission": "not_established",
        "certification_claim": "none",
        "transformer_authority": "none",
        "confidence_authority": "none",
        "source_trust_authority": "none",
        "independent_corroboration": "not_established",
        "repetition_creates_independent_origin": False,
        "root_origin_preserved": True,
    }


def _derivation_id(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def normalize_derivation(value: dict[str, Any], expected_scope: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize a first-order transformation while discarding authority-shaped input.

    Only the bounded fields below are consumed. Caller-supplied PAMA outcomes,
    permissions, certification, lifecycle state, prompts, raw output content,
    and similar fields have no output path.
    """
    if not isinstance(value, dict):
        raise ValueError("derivation input must be an object")

    root_origin_refs = _refs(value.get("root_origin_refs"), "root_origin_refs", required=True)
    immediate_source_refs = _refs(value.get("immediate_source_refs"), "immediate_source_refs", required=True)
    source_trust = _trust(value.get("source_trust"), "source_trust")
    scope = _scope(value.get("scope"))
    evidence_refs = _refs(value.get("evidence_refs"), "evidence_refs", required=True)
    prior_derivation_refs = _refs(value.get("prior_derivation_refs"), "prior_derivation_refs")

    transform = value.get("transformation")
    if not isinstance(transform, dict):
        raise ValueError("transformation must be an object")
    transformation: dict[str, Any] = {
        "method": _required_string(transform.get("method"), "transformation.method"),
        "transformer_ref": _required_string(transform.get("transformer_ref"), "transformation.transformer_ref"),
        "transformer_version": _required_string(transform.get("transformer_version"), "transformation.transformer_version"),
        "transformer_trust": _trust(transform.get("transformer_trust"), "transformation.transformer_trust"),
        "output_ref": _required_string(transform.get("output_ref"), "transformation.output_ref"),
    }
    mode = _optional_enum(transform.get("mode"), "transformation.mode", TRANSFORMATION_MODES)
    status = _optional_enum(transform.get("status"), "transformation.status", TRANSFORMATION_STATUSES)
    if mode is not None:
        transformation["mode"] = mode
    if status is not None:
        transformation["status"] = status
    transformation.update(_output_custody(transform))

    confidence = _confidence(value.get("confidence"))
    created_at = _required_string(value.get("created_at"), "created_at")
    depth = value.get("derivation_depth", 1)
    if not isinstance(depth, int) or isinstance(depth, bool) or depth < 1:
        raise ValueError("derivation_depth must be an integer >= 1")

    identity_payload = {
        "root_origin_refs": root_origin_refs,
        "immediate_source_refs": immediate_source_refs,
        "source_trust": source_trust,
        "transformation": transformation,
        "prior_derivation_refs": prior_derivation_refs,
        "derivation_depth": depth,
        "scope": scope,
        "evidence_refs": evidence_refs,
        "confidence": confidence,
        "created_at": created_at,
    }
    result = {
        "profile_version": PROFILE_VERSION,
        "derivation_id": _derivation_id(identity_payload),
        "root_origin_refs": root_origin_refs,
        "immediate_source_refs": immediate_source_refs,
        "source_trust": source_trust,
        "transformation": transformation,
        "prior_derivation_refs": prior_derivation_refs,
        "derivation_depth": depth,
        "scope": scope,
        "evidence_refs": evidence_refs,
        "binding": _binding(scope, expected_scope),
        "created_at": created_at,
        "interpretation": _interpretation(),
    }
    if confidence is not None:
        result["confidence"] = confidence
    receipts.validate("derivation-evidence.schema.json", result)
    return result


def _governed_scope_for_child(
    source_scope: dict[str, Any],
    narrowed_scope: dict[str, Any] | None,
    scope_basis_refs: tuple[str, ...] | list[str],
) -> dict[str, Any]:
    """Return preserved scope or an explicitly justified narrower scope.

    V0.1 does not infer scope hierarchy from names. Narrowing is an explicit API
    operation: the new scope ref must differ, tenant/project boundaries must
    remain identical, and at least one basis ref is required. Arbitrary scope
    fields inside transformer metadata are never consulted.
    """
    if narrowed_scope is None:
        if scope_basis_refs:
            raise ValueError("scope_basis_refs require narrowed_scope")
        return deepcopy(source_scope)

    proposed = _scope(narrowed_scope)
    basis_refs = _refs(scope_basis_refs, "scope_basis_refs", required=True)
    if proposed["scope_ref"] == source_scope["scope_ref"]:
        raise ValueError("narrowed scope_ref must differ from source scope_ref")
    if proposed["tenant_ref"] != source_scope["tenant_ref"]:
        raise ValueError("derivation scope narrowing cannot change tenant_ref")
    if proposed["project_ref"] != source_scope["project_ref"]:
        raise ValueError("derivation scope narrowing cannot change project_ref")
    return {
        "scope_ref": proposed["scope_ref"],
        "tenant_ref": proposed["tenant_ref"],
        "project_ref": proposed["project_ref"],
        "relation": "narrowed",
        "basis_refs": basis_refs,
    }


def derive_from(
    source_derivation: dict[str, Any],
    transformation: dict[str, Any],
    expected_scope: dict[str, Any] | None = None,
    *,
    narrowed_scope: dict[str, Any] | None = None,
    scope_basis_refs: tuple[str, ...] | list[str] = (),
) -> dict[str, Any]:
    """Create a later derivation without minting a new root origin.

    The inherited source-trust and scope values are evidence metadata only. A
    caller cannot use transformer metadata to rewrite them. Scope may be
    narrowed only through the explicit ``narrowed_scope`` API with basis refs.
    """
    receipts.validate("derivation-evidence.schema.json", source_derivation)
    if not isinstance(transformation, dict):
        raise ValueError("transformation must be an object")

    evidence_refs = _refs(transformation.get("evidence_refs"), "evidence_refs", required=True)
    child_scope = _governed_scope_for_child(source_derivation["scope"], narrowed_scope, scope_basis_refs)
    child_transformation: dict[str, Any] = {
        "method": transformation.get("method"),
        "transformer_ref": transformation.get("transformer_ref"),
        "transformer_version": transformation.get("transformer_version"),
        "transformer_trust": transformation.get("transformer_trust"),
        "output_ref": transformation.get("output_ref"),
    }
    for field in ("mode", "status", "output_type", "output_digest"):
        if transformation.get(field) is not None:
            child_transformation[field] = transformation.get(field)

    value = {
        "root_origin_refs": deepcopy(source_derivation["root_origin_refs"]),
        "immediate_source_refs": [source_derivation["derivation_id"]],
        "source_trust": source_derivation["source_trust"],
        "transformation": child_transformation,
        "prior_derivation_refs": list(dict.fromkeys(
            source_derivation["prior_derivation_refs"] + [source_derivation["derivation_id"]]
        )),
        "derivation_depth": source_derivation["derivation_depth"] + 1,
        "scope": child_scope,
        "evidence_refs": list(dict.fromkeys(source_derivation["evidence_refs"] + evidence_refs)),
        "confidence": transformation.get("confidence"),
        "created_at": transformation.get("created_at"),
    }
    return normalize_derivation(value, expected_scope=expected_scope)
