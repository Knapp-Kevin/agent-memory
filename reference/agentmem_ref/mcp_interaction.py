"""Governed Model Context Protocol interaction evidence for issue #190.

MCP supplies transport/runtime facts about tool and resource interactions.  This
module preserves those facts as minimized evidence without treating request IDs,
server identity, successful results, or resource content as Agent Memory
authority, execution proof, durable memory, or lifecycle satisfaction.
"""

from __future__ import annotations

import hashlib
import re

import rfc8785

from . import receipts

PROFILE_VERSION = "0.1.0"
MCP_REVISION = "2026-07-28"
MCP_SOURCE_COMMIT = "5f5440bb26a62e2cf3440b92da5a667efa03b267"
MCP_SOURCE_REF = (
    "github://modelcontextprotocol/modelcontextprotocol/"
    + MCP_SOURCE_COMMIT
    + "/docs/specification/2026-07-28"
)

INTERACTION_METHODS = {
    "tool_call": "tools/call",
    "resource_read": "resources/read",
}
MEMORY_EFFECTS = {"none", "memory_candidate", "durable_mutation"}
REQUEST_STATUSES = {"observed", "not_observed"}
RESULT_STATUSES = {"complete", "input_required", "mcp_error", "unavailable", "not_observed"}
RESULT_CLASSIFICATIONS = {
    "success",
    "tool_error",
    "protocol_error",
    "input_required",
    "unavailable",
    "not_observed",
}
GOVERNANCE_STATUSES = {"available", "unavailable", "not_required"}
EFFECTIVE_DECISIONS = {"allow", "warn", "require_approval", "deny"}
_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _sha256_ref(value: dict) -> str:
    return "sha256:" + hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def _require_ref(name: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _require_digest(name: str, value: object) -> str:
    if not isinstance(value, str) or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase sha256 digest reference")
    return value


def _require_request_id(value: object) -> str | int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("request_id must be a non-empty string or integer")
    if isinstance(value, str) and not value:
        raise ValueError("request_id must be a non-empty string or integer")
    return value


def _validate_result_combination(result_status: str, result_classification: str, result_digest: object) -> str | None:
    allowed = {
        "complete": {"success", "tool_error"},
        "input_required": {"input_required"},
        "mcp_error": {"protocol_error"},
        "unavailable": {"unavailable"},
        "not_observed": {"not_observed"},
    }
    if result_classification not in allowed[result_status]:
        raise ValueError(
            f"result_classification {result_classification!r} is inconsistent with result_status {result_status!r}"
        )
    if result_status in {"complete", "input_required", "mcp_error"}:
        return _require_digest("result_digest", result_digest)
    if result_digest is not None:
        raise ValueError("unavailable/not_observed results must not claim a result_digest")
    return None


def _binding(adapter_result: dict, expected_context: dict | None, memory_effect: str) -> tuple[str, list[str]]:
    if expected_context is None:
        if memory_effect == "durable_mutation":
            return "mismatch", ["expected_context_missing"]
        return "not_evaluated", []
    if not isinstance(expected_context, dict):
        raise ValueError("expected_context must be an object when provided")

    reasons: list[str] = []
    fields = ("action_ref", "input_identity", "scope_ref", "tenant_ref", "project_ref")
    for field in fields:
        expected = expected_context.get(field)
        if expected is None:
            continue
        observed = adapter_result.get(field)
        if observed is None:
            reasons.append(f"{field}_missing")
        elif observed != expected:
            reasons.append(f"{field}_mismatch")

    if memory_effect == "durable_mutation":
        for required in ("action_ref", "input_identity", "scope_ref"):
            if expected_context.get(required) is None:
                reasons.append(f"expected_{required}_missing")
            elif adapter_result.get(required) is None and f"{required}_missing" not in reasons:
                reasons.append(f"{required}_missing")

    return ("mismatch", reasons) if reasons else ("exact", [])


def _governance_alignment(
    *,
    memory_effect: str,
    governance_status: str,
    effective_decision: str | None,
    result_status: str,
) -> str:
    if memory_effect != "durable_mutation":
        return "not_applicable" if governance_status == "not_required" else "not_evaluated"
    if governance_status != "available":
        return "blocked_governance_unavailable"
    assert effective_decision is not None
    if effective_decision == "deny":
        if result_status in {"complete", "input_required", "mcp_error"}:
            return "result_observed_under_deny"
        return "within_governance"
    if effective_decision == "require_approval":
        # MCP evidence cannot prove approval satisfaction.  That remains the
        # execution-witness/approval-evidence boundary from #187/#152.
        return "approval_not_established"
    return "within_governance"


def normalize_mcp_interaction(adapter_result: dict, expected_context: dict | None = None) -> dict:
    """Normalize one MCP tools/call or resources/read interaction.

    Unknown peer/runtime fields are intentionally discarded.  Callers may pass
    raw arguments/results to their own adapter long enough to compute digests,
    but this normalizer neither requires nor copies those payloads.
    """

    if not isinstance(adapter_result, dict):
        raise ValueError("adapter_result must be an object")

    revision = adapter_result.get("protocol_revision")
    source_commit = adapter_result.get("protocol_source_commit")
    if revision != MCP_REVISION:
        raise ValueError(f"unsupported MCP protocol revision {revision!r}")
    if source_commit != MCP_SOURCE_COMMIT:
        raise ValueError("MCP protocol source commit does not match the pinned stable revision")

    interaction_kind = adapter_result.get("interaction_kind")
    if interaction_kind not in INTERACTION_METHODS:
        raise ValueError(f"invalid interaction_kind {interaction_kind!r}")
    method = adapter_result.get("method")
    if method != INTERACTION_METHODS[interaction_kind]:
        raise ValueError(f"method {method!r} does not match interaction_kind {interaction_kind!r}")

    memory_effect = adapter_result.get("memory_effect")
    if memory_effect not in MEMORY_EFFECTS:
        raise ValueError(f"invalid memory_effect {memory_effect!r}")
    request_status = adapter_result.get("request_status")
    if request_status not in REQUEST_STATUSES:
        raise ValueError(f"invalid request_status {request_status!r}")
    result_status = adapter_result.get("result_status")
    if result_status not in RESULT_STATUSES:
        raise ValueError(f"invalid result_status {result_status!r}")
    result_classification = adapter_result.get("result_classification")
    if result_classification not in RESULT_CLASSIFICATIONS:
        raise ValueError(f"invalid result_classification {result_classification!r}")
    if request_status == "not_observed" and result_status not in {"not_observed", "unavailable"}:
        raise ValueError("an unobserved request cannot claim an observed MCP result")

    governance_status = adapter_result.get("governance_status")
    if governance_status not in GOVERNANCE_STATUSES:
        raise ValueError(f"invalid governance_status {governance_status!r}")
    effective_decision = adapter_result.get("effective_decision")
    if governance_status == "available":
        if effective_decision not in EFFECTIVE_DECISIONS:
            raise ValueError("available governance requires a valid effective_decision")
    elif effective_decision is not None:
        raise ValueError("effective_decision requires governance_status='available'")
    if memory_effect == "durable_mutation" and governance_status == "not_required":
        raise ValueError("durable mutation cannot declare governance not required")

    result_digest = _validate_result_combination(
        result_status,
        result_classification,
        adapter_result.get("result_digest"),
    )
    mcp_error_code = adapter_result.get("mcp_error_code")
    if result_status == "mcp_error":
        if isinstance(mcp_error_code, bool) or not isinstance(mcp_error_code, int):
            raise ValueError("mcp_error result requires integer mcp_error_code")
    elif mcp_error_code is not None:
        raise ValueError("mcp_error_code is only valid for mcp_error results")

    body: dict = {
        "protocol": {
            "name": "mcp",
            "revision": MCP_REVISION,
            "source_ref": _require_ref(
                "protocol_source_ref",
                adapter_result.get("protocol_source_ref", MCP_SOURCE_REF),
            ),
            "source_commit": MCP_SOURCE_COMMIT,
        },
        "interaction_kind": interaction_kind,
        "method": method,
        "client_ref": _require_ref("client_ref", adapter_result.get("client_ref")),
        "server_ref": _require_ref("server_ref", adapter_result.get("server_ref")),
        "request_id": _require_request_id(adapter_result.get("request_id")),
        "target_ref": _require_ref("target_ref", adapter_result.get("target_ref")),
        "memory_effect": memory_effect,
        "request_status": request_status,
        "result_status": result_status,
        "result_classification": result_classification,
        "governance_status": governance_status,
        "request_digest": _require_digest("request_digest", adapter_result.get("request_digest")),
        "observed_at": _require_ref("observed_at", adapter_result.get("observed_at")),
        "evidence_refs": list(dict.fromkeys(adapter_result.get("evidence_refs", ()))),
        "interpretation": {
            "authority_effect": "none",
            "memory_admission": "not_established",
            "execution_claim": "not_established",
            "lifecycle_satisfaction": "not_established",
            "request_id_authority": "none",
            "server_identity_authority": "none",
        },
    }
    if not all(isinstance(value, str) and value for value in body["evidence_refs"]):
        raise ValueError("evidence_refs must contain non-empty strings")

    if effective_decision is not None:
        body["effective_decision"] = effective_decision
    if result_digest is not None:
        body["result_digest"] = result_digest
    if mcp_error_code is not None:
        body["mcp_error_code"] = mcp_error_code

    optional_refs = (
        "session_ref",
        "transport_ref",
        "action_ref",
        "input_identity",
        "scope_ref",
        "tenant_ref",
        "project_ref",
        "pama_decision_ref",
        "composition_ref",
        "approval_evidence_ref",
        "execution_witness_ref",
        "trace_correlation_ref",
    )
    for name in optional_refs:
        value = adapter_result.get(name)
        if value is None:
            continue
        if name == "input_identity":
            body[name] = _require_digest(name, value)
        else:
            body[name] = _require_ref(name, value)

    binding_status, binding_reasons = _binding(adapter_result, expected_context, memory_effect)
    body["binding_status"] = binding_status
    body["binding_reasons"] = binding_reasons
    if memory_effect == "durable_mutation" and binding_status == "mismatch":
        body["governance_alignment"] = "binding_mismatch"
    else:
        body["governance_alignment"] = _governance_alignment(
            memory_effect=memory_effect,
            governance_status=governance_status,
            effective_decision=effective_decision,
            result_status=result_status,
        )

    identity_body = {key: value for key, value in body.items() if key != "observed_at"}
    document = {
        "schema_version": "1.0.0",
        "profile_version": PROFILE_VERSION,
        "interaction_id": f"mcp-interaction:{_sha256_ref(identity_body)}",
        **body,
    }
    receipts.validate("mcp-interaction-evidence.schema.json", document)
    return document
