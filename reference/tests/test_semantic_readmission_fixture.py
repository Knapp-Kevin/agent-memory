"""Drive the semantic rejected-value fixture through the optional profile."""

from __future__ import annotations

import json
import unittest

from tests.qualified_fixtures import corpus_for, registry_for, rule
from pathlib import Path

from agentmem_ref import policy
from agentmem_ref.adapter import Clock
from agentmem_ref.readmission import SemanticSimilaritySignal
from agentmem_ref.semantic_readmission_adapter import SemanticReadmissionAdapter
from agentmem_ref.substrate import InMemoryTemporalGraph

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "fixtures" / "rejected-value-semantic-reentry.json"


def _proposal(
    proposal_id: str,
    *,
    operation: str = "promotion",
    snapshot: str = "",
    approvals: tuple[str, ...] = (),
    reviewed: bool = False,
) -> policy.Proposal:
    return policy.Proposal(
        proposal_id=proposal_id,
        actor_id="agent:fixture",
        charter_version="charter:semantic-fixture",
        target_reference="mem:deploy-window",
        target_class=policy.M2,
        scope="tenant-a",
        operation=operation,
        current_strength="promoted" if operation == "correction" else "reinforced",
        proposed_strength="promoted",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class="low",
        evidence_refs=(f"evidence:{proposal_id}",),
        approval_refs=approvals,
        review_satisfied=reviewed,
        state_snapshot=snapshot,
        tenant_ref="tenant-a",
    )


class SemanticReadmissionFixtureTests(unittest.TestCase):
    def test_fixture_expected_behavior_is_executable(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        values = data["rejected_value"]
        expected = data["expected_behavior"]
        signal_data = data["semantic_signal"]

        # ADR-037 step 4b-2: expected semantic change (entry #24).
        corpus = corpus_for(rule(
            rule_id="rule:fixture-correction", target="mem:deploy-window",
            criterion="value-correction", from_state=values["original"],
            to_values=(values["current_correction"],),
        ), rule(
            rule_id="rule:fixture-reversal", target="mem:deploy-window",
            criterion="value-reversal", from_state=values["current_correction"],
            to_values=(values["semantic_paraphrase"],),
        ))
        adapter = SemanticReadmissionAdapter(
            InMemoryTemporalGraph(), tenant="tenant-a", clock=Clock(),
            verifier_registry=registry_for(corpus),
        )
        original = adapter.commit_proposal(_proposal("fixture-original"), values["original"])
        self.assertTrue(original.committed)
        corrected = adapter.commit_proposal(
            _proposal(
                "fixture-correction",
                operation="correction",
                snapshot="v1",
                approvals=("approval:fixture-owner",),
                reviewed=True,
            ),
            values["current_correction"],
            evidence=corpus.evidence_for(
                target_reference="mem:deploy-window", criterion="value-correction",
                pre_state=values["original"],
                proposed_value=values["current_correction"]),
        )
        self.assertTrue(corrected.committed)

        exact = adapter.commit_with_semantic_signal(
            _proposal("fixture-exact", snapshot="v2"),
            values["original"],
        )
        self.assertFalse(exact.committed)
        self.assertEqual(exact.refusal, expected["exact_reentry_reason"])

        rejection_ref = adapter.active_rejection_records("mem:deploy-window")[0]["rejection_id"]
        signal = SemanticSimilaritySignal(
            memory_id="mem:deploy-window",
            rejection_ref=rejection_ref,
            estimator_id=signal_data["estimator_id"],
            estimator_version=signal_data["estimator_version"],
            candidate_match=signal_data["candidate_match"],
            confidence=signal_data["confidence"],
        )
        semantic = adapter.commit_with_semantic_signal(
            _proposal("fixture-semantic", snapshot="v2"),
            values["semantic_paraphrase"],
            semantic_signal=signal,
        )
        self.assertEqual(signal.candidate_match, expected["semantic_candidate_match"])
        self.assertEqual(semantic.routing.consequence, expected["semantic_consequence"])
        self.assertEqual(semantic.committed, expected["ordinary_semantic_reentry_commits"])
        self.assertFalse(expected["semantic_signal_is_authority"])

        approved = adapter.commit_with_semantic_signal(
            _proposal(
                "fixture-approved-reversal",
                operation="correction",
                snapshot="v2",
                approvals=("approval:fixture-reversal",),
                reviewed=True,
            ),
            values["semantic_paraphrase"],
            semantic_signal=signal,
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            # The fixture's declared property -- an approved correction may
            # re-enter through PAMA -- is unchanged. Only the discharge route is.
            evidence=corpus.evidence_for(
                target_reference="mem:deploy-window", criterion="value-reversal",
                pre_state=values["current_correction"],
                proposed_value=values["semantic_paraphrase"]),
        )
        self.assertEqual(approved.committed, expected["approved_correction_may_reenter_through_pama"])


if __name__ == "__main__":
    unittest.main()
