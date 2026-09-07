"""Sprint 4a (LD6): DoD 20 at the public surface -- every entry point that can reach a governed
mutation forwards the caller's evidence and attestation unchanged, or parks; the read-only stages
call neither seam. Asserted by driving each function through a recording adapter, not by reading
source."""

from __future__ import annotations

import inspect
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.api import surface  # noqa: E402
from agentmem_ref.adapter import GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402
from tests.qualified_fixtures import corpus_for, rule  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
EXAMPLE = json.loads((REPO / "reference/fixtures/api/proposal-envelope.example.json").read_text(encoding="utf-8"))
ORG = "org:example"
WRITERS = {"commit": surface.commit, "forget": surface.forget}
READERS = {"propose": surface.propose, "approve": surface.approve, "recall": surface.recall, "history": surface.history, "posture": surface.posture}
# Sprint 4c-2: `authorize` forwards evidence and attestation to the adapter's evaluator and binds through
# `apply_action_governance`; `witness` consumes an authorization at `record_runtime_execution`. Neither is a
# reader (both retain state) and neither reaches a mutation seam.
AUTHORITY = {"authorize": surface.authorize, "witness": surface.witness}
ACTION = json.loads((REPO / "reference/fixtures/api/action-envelope.example.json").read_text(encoding="utf-8"))
OBSERVATION = json.loads((REPO / "reference/fixtures/api/execution-observation.example.json").read_text(encoding="utf-8"))


class RecordingAdapter(GovernedMemoryAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls: list[tuple[str, object, object]] = []
        self.evaluations: list[tuple[object, object]] = []

    def commit_proposal(self, proposal, fact_text, *args, **kwargs):
        self.calls.append(("commit_proposal", kwargs.get("evidence"), kwargs.get("attestation")))
        return super().commit_proposal(proposal, fact_text, *args, **kwargs)

    def governed_delete(self, *args, **kwargs):
        self.calls.append(("governed_delete", kwargs.get("evidence"), kwargs.get("external_verification")))
        return super().governed_delete(*args, **kwargs)

    def evaluate_proposal(self, proposal, *, evidence=None, attestation=None):
        self.evaluations.append((evidence, attestation))
        return super().evaluate_proposal(proposal, evidence=evidence, attestation=attestation)


def _medium_correction(target: str) -> dict:
    return {**EXAMPLE, "target_reference": target, "operation": "correction", "risk_class": "medium", "state_snapshot": "v1"}


class PublicSurfaceForwardsOrParks(unittest.TestCase):
    def setUp(self):
        self.memory = RecordingAdapter(InMemoryTemporalGraph(), tenant=ORG)
        seed = surface.commit(self.memory, EXAMPLE, "release branch release")
        self.assertTrue(seed["committed"])
        self.memory.calls.clear()
        self.target = EXAMPLE["target_reference"]

    def test_every_public_function_is_classified(self):
        self.assertEqual(set(surface.__all__), set(WRITERS) | set(READERS) | set(AUTHORITY))

    def test_writers_forward_evidence_and_attestation_unchanged(self):
        corpus = corpus_for(rule(rule_id="rule:api-dod20", target=self.target, criterion="value-correction",
                                 from_state="release branch release", to_values=("release branch main",)))
        evidence = corpus.evidence_for(target_reference=self.target, criterion="value-correction",
                                       pre_state="release branch release", proposed_value="release branch main")
        attestation = policy.ExternalVerification(bound_proposal_id=EXAMPLE["proposal_id"], verifier_principal_id="human:reviewer",
                                                  authority_kind=policy.HUMAN_CONFIRMATION, max_risk_class="critical")
        for name, fn in WRITERS.items():
            with self.subTest(function=name):
                self.memory.calls.clear()
                envelope = _medium_correction(self.target)
                args = (self.memory, envelope, "release branch main") if name == "commit" else (self.memory, envelope)
                fn(*args, evidence=evidence, attestation=attestation)
                (seam, seen_evidence, seen_attestation), = self.memory.calls
                self.assertEqual(list(seen_evidence), list(evidence), seam)
                self.assertIs(seen_attestation, attestation, seam)

    def test_writers_park_at_medium_without_evidence(self):
        for name, fn in WRITERS.items():
            with self.subTest(function=name):
                self.memory.calls.clear()
                envelope = _medium_correction(self.target)
                args = (self.memory, envelope, "release branch main") if name == "commit" else (self.memory, envelope)
                result = fn(*args)
                (seam, seen_evidence, seen_attestation), = self.memory.calls
                self.assertIsNone(seen_evidence); self.assertIsNone(seen_attestation)
                self.assertFalse(result["committed"])
                self.assertEqual(result["outcome"], policy.REQUIRE_REVIEW)

    def test_readers_reach_no_mutation_seam(self):
        recall_context = json.loads((REPO / "reference/fixtures/api/recall-context.example.json").read_text(encoding="utf-8"))
        surface.propose(self.memory, _medium_correction(self.target))
        surface.approve(self.memory, _medium_correction(self.target))
        surface.recall(self.memory, "release branch", recall_context)
        surface.history(self.memory, {"contract_version": "1.1.0", "target_reference": self.target})
        posture = surface.posture(REPO / "reference/fixtures/runtime-configuration/reference-composed-runtime.json")
        self.assertEqual(posture["stage"], "posture")
        self.assertNotIn("memory", inspect.signature(surface.posture).parameters)  # posture takes no adapter: structurally read-only
        self.assertEqual(self.memory.calls, [])
        self.assertEqual(self.memory.state_version(self.target), 1)

    def test_authority_stages_reach_no_mutation_seam(self):
        bound = surface.authorize(self.memory, ACTION)
        self.assertTrue(bound["action_authority"]["bound"])
        witnessed = surface.witness(self.memory, OBSERVATION)
        self.assertEqual(witnessed["witness"]["decision_alignment"], "consistent")
        self.assertEqual(self.memory.calls, [])

    def test_authorize_forwards_evidence_and_attestation_unchanged(self):
        attestation = policy.ExternalVerification(bound_proposal_id=ACTION["proposal_id"], verifier_principal_id="human:reviewer",
                                                  authority_kind=policy.HUMAN_CONFIRMATION, max_risk_class="critical")
        from agentmem_ref import procedural_memory as pm
        skill = pm.SkillArtifact(skill_id="release-workflow", version=1, purpose="release", scope="project", isolation_domain_refs=("project:example",),
                                 required_isolation_domain_refs=("project:example",), procedure_markdown="- cut", provenance_refs=("prov-1",))
        evidence = list(pm.evidence_for(skill))
        self.memory.evaluations.clear()
        surface.authorize(self.memory, {**ACTION, "risk_class": "medium"}, evidence=evidence, attestation=attestation)
        (seen_evidence, seen_attestation), = self.memory.evaluations
        self.assertEqual(list(seen_evidence), list(evidence))
        self.assertIs(seen_attestation, attestation)

    def test_authorize_parks_at_medium_without_evidence(self):
        result = surface.authorize(self.memory, {**ACTION, "risk_class": "medium"})
        self.assertEqual(result["outcome"], policy.REQUIRE_REVIEW)
        self.assertFalse(result["action_authority"]["bound"])
        self.assertEqual(result["action_authority"]["requirement"], "enter_pending_verification")
        refused = surface.witness(self.memory, OBSERVATION)
        self.assertEqual(refused["refusal"], "no bound decision for action")
        self.assertNotIn("witness", refused)


if __name__ == "__main__":
    unittest.main()
