"""Cedar adapter-edge tests that do not require an installed Cedar binary."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agentmem_ref import policy
from agentmem_ref.cedar_policy_comparator import (
    CEDAR_POLICY_SHA256,
    build_cedar_request,
    minimized_cedar_context,
    parse_cedar_authorize_output,
    policy_sha256,
    request_digest,
)
from agentmem_ref.enforcement_composition import build_projection


class CedarPolicyComparatorTests(unittest.TestCase):
    def _projection(self):
        proposal = policy.Proposal(
            proposal_id="proposal:cedar:minimize",
            actor_id="actor:test",
            charter_version="charter:v1",
            target_reference="mem:cedar:minimize",
            target_class=policy.M2,
            scope="scope:tenant-a/project-a",
            operation="promotion",
            current_strength="reinforced",
            proposed_strength="promoted",
            downstream_authority=policy.A1,
            reversibility="reversible",
            risk_class="low",
            evidence_refs=("evidence:cedar",),
            state_snapshot="v0",
            tenant_ref="tenant-a",
            purpose="cedar-allow",
            isolation_domain_refs=("scope:tenant-a/project-a",),
            project_ref="project-a",
        )
        return build_projection(proposal, policy.evaluate(proposal))

    def test_parse_allow_with_verbose_policy_id(self):
        parsed = parse_cedar_authorize_output(
            "\nALLOW\n\nnote: this decision was due to the following policies:\n  agent_memory_permit\n\n",
            0,
        )
        self.assertEqual(parsed["decision"], "allow")
        self.assertEqual(parsed["determining_policy_ids"], ("agent_memory_permit",))

    def test_parse_deny_exit_two_is_valid_policy_decision(self):
        parsed = parse_cedar_authorize_output(
            "\nDENY\n\nnote: this decision was due to the following policies:\n  agent_memory_deny_purpose\n\n",
            2,
        )
        self.assertEqual(parsed["decision"], "deny")
        self.assertEqual(parsed["determining_policy_ids"], ("agent_memory_deny_purpose",))

    def test_parse_rejects_missing_decision(self):
        with self.assertRaisesRegex(ValueError, "exactly one ALLOW or DENY"):
            parse_cedar_authorize_output("note: no policies applied\n", 0)

    def test_parse_rejects_ambiguous_decision(self):
        with self.assertRaisesRegex(ValueError, "exactly one ALLOW or DENY"):
            parse_cedar_authorize_output("ALLOW\nDENY\n", 0)

    def test_parse_rejects_decision_exit_mismatch(self):
        with self.assertRaisesRegex(ValueError, "decision/exit mismatch"):
            parse_cedar_authorize_output("DENY\n", 0)

    def test_policy_digest_is_pinned(self):
        self.assertEqual(policy_sha256(), CEDAR_POLICY_SHA256)

    def test_policy_digest_is_eol_independent(self):
        text = "permit(principal, action, resource);\n// line two\n"
        with tempfile.TemporaryDirectory() as tmp:
            lf = Path(tmp) / "lf.cedar"
            crlf = Path(tmp) / "crlf.cedar"
            lf.write_bytes(text.encode("utf-8"))
            crlf.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
            self.assertEqual(policy_sha256(lf), policy_sha256(crlf))

    def test_minimized_context_has_no_raw_payload_surface(self):
        projection = self._projection()
        minimized = minimized_cedar_context(projection)
        self.assertEqual(minimized["input_identity"], projection["input_identity"])
        self.assertEqual(minimized["purpose"], "cedar-allow")
        for forbidden in (
            "evidence_refs",
            "authority_refs",
            "raw_memory",
            "memory_content",
            "prompt",
            "hidden_reasoning",
        ):
            self.assertNotIn(forbidden, minimized)

    def test_request_binds_exact_projection_identity(self):
        projection = self._projection()
        request = build_cedar_request(projection)
        self.assertEqual(request["context"]["input_identity"], projection["input_identity"])
        self.assertEqual(request["principal"], 'Agent::"actor:test"')
        self.assertEqual(request["action"], 'Action::"promotion"')
        self.assertEqual(request["resource"], 'Memory::"mem:cedar:minimize"')
        self.assertTrue(request_digest(request).startswith("sha256:"))

    def test_request_digest_changes_with_bound_identity(self):
        first = self._projection()
        second = dict(first)
        second["input_identity"] = "sha256:" + "f" * 64
        self.assertNotEqual(
            request_digest(build_cedar_request(first)),
            request_digest(build_cedar_request(second)),
        )

    def test_minimized_request_does_not_adopt_authority_shaped_fields(self):
        projection = self._projection()
        projection.update(
            {
                "standing_authority": True,
                "approval": "granted",
                "execution_status": "executed",
                "enforcement_status": "enforced",
                "raw_memory": "secret",
            }
        )
        request = build_cedar_request(projection)
        context = request["context"]
        self.assertNotIn("standing_authority", context)
        self.assertNotIn("approval", context)
        self.assertNotIn("execution_status", context)
        self.assertNotIn("enforcement_status", context)
        self.assertNotIn("raw_memory", context)


if __name__ == "__main__":
    unittest.main()
