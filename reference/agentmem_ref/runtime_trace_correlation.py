"""Privacy-safe runtime trace correlation for issue #185.

The V0.1 profile consumes a bounded runtime/telemetry adapter result and emits
only stable trace identifiers plus Agent Memory references needed for
correlation. Unknown adapter fields are intentionally discarded so raw memory,
prompts, tool payloads, or peer-specific semantic attributes cannot become
canonical correlation state by accident.
"""

from __future__ import annotations

import hashlib
import re

import rfc8785

from . import receipts

PROFILE_VERSION = "0.1.0"

OBSERVED = "observed"
NOT_OBSERVED = "not_observed"
TELEMETRY_UNAVAILABLE = "telemetry_unavailable"

SAMPLED = "sampled"
NOT_SAMPLED = "not_sampled"
SAMPLING_UNKNOWN = "unknown"

BINDING_EXACT = "exact"
BINDING_MISMATCH = "mismatch"
BINDING_NOT_EVALUATED = "not_evaluated"

_TELEMETRY_STATUSES = {OBSERVED, NOT_OBSERVED, TELEMETRY_UNAVAILABLE}
_SAMPLING_STATES = {SAMPLED, NOT_SAMPLED, SAMPLING_UNKNOWN}
_TRACE_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_SPAN_ID_RE = re.compile(r"^[0-9a-f]{16}$")


def _sha256_ref(value: dict) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _require_ref(name: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _validate_trace_id(value: object) -> str:
    if not isinstance(value, str) or not _TRACE_ID_RE.fullmatch(value):
        raise ValueError("trace_id must be 32 lowercase hexadecimal characters")
    if value == "0" * 32:
        raise ValueError("trace_id must not be all zero")
    return value


def _validate_span_id(name: str, value: object) -> str:
    if not isinstance(value, str) or not _SPAN_ID_RE.fullmatch(value):
        raise ValueError(f"{name} must be 16 lowercase hexadecimal characters")
    if value == "0" * 16:
        raise ValueError(f"{name} must not be all zero")
    return value


def normalize_trace_correlation(adapter_result: dict, expected_context: dict) -> dict:
    """Normalize runtime trace metadata into a vendor-neutral correlation record.

    ``adapter_result`` may contain arbitrary peer/runtime fields. Only the
    whitelisted V0.1 correlation surface is copied. ``expected_context`` binds
    the supplied telemetry to the intended Agent Memory action/input/scope.
    Mismatches are preserved as evidence rather than silently re-associated.
    """

    if not isinstance(adapter_result, dict) or not isinstance(expected_context, dict):
        raise ValueError("adapter_result and expected_context must be objects")

    telemetry_status = adapter_result.get("telemetry_status")
    if telemetry_status not in _TELEMETRY_STATUSES:
        raise ValueError(f"invalid telemetry_status {telemetry_status!r}")

    sampling_state = adapter_result.get("sampling_state", SAMPLING_UNKNOWN)
    if sampling_state not in _SAMPLING_STATES:
        raise ValueError(f"invalid sampling_state {sampling_state!r}")

    runtime_ref = _require_ref("runtime_ref", adapter_result.get("runtime_ref"))
    action_ref = _require_ref("action_ref", adapter_result.get("action_ref"))
    scope_ref = _require_ref("scope_ref", adapter_result.get("scope_ref"))
    correlated_at = _require_ref("correlated_at", adapter_result.get("correlated_at"))

    trace_id: str | None = None
    span_id: str | None = None
    parent_span_id: str | None = None

    if telemetry_status == OBSERVED:
        trace_id = _validate_trace_id(adapter_result.get("trace_id"))
        span_id = _validate_span_id("span_id", adapter_result.get("span_id"))
        if adapter_result.get("parent_span_id") is not None:
            parent_span_id = _validate_span_id("parent_span_id", adapter_result["parent_span_id"])
    else:
        # Absence/unavailability is itself useful evidence state. Carrying trace
        # IDs with an unobserved record would make the semantics ambiguous.
        if any(adapter_result.get(name) is not None for name in ("trace_id", "span_id", "parent_span_id")):
            raise ValueError("unobserved/unavailable telemetry must not claim trace or span identifiers")

    binding_reasons: list[str] = []
    if telemetry_status == OBSERVED:
        for field in ("action_ref", "input_identity", "scope_ref", "tenant_ref", "project_ref"):
            expected = expected_context.get(field)
            if expected is None:
                continue
            observed = adapter_result.get(field)
            if observed is None:
                binding_reasons.append(f"{field}_missing")
            elif observed != expected:
                binding_reasons.append(f"{field}_mismatch")
        binding_status = BINDING_MISMATCH if binding_reasons else BINDING_EXACT
    else:
        binding_status = BINDING_NOT_EVALUATED

    body = {
        "telemetry_status": telemetry_status,
        "sampling_state": sampling_state,
        "binding_status": binding_status,
        "binding_reasons": binding_reasons,
        "runtime_ref": runtime_ref,
        "action_ref": action_ref,
        "scope_ref": scope_ref,
        "correlated_at": correlated_at,
        "authority_effect": "none",
        "execution_claim": "not_established",
        "lifecycle_satisfaction": "not_established",
    }

    if trace_id is not None:
        body["trace_id"] = trace_id
    if span_id is not None:
        body["span_id"] = span_id
    if parent_span_id is not None:
        body["parent_span_id"] = parent_span_id

    optional_strings = (
        "service_ref",
        "input_identity",
        "pama_decision_ref",
        "composition_ref",
        "execution_witness_ref",
        "tenant_ref",
        "project_ref",
    )
    for name in optional_strings:
        value = adapter_result.get(name)
        if value is not None:
            body[name] = _require_ref(name, value)

    for name in ("external_evidence_refs", "policy_refs"):
        values = adapter_result.get(name)
        if values is not None:
            if not isinstance(values, (list, tuple)) or not all(isinstance(item, str) and item for item in values):
                raise ValueError(f"{name} must be a list of non-empty strings")
            body[name] = list(dict.fromkeys(values))

    identity_body = {
        key: value
        for key, value in body.items()
        if key not in {"correlated_at"}
    }
    document = {
        "schema_version": "1.0.0",
        "profile_version": PROFILE_VERSION,
        "correlation_id": f"runtime-trace-correlation:{_sha256_ref(identity_body)}",
        **body,
    }
    receipts.validate("runtime-trace-correlation.schema.json", document)
    return document
