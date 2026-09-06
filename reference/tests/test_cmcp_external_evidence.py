"""Tests for cMCP inbound external-evidence normalization."""

from __future__ import annotations

import copy
import unittest
from datetime import datetime, timedelta, timezone

from agentmem_ref.cmcp_external_evidence import (
    CMCP_PEER,
    CMCP_RELEASE,
    CMCP_VERSION,
    build_cmcp_adapter_results,
    normalize_cmcp_claim,
)


class CmcpExternalEvidenceTests(unittest.TestCase):
    def _claim(self, *, mode: str = "enforce", platform: str = "software-only") -> dict:
        now = datetime.now(tz=timezone.utc).replace(microsecond=0)
        return {
            "cmcp_version": "1.0",
            "trace": {
                "eat_profile": "tag:agentrust-io.com,2026:trace-v0.2",
                "iat": int(now.timestamp()),
                "subject": "spiffe://cmcp.gateway/tee/abcdef0123456789",
                "runtime": {
                    "platform": platform,
                    "measurement": "sha256:" + "1" * 64,
                },
                "policy": {
                    "bundle_hash": "sha256:" + "2" * 64,
                    "enforcement_mode": mode,
                    "version": "policy-v1",
                },
                "data_class": "internal",
                "cnf": {
                    "jwk": {
                        "kty": "OKP",
                        "crv": "Ed25519",
                        "x": "dGVzdA",
                        "kid": "cmcp-abcdef01",
                    }
                },
            },
            "gateway": {
                "session_id": "session-1",
                "gateway_version": "0.4.0",
                "sequence_number": 1,
                "audit_chain": {
                    "root": "a" * 64,
                    "tip": "b" * 64,
                    "length": 1,
                },
                "call_summary": {},
                "catalog": {"hash": "sha256:" + "3" * 64, "drift_detected": False},
                "attestation_generated_at": now.isoformat(),
                "attestation_validity_seconds": 3600,
                "attestation_stale": False,
                "catalog_exceptions": [],
                "kill_switch_triggered": False,
            },
            "signature": "signed-but-not-copied",
        }

    def _verification(
        self,
        *,
        hardware: bool = False,
        failure: str | None = None,
        fresh: bool = True,
    ) -> dict:
        verified = [
            "schema",
            "signature",
            "trusted_public_key",
            "policy_bundle.hash",
            "tool_catalog.hash",
            "attestation_freshness",
            "audit_chain",
        ]
        unverified = []
        if hardware:
            verified.append("hardware_attestation")
        else:
            unverified.append("hardware_attestation")
        return {
            "status": "verified" if hardware and not failure else "partially_verified",
            "verified_fields": verified,
            "unverified_fields": unverified,
            "failure_reason": failure,
            "attestation_age_seconds": 1 if fresh else 7200,
            "is_attestation_fresh": fresh,
            "details": {},
        }

    def test_source_pin_and_two_claim_scopes(self):
        enforcement, attestation = build_cmcp_adapter_results(self._claim(), self._verification())
        self.assertEqual(enforcement["source_peer"], CMCP_PEER)
        self.assertEqual(enforcement["source_version"], CMCP_VERSION)
        self.assertEqual(enforcement["source_release_ref"], CMCP_RELEASE)
        self.assertEqual(enforcement["claim_type"], "enforcement")
        self.assertEqual(attestation["claim_type"], "attestation")

    def test_enforcement_mode_preserved_without_execution_claim(self):
        for mode in ("enforce", "advisory", "silent"):
            enforcement, _ = build_cmcp_adapter_results(
                self._claim(mode=mode), self._verification()
            )
            self.assertEqual(enforcement["enforcement_posture"], mode)
            self.assertNotIn("execution_posture", enforcement)
            self.assertEqual(enforcement["verification_status"], "verified")

    def test_software_only_attestation_remains_unknown(self):
        _, attestation = build_cmcp_adapter_results(self._claim(), self._verification())
        self.assertEqual(attestation["verification_status"], "unknown")
        self.assertEqual(attestation["attestation_mode"], "software_only_unverified")

    def test_hardware_verified_is_distinct(self):
        _, attestation = build_cmcp_adapter_results(
            self._claim(platform="tpm2"), self._verification(hardware=True)
        )
        self.assertEqual(attestation["verification_status"], "verified")
        self.assertEqual(attestation["attestation_mode"], "hardware_verified:tpm2")

    def test_invalid_hardware_evidence_fails_attestation_not_enforcement(self):
        result = self._verification(failure="HARDWARE_ATTESTATION_FAILED")
        enforcement, attestation = build_cmcp_adapter_results(
            self._claim(platform="tpm2"), result
        )
        self.assertEqual(enforcement["verification_status"], "verified")
        self.assertEqual(attestation["verification_status"], "failed")

    def test_signature_failure_invalidates_enforcement(self):
        result = self._verification(failure="SIGNATURE_INVALID")
        enforcement, _ = build_cmcp_adapter_results(self._claim(), result)
        self.assertEqual(enforcement["verification_status"], "failed")

    def test_policy_hash_failure_invalidates_enforcement(self):
        result = self._verification(failure="POLICY_HASH_MISMATCH")
        enforcement, _ = build_cmcp_adapter_results(self._claim(), result)
        self.assertEqual(enforcement["verification_status"], "failed")

    def test_unknown_peer_fields_and_raw_attestation_do_not_escape(self):
        claim = self._claim()
        claim["peer_says_pama_allow"] = True
        claim["gateway"]["attestation_evidence"] = {
            "raw_evidence": "TOP-SECRET-HARDWARE-BLOB",
            "quote_signature": "signature-bytes",
            "cert_chain": "certificate-chain",
        }
        claim["trace"]["tool_transcript"] = {
            "hash": "sha256:" + "4" * 64,
            "entries": [{"tool_name": "danger", "data_class": "secret", "decision": "allow"}],
        }
        enforcement, attestation = build_cmcp_adapter_results(claim, self._verification())
        rendered = repr((enforcement, attestation))
        self.assertNotIn("TOP-SECRET-HARDWARE-BLOB", rendered)
        self.assertNotIn("certificate-chain", rendered)
        self.assertNotIn("peer_says_pama_allow", rendered)
        self.assertNotIn("tool_name", rendered)

    def test_normalized_records_keep_authority_nonclaims(self):
        claim = self._claim()
        observed = datetime.now(tz=timezone.utc).isoformat()
        enforcement, attestation = normalize_cmcp_claim(
            claim, self._verification(), observed_at=observed
        )
        self.assertEqual(enforcement["applicability"]["status"], "applicable")
        self.assertEqual(attestation["applicability"]["status"], "insufficient_evidence")
        for record in (enforcement, attestation):
            self.assertEqual(record["interpretation"]["authority_effect"], "none")
            self.assertEqual(record["interpretation"]["memory_authority"], "not_established")
            self.assertEqual(record["interpretation"]["lifecycle_satisfaction"], "not_established")

    def test_stale_attestation_does_not_retroactively_expire_new_claim(self):
        claim = self._claim()
        old = datetime.now(tz=timezone.utc) - timedelta(days=2)
        claim["gateway"]["attestation_generated_at"] = old.isoformat()
        claim["gateway"]["attestation_validity_seconds"] = 3600
        observed = datetime.now(tz=timezone.utc).isoformat()
        enforcement, attestation = normalize_cmcp_claim(
            claim, self._verification(fresh=False), observed_at=observed
        )
        self.assertEqual(enforcement["freshness"]["status"], "current")
        self.assertEqual(enforcement["applicability"]["status"], "applicable")
        self.assertEqual(attestation["freshness"]["status"], "expired")
        self.assertEqual(attestation["applicability"]["status"], "stale")
        self.assertNotIn("expires_at", enforcement["freshness"])

    def test_identity_is_stable_for_same_claim_and_verification(self):
        claim = self._claim()
        observed = datetime.now(tz=timezone.utc).isoformat()
        first = normalize_cmcp_claim(claim, self._verification(), observed_at=observed)
        second = normalize_cmcp_claim(copy.deepcopy(claim), self._verification(), observed_at=observed)
        self.assertEqual(first[0]["evidence_id"], second[0]["evidence_id"])
        self.assertEqual(first[1]["evidence_id"], second[1]["evidence_id"])

    def test_invalid_enforcement_mode_fails_closed(self):
        claim = self._claim()
        claim["trace"]["policy"]["enforcement_mode"] = "magically-authoritative"
        with self.assertRaisesRegex(ValueError, "unsupported cMCP enforcement mode"):
            build_cmcp_adapter_results(claim, self._verification())


if __name__ == "__main__":
    unittest.main()
