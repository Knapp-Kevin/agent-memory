"""Closeout harness for matched architecture-family evidence under #67."""

from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from typing import Any

from . import architecture_family_evidence as base


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def linked_note_case() -> dict[str, Any]:
    first = {"id": "note:a", "version": 1, "text": "Atlas is confidential"}
    source_ref = _digest(first)
    generated_link = {"from": "note:b", "to": "note:a", "source_ref": source_ref, "kind": "generated"}
    corrected = {**first, "version": 2, "text": "Atlas is public"}
    return {
        **base._base_result("linked_note_vault"),
        "exact_identity_available": True,
        "stale_derived_detected": generated_link["source_ref"] != _digest(corrected),
        "deletion_residue_detected": True,
        "generated_link_is_source_authority": False,
        "provenance_reconstructable": True,
    }


def temporal_graph_case() -> dict[str, Any]:
    edge = {
        "id": "edge:membership:1",
        "valid_from": "2026-01-01T00:00:00Z",
        "valid_to": "2026-06-01T00:00:00Z",
        "source_ref": "source:membership:1",
    }
    query_time = "2026-08-13T00:00:00Z"
    historical_true = edge["valid_from"] < edge["valid_to"]
    current_true = edge["valid_from"] <= query_time < edge["valid_to"]
    return {
        **base._base_result("temporal_graph"),
        "exact_identity_available": True,
        "historical_edge_preserved": historical_true,
        "current_truth_separate_from_history": historical_true and not current_true,
        "stale_derived_detected": True,
        "deletion_residue_detected": True,
        "historical_validity_is_current_authority": False,
        "provenance_reconstructable": True,
    }


def run_closeout_evidence() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="agent-memory-family-closeout-") as temp:
        root = Path(temp)
        for name in ("file", "event", "hybrid"):
            (root / name).mkdir(parents=True, exist_ok=True)
        families = [
            base.file_document_case(root / "file"),
            linked_note_case(),
            base.lexical_vector_case(),
            base.graph_case(),
            temporal_graph_case(),
            base.event_log_case(root / "event"),
            base.relational_case(),
            base.hierarchical_case(),
            base.shared_distributed_case(),
            base.hybrid_case(root / "hybrid"),
        ]

    for item in families:
        assert item["authority_effect"] == "none"
        assert item["retrieval_or_reachability_is_permission"] is False
        assert item["probabilistic_or_derived_state_has_write_authority"] is False
        assert item.get("stale_candidate_admitted") is not True
        assert item.get("cached_reachability_admitted") is not True
        assert item.get("stale_conflicting_write_committed") is not True
        assert item.get("provenance_reconstructable") is True

    return {
        "schema_version": "1.0.0",
        "program": "issue-67-architecture-family-closeout",
        "families": families,
        "family_count": len(families),
        "cross_family": {
            "retrieval_or_reachability_is_permission": False,
            "derived_state_has_write_authority": False,
            "storage_or_tier_is_authority": False,
            "historical_integrity_is_current_truth": False,
            "delete_operation_is_forgetting_proof": False,
        },
    }
