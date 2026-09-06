from __future__ import annotations

import unittest

from agent_memory_hermes import HERMES_COMMIT
from agent_memory_hermes.config import IntegrationConfig
from agent_memory_hermes.coverage import build_coverage_report


class RecursiveScenarioCoverageTests(unittest.TestCase):
    def test_all_research_scenarios_have_executable_coverage_disposition(self) -> None:
        report = build_coverage_report(
            IntegrationConfig(mode="govern", governor_command=("/bin/true",)),
            observed_hermes_revision=HERMES_COMMIT,
        )
        scenarios = {
            item["scenario_id"]: item for item in report["recursive_evidence_scenarios"]
        }
        self.assertEqual(
            set(scenarios),
            {
                "self_reinforcing_skill_lineage",
                "correction_relearned_by_background_review",
                "stale_human_approval_replay",
                "curator_archive_during_pending_dependency",
                "provider_mirror_failure_after_builtin_commit",
            },
        )
        self.assertIn("independent corroboration", scenarios["self_reinforcing_skill_lineage"]["requirement"])
        self.assertIn("non-current", scenarios["correction_relearned_by_background_review"]["requirement"])
        self.assertEqual(
            scenarios["stale_human_approval_replay"]["status"],
            "uncovered_requires_future_durable_state_hook",
        )
        self.assertIn("before-state digest", scenarios["stale_human_approval_replay"]["requirement"])
        self.assertEqual(
            scenarios["curator_archive_during_pending_dependency"]["blocking_surface"],
            "deterministic_curator_archive",
        )
        mirror = scenarios["provider_mirror_failure_after_builtin_commit"]
        self.assertEqual(mirror["status"], "modeled")
        self.assertIn("unsettled/non-quiescent", mirror["requirement"])


if __name__ == "__main__":
    unittest.main()
