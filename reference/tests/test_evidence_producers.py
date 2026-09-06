"""ADR-037 step 4b-1: modules produce evidence from what they already hold.

Written against the plausible wrong implementation. That one mints an
artifact_ref and a digest to satisfy the classifier, ships a verifier that
returns True, certifies its own evidence, tells producers apart by a label, and
proves the migration only at whichever risk class passes most easily.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

from agentmem_ref import dashclaw_external_verdict as dashclaw
from agentmem_ref import evidence_qualification as eq
from agentmem_ref import policy
from agentmem_ref import procedural_memory as pm
from agentmem_ref import reusable_grants as rg


def _skill(**kw):
    base = dict(
        skill_id="skill-1", version=1, purpose="p", scope="project",
        isolation_domain_refs=("d1",), required_isolation_domain_refs=("d1",),
        procedure_markdown="# steps", provenance_refs=("prov-1",),
    )
    base.update(kw)
    return pm.SkillArtifact(**base)


def _grant():
    return {
        "grant_id": "reusable-grant:seed",
        "proposal_id": "prop-1", "ratification_ref": "ratif-1",
        "ratifying_principal_ref": "human-1", "operation": "decision_overwrite",
        "scope_refs": ["project"], "policy_version_ref": "ref-p1",
        "issued_at": "2026-09-05T00:00:00Z", "evidence_refs": ["e1"],
    }


def _proposal(risk="low", **kw):
    base = dict(
        proposal_id="prop-1", actor_id="actor-1", charter_version="v1",
        target_reference="memory-1", target_class="semantic", scope="project",
        operation="write", current_strength=0.1, proposed_strength=0.2,
        downstream_authority=False, reversibility="reversible",
        risk_class=risk, evidence_refs=("e1",),
    )
    base.update(kw)
    return policy.Proposal(**base)


def _attestation(pid="prop-1"):
    return policy.ExternalVerification(
        bound_proposal_id=pid, verifier_principal_id="human-1",
        authority_kind=policy.HUMAN_CONFIRMATION, max_risk_class="critical",
    )


class ProceduralMemoryProducesRealEvidence(unittest.TestCase):
    """DoD 1, 2 -- LD1, LD2."""

    def _evidence(self, artifact):
        return pm.evidence_for(artifact)

    def test_evidence_is_artifact_bound_from_existing_material(self):
        artifact = _skill()
        (item,) = self._evidence(artifact)

        self.assertEqual(item.digest, artifact.content_sha256)
        self.assertEqual(item.artifact_ref, artifact.version_reference)
        self.assertEqual(eq.qualify(item).qualification_class, eq.ARTIFACT_BOUND)

    def test_a_real_verifier_reaches_verified(self):
        """DoD 2 / LD2. Targets `verified`, not the `asserted` low risk permits."""
        artifact = _skill()
        (item,) = self._evidence(artifact)
        registry = {pm.PAYLOAD_VERIFIER: pm.payload_verifier(artifact)}

        self.assertEqual(eq.qualify(item, verifiers=registry).binding_status, eq.VERIFIED)

    def test_a_tampered_payload_is_refuted_not_merely_unverified(self):
        """The verifier must be real, not a lambda returning True."""
        artifact = _skill()
        (item,) = self._evidence(artifact)
        tampered = replace(artifact, purpose="something else")
        registry = {pm.PAYLOAD_VERIFIER: pm.payload_verifier(tampered)}

        status = eq.qualify(item, verifiers=registry).binding_status
        self.assertEqual(status, eq.REFUTED)
        self.assertNotEqual(status, eq.ASSERTED)

    def test_an_unregistered_verifier_leaves_it_asserted(self):
        """Naming is not holding. The evaluator still decides (LD5)."""
        (item,) = self._evidence(_skill())
        self.assertEqual(eq.qualify(item, verifiers={}).binding_status, eq.ASSERTED)


class ReusableGrantsProducesRealEvidence(unittest.TestCase):
    """DoD 3 -- reusing Loop 6's tamper detection, not a new one."""

    def test_evidence_is_artifact_bound_from_grant_body_digest(self):
        grant = _grant()
        (item,) = rg.evidence_for(grant)

        self.assertEqual(item.digest, rg.grant_body_digest(grant))
        self.assertEqual(eq.qualify(item).qualification_class, eq.ARTIFACT_BOUND)

    def test_a_tampered_grant_body_is_refuted(self):
        grant = _grant()
        (item,) = rg.evidence_for(grant)
        # `operation` IS in _GRANT_BODY_KEYS, so editing it moves the digest.
        tampered = dict(grant, operation="something_else")
        registry = {rg.GRANT_BODY_VERIFIER: rg.grant_body_verifier(tampered)}

        self.assertEqual(eq.qualify(item, verifiers=registry).binding_status, eq.REFUTED)

    def test_an_untampered_grant_verifies(self):
        grant = _grant()
        (item,) = rg.evidence_for(grant)
        registry = {rg.GRANT_BODY_VERIFIER: rg.grant_body_verifier(grant)}

        self.assertEqual(eq.qualify(item, verifiers=registry).binding_status, eq.VERIFIED)


