"""The doctrine fixture corpus, driven through executable conformance checks.

Two kinds of test live here, and the second is what makes the first mean
anything:

1. every fixture's declared authority and specialized assertion contracts are
   checked; and
2. the checkers are mutation-tested, so a passing corpus is evidence rather
   than a collection of checks that cannot fail.

Run: python -m unittest discover -s reference/tests -t reference
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import fixture_conformance as fc  # noqa: E402

REPO_FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


class FixtureCorpusTests(unittest.TestCase):
    def test_corpus_is_present_and_versioned(self):
        fixtures = fc.load_fixtures()
        self.assertGreaterEqual(len(fixtures), 25)
        for name, fixture in fixtures:
            self.assertIn("fixture_version", fixture, f"{name} lacks fixture_version")

    def test_every_declared_contract_is_enforced(self):
        result = fc.run()
        self.assertEqual(
            result["fixtures_failed"],
            [],
            msg=f"fixture conformance failures: {json.dumps(result['failures'], indent=2)}",
        )
        self.assertEqual(len(result["fixtures_run"]), len(list(REPO_FIXTURES.glob("*.json"))))
        self.assertGreater(result["fixtures_with_authority_envelope"], 0)
        self.assertGreaterEqual(result["fixtures_with_epistemic_promotion"], 3)


class CheckerHasTeethTests(unittest.TestCase):
    """A conformance check that cannot fail is decoration."""

    def setUp(self) -> None:
        source = REPO_FIXTURES / "high-confidence-false-promotion.json"
        self.base = json.loads(source.read_text(encoding="utf-8"))

    def _run_mutant(self, fixture: dict, mutate) -> dict:
        mutant = json.loads(json.dumps(fixture))
        mutate(mutant)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mutant.json"
            path.write_text(json.dumps(mutant), encoding="utf-8")
            return fc.run(Path(tmp))

    def test_detects_permitted_and_prohibited_overlap(self):
        result = self._run_mutant(
            self.base,
            lambda f: f["governed_uncertainty"].update(
                {"permitted_actions": ["crystallize", "mark_disputed"]}
            ),
        )
        self.assertEqual(result["fixtures_failed"], ["mutant"])

    def test_detects_selection_of_prohibited_action(self):
        result = self._run_mutant(
            self.base,
            lambda f: f["governed_uncertainty"].update({"selected_action": "crystallize"}),
        )
        self.assertEqual(result["fixtures_failed"], ["mutant"])

    def test_detects_selection_outside_permitted_set(self):
        result = self._run_mutant(
            self.base,
            lambda f: f["governed_uncertainty"].update({"selected_action": "invented_action"}),
        )
        self.assertEqual(result["fixtures_failed"], ["mutant"])

    def test_detects_crystallization_against_stated_expectation(self):
        result = self._run_mutant(
            self.base,
            lambda f: f["governed_uncertainty"]["permitted_actions"].append("crystallize_anyway"),
        )
        self.assertEqual(result["fixtures_failed"], ["mutant"])


class EpistemicPromotionCheckerHasTeethTests(unittest.TestCase):
    def setUp(self) -> None:
        derived = REPO_FIXTURES / "derived-self-corroboration.json"
        corroborated = REPO_FIXTURES / "independent-corroboration-arrives.json"
        self.derived = json.loads(derived.read_text(encoding="utf-8"))
        self.corroborated = json.loads(corroborated.read_text(encoding="utf-8"))

    def _run_mutant(self, fixture: dict, mutate) -> dict:
        mutant = json.loads(json.dumps(fixture))
        mutate(mutant)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mutant.json"
            path.write_text(json.dumps(mutant), encoding="utf-8")
            return fc.run(Path(tmp))

    def test_detects_derived_copy_inventing_new_origin(self):
        result = self._run_mutant(
            self.derived,
            lambda f: f["epistemic_promotion"]["lineage"][1].update(
                {"origin_refs": ["origin:invented"]}
            ),
        )
        self.assertEqual(result["fixtures_failed"], ["mutant"])

    def test_detects_fake_independent_source_count(self):
        result = self._run_mutant(
            self.derived,
            lambda f: f["epistemic_promotion"]["expected"].update(
                {"independent_origin_count": 3}
            ),
        )
        self.assertEqual(result["fixtures_failed"], ["mutant"])

    def test_detects_repetition_claimed_as_corroboration(self):
        result = self._run_mutant(
            self.derived,
            lambda f: f["epistemic_promotion"]["expected"].update(
                {"corroboration_threshold_met": True}
            ),
        )
        self.assertEqual(result["fixtures_failed"], ["mutant"])

    def test_detects_certification_without_gate(self):
        result = self._run_mutant(
            self.corroborated,
            lambda f: (
                f["memory_unit"]["certification"].update({"status": "pass"}),
                f["epistemic_promotion"]["expected"].update({"certification_status": "pass"}),
            ),
        )
        self.assertEqual(result["fixtures_failed"], ["mutant"])


if __name__ == "__main__":
    unittest.main()
