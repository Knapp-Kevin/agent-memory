"""GAP-SEC-04: grant evaluation verifies against a record the presenter does not write.

A grant is content-addressed, so it attests to its own consistency and never to
its own authenticity: edit the body, recompute the id, and the artifact is
perfectly self-consistent. Loop 4's probe demonstrated exactly that, which is
why the operator chose to bind evaluation to independently-held ratification
evidence rather than ship a digest check.
"""
import copy
import unittest

from agentmem_ref import receipts
from agentmem_ref.reusable_grant_harness import (
    EXPIRES, ISSUED, OPERATION, POLICY, _proposal, projection,
)
from agentmem_ref.reusable_grants import (
    RatificationRegistry,
    evaluate_pama_with_reusable_grant,
    evaluate_reusable_grant,
    grant_body_digest,
    ratify_reusable_grant,
)


def _ratify(proposal_doc, registry=None, **overrides):
    kwargs = dict(
        ratification_ref="ratification:explicit:1",
        ratifying_principal_ref="principal:operator",
        ratifier_authority_evidence_ref="authority-evidence:operator:1",
        ratifier_authority_verified=True,
        approved_operation=proposal_doc["requested_operation"],
        approved_scope_refs=tuple(proposal_doc["scope_refs"]),
        approved_material_conditions=tuple(proposal_doc["material_conditions"]),
        policy_version_ref=proposal_doc["policy_version_ref"],
        issued_at=ISSUED,
        expires_at=EXPIRES,
        revocation_mechanism_ref=proposal_doc["revocation_mechanism_ref"],
        registry=registry,
    )
    kwargs.update(overrides)
    return ratify_reusable_grant(proposal_doc, **kwargs)


class RatificationAnchorTest(unittest.TestCase):
    def setUp(self):
        self.projection = projection("projection:sec04-anchor")
        self.proposal = _proposal(self.projection)
        self.registry = RatificationRegistry()
        self.grant = _ratify(self.proposal, registry=self.registry)

    def _evaluate(self, grant, **overrides):
        kwargs = dict(
            expected_operation=OPERATION,
            current_policy_version_ref=POLICY,
            observed_at=ISSUED,
            ratification_evidence_present=True,
            registry=self.registry,
        )
        kwargs.update(overrides)
        return evaluate_reusable_grant(grant, self.projection, **kwargs)

    def test_untampered_grant_verifies(self):
        """DoD 1."""
        result = self._evaluate(self.grant)
        self.assertEqual("current", result["status"])
        self.assertIn("ratification_evidence_verified", result["reasons"])

    def test_tampered_body_with_stale_id_is_caught_by_integrity(self):
        """DoD 2: the cheap tamper."""
        tampered = copy.deepcopy(self.grant)
        tampered["expires_at"] = "2030-01-01T00:00:00Z"
        result = self._evaluate(tampered)
        self.assertEqual("invalid", result["status"])
        self.assertIn("grant_body_tampered", result["reasons"])

    def test_recomputed_id_is_caught_because_it_was_never_ratified(self):
        """DoD 3 — the case that defeated the digest-only fix.

        Loop 4's probe tampered the expiry, recomputed grant_id, and evaluation
        returned `current` against a perfectly self-consistent artifact. The
        digest cannot catch this because it is a function of the thing being
        checked. The registration gate can.
        """
        tampered = copy.deepcopy(self.grant)
        tampered["expires_at"] = "2030-01-01T00:00:00Z"
        tampered["grant_id"] = grant_body_digest(tampered)
        self.assertEqual(tampered["grant_id"], grant_body_digest(tampered),
                         "precondition: the forged artifact is self-consistent")

        result = self._evaluate(tampered)
        self.assertEqual("invalid", result["status"])
        self.assertIn("ratification_evidence_unregistered", result["reasons"])
        self.assertNotIn("ratification_evidence_verified", result["reasons"])

    def test_the_forged_grant_cannot_obtain_a_registration(self):
        """DoD 3b: the actual control, tested directly.

        An implementation exposing a public `register(grant)` passes DoD 1-3 and
        fails here. Obtaining a record for the tampered values requires ratifying
        them, and ratification refuses an expiry beyond the proposed validity.
        """
        with self.assertRaises(ValueError):
            _ratify(self.proposal, registry=self.registry,
                    expires_at="2030-01-01T00:00:00Z")

    def test_registry_exposes_no_public_registration_method(self):
        """DoD 3c: the V1 defect must not return by later convenience."""
        public = {name for name in dir(self.registry) if not name.startswith("_")}
        self.assertEqual({"resolve"}, public)

    def test_unregistered_grant_is_invalid(self):
        """DoD 4: a grant no ratification in this registry produced."""
        other_registry = RatificationRegistry()
        unregistered = _ratify(
            _proposal(projection("projection:elsewhere")), registry=other_registry
        )
        result = evaluate_reusable_grant(
            unregistered, self.projection,
            expected_operation=OPERATION, current_policy_version_ref=POLICY,
            observed_at=ISSUED, ratification_evidence_present=True,
            registry=self.registry,
        )
        self.assertEqual("invalid", result["status"])
        self.assertIn("ratification_evidence_unregistered", result["reasons"])

    def test_registration_refuses_to_overwrite(self):
        """DoD 7: retained defence, not the anchoring property."""
        with self.assertRaises(ValueError):
            self.registry._record_ratification(self.grant)


