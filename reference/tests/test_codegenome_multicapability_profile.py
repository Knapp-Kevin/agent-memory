"""CodeGenome multi-capability profile boundaries for #293."""

from __future__ import annotations

from copy import deepcopy
import json
import sys
import unittest
from pathlib import Path

import jsonschema

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.codegenome_profile import (  # noqa: E402
    CODEGENOME_COMMIT,
    CodeGenomeProfileError,
    build_profile_report,
    validate_profile,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE_PATH = ROOT / "reference" / "fixtures" / "component-capabilities" / "codegenome.example.json"
SCHEMA_PATH = ROOT / "schemas" / "component-capability-profile.schema.json"


def profile() -> dict:
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))


def capability(value: dict, capability_id: str) -> dict:
    return next(item for item in value["capabilities"] if item["capability_id"] == capability_id)


class CodeGenomeMultiCapabilityProfileTests(unittest.TestCase):
    def test_profile_is_schema_valid_and_evidence_bounded(self):
        value = profile()
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        errors = list(jsonschema.Draft202012Validator(schema).iter_errors(value))
        self.assertEqual(errors, [], [error.message for error in errors])

        component = validate_profile(value)
        self.assertEqual(component.component_version, CODEGENOME_COMMIT)
        self.assertEqual(len(component.capabilities), 18)

        report = build_profile_report(value, agent_memory_commit="a" * 40)
        self.assertTrue(all(report["invariants"].values()), report["invariants"])
        self.assertEqual(report["maturity_counts"]["declared"], 2)
        self.assertEqual(report["maturity_counts"]["implemented"], 15)
        self.assertEqual(report["maturity_counts"]["evidence_proven"], 1)
        self.assertEqual(report["maturity_counts"]["reference_qualified"], 0)
        self.assertEqual(
            report["proposal_only_surfaces"],
            ["experiment_evaluation", "impact_propagation"],
        )
        self.assertEqual(report["authority_effect"], "none")

    def test_vector_runtime_cannot_be_promoted_from_source_implementation(self):
        value = profile()
        capability(value, "vector_candidate_retrieval")["maturity"] = "runtime_wired"
        with self.assertRaisesRegex(CodeGenomeProfileError, "exceeds evidence ceiling"):
            validate_profile(value)

    def test_graph_rag_cannot_hitchhike_on_graph_traversal(self):
        value = profile()
        graph_rag = capability(value, "graph_augmented_context_assembly")
        graph_rag["maturity"] = "implemented"
        graph_rag["enabled"] = True
        with self.assertRaises(CodeGenomeProfileError):
            validate_profile(value)

    def test_lsp_stub_cannot_be_activated(self):
        value = profile()
        capability(value, "lsp_overlay")["enabled"] = True
        with self.assertRaisesRegex(CodeGenomeProfileError, "must remain disabled"):
            validate_profile(value)

    def test_deletion_rebuild_stays_disabled_without_residue_qualification(self):
        value = profile()
        capability(value, "deletion_rebuild")["enabled"] = True
        with self.assertRaisesRegex(CodeGenomeProfileError, "must remain disabled"):
            validate_profile(value)

    def test_source_version_change_invalidates_profile(self):
        value = profile()
        value["component_version"] = "b" * 40
        value["runtime_ref"] = f"MythologIQ-Labs-LLC/CodeGenome@{'b' * 40}"
        with self.assertRaisesRegex(CodeGenomeProfileError, "exact tested commit"):
            validate_profile(value)

    def test_traversal_must_preserve_exact_qualification_binding(self):
        value = profile()
        traversal = capability(value, "code_graph_traversal")
        traversal["evidence_refs"] = [
            item for item in traversal["evidence_refs"] if not item.startswith("qualification:")
        ]
        with self.assertRaisesRegex(CodeGenomeProfileError, "exact code-graph qualification profile"):
            validate_profile(value)

    def test_provider_scope_cannot_be_laundered_into_agent_memory_scope(self):
        value = profile()
        capability(value, "code_graph_traversal")["scope_posture"] = "inherits_agent_memory_scope"
        with self.assertRaisesRegex(CodeGenomeProfileError, "external_scope_bridge"):
            validate_profile(value)

    def test_component_output_cannot_gain_direct_authority(self):
        value = profile()
        capability(value, "code_graph_traversal")["authority_effect"] = "proposal_only"
        with self.assertRaisesRegex(CodeGenomeProfileError, "authority_effect must remain none"):
            validate_profile(value)

    def test_capability_inventory_drift_requires_explicit_review(self):
        value = profile()
        value["capabilities"] = deepcopy(value["capabilities"][:-1])
        with self.assertRaisesRegex(CodeGenomeProfileError, "capability inventory changed"):
            validate_profile(value)

    def test_agent_memory_evidence_requires_exact_commit_identity(self):
        value = profile()
        with self.assertRaisesRegex(CodeGenomeProfileError, "40 lowercase hex"):
            build_profile_report(value, agent_memory_commit="main")


if __name__ == "__main__":
    unittest.main()