class DashClawSeparatesProducersByLineage(unittest.TestCase):
    """DoD 4, 4b -- LD4, audit V3. Lineage, never a label."""

    def _bound(self, authority=True):
        return dashclaw.BoundMutation(
            request_id="r1", input_identity="i1", org_id="o1", agent_id="a1",
            fact_text="the fact", content_sha256=dashclaw.sha256_text("the fact"),
            proposal=_proposal(), proposal_digest="sha256:pd",
            authority_resolved=authority,
            authority_evidence_ref="authority-grant:fixture" if authority else "",
            authority_reason="ok",
        )

    def test_provider_and_module_evidence_land_in_different_groups(self):
        items = dashclaw.evidence_for(self._bound())
        self.assertEqual(len(items), 2)

        analysis = eq.group_by_dependence(items)

        self.assertEqual(analysis.independent_group_count, 2)
        domains = {i.failure_domain for i in items}
        self.assertIn("dashclaw-provider-authority", domains)
        self.assertIn("agent-memory-mutation-content", domains)

    def test_evidence_item_gains_no_producer_field(self):
        """DoD 4b / audit V3. The tenth instance, declined.

        Loop 10 refused a principal field on EvidenceItem. Satisfying DoD 4 with
        a `produced_by` label would have reintroduced it.
        """
        fields = set(eq.EvidenceItem.__dataclass_fields__)
        for forbidden in ("produced_by", "producer", "principal", "actor_id",
                          "verifier_principal_id", "source_party"):
            self.assertNotIn(forbidden, fields)

    def test_the_content_verifier_is_real(self):
        items = dashclaw.evidence_for(self._bound())
        content = [i for i in items if i.verifier == dashclaw.CONTENT_VERIFIER][0]

        good = {dashclaw.CONTENT_VERIFIER: dashclaw.content_verifier("the fact")}
        bad = {dashclaw.CONTENT_VERIFIER: dashclaw.content_verifier("a different fact")}

        self.assertEqual(eq.qualify(content, verifiers=good).binding_status, eq.VERIFIED)
        self.assertEqual(eq.qualify(content, verifiers=bad).binding_status, eq.REFUTED)

    def test_unresolved_authority_yields_only_module_evidence(self):
        items = dashclaw.evidence_for(self._bound(authority=False))
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].failure_domain, "agent-memory-mutation-content")


