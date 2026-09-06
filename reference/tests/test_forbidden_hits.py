"""Executable forbidden-hit lifecycle assertions for issue #148."""

from __future__ import annotations

import unittest
from pathlib import Path

from agentmem_ref import forbidden_hits

ROOT = Path(__file__).resolve().parents[2]


class ForbiddenHitTests(unittest.TestCase):
    def test_declared_forbidden_hit_matrix_matches_reference_behavior(self):
        report = forbidden_hits.run()

        self.assertEqual(report["failures"], [])
        self.assertEqual(len(report["assertions_run"]), 9)
        self.assertEqual(len(report["forbidden_classes"]), 9)
        self.assertTrue(all(item["passed"] for item in report["coverage"]))

        discovered_but_blocked = [
            item
            for item in report["coverage"]
            if item["candidate_discovered"] and not item["admitted"]
        ]
        self.assertGreaterEqual(len(discovered_but_blocked), 1)
        self.assertTrue(
            any(item["expected_refusal"] == "superseded_not_current" for item in discovered_but_blocked)
        )

    def test_assertion_checker_detects_stage_regression(self):
        assertion = forbidden_hits.load_assertions()[0]
        observation = forbidden_hits.ForbiddenHitObservation(
            assertion_id=assertion.assertion_id,
            candidate_discovered=assertion.candidate_discovered,
            admitted=True,
            context_surfaced=True,
            downstream_influence=True,
            refusal="",
        )

        with self.assertRaises(forbidden_hits.ForbiddenHitMismatch):
            forbidden_hits.compare(assertion, observation)

    def test_assertion_checker_detects_wrong_refusal_reason(self):
        assertion = forbidden_hits.load_assertions()[0]
        observation = forbidden_hits.ForbiddenHitObservation(
            assertion_id=assertion.assertion_id,
            candidate_discovered=assertion.candidate_discovered,
            admitted=assertion.admitted,
            context_surfaced=assertion.context_surfaced,
            downstream_influence=assertion.downstream_influence,
            refusal="some_other_reason",
        )

        with self.assertRaises(forbidden_hits.ForbiddenHitMismatch):
            forbidden_hits.compare(assertion, observation)

    def test_all_later_stages_are_explicit_even_when_admission_blocks(self):
        report = forbidden_hits.run()
        for item in report["coverage"]:
            for field in ("candidate_discovered", "admitted", "context_surfaced", "downstream_influence"):
                self.assertIn(field, item)
                self.assertIsInstance(item[field], bool)

    def test_mapped_source_evidence_paths_exist(self):
        for assertion in forbidden_hits.load_assertions():
            relative_path = assertion.source_evidence.split("::", 1)[0]
            with self.subTest(assertion_id=assertion.assertion_id, source=relative_path):
                self.assertTrue((ROOT / relative_path).is_file(), relative_path)


if __name__ == "__main__":
    unittest.main()