class DeclaredHostProfileTest(unittest.TestCase):
    """DoD 5, 6: option D stays available and stays labelled."""

    def setUp(self):
        self.projection = projection("projection:sec04-profile")
        self.grant = _ratify(_proposal(self.projection))

    def _evaluate(self, **overrides):
        kwargs = dict(
            expected_operation=OPERATION, current_policy_version_ref=POLICY,
            observed_at=ISSUED, ratification_evidence_present=True,
        )
        kwargs.update(overrides)
        return evaluate_reusable_grant(self.grant, self.projection, **kwargs)

    def test_asserted_profile_is_current_but_labelled(self):
        result = self._evaluate()
        self.assertEqual("current", result["status"])
        self.assertIn("ratification_evidence_asserted", result["reasons"])
        self.assertNotIn("ratification_evidence_verified", result["reasons"])

    def test_asserting_false_is_still_invalid(self):
        result = self._evaluate(ratification_evidence_present=False)
        self.assertEqual("invalid", result["status"])
        self.assertIn("ratification_evidence_missing", result["reasons"])

    def test_silence_never_reads_as_verified(self):
        """Absence of a marker must not imply the stronger claim."""
        for result in (self._evaluate(),
                       self._evaluate(ratification_evidence_present=False)):
            self.assertNotIn("ratification_evidence_verified", result["reasons"])


class SchemaAndBridgeTest(unittest.TestCase):
    def setUp(self):
        self.projection = projection("projection:sec04-schema")
        self.registry = RatificationRegistry()
        self.grant = _ratify(_proposal(self.projection), registry=self.registry)

    def test_results_still_validate_against_the_unmodified_schema(self):
        """DoD 8: provenance rides `reasons`, so no schema change was needed."""
        for registry in (self.registry, None):
            result = evaluate_reusable_grant(
                self.grant, self.projection,
                expected_operation=OPERATION, current_policy_version_ref=POLICY,
                observed_at=ISSUED, ratification_evidence_present=True,
                registry=registry,
            )
            receipts.validate("reusable-grant-evaluation.schema.json", result)

    def test_bridge_still_refuses_external_verification(self):
        """DoD 9: LD5's restraint, verified rather than assumed."""
        from agentmem_ref import policy

        evaluation = evaluate_reusable_grant(
            self.grant, self.projection,
            expected_operation=OPERATION, current_policy_version_ref=POLICY,
            observed_at=ISSUED, ratification_evidence_present=True,
            registry=self.registry,
        )
        proposal = policy.Proposal(
            proposal_id="p", actor_id="agent:a", charter_version="v1",
            target_reference="mem:A", target_class=policy.M1,
            scope=evaluation["scope_refs"][0], operation=evaluation["operation"],
            current_strength="observed", proposed_strength="tentative",
            downstream_authority=policy.A1, reversibility="irreversible",
            risk_class="critical", evidence_refs=("ep-1",), tenant_ref="t",
        )
        baseline = policy.evaluate(proposal)
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, baseline.outcome)
        decision = evaluate_pama_with_reusable_grant(proposal, evaluation)
        self.assertEqual(policy.REQUIRE_EXTERNAL_VERIFICATION, decision.outcome)


if __name__ == "__main__":
    unittest.main()
