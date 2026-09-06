"""Executable security evidence-depth and poisoning boundary tests for issue #196."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agentmem_ref.security_evidence_depth import (
    LEVELS,
    build_report,
    classify_evidence_levels,
    run_poisoning_harness,
    with_behavioral_failure,
)

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "fixtures" / "security-evidence-depth-matrix.json"
COMMIT = "1" * 40


class SecurityEvidenceDepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(MATRIX.read_text(encoding="utf-8"))

    def test_fixture_negative_level_cases_do_not_infer_missing_levels(self):
        for case in self.matrix["negative_cases"]:
            with self.subTest(case_id=case["case_id"]):
                depth = classify_evidence_levels(case["evidence_refs"])
                self.assertEqual(depth["demonstrated_levels"], case["expected_demonstrated_levels"])
                self.assertEqual(depth["explicitly_unproven_levels"], case["expected_unproven_levels"])

    def test_noncontiguous_levels_remain_noncontiguous(self):
        depth = classify_evidence_levels(
            {"D": ["doc:one"], "F": [], "H": ["harness:one"], "R": [], "P": []}
        )
        self.assertEqual(depth["demonstrated_levels"], ["D", "H"])
        self.assertEqual(depth["highest_demonstrated_level"], "H")
        self.assertIn("F", depth["explicitly_unproven_levels"])

    def test_all_three_required_poisoning_behavioral_cases_pass(self):
        harness = run_poisoning_harness()
        self.assertTrue(harness["passed"])
        self.assertEqual(
            set(harness["cases"]),
            {"direct_external_write", "mcp_ingestion", "a2a_ingestion"},
        )
        for case in harness["cases"].values():
            self.assertTrue(case["passed"], case)

    def test_report_without_runtime_artifact_claims_h_not_r_or_p(self):
        report = build_report(COMMIT)
        self.assertTrue(report["required_behavioral_cases_passed"])
        self.assertNotIn("score", report)
        self.assertNotIn("composite_score", report)
        self.assertEqual(report["evidence_model"]["levels"], list(LEVELS))

        for claim in report["claims"]:
            self.assertIn("D", claim["demonstrated_levels"])
            self.assertIn("F", claim["demonstrated_levels"])
            self.assertIn("H", claim["demonstrated_levels"])
            self.assertNotIn("R", claim["demonstrated_levels"])
            self.assertNotIn("P", claim["demonstrated_levels"])
            self.assertIn("R", claim["explicitly_unproven_levels"])
            self.assertIn("P", claim["explicitly_unproven_levels"])
            self.assertEqual(claim["production_evidence_refs"], [])

    def _benchmark(self, commit: str, *, metric: int = 0, passed: bool = True) -> dict:
        return {
            "agent_memory_commit": commit,
            "hard_gates_passed": passed,
            "metrics": {"authority_from_confidence_count": metric},
            "cases": {"authority_from_confidence": {"passed": passed and metric == 0}},
        }

    def test_same_head_p5_artifact_can_support_only_direct_r(self):
        report = build_report(COMMIT, benchmark_security=self._benchmark(COMMIT))
        by_id = {claim["claim_id"]: claim for claim in report["claims"]}
        direct = by_id["poisoning:direct-external-write"]
        mcp = by_id["poisoning:mcp-ingestion"]
        a2a = by_id["poisoning:a2a-ingestion"]

        self.assertIn("R", direct["demonstrated_levels"])
        self.assertEqual(direct["runtime_evidence_head"], COMMIT)
        self.assertNotIn("P", direct["demonstrated_levels"])
        self.assertNotIn("R", mcp["demonstrated_levels"])
        self.assertNotIn("R", a2a["demonstrated_levels"])

    def test_stale_runtime_artifact_is_historical_not_current_r(self):
        stale_commit = "2" * 40
        report = build_report(COMMIT, benchmark_security=self._benchmark(stale_commit))
        direct = next(claim for claim in report["claims"] if claim["claim_id"] == "poisoning:direct-external-write")
        self.assertNotIn("R", direct["demonstrated_levels"])
        self.assertIn("R", direct["explicitly_unproven_levels"])
        self.assertIn("stale_runtime_evidence_refs", direct)
        self.assertIn(stale_commit, direct["stale_runtime_evidence_refs"][0])
        self.assertNotIn("runtime_evidence_head", direct)

    def test_failing_or_nonpassing_runtime_artifact_does_not_create_r(self):
        bad_metric = build_report(COMMIT, benchmark_security=self._benchmark(COMMIT, metric=1, passed=False))
        direct = next(claim for claim in bad_metric["claims"] if claim["claim_id"] == "poisoning:direct-external-write")
        self.assertNotIn("R", direct["demonstrated_levels"])

    def test_behavioral_failure_cannot_hide_behind_other_levels(self):
        report = build_report(COMMIT, benchmark_security=self._benchmark(COMMIT))
        mutated = with_behavioral_failure(report, "poisoning:direct-external-write")
        direct = next(claim for claim in mutated["claims"] if claim["claim_id"] == "poisoning:direct-external-write")
        self.assertFalse(mutated["required_behavioral_cases_passed"])
        self.assertFalse(direct["behavioral_passed"])
        self.assertNotIn("H", direct["demonstrated_levels"])
        self.assertIn("H", direct["explicitly_unproven_levels"])
        # Independent same-head runtime evidence remains R rather than being
        # erased or averaged into a composite status.
        self.assertIn("R", direct["demonstrated_levels"])

    def test_external_mapping_cannot_claim_certification(self):
        from agentmem_ref.security_evidence_depth import _claim

        with self.assertRaisesRegex(ValueError, "certification_claim='none'"):
            _claim(
                agent_memory_commit=COMMIT,
                claim_id="mapping:test",
                title="Mapping test",
                threat_family="test",
                doctrine_refs=["doc:test"],
                fixture_refs=["fixture:test"],
                harness_ref="harness:test",
                behavioral_passed=True,
                external_mappings=[
                    {
                        "source": "Example Standard",
                        "version": "1.0",
                        "control_ref": "CTRL-1",
                        "certification_claim": "certified",
                    }
                ],
            )

    def test_valid_external_mapping_is_explicitly_non_certifying(self):
        from agentmem_ref.security_evidence_depth import _claim

        claim = _claim(
            agent_memory_commit=COMMIT,
            claim_id="mapping:test",
            title="Mapping test",
            threat_family="test",
            doctrine_refs=["doc:test"],
            fixture_refs=["fixture:test"],
            harness_ref="harness:test",
            behavioral_passed=True,
            external_mappings=[
                {
                    "source": "Example Standard",
                    "version": "1.0",
                    "control_ref": "CTRL-1",
                    "certification_claim": "none",
                }
            ],
        )
        self.assertEqual(claim["external_mappings"][0]["certification_claim"], "none")
        self.assertIn("does not assert external certification", claim["non_certification_statement"])

    def test_exact_commit_identity_is_required(self):
        for invalid in ("", "abc", "G" * 40, "1" * 39, "1" * 41):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "exact 40-hex commit"):
                    build_report(invalid)

    def test_protocol_transport_success_does_not_upgrade_evidence_depth(self):
        report = build_report(COMMIT)
        for claim_id in ("poisoning:mcp-ingestion", "poisoning:a2a-ingestion"):
            claim = next(claim for claim in report["claims"] if claim["claim_id"] == claim_id)
            self.assertEqual(claim["highest_demonstrated_level"], "H")
            self.assertEqual(claim["runtime_evidence_refs"], [])
            self.assertIn("R", claim["explicitly_unproven_levels"])
            self.assertIn("P", claim["explicitly_unproven_levels"])


if __name__ == "__main__":
    unittest.main()
