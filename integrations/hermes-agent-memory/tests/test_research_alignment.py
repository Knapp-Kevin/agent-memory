from __future__ import annotations

import json
from pathlib import Path
import unittest

from agent_memory_hermes import HERMES_COMMIT, MUTATION_SURFACES, STRICT_BLOCKERS

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "docs/programs/hermes-research/hermes-mutation-surface.json"


class ResearchAlignmentTests(unittest.TestCase):
    def test_integration_profile_matches_completed_317_research_boundary(self) -> None:
        value = json.loads(RESEARCH.read_text(encoding="utf-8"))
        self.assertEqual(value["hermes"]["commit"], HERMES_COMMIT)
        self.assertEqual(
            {item["id"] for item in value["surfaces"]},
            set(MUTATION_SURFACES),
        )
        self.assertEqual(
            set(value["integration_postures"]["strict"]["blocking_gaps"]),
            set(STRICT_BLOCKERS),
        )
        self.assertFalse(value["integration_postures"]["strict"]["supported_today"])
        self.assertEqual(value["authority_effect"], "none")
        self.assertEqual(value["doctrine_disposition"], "no_new_adr")


if __name__ == "__main__":
    unittest.main()
