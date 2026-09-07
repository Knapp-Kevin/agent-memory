"""Dependency-free Agent Manifest external-evidence adapter tests for issue #223."""

from __future__ import annotations

import copy
import unittest

from agentmem_ref import policy
from agentmem_ref.agent_manifest_external_evidence import (
    AGENT_MANIFEST_PEER,
    AGENT_MANIFEST_RELEASE,
    AGENT_MANIFEST_VERSION,
    build_agent_manifest_adapter_results,
    normalize_agent_manifest_evidence,
)


class AgentManifestExternalEvidenceTests(unittest.TestCase):
    def _manifest(self, *, expires_at: str = "2026-09-13T06:30:00Z") -> dict:
        return {
            "manifest_id": "018f4a3b-2c1d-7e5f-a8b9-0d1e2f3a4b5c",
            "agent_id": "spiffe://trust.example/agent/memory/prod",
            "issuer": "spiffe://trust.example/issuer/security",
            "version": "0.2",
            "issued_at": "2026-08-13T06:30:00Z",
            "expires_at": expires_at,
            "crypto_profile": "standard",
            "artifacts": {
                "system_prompt": {"hash": "sha256:" + "a" * 64},
                "policy_bundle": {"hash": "sha256:" + "b" * 64},
                "tool_manifest": {"catalog_hash": "sha256:" + "c" * 64},
                "model_identity": {
                    "provider": "fixture",
                    "model_id": "fixture-model",
                    "version": "fixture-model-v1",
                    "deployment_type": "api",
                },
                "memory_baseline": {
                    "snapshot_hash": "sha256:" + "d" * 64,
                },
            },
            "peer_says_pama_allow": True,
            "raw_system_prompt": "SECRET PROMPT CONTENT MUST NOT ESCAPE",
        }

    def _verification(
        self,
        *,
        overall: str = "VALID",
        signature_verified: bool = True,
        attestation_verified: bool = False,
        memory_status: str = "MATCH",
    ) -> dict:
        return {
            "verification_id": "verify-1",
            "result": overall,
            "signature_verified": signature_verified,
            "attestation_verified": attestation_verified,
            "fields_verified": {
                "system_prompt": "MATCH",
                "policy_bundle": "MATCH",
                "tool_manifest": "MATCH",
                "model_identity": "MATCH",
                "rag_corpus": "NOT_BOUND",
                "memory_baseline": memory_status,
                "decision_trace": "NOT_BOUND",
                "supply_chain": "NOT_BOUND",
                "delegation_chain": "NOT_PRESENT",
                "hitl_record": "NOT_REQUIRED",
            },
            "mismatch_details": [],
            "warnings": [],
        }

    def _normalized(self, **verification_overrides):
        return normalize_agent_manifest_evidence(
            self._manifest(),
            self._verification(**verification_overrides),
            observed_at="2026-08-13T06:31:00Z",
            envelope_digest="sha256:" + "e" * 64,
            signer_id="key:ed25519:test",
        )

    def test_source_pin_and_three_claim_scopes(self):
        identity, configuration, attestation = build_agent_manifest_adapter_results(
            self._manifest(),
            self._verification(),
            envelope_digest="sha256:" + "e" * 64,
            signer_id="key:ed25519:test",
        )
        self.assertEqual(identity["source_peer"], AGENT_MANIFEST_PEER)
        self.assertEqual(identity["source_version"], AGENT_MANIFEST_VERSION)
        self.assertEqual(identity["source_release_ref"], AGENT_MANIFEST_RELEASE)
        self.assertEqual(identity["claim_type"], "identity")
        self.assertEqual(configuration["claim_type"], "runtime_configuration")
        self.assertEqual(attestation["claim_type"], "attestation")

    def test_valid_identity_and_configuration_are_applicable_but_attestation_is_not(self):
        identity, configuration, attestation = self._normalized()
        self.assertEqual(identity["applicability"]["status"], "applicable")
        self.assertEqual(configuration["applicability"]["status"], "applicable")
        self.assertEqual(attestation["applicability"]["status"], "insufficient_evidence")
        self.assertEqual(attestation["claim"]["attestation_mode"], "not_established")

    def test_hardware_attestation_is_separate_when_verified(self):
        identity, configuration, attestation = self._normalized(attestation_verified=True)
        self.assertEqual(identity["applicability"]["status"], "applicable")
        self.assertEqual(configuration["applicability"]["status"], "applicable")
        self.assertEqual(attestation["applicability"]["status"], "applicable")
        self.assertEqual(attestation["claim"]["attestation_mode"], "hardware_verified")

    def test_configuration_mismatch_does_not_erase_verified_identity(self):
        identity, configuration, attestation = self._normalized(
            overall="MISMATCH",
            memory_status="MISMATCH",
        )
        self.assertEqual(identity["verification"]["status"], "verified")
        self.assertEqual(identity["applicability"]["status"], "applicable")
        self.assertEqual(configuration["verification"]["status"], "failed")
        self.assertEqual(configuration["applicability"]["status"], "invalid")
        self.assertEqual(attestation["applicability"]["status"], "insufficient_evidence")

    def test_unverifiable_signature_never_becomes_applicable_identity(self):
        identity, configuration, _ = self._normalized(
            overall="UNVERIFIABLE",
            signature_verified=False,
        )
        self.assertEqual(identity["verification"]["status"], "unknown")
        self.assertEqual(identity["applicability"]["status"], "insufficient_evidence")
        self.assertEqual(configuration["applicability"]["status"], "insufficient_evidence")

    def test_revoked_manifest_is_stale_even_with_valid_signature_and_matching_configuration(self):
        identity, configuration, _ = self._normalized(overall="REVOKED")
        self.assertEqual(identity["verification"]["status"], "verified")
        self.assertEqual(identity["revocation"]["status"], "revoked")
        self.assertEqual(identity["applicability"]["status"], "stale")
        self.assertEqual(configuration["applicability"]["status"], "stale")

    def test_expired_manifest_is_stale_without_turning_expiry_into_signature_failure(self):
        manifest = self._manifest(expires_at="2026-08-13T06:30:30Z")
        identity, configuration, _ = normalize_agent_manifest_evidence(
            manifest,
            self._verification(overall="EXPIRED"),
            observed_at="2026-08-13T06:31:00Z",
        )
        self.assertEqual(identity["verification"]["status"], "verified")
        self.assertEqual(identity["freshness"]["status"], "expired")
        self.assertEqual(identity["applicability"]["status"], "stale")
        self.assertEqual(configuration["applicability"]["status"], "stale")

    def test_memory_baseline_is_only_configuration_evidence(self):
        identity, configuration, _ = self._normalized()
        rendered = repr((identity, configuration))
        self.assertIn("agent-manifest:memory-baseline:sha256:", rendered)
        self.assertNotIn("canonical_memory", rendered)
        self.assertNotIn("current_memory", rendered)
        self.assertEqual(configuration["interpretation"]["memory_authority"], "not_established")
        self.assertEqual(configuration["interpretation"]["lifecycle_satisfaction"], "not_established")

    def test_unknown_peer_authority_and_raw_artifacts_do_not_escape(self):
        identity, configuration, attestation = build_agent_manifest_adapter_results(
            self._manifest(), self._verification()
        )
        rendered = repr((identity, configuration, attestation))
        self.assertNotIn("peer_says_pama_allow", rendered)
        self.assertNotIn("SECRET PROMPT CONTENT MUST NOT ESCAPE", rendered)
        self.assertNotIn("raw_system_prompt", rendered)

    def test_normalized_records_keep_explicit_authority_nonclaims(self):
        for record in self._normalized():
            self.assertEqual(record["interpretation"]["authority_effect"], "none")
            self.assertEqual(record["interpretation"]["memory_authority"], "not_established")
            self.assertEqual(record["interpretation"]["semantic_correctness"], "not_established")
            self.assertEqual(record["interpretation"]["lifecycle_satisfaction"], "not_established")

    def test_same_valid_manifest_evidence_cannot_widen_high_consequence_pama(self):
        identity, configuration, _ = self._normalized()
        evidence_refs = (identity["evidence_id"], configuration["evidence_id"])

        low = policy.evaluate(
            policy.Proposal(
                proposal_id="proposal:low-read",
                actor_id="agent:test",
                charter_version="v1",
                target_reference="memory:low",
                target_class=policy.M0,
                scope="scope:project-a",
                operation="runtime_assembly",
                current_strength="transient",
                proposed_strength="transient",
                downstream_authority=policy.A0,
                reversibility="reversible",
                risk_class="low",
                evidence_refs=evidence_refs,
            )
        )
        high = policy.evaluate(
            policy.Proposal(
                proposal_id="proposal:critical-scope-expansion",
                actor_id="agent:test",
                charter_version="v1",
                target_reference="memory:high",
                target_class=policy.M5,
                scope="scope:project-a",
                operation="scope_expansion",
                current_strength="project",
                proposed_strength="cross_tenant",
                downstream_authority=policy.A5,
                reversibility="irreversible",
                risk_class="critical",
                evidence_refs=evidence_refs,
            )
        )

        self.assertEqual(low.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(high.outcome, policy.BLOCK)
        self.assertNotIn("scope_expansion", high.permitted_actions)
        self.assertIn("scope_expansion", high.prohibited_actions)

    def test_evidence_identity_is_stable_for_same_inputs(self):
        first = self._normalized()
        second = normalize_agent_manifest_evidence(
            copy.deepcopy(self._manifest()),
            copy.deepcopy(self._verification()),
            observed_at="2026-08-13T06:31:00Z",
            envelope_digest="sha256:" + "e" * 64,
            signer_id="key:ed25519:test",
        )
        self.assertEqual([record["evidence_id"] for record in first], [record["evidence_id"] for record in second])


if __name__ == "__main__":
    unittest.main()
