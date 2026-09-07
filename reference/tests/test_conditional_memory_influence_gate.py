"""Gate-state tests for model-internal conditional-memory influence."""

import unittest

from agentmem_ref.conditional_memory_influence import map_currentness, normalize_influence


def table(partition="tenant-a/project-a", table_id="table:t1", char="a"):
    return {
        "table_id": table_id,
        "table_digest": "sha256:" + char * 64,
        "model_ref": "model:fixture",
        "checkpoint_ref": "checkpoint:1",
        "tokenizer_ref": "tokenizer:1",
        "normalization_ref": "normalization:1",
        "addressing_config_ref": "addressing:format-v1",
        "injection_point_ref": "layer:1",
        "partition_ref": partition,
        "derivation_ref": f"derivation:{table_id}",
        "currentness_ref": f"currentness:{table_id}",
        "suppression_overlay_ref": "overlay:v1",
        "build_receipt_ref": f"receipt:{table_id}",
    }


def request(partition="tenant-a/project-a"):
    return {"partition_ref": partition, "tenant_ref": "tenant-a", "project_ref": "project-a", "purpose": "runtime inference"}


def record(**changes):
    values = {
        "influence_id": "influence:1",
        "lookup_ref": "lookup:1",
        "address": [11, 17],
        "table": table(),
        "request": request(),
        "currentness": "current",
        "suppression": "clear",
        "enforcement_posture": "mechanically_enforced",
        "correlation_ref": "trace:1",
        "observed_at": "2026-08-13T13:15:00Z",
    }
    values.update(changes)
    return normalize_influence(**values)


class ConditionalMemoryInfluenceGateTests(unittest.TestCase):
    def test_current_matching_table_is_eligible(self):
        result = record()
        self.assertEqual(result["gate"]["result"], "allow")
        self.assertTrue(result["gate"]["influence_eligible"])

    def test_revoked_and_deleted_residue_can_resolve_but_are_blocked(self):
        for state in ("revoked", "deleted_residue", "stale"):
            with self.subTest(state=state):
                result = record(currentness=state)
                self.assertEqual(result["gate"]["result"], "block_stale")
                self.assertFalse(result["gate"]["influence_eligible"])
        self.assertIn("external_deletion_is_not_internal_forgetting", record(currentness="deleted_residue")["nonclaims"])

    def test_partition_mismatch_blocks_before_influence(self):
        result = record(request=request("tenant-b/project-b"))
        self.assertEqual(result["gate"]["result"], "block_scope")

    def test_suppression_overlay_blocks_current_table(self):
        result = record(suppression="suppressed")
        self.assertEqual(result["gate"]["result"], "block_suppressed")

    def test_unknown_evidence_and_unsupported_format_fail_closed(self):
        for changes in (
            {"currentness": "unknown"},
            {"suppression": "unknown"},
            {"table": table(partition=None)},
            {"table_version_supported": False},
        ):
            with self.subTest(changes=changes):
                result = record(**changes)
                self.assertEqual(result["gate"]["result"], "block_unknown")
                self.assertFalse(result["gate"]["influence_eligible"])

    def test_research_currentness_maps_without_peer_vocabulary_leak(self):
        self.assertEqual(map_currentness("current", "current"), "current")
        self.assertEqual(map_currentness("revalidation_required", "revoked"), "revoked")
        self.assertEqual(map_currentness("revalidation_required", "deleted"), "deleted_residue")
        self.assertEqual(map_currentness("revalidation_required", "current"), "stale")
        self.assertEqual(map_currentness(None, None), "unknown")

    def test_evidence_is_minimized(self):
        result = record(address={"token_ids": [101, 202], "heads": [3, 7]})
        encoded = str(result)
        self.assertNotIn("token_ids", encoded)
        self.assertNotIn("[101, 202]", encoded)
        self.assertRegex(result["opaque_address_digest"], r"^sha256:[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
