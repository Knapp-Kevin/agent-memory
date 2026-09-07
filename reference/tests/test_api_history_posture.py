"""Sprint 4c-1 (LD2, LD3): history and posture on the public surface, read only, from records that exist."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref import procedural_memory as pm  # noqa: E402
from agentmem_ref.adapter import GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.api import contract, surface  # noqa: E402
from agentmem_ref.core import receipts  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "reference" / "fixtures" / "api"
EXAMPLE = json.loads((FIXTURES / "proposal-envelope.example.json").read_text(encoding="utf-8"))
RECALL = json.loads((FIXTURES / "recall-context.example.json").read_text(encoding="utf-8"))
COMPOSED = REPO / "reference" / "fixtures" / "runtime-configuration" / "reference-composed-runtime.json"
ORG = "org:example"
TARGET = EXAMPLE["target_reference"]
OTHER = "repo:example:other-branch"


def _target(reference: str = TARGET) -> dict:
    return {"contract_version": contract.CONTRACT_VERSION, "target_reference": reference}


def _skill_evidence():
    skill = pm.SkillArtifact(skill_id="skill-1", version=1, purpose="p", scope="project", isolation_domain_refs=("d1",),
                             required_isolation_domain_refs=("d1",), procedure_markdown="# steps", provenance_refs=("prov-1",))
    return pm.evidence_for(skill)


class History(unittest.TestCase):
    def setUp(self):
        self.memory = GovernedMemoryAdapter(InMemoryTemporalGraph(), tenant=ORG)
        self.assertTrue(surface.commit(self.memory, EXAMPLE, "release branch release")["committed"])
        self.assertTrue(surface.commit(self.memory, {**EXAMPLE, "proposal_id": "proposal-other", "target_reference": OTHER}, "other branch")["committed"])
        surface.recall(self.memory, "release branch", RECALL)

    def test_history_after_commit_and_recall(self):
        fact = self.memory.current_fact_uuid(TARGET)
        result = surface.history(self.memory, _target())
        self.assertEqual(result["stage"], "history")
        h = result["history"]
        self.assertEqual(h["current_fact_uuid"], fact)
        self.assertEqual(h["state_version"], 1)
        self.assertIs(h["tombstoned"], False)
        self.assertTrue(h["events"]); self.assertTrue(all(e["memory_id"] == TARGET for e in h["events"]))
        self.assertIn("memory.propose", {e["event_type"] for e in h["events"]})
        self.assertNotIn("rejected_values", h)
        other = surface.history(self.memory, _target(OTHER))["history"]
        self.assertTrue(all(e["memory_id"] == OTHER for e in other["events"]))
        self.assertNotEqual(other["current_fact_uuid"], fact)

    def test_history_rejected_values_by_value(self):
        # A rejection is recorded when a correction commits and supersedes the prior value
        # (adapter.record_correction); a parked correction records nothing.
        parked = surface.commit(self.memory, {**EXAMPLE, "operation": "correction", "risk_class": "medium", "state_snapshot": "v1"}, "release branch main")
        self.assertFalse(parked["committed"])
        self.assertEqual(surface.history(self.memory, _target(), fact_text="release branch main")["history"]["rejected_values"], [])
        before = self.memory.current_fact_uuid(TARGET)
        committed = surface.commit(self.memory, {**EXAMPLE, "operation": "correction", "risk_class": "medium", "state_snapshot": "v1"}, "release branch main", evidence=_skill_evidence())
        self.assertTrue(committed["committed"])
        h = surface.history(self.memory, _target(), fact_text="release branch release")["history"]
        self.assertEqual(len(h["rejected_values"]), 1)
        self.assertEqual(h["rejected_values"][0]["superseded_fact_uuid"], before)
        self.assertEqual(h["state_version"], 2)

    def test_history_unknown_target(self):
        h = surface.history(self.memory, _target("repo:example:nothing"))["history"]
        self.assertIsNone(h["current_fact_uuid"]); self.assertEqual(h["state_version"], 0)
        self.assertIs(h["tombstoned"], False); self.assertEqual(h["events"], [])

    def test_history_after_forget(self):
        deletion = {**EXAMPLE, "operation": "pruning", "risk_class": "low", "state_snapshot": "v1", "reversibility": "reversible"}
        result = surface.forget(self.memory, deletion, evidence=_skill_evidence())
        h = surface.history(self.memory, _target())["history"]
        self.assertEqual(h["tombstoned"], bool(result["committed"]))
        if result["committed"]:
            self.assertIsNone(h["current_fact_uuid"])

    def test_history_version_gate(self):
        result = surface.history(self.memory, {"contract_version": "2.0.0", "target_reference": TARGET})
        self.assertEqual((result["stage"], result["compatibility"]), ("none", contract.INCOMPATIBLE))
        older = surface.history(self.memory, {"contract_version": "1.0.0", "target_reference": TARGET})
        self.assertEqual(older["stage"], "history")


class Posture(unittest.TestCase):
    def test_posture_on_the_composed_fixture(self):
        with tempfile.TemporaryDirectory() as state:
            results = [surface.posture(COMPOSED, state_dir=state), surface.posture(COMPOSED)]
        for result in results:
            self.assertEqual((result["stage"], result["compatibility"]), ("posture", contract.CURRENT))
            receipts.validate(contract.POSTURE_SCHEMA, result["posture"])
            self.assertIn("operational_readiness", result["posture"])
            self.assertIn(result["posture"]["configuration_startable"], (True, False))

    def test_posture_missing_configuration(self):
        result = surface.posture(REPO / "nonexistent-configuration.json")
        self.assertEqual(result["stage"], "none")
        self.assertIn("not found", result["validation_error"])


if __name__ == "__main__":
    unittest.main()