class DischargeAtTheRiskClassesEachModuleConstructs(unittest.TestCase):
    """DoD 5, 5b -- audit V2. Not whichever class passes most easily."""

    def _skill_evidence(self, artifact, verified):
        registry = {pm.PAYLOAD_VERIFIER: pm.payload_verifier(artifact)} if verified else None
        return eq.group_by_dependence(pm.evidence_for(artifact), verifiers=registry)

    def test_procedural_memory_discharges_at_low_risk(self):
        artifact = _skill()
        analysis = self._skill_evidence(artifact, verified=False)

        decision = policy.evaluate_with_qualified_evidence(_proposal("low"), analysis)

        self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(decision.discharge_authority, policy.DELEGATED_POLICY)

    def test_procedural_memory_discharges_at_high_risk_only_with_both_axes(self):
        """The module constructs high-risk proposals too. R5 requires both."""
        artifact = _skill()
        analysis = self._skill_evidence(artifact, verified=True)

        decision = policy.evaluate_with_qualified_evidence(
            _proposal("high"), analysis, attestation=_attestation()
        )

        self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(decision.discharge_authority, policy.HUMAN_CONFIRMATION)

    def test_asserted_only_evidence_does_not_discharge_at_high_risk(self):
        """DoD 5b. The negative half -- a pass cannot come from a lenient ladder."""
        artifact = _skill()
        analysis = self._skill_evidence(artifact, verified=False)

        decision = policy.evaluate_with_qualified_evidence(
            _proposal("high"), analysis, attestation=_attestation()
        )

        self.assertNotEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertIn(policy.INSUFFICIENT_BINDING_STATUS, decision.reasons)

    def test_reusable_grant_evidence_discharges_at_high_risk_when_verified(self):
        grant = _grant()
        analysis = eq.group_by_dependence(
            rg.evidence_for(grant),
            verifiers={rg.GRANT_BODY_VERIFIER: rg.grant_body_verifier(grant)},
        )

        decision = policy.evaluate_with_qualified_evidence(
            _proposal("high"), analysis, attestation=_attestation()
        )

        self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)

    def test_dashclaw_evidence_discharges_at_high_risk_when_verified(self):
        mutation = dashclaw.BoundMutation(
            request_id="r1", input_identity="i1", org_id="o1", agent_id="a1",
            fact_text="the fact", content_sha256=dashclaw.sha256_text("the fact"),
            proposal=_proposal(), proposal_digest="sha256:pd",
            authority_resolved=True, authority_evidence_ref="authority-grant:fixture",
            authority_reason="ok",
        )
        analysis = eq.group_by_dependence(
            dashclaw.evidence_for(mutation),
            verifiers={dashclaw.CONTENT_VERIFIER: dashclaw.content_verifier("the fact")},
        )

        decision = policy.evaluate_with_qualified_evidence(
            _proposal("high"), analysis, attestation=_attestation()
        )

        self.assertEqual(decision.outcome, policy.ALLOW_WITH_LEDGER)


class ProducersProduceAndNothingMore(unittest.TestCase):
    """DoD 6, 7 -- LD3, LD5."""

    _MODULES = (pm, rg, dashclaw)

    def test_no_module_ships_a_verifier_registry(self):
        """Supplying an implementation is not holding the registry."""
        for module in self._MODULES:
            for name in dir(module):
                if name.startswith("_"):
                    continue
                value = getattr(module, name)
                if isinstance(value, dict) and any(
                    callable(v) for v in value.values()
                ):
                    self.fail(f"{module.__name__}.{name} looks like a verifier registry")

    def test_modules_export_verifier_implementations(self):
        self.assertTrue(callable(pm.payload_verifier))
        self.assertTrue(callable(rg.grant_body_verifier))
        self.assertTrue(callable(dashclaw.content_verifier))

    def test_no_producer_returns_a_decision(self):
        """LD3. Producing and certifying are different acts (R1)."""
        for produced in (pm.evidence_for(_skill()), rg.evidence_for(_grant())):
            for item in produced:
                self.assertIsInstance(item, eq.EvidenceItem)
                self.assertNotIsInstance(item, policy.Decision)


class TheMigrationIsAdditive(unittest.TestCase):
    """DoD 9, 10 -- LD6, LD7. 'Additive' is a checked claim."""

    def test_the_legacy_asserted_path_no_longer_discharges(self):
        """ADR-037 step 4b-2: expected semantic change (entry #24).

        Loop 13 asserted the legacy path still worked, which was the point of an
        additive migration. 4b-2 removes it, so the three producers' evidence
        paths are now the only way through -- which is what they were built for.
        """
        proposal = _proposal("low", review_satisfied=True, approval_refs=("approver-1",))
        self.assertEqual(policy.evaluate(proposal).outcome, policy.REQUIRE_REVIEW)

    def test_procedural_memory_still_sets_review_satisfied(self):
        """LD7. Removing it belongs to the flip, not here."""
        import inspect

        source = inspect.getsource(pm)
        self.assertIn("review_satisfied=True", source)


if __name__ == "__main__":
    unittest.main()
