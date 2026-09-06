"""#293 CodeGenome traversal scope and deletion/residue closeout tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.code_graph_qualification import CODEGENOME_COMMIT  # noqa: E402
from agentmem_ref.codegenome_profile import profile_digest  # noqa: E402
from agentmem_ref.codegenome_scope_residue import (  # noqa: E402
    CodeGenomeScopeResidueError,
    ExternalScopeBinding,
    build_closeout_report,
    evaluate_scope_bridge,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE = ROOT / "reference" / "fixtures" / "component-capabilities" / "codegenome.example.json"


def profile_value() -> dict:
    return json.loads(PROFILE.read_text(encoding="utf-8"))


def binding(profile: dict | None = None) -> ExternalScopeBinding:
    value = profile if profile is not None else profile_value()
    return ExternalScopeBinding(
        binding_ref="scope-binding:codegenome:fixture-main:tenant-a-project-a",
        component_id="codegenome",
        component_version=CODEGENOME_COMMIT,
        component_profile_digest=profile_digest(value),
        provider_scope_ref="repo://fixture/codegenome-main",
        agent_memory_scope_ref="tenant://tenant-a/project/project-a",
        tenant_ref="tenant-a",
        project_ref="project-a",
    )


def admission_args(item: ExternalScopeBinding) -> dict[str, str]:
    return {
        "component_version": item.component_version,
        "component_profile_digest": item.component_profile_digest,
    }


class CodeGenomeScopeResidueTests(unittest.TestCase):
    def test_exact_external_scope_binding_is_required_and_version_bound(self):
        item = binding()
        exact = evaluate_scope_bridge(
            binding=item,
            provider_scope_ref=item.provider_scope_ref,
            agent_memory_scope_ref=item.agent_memory_scope_ref,
            **admission_args(item),
        )
        self.assertTrue(exact.admitted)
        self.assertEqual(exact.reason, "exact_external_scope_binding")
        self.assertEqual(exact.authority_effect, "none")

        missing = evaluate_scope_bridge(
            binding=None,
            provider_scope_ref=item.provider_scope_ref,
            agent_memory_scope_ref=item.agent_memory_scope_ref,
            **admission_args(item),
        )
        self.assertFalse(missing.admitted)
        self.assertEqual(missing.reason, "external_scope_binding_missing")

        stale_version = evaluate_scope_bridge(
            binding=item,
            component_version="0" * 40,
            component_profile_digest=item.component_profile_digest,
            provider_scope_ref=item.provider_scope_ref,
            agent_memory_scope_ref=item.agent_memory_scope_ref,
        )
        self.assertFalse(stale_version.admitted)
        self.assertEqual(stale_version.reason, "component_version_mismatch")

        stale_profile = evaluate_scope_bridge(
            binding=item,
            component_version=item.component_version,
            component_profile_digest="sha256:" + "0" * 64,
            provider_scope_ref=item.provider_scope_ref,
            agent_memory_scope_ref=item.agent_memory_scope_ref,
        )
        self.assertFalse(stale_profile.admitted)
        self.assertEqual(stale_profile.reason, "component_profile_mismatch")

        provider_mismatch = evaluate_scope_bridge(
            binding=item,
            provider_scope_ref="repo://foreign/codegenome-main",
            agent_memory_scope_ref=item.agent_memory_scope_ref,
            **admission_args(item),
        )
        self.assertFalse(provider_mismatch.admitted)
        self.assertEqual(provider_mismatch.reason, "provider_scope_mismatch")

        scope_mismatch = evaluate_scope_bridge(
            binding=item,
            provider_scope_ref=item.provider_scope_ref,
            agent_memory_scope_ref="tenant://tenant-b/project/project-a",
            **admission_args(item),
        )
        self.assertFalse(scope_mismatch.admitted)
        self.assertEqual(scope_mismatch.reason, "agent_memory_scope_mismatch")

    def test_binding_cannot_target_another_component(self):
        value = profile_value()
        with self.assertRaisesRegex(CodeGenomeScopeResidueError, "must target codegenome"):
            ExternalScopeBinding(
                binding_ref="binding:bad",
                component_id="graphify",
                component_version=CODEGENOME_COMMIT,
                component_profile_digest=profile_digest(value),
                provider_scope_ref="repo://fixture/codegenome-main",
                agent_memory_scope_ref="tenant://tenant-a/project/project-a",
                tenant_ref="tenant-a",
                project_ref="project-a",
            )

    def test_v1_to_v2_source_deletion_is_currentness_not_erasure_claim(self):
        profile = profile_value()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            v1 = root / "v1.json"
            v2 = root / "v2.json"
            v1_manifest = root / "v1-store-manifest.txt"
            v2_manifest = root / "v2-store-manifest.txt"
            v1.write_text(json.dumps([{"node": "line 1:1"}, {"node": "line 5:1"}]), encoding="utf-8")
            v2.write_text(json.dumps([{"node": "line 5:1"}, {"node": "line 13:1"}]), encoding="utf-8")
            v1_manifest.write_text("v1-store/file.bin sha256:aaa\n", encoding="utf-8")
            v2_manifest.write_text("v2-store/file.bin sha256:bbb\n", encoding="utf-8")

            report = build_closeout_report(
                agent_memory_commit="a" * 40,
                component_profile=profile,
                binding=binding(profile),
                v1_main_downstream=v1,
                v2_main_downstream=v2,
                v1_store_manifest=v1_manifest,
                v2_store_manifest=v2_manifest,
            )

        self.assertTrue(all(report["invariants"].values()), report["invariants"])
        self.assertFalse(report["scope_bridge"]["stale_component"]["admitted"])
        self.assertFalse(report["scope_bridge"]["stale_profile"]["admitted"])
        deletion = report["deletion_rebuild"]
        self.assertEqual(deletion["currentness_result"], "deleted_source_not_current")
        self.assertFalse(deletion["old_source_current_after_rebuild"])
        self.assertTrue(deletion["replacement_source_current_after_rebuild"])
        self.assertTrue(deletion["historical_provider_artifact_retained"])
        self.assertFalse(deletion["historical_provider_artifact_current"])
        self.assertFalse(deletion["physical_erasure_proven"])
        self.assertEqual(
            deletion["residue_posture"],
            "historical_provider_artifact_disclosed_not_current",
        )
        self.assertEqual(report["authority_effect"], "none")

    def test_profile_drift_invalidates_existing_scope_binding(self):
        profile = profile_value()
        item = binding(profile)
        changed = json.loads(json.dumps(profile))
        next(cap for cap in changed["capabilities"] if cap["capability_id"] == "vector_similarity")[
            "limitations"
        ].append("new_unverified_profile_state")
        result = evaluate_scope_bridge(
            binding=item,
            component_version=CODEGENOME_COMMIT,
            component_profile_digest=profile_digest(changed),
            provider_scope_ref=item.provider_scope_ref,
            agent_memory_scope_ref=item.agent_memory_scope_ref,
        )
        self.assertFalse(result.admitted)
        self.assertEqual(result.reason, "component_profile_mismatch")

    def test_deleted_source_remaining_current_fails_closeout_invariant(self):
        profile = profile_value()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            v1 = root / "v1.json"
            v2 = root / "v2.json"
            v1_manifest = root / "v1.txt"
            v2_manifest = root / "v2.txt"
            v1.write_text(json.dumps([{"node": "line 1:1"}]), encoding="utf-8")
            v2.write_text(json.dumps([{"node": "line 1:1"}, {"node": "line 13:1"}]), encoding="utf-8")
            v1_manifest.write_text("old", encoding="utf-8")
            v2_manifest.write_text("new", encoding="utf-8")
            report = build_closeout_report(
                agent_memory_commit="b" * 40,
                component_profile=profile,
                binding=binding(profile),
                v1_main_downstream=v1,
                v2_main_downstream=v2,
                v1_store_manifest=v1_manifest,
                v2_store_manifest=v2_manifest,
            )
        self.assertFalse(report["invariants"]["source_deleted_old_leaf_not_current_after_rebuild"])


if __name__ == "__main__":
    unittest.main()
