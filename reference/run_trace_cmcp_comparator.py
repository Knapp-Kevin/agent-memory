"""Execute P4.5c evidence through the released cMCP audit-bundle verifier.

Run this in an isolated environment containing the pinned external packages:

    cmcp-runtime==0.4.0
    agentrust-trace==0.9.0
    agent-manifest==0.11.2
    rfc8785==0.1.4

The isolation is intentional: cmcp-runtime 0.4.0's AGT dependency line resolves a
cryptography version below the P4.5a validation profile's cryptography==50.0.0.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.portable_evidence import IssuerKey, issue_evidence  # noqa: E402
from agentmem_ref.trace_action_evidence import (  # noqa: E402
    TraceReceiptIssuer,
    issue_trace_action_evidence,
)
from cmcp_verify import verify_audit_bundle  # type: ignore[import-not-found]  # noqa: E402


def _audit_entry(call_id: str, external_execution_evidence: dict) -> dict:
    entry = {
        "call_id": call_id,
        "external_execution_evidence": external_execution_evidence,
        "prev_entry_hash": "genesis",
    }
    entry["entry_hash"] = hashlib.sha256(
        json.dumps(entry, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()
    return entry


def main() -> None:
    expected_versions = {
        "cmcp-runtime": "0.4.0",
        "agentrust-trace": "0.9.0",
        "agent-manifest": "0.11.2",
        "rfc8785": "0.1.4",
    }
    actual_versions = {name: importlib.metadata.version(name) for name in expected_versions}
    if actual_versions != expected_versions:
        raise AssertionError(f"comparator version drift: {actual_versions!r}")

    am_key = IssuerKey(
        issuer_id="issuer:agent-memory-reference",
        key_id="am-key-p45c",
        private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33))),
        valid_from="2026-08-01T00:00:00Z",
        valid_until="2026-08-31T23:59:59Z",
    )
    runtime_issuer = TraceReceiptIssuer(
        issuer_id="spiffe://runtime.example/agent-memory-controller",
        private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(33, 65))),
    )
    receipt = {
        "schema_version": "1.0.0",
        "receipt_id": "receipt:p45c:cmcp",
        "requested_action": "permanent_deletion",
        "policy_version": "pama-2026-08",
        "permitted_actions": ["permanent_deletion"],
        "selected_action": "permanent_deletion",
        "selection_mode": "deterministic",
        "timestamp": "2026-08-11T21:10:01Z",
    }
    portable = issue_evidence(
        receipt,
        issuer_id=am_key.issuer_id,
        key=am_key,
        issued_at="2026-08-11T21:10:02Z",
        action_ref="action:p45c:cmcp",
        memory_action="permanent_deletion",
        governance_disposition="committed",
        policy_ref="policy:pama-2026-08",
        authority_state_ref="authority:rev-32",
        decision_time="2026-08-11T21:10:01Z",
        scope_ref="scope:opaque:p45c",
        before_state_ref="sha256:" + "3" * 64,
        after_state_ref="sha256:" + "4" * 64,
        lifecycle_result="residual",
        source_domain_ref="domain:opaque:source",
        destination_domain_ref="domain:opaque:deleted",
    )
    call_id = "call:p45c:cmcp"
    trace_bundle = issue_trace_action_evidence(
        portable,
        issuer=runtime_issuer,
        call_id=call_id,
        execution_outcome="accepted",
        execution_time="2026-08-11T21:10:03Z",
    )
    envelope = trace_bundle["external_execution_evidence"]
    key = runtime_issuer.trust_key()
    trusted = {key.key_id: key.raw_public_key}

    good = verify_audit_bundle(
        {"entries": [_audit_entry(call_id, envelope)]},
        external_evidence_keys=trusted,
    )
    if not good.verified:
        raise AssertionError(f"released cMCP verifier rejected P4.5c envelope: {good.failures}")

    replayed = copy.deepcopy(envelope)
    replayed["linked_call_id"] = "call:p45c:other"
    wrong_call = verify_audit_bundle(
        {"entries": [_audit_entry(call_id, replayed)]},
        external_evidence_keys=trusted,
    )
    if wrong_call.verified or not any("linked_call_id" in item for item in wrong_call.failures):
        raise AssertionError(f"released cMCP verifier did not reject wrong-call replay: {wrong_call.failures}")

    bad_signature = copy.deepcopy(envelope)
    bad_signature["signature"] = "A" * 86
    signature_result = verify_audit_bundle(
        {"entries": [_audit_entry(call_id, bad_signature)]},
        external_evidence_keys=trusted,
    )
    if signature_result.verified or not any("signature" in item for item in signature_result.failures):
        raise AssertionError(
            f"released cMCP verifier did not reject signature tamper: {signature_result.failures}"
        )

    unknown_key = verify_audit_bundle(
        {"entries": [_audit_entry(call_id, envelope)]},
        external_evidence_keys={},
    )
    if unknown_key.verified or not any("no trusted key" in item for item in unknown_key.failures):
        raise AssertionError(f"released cMCP verifier did not fail closed on missing trust: {unknown_key.failures}")

    print(
        json.dumps(
            {
                "comparator": "cmcp_verify.verify_audit_bundle",
                "versions": actual_versions,
                "valid_envelope": good.verified,
                "wrong_call_rejected": not wrong_call.verified,
                "signature_tamper_rejected": not signature_result.verified,
                "unknown_key_rejected": not unknown_key.verified,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
