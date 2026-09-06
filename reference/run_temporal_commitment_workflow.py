#!/usr/bin/env python3
"""Focused executable evidence for #259 / ADR-031."""

from __future__ import annotations

import argparse
import copy
import importlib.metadata
import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from agentmem_ref.temporal_commitment import (
    UOR_CONTENT_REFERENCE_PROFILE,
    address_temporal_commitment,
    build_external_witness_evidence,
    build_temporal_commitment,
    detect_linear_forks,
    evaluate_linear_order,
    evaluate_temporal_currentness,
    sign_temporal_commitment,
    verify_temporal_attestation,
    verify_witness_binding,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "reference" / "testdata" / "temporal-commitment-adversarial.json"
UOR_SOURCE_COMMIT = "d78f82f26034880e91b1d54c21900a33ab73f695"
UOR_RELEASE = "v0.2.0"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    from uor_addr import AddressError, kappa

    binding_version = importlib.metadata.version("uor-addr")
    if binding_version != "0.2.0":
        raise RuntimeError(f"unexpected uor-addr version: {binding_version}")

    def py_address(raw: bytes) -> str:
        try:
            return kappa.json_address(raw)
        except AddressError as exc:
            raise RuntimeError(str(exc)) from exc

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    base = fixture["base"]

    def build(material: dict, **ordering):
        return build_temporal_commitment(
            event_type=material["event_type"],
            subject_ref=material["subject_ref"],
            payload_digest=material["payload_digest"],
            temporal_claims=material["temporal_claims"],
            scope_ref=material["scope_ref"],
            domain_schema_ref=material["domain_schema_ref"],
            domain_schema_digest=material["domain_schema_digest"],
            projection_profile=material["projection_profile"],
            projection_version=material["projection_version"],
            **ordering,
        )

    root = build(
        base,
        ordering_mode="linear_stream",
        stream_ref="stream:alpha",
        sequence=0,
        predecessor_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
    )
    root_ref = address_temporal_commitment(root, address_fn=py_address)
    child = build(
        base,
        ordering_mode="linear_stream",
        stream_ref="stream:alpha",
        sequence=1,
        predecessor_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
        predecessor_refs=[root_ref],
    )
    child_ref = address_temporal_commitment(child, address_fn=py_address)

    changed_time = copy.deepcopy(base)
    changed_time["temporal_claims"]["event_time"] = "2026-08-13T19:05:00Z"
    changed_time_commitment = build(
        changed_time,
        ordering_mode="linear_stream",
        stream_ref="stream:alpha",
        sequence=1,
        predecessor_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
        predecessor_refs=[root_ref],
    )
    changed_time_ref = address_temporal_commitment(changed_time_commitment, address_fn=py_address)

    changed_profile = copy.deepcopy(base)
    changed_profile["projection_version"] = "0.2.0"
    changed_profile_commitment = build(
        changed_profile,
        ordering_mode="linear_stream",
        stream_ref="stream:alpha",
        sequence=1,
        predecessor_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
        predecessor_refs=[root_ref],
    )
    changed_profile_ref = address_temporal_commitment(changed_profile_commitment, address_fn=py_address)

    key = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(fixture["test_key"]["seed_hex"]))
    attestation = sign_temporal_commitment(
        content_ref=child_ref,
        private_key=key,
        key_ref=fixture["test_key"]["key_ref"],
        content_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
    )
    trusted = verify_temporal_attestation(attestation, public_key=key.public_key(), trust_status="trusted")
    untrusted = verify_temporal_attestation(attestation, public_key=key.public_key(), trust_status="untrusted")
    tampered = copy.deepcopy(attestation)
    tampered["content_ref"] = changed_time_ref
    tampered_result = verify_temporal_attestation(tampered, public_key=key.public_key(), trust_status="trusted")

    order = evaluate_linear_order(
        child,
        predecessor_commitment=root,
        address_fn=py_address,
        address_profile=UOR_CONTENT_REFERENCE_PROFILE,
    )
    wrong_order_profile = evaluate_linear_order(
        child,
        predecessor_commitment=root,
        address_fn=py_address,
        address_profile="test/wrong-reference-profile",
    )

    fork_material = copy.deepcopy(base)
    fork_material["payload_digest"] = "sha256:" + "7" * 64
    fork_child = build(
        fork_material,
        ordering_mode="linear_stream",
        stream_ref="stream:alpha",
        sequence=1,
        predecessor_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
        predecessor_refs=[root_ref],
    )
    fork_ref = address_temporal_commitment(fork_child, address_fn=py_address)
    forks = detect_linear_forks(
        [
            {"content_ref": root_ref, "commitment": root},
            {"content_ref": child_ref, "commitment": child},
            {"content_ref": fork_ref, "commitment": fork_child},
        ],
        address_fn=py_address,
        content_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
    )

    witness = build_external_witness_evidence(
        witness_profile="rfc3161-verified-by-host",
        subject_kind="temporal_commitment",
        subject_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
        subject_ref=child_ref,
        claim_kind="existence_by_time",
        verification_status="verified",
        witnessed_at="2026-08-13T19:01:00Z",
        proof_ref="evidence:test-witness:1",
    )
    witness_good = verify_witness_binding(
        witness,
        expected_subject_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
        expected_subject_ref=child_ref,
    )
    witness_wrong = verify_witness_binding(
        witness,
        expected_subject_reference_profile="test/wrong-reference-profile",
        expected_subject_ref=child_ref,
    )

    historical_before = copy.deepcopy(child)
    currentness = evaluate_temporal_currentness(
        commitment_reference_profile=UOR_CONTENT_REFERENCE_PROFILE,
        commitment_ref=child_ref,
        status="superseded",
        evaluated_at="2026-08-13T20:00:00Z",
        evidence_refs=["evidence:correction:temporal-1"],
        superseding_refs=[changed_time_ref],
    )

    checks = {
        "exact_uor_release_loaded": binding_version == "0.2.0",
        "uor_temporal_labels_are_distinct": root_ref != child_ref,
        "temporal_mutation_changes_identity": changed_time_ref != child_ref,
        "semantic_profile_mutation_changes_identity": changed_profile_ref != child_ref,
        "trusted_signature_is_valid": trusted["cryptographic_status"] == "valid",
        "signature_tamper_is_invalid": tampered_result["cryptographic_status"] == "invalid",
        "untrusted_signature_stays_non_authoritative": untrusted["cryptographic_status"] == "valid" and not untrusted["trusted_signer"] and untrusted["authority_effect"] == "none",
        "trusted_signature_does_not_establish_time_or_authority": trusted["trusted_time"] == "not_established" and trusted["authority_effect"] == "none",
        "local_order_valid": order["local_order_valid"] is True,
        "reference_profile_mismatch_is_rejected": wrong_order_profile["status"] == "invalid" and "predecessor_reference_profile_mismatch" in wrong_order_profile["reason_codes"],
        "linear_order_does_not_claim_complete_history": order["complete_history_proven"] is False,
        "linear_order_does_not_claim_non_equivocation": order["non_equivocation_proven"] is False,
        "fork_is_exposed_without_canonical_child": len(forks) == 1 and forks[0]["canonical_child"] is None,
        "witness_binds_exact_subject_and_profile": witness_good["bound"] is True and witness_wrong["bound"] is False,
        "witness_does_not_prove_event_occurrence_time": witness_good["event_occurrence_time_proven"] is False,
        "supersession_does_not_rewrite_historical_commitment": child == historical_before and currentness["interpretation"]["historical_commitment_mutated"] is False and currentness["interpretation"]["cryptographic_validity_changed"] is False,
    }

    report = {
        "schema_version": "1.0.0",
        "issue": 259,
        "research_issue": 258,
        "adr": "ADR-031",
        "agent_memory_commit": args.agent_memory_commit,
        "uor": {
            "release": UOR_RELEASE,
            "source_commit": UOR_SOURCE_COMMIT,
            "python_binding": f"uor-addr=={binding_version}",
            "content_reference_profile": UOR_CONTENT_REFERENCE_PROFILE,
            "cross_language_evidence_workflow": "UOR Addr Compatibility",
        },
        "temporal_objects": [
            {"id": "root", "content_ref": root_ref},
            {"id": "child", "content_ref": child_ref, "predecessor_reference_profile": UOR_CONTENT_REFERENCE_PROFILE, "predecessor_ref": root_ref},
            {"id": "child-time-mutated", "content_ref": changed_time_ref, "predecessor_ref": root_ref},
            {"id": "child-profile-mutated", "content_ref": changed_profile_ref, "predecessor_ref": root_ref},
        ],
        "checks": checks,
        "forks": forks,
        "currentness": currentness,
        "interpretation": {
            "content_identity_authority_effect": "none",
            "signature_authority_effect": "none",
            "witness_authority_effect": "none",
            "currentness_authority_effect": "none",
            "complete_history_claimed": False,
            "event_occurrence_time_proven_by_witness": False,
        },
        "metrics": {
            "check_count": len(checks),
            "failed_checks": sum(value is not True for value in checks.values()),
        },
    }
    Path(args.output).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if report["metrics"]["failed_checks"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
