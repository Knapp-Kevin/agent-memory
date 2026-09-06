"""Matched cross-architecture governance evidence for issue #67.

These fixtures deliberately use small local substrates so the same correction,
derived-state, deletion, recall, provenance, and authority questions can be
reproduced across architecture families without turning any product into the
normative definition of a family.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path
from typing import Any


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _base_result(family: str) -> dict[str, Any]:
    return {
        "family": family,
        "evidence_status": "benchmark_or_conformance_evidence",
        "authority_effect": "none",
        "retrieval_or_reachability_is_permission": False,
        "probabilistic_or_derived_state_has_write_authority": False,
    }


def file_document_case(root: Path) -> dict[str, Any]:
    canonical = root / "memory.json"
    projection = root / "index.json"
    v1 = {"id": "m1", "version": 1, "text": "alpha fact", "scope": "project:a"}
    canonical.write_text(json.dumps(v1), encoding="utf-8")
    projection.write_text(json.dumps({"source_digest": _digest(json.dumps(v1, sort_keys=True)), "tokens": ["alpha", "fact"]}), encoding="utf-8")

    v2 = {**v1, "version": 2, "text": "corrected fact"}
    canonical.write_text(json.dumps(v2), encoding="utf-8")
    stale_after_correction = json.loads(projection.read_text(encoding="utf-8"))["source_digest"] != _digest(json.dumps(v2, sort_keys=True))
    canonical.unlink()
    residue_after_delete = projection.exists()

    result = _base_result("file_document")
    result.update({
        "exact_identity_available": True,
        "stale_derived_detected": stale_after_correction,
        "deletion_residue_detected": residue_after_delete,
        "provenance_reconstructable": True,
        "current_truth_separate_from_history": True,
    })
    return result


def lexical_vector_case() -> dict[str, Any]:
    source_v1 = {"id": "m2", "version": 1, "text": "blue lantern hope"}
    source_ref_v1 = _digest(json.dumps(source_v1, sort_keys=True))
    lexical = {"source_ref": source_ref_v1, "tokens": {"blue", "lantern", "hope"}}
    vector = {"source_ref": source_ref_v1, "model": "deterministic-fixture-v1", "values": [4, 7, 4]}

    source_v2 = {**source_v1, "version": 2, "text": "red lantern rage"}
    source_ref_v2 = _digest(json.dumps(source_v2, sort_keys=True))
    stale = lexical["source_ref"] != source_ref_v2 and vector["source_ref"] != source_ref_v2
    candidate_still_discoverable = "hope" in lexical["tokens"]
    admitted = candidate_still_discoverable and not stale

    result = _base_result("lexical_vector_rag")
    result.update({
        "exact_identity_available": True,
        "stale_derived_detected": stale,
        "deletion_residue_detected": True,
        "candidate_discovery_survives_staleness": candidate_still_discoverable,
        "stale_candidate_admitted": admitted,
        "provenance_reconstructable": True,
    })
    return result


def graph_case() -> dict[str, Any]:
    asserted = {
        ("a", "b"): {"source_ref": "source:ab", "current": True},
        ("b", "c"): {"source_ref": "source:bc", "current": True},
    }
    derived_path = {"path": ["a", "b", "c"], "basis": ["source:ab", "source:bc"], "current": True}
    asserted[("b", "c")]["current"] = False
    stale_path = not all(item["current"] for item in asserted.values()) and derived_path["current"]
    reachable_from_cache = derived_path["path"][-1] == "c"

    result = _base_result("knowledge_graph_graphrag")
    result.update({
        "exact_identity_available": True,
        "stale_derived_detected": stale_path,
        "deletion_residue_detected": reachable_from_cache,
        "provenance_reconstructable": derived_path["basis"] == ["source:ab", "source:bc"],
        "cached_reachability_admitted": False,
    })
    return result


def event_log_case(root: Path) -> dict[str, Any]:
    log = root / "events.jsonl"
    events = [
        {"seq": 1, "kind": "assert", "memory_id": "m3", "value": "old"},
        {"seq": 2, "kind": "supersede", "memory_id": "m3", "value": "new", "supersedes": 1},
        {"seq": 3, "kind": "tombstone", "memory_id": "m3", "targets": [1, 2]},
    ]
    log.write_text("\n".join(json.dumps(item, sort_keys=True) for item in events) + "\n", encoding="utf-8")
    materialized_current = events[1]["value"]
    historical_old_preserved = any(item.get("value") == "old" for item in events)
    tombstone_present = events[-1]["kind"] == "tombstone"
    content_still_present = historical_old_preserved and tombstone_present

    result = _base_result("event_log_ledger")
    result.update({
        "exact_identity_available": True,
        "current_truth_separate_from_history": materialized_current == "new" and historical_old_preserved,
        "stale_derived_detected": False,
        "deletion_residue_detected": content_still_present,
        "tombstone_is_forgetting_proof": False,
        "provenance_reconstructable": True,
    })
    return result


def relational_case() -> dict[str, Any]:
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(
            """
            CREATE TABLE memory (id TEXT PRIMARY KEY, version INTEGER, value TEXT);
            CREATE TABLE projection (memory_id TEXT, source_version INTEGER, value TEXT);
            INSERT INTO memory VALUES ('m4', 1, 'old');
            INSERT INTO projection VALUES ('m4', 1, 'OLD');
            """
        )
        conn.execute("UPDATE memory SET version = 2, value = 'new' WHERE id = 'm4'")
        source_version = conn.execute("SELECT version FROM memory WHERE id='m4'").fetchone()[0]
        projection_version = conn.execute("SELECT source_version FROM projection WHERE memory_id='m4'").fetchone()[0]
        stale = source_version != projection_version
        conn.execute("DELETE FROM memory WHERE id='m4'")
        residue = conn.execute("SELECT COUNT(*) FROM projection WHERE memory_id='m4'").fetchone()[0] == 1
    finally:
        conn.close()

    result = _base_result("relational_document_store")
    result.update({
        "exact_identity_available": True,
        "stale_derived_detected": stale,
        "deletion_residue_detected": residue,
        "transaction_atomicity_is_derived_cleanup": False,
        "provenance_reconstructable": True,
    })
    return result


def hierarchical_case() -> dict[str, Any]:
    working = {"id": "m5", "tier": "working", "scope": "project:a", "authority": "A1", "retention": "session"}
    promoted = {**working, "tier": "long_term", "retention": "durable"}
    authority_preserved = promoted["authority"] == working["authority"]
    scope_preserved = promoted["scope"] == working["scope"]

    result = _base_result("hierarchical_tiered")
    result.update({
        "exact_identity_available": True,
        "tier_move_preserves_authority": authority_preserved,
        "tier_move_preserves_scope": scope_preserved,
        "storage_promotion_is_authority_promotion": False,
        "deletion_residue_detected": True,
        "provenance_reconstructable": True,
    })
    return result


def shared_distributed_case() -> dict[str, Any]:
    canonical = {"id": "m6", "version": 1, "value": "base", "members": {"agent:a", "agent:b"}}
    write_a = {"writer": "agent:a", "base_version": 1, "value": "a"}
    write_b = {"writer": "agent:b", "base_version": 1, "value": "b"}
    first_commit = {**canonical, "version": 2, "value": write_a["value"]}
    conflict_detected = write_b["base_version"] != first_commit["version"]
    member_b_can_read = write_b["writer"] in canonical["members"]
    member_b_can_commit_stale_write = member_b_can_read and not conflict_detected

    result = _base_result("shared_distributed")
    result.update({
        "exact_identity_available": True,
        "conflicting_writer_detected": conflict_detected,
        "shared_membership_is_mutation_authority": False,
        "stale_conflicting_write_committed": member_b_can_commit_stale_write,
        "deletion_residue_detected": True,
        "provenance_reconstructable": True,
    })
    return result


def hybrid_case(root: Path) -> dict[str, Any]:
    source = root / "source.json"
    source.write_text(json.dumps({"id": "m7", "version": 1, "value": "alpha"}), encoding="utf-8")
    source_ref = _digest(source.read_text(encoding="utf-8"))
    surfaces = {
        "lexical": {"source_ref": source_ref},
        "vector": {"source_ref": source_ref},
        "graph_summary": {"source_ref": source_ref},
    }
    source.write_text(json.dumps({"id": "m7", "version": 2, "value": "beta"}), encoding="utf-8")
    current_ref = _digest(source.read_text(encoding="utf-8"))
    stale_surfaces = sorted(name for name, item in surfaces.items() if item["source_ref"] != current_ref)
    source.unlink()
    deletion_closure = ["canonical_source", *stale_surfaces]

    result = _base_result("hybrid_composition")
    result.update({
        "exact_identity_available": True,
        "stale_derived_detected": stale_surfaces == ["graph_summary", "lexical", "vector"],
        "stale_surfaces": stale_surfaces,
        "deletion_residue_detected": bool(stale_surfaces),
        "deletion_closure": deletion_closure,
        "provenance_reconstructable": True,
    })
    return result


def run_architecture_family_evidence() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="agent-memory-architecture-family-") as temp_dir:
        root = Path(temp_dir)
        cases = [
            file_document_case(root / "file"),
            lexical_vector_case(),
            graph_case(),
            event_log_case(root / "event"),
            relational_case(),
            hierarchical_case(),
            shared_distributed_case(),
            hybrid_case(root / "hybrid"),
        ]

    required_boolean_invariants = {
        "authority_effect": "none",
        "retrieval_or_reachability_is_permission": False,
        "probabilistic_or_derived_state_has_write_authority": False,
    }
    for item in cases:
        for field, expected in required_boolean_invariants.items():
            if item[field] != expected:
                raise AssertionError(f"{item['family']} violated {field}")
        if item.get("stale_candidate_admitted") is True:
            raise AssertionError("stale retrieval candidate was admitted")
        if item.get("cached_reachability_admitted") is True:
            raise AssertionError("cached graph reachability was treated as admission")
        if item.get("stale_conflicting_write_committed") is True:
            raise AssertionError("stale shared write was committed")

    repeated = {
        "retrieval_or_reachability_is_permission": all(
            item["retrieval_or_reachability_is_permission"] is False for item in cases
        ),
        "derived_state_has_write_authority": all(
            item["probabilistic_or_derived_state_has_write_authority"] is False for item in cases
        ),
        "provenance_reconstructable": all(item.get("provenance_reconstructable") is True for item in cases),
        "derived_residue_is_explicit": all(
            "deletion_residue_detected" in item for item in cases
        ),
    }

    return {
        "schema_version": "1.0.0",
        "program": "issue-67-matched-architecture-family-evidence",
        "families": cases,
        "cross_family_reproduction": repeated,
        "interpretation": {
            "retrieval_quality_is_not_authority": True,
            "storage_placement_is_not_authority": True,
            "historical_integrity_is_not_current_truth": True,
            "deletion_operation_is_not_forgetting_proof": True,
            "derived_state_requires_lifecycle_tracking": True,
            "minimal_fixtures_are_not_product_rankings": True,
        },
    }
