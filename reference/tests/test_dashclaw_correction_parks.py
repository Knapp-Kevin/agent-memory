"""Sprint 3c: an exactly-approved medium DashClaw correction parks, and the seam forwards no evidence.

Since ADR-037 step 4b-2 (ledger Entry #24) an approval bound to the exact
``input_identity`` satisfies the DashClaw half of ``commit_bound_mutation`` and
no longer discharges PAMA's ``require_review``: the adapter parks the proposal
with ``review_requires_qualified_evidence``. The second test names the path the
seam must not take: the module's ``evidence_for`` yields two ``artifact_bound``
digests, and at medium risk the ladder accepts ``asserted`` binding, so
forwarding them would commit the correction on binding and authority material
alone -- the circularity the 4b-2 ruling rejected.
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import dashclaw_external_verdict as dashclaw  # noqa: E402
from agentmem_ref import policy  # noqa: E402
from agentmem_ref.adapter import GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.dashclaw_governed_commit import DashClawGovernedCommitter  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402
from agentmem_ref.verification import VerifierRegistry  # noqa: E402
from tests.test_dashclaw_external_verdict import AGENT, AUTHORITY, ORG, mutation_request  # noqa: E402

HUMAN = "human:release-manager"


class RecordingAdapter(GovernedMemoryAdapter):
    """Records the ``evidence`` argument of every ``commit_proposal`` call."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.evidence_seen: list = []

    def commit_proposal(self, proposal, fact_text, *args, **kwargs):
        self.evidence_seen.append(kwargs.get("evidence"))
        return super().commit_proposal(proposal, fact_text, *args, **kwargs)


def _bound(operation, risk, snapshot, value="release branch release"):
    return dashclaw.parse_mutation_request(
        mutation_request(value=value, operation=operation, risk=risk, state_snapshot=snapshot), AUTHORITY
    )


class ApprovedCorrectionParks(unittest.TestCase):
    def test_approved_medium_correction_parks_and_forwards_no_evidence(self):
        memory = RecordingAdapter(InMemoryTemporalGraph(), tenant=ORG)
        committer = DashClawGovernedCommitter(memory, AUTHORITY)
        seed = committer.commit(_bound("promotion", "low", "v0"))
        self.assertTrue(seed.committed)

        correction = _bound("correction", "medium", "v1", value="release branch main")
        result = committer.commit(
            correction,
            approval_ref="approval:release-v2",
            approval_actor_id=HUMAN,
            approved_input_identity=correction.input_identity,
        )

        self.assertFalse(result.committed)
        self.assertIsNone(result.refusal)
        decision = result.adapter_result.decision
        self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW)
        self.assertIn(policy.REVIEW_REQUIRES_QUALIFIED_EVIDENCE, decision.reasons)
        self.assertEqual(result.adapter_result.receipt["decision_outcome"], "require_review")
        self.assertEqual(memory.state_version(correction.proposal.target_reference), 1)
        self.assertEqual(memory.evidence_seen[-1], None)

    def test_forwarding_producer_evidence_would_discharge_at_medium(self):
        memory = GovernedMemoryAdapter(
            InMemoryTemporalGraph(), tenant=ORG, verifier_registry=VerifierRegistry()
        )
        seed = _bound("promotion", "low", "v0")
        self.assertTrue(memory.commit_proposal(seed.proposal, seed.fact_text).committed)

        correction = _bound("correction", "medium", "v1", value="release branch main")
        proposal = replace(correction.proposal, review_satisfied=False, approval_refs=())
        result = memory.commit_proposal(
            proposal, correction.fact_text, evidence=dashclaw.evidence_for(correction)
        )

        self.assertTrue(result.committed)
        self.assertEqual(result.decision.outcome, policy.ALLOW_WITH_LEDGER)
        self.assertEqual(result.decision.discharge_authority, policy.DELEGATED_POLICY)
        self.assertEqual(memory.state_version(correction.proposal.target_reference), 2)


if __name__ == "__main__":
    unittest.main()
