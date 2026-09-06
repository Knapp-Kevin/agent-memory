"""P6 adversarial comparator for the Mem0 OSS memory layer.

The comparator executes Mem0's real Memory class, Qdrant-backed local vector
store, and SQLite history at a pinned package version. Only the external model
construction seams are replaced with deterministic local doubles so CI needs no
credentials and does not measure model variance.

Observed behavior is classified with the runtime-evidence program's existing
five-value vocabulary. A gap against Agent Memory is not automatically a Mem0
bug: the comparator measures what the external system provides and separately
states what an Agent Memory wrapper would still have to enforce.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import math
import os
import tempfile
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from . import receipts

MEM0_PACKAGE = "mem0ai"
MEM0_VERSION = "2.0.18"
REPORT_TYPE = "agent-memory-p6-mem0-comparator"
REPORT_VERSION = "1.0.0"

NATIVE = "NATIVE"
CONFIGURABLE = "CONFIGURABLE"
WRAPPER_REQUIRED = "WRAPPER_REQUIRED"
NOT_REPRESENTABLE = "NOT_REPRESENTABLE"
UNKNOWN_NEEDS_TEST = "UNKNOWN_NEEDS_TEST"
CLASSIFICATIONS = {
    NATIVE,
    CONFIGURABLE,
    WRAPPER_REQUIRED,
    NOT_REPRESENTABLE,
    UNKNOWN_NEEDS_TEST,
}


class DeterministicEmbedder:
    """Small credential-free embedder used only to drive Mem0 storage/search."""

    def __init__(self, dims: int = 8):
        self.config = SimpleNamespace(embedding_dims=dims)
        self._dims = dims

    def embed(self, text: str, memory_action: str | None = None):
        if not isinstance(text, str):
            text = str(text)
        values = [0.25] * self._dims
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        for index, byte in enumerate(digest):
            values[index % self._dims] += byte / 255.0
        norm = math.sqrt(sum(value * value for value in values)) or 1.0
        return [value / norm for value in values]

    def embed_batch(self, texts, memory_action: str | None = None):
        return [self.embed(text, memory_action) for text in texts]


class UnusedLLM:
    """Construction double. P6 uses infer=False, so generation must never run."""

    def __init__(self):
        self.config = {}

    def generate_response(self, *args, **kwargs):  # pragma: no cover - must remain unreachable
        raise AssertionError("P6 Mem0 comparator invoked the LLM despite infer=False")


def _scenario(classification: str, passed: bool, observations: dict, wrapper_implication: str) -> dict:
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"unknown comparator classification: {classification}")
    return {
        "classification": classification,
        "passed": bool(passed),
        "observations": observations,
        "agent_memory_wrapper_implication": wrapper_implication,
    }


def evaluate_report(report: dict) -> bool:
    """Fail closed if execution failed or an unknown classification appears."""
    scenarios = report.get("scenarios", {})
    if not scenarios:
        return False
    for scenario in scenarios.values():
        if scenario.get("classification") not in CLASSIFICATIONS:
            return False
        if scenario.get("passed") is not True:
            return False
    return True


def _ids(result: dict) -> set[str]:
    return {str(item["id"]) for item in result.get("results", [])}


def _history_has(history: list[dict], event: str, *, old=None, new=None, deleted=None) -> bool:
    for item in history:
        if item.get("event") != event:
            continue
        if old is not None and item.get("old_memory") != old:
            continue
        if new is not None and item.get("new_memory") != new:
            continue
        if deleted is not None and bool(item.get("is_deleted")) != deleted:
            continue
        return True
    return False


def run_mem0_comparator(agent_memory_commit: str) -> dict:
    commit = agent_memory_commit.lower()
    if len(commit) != 40 or any(ch not in "0123456789abcdef" for ch in commit):
        raise ValueError("agent_memory_commit must be an exact 40-hex commit")

    # Must be set before Mem0's telemetry module is imported.
    os.environ["MEM0_TELEMETRY"] = "false"
    installed_version = importlib.metadata.version(MEM0_PACKAGE)
    if installed_version != MEM0_VERSION:
        raise RuntimeError(f"expected {MEM0_PACKAGE}=={MEM0_VERSION}, found {installed_version}")

    import mem0.memory.main as mem0_main  # noqa: PLC0415

    embedder = DeterministicEmbedder(dims=8)
    with tempfile.TemporaryDirectory(prefix="agent-memory-p6-mem0-") as tmp:
        root = Path(tmp)
        config = {
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "agent_memory_p6",
                    "path": str(root / "qdrant"),
                    "embedding_model_dims": 8,
                },
            },
            "embedder": {"provider": "openai", "config": {}},
            "llm": {"provider": "openai", "config": {}},
            "history_db_path": str(root / "history.db"),
        }

        with ExitStack() as stack:
            stack.enter_context(patch.object(mem0_main.EmbedderFactory, "create", return_value=embedder))
            stack.enter_context(patch.object(mem0_main.LlmFactory, "create", return_value=UnusedLLM()))
            memory = mem0_main.Memory.from_config(config)
            try:
                scenarios = _execute_scenarios(memory)
            finally:
                memory.close()

    report = {
        "report_type": REPORT_TYPE,
        "version": REPORT_VERSION,
        "agent_memory_commit": commit,
        "comparator": {
            "repository": "mem0ai/mem0",
            "package": MEM0_PACKAGE,
            "package_version": installed_version,
            "release": f"v{installed_version}",
            "license": "Apache-2.0",
        },
        "execution": {
            "memory_implementation": "mem0.memory.main.Memory",
            "vector_store": "Mem0 VectorStoreFactory -> local Qdrant",
            "history_store": "Mem0 SQLiteManager",
            "inference": "infer=False; no LLM extraction invoked",
            "embedder_boundary": "Mem0 embedder factory replaced by deterministic 8-dimensional local double",
            "llm_boundary": "Mem0 LLM factory replaced by construction-only local double; generation is forbidden",
            "telemetry": "MEM0_TELEMETRY=false before import",
            "external_credentials_required": False,
        },
        "classification_vocabulary": sorted(CLASSIFICATIONS),
        "scenarios": scenarios,
        "execution_success": False,
        "known_limits": [
            "This executes Mem0 OSS Python 2.0.18 with local Qdrant and SQLite history; it does not test the hosted Mem0 platform or its authorization controls.",
            "LLM extraction quality is intentionally out of scope. infer=False preserves Mem0 persistence, scope, update, delete, history, and vector-store behavior while removing external model variance.",
            "The deterministic embedder is a test driver, not a retrieval-quality benchmark. Search is used only to test scope filtering, not relevance quality.",
            "Physical deletion from the tested Mem0 vector store plus a DELETE history event is not evidence of transitive forgetting across every possible derived representation.",
            "Direct-ID APIs are classified as an Agent Memory wrapper boundary, not alleged to be a Mem0 vulnerability or product defect.",
            "No Agent Memory conformance level or ADR status changes as a result of this comparator.",
        ],
    }
    report["execution_success"] = evaluate_report(report)
    receipts.validate("mem0-comparator-report.schema.json", report)
    return report


def _execute_scenarios(memory) -> dict:
    user_a = "user:p6:a"
    user_b = "user:p6:b"

    added_a = memory.add("alpha private memory", user_id=user_a, infer=False)
    added_b = memory.add("beta private memory", user_id=user_b, infer=False)
    id_a = str(added_a["results"][0]["id"])
    id_b = str(added_b["results"][0]["id"])

    all_a = memory.get_all(filters={"user_id": user_a}, top_k=20)
    all_b = memory.get_all(filters={"user_id": user_b}, top_k=20)
    search_a = memory.search("private memory", filters={"user_id": user_a}, top_k=20, threshold=0.0)
    search_b = memory.search("private memory", filters={"user_id": user_b}, top_k=20, threshold=0.0)
    scoped_passed = (
        id_a in _ids(all_a)
        and id_b not in _ids(all_a)
        and id_b in _ids(all_b)
        and id_a not in _ids(all_b)
        and id_b not in _ids(search_a)
        and id_a not in _ids(search_b)
    )
    scoped = _scenario(
        CONFIGURABLE,
        scoped_passed,
        {
            "user_a_get_all_ids": sorted(_ids(all_a)),
            "user_b_get_all_ids": sorted(_ids(all_b)),
            "user_a_search_cross_scope_hits": len(_ids(search_a) & {id_b}),
            "user_b_search_cross_scope_hits": len(_ids(search_b) & {id_a}),
            "query_api_requires_entity_filter": True,
        },
        "Mem0's tested query paths require and honor caller-supplied entity filters, but Agent Memory must still bind those identifiers to authenticated scope/authority rather than trust caller choice alone.",
    )

    laundering = memory.add(
        "identity laundering probe",
        user_id=user_a,
        metadata={"user_id": user_b, "probe": "identity-laundering"},
        infer=False,
    )
    laundering_id = str(laundering["results"][0]["id"])
    laundering_record = memory.get(laundering_id)
    laundering_passed = (
        laundering_record is not None
        and laundering_record.get("user_id") == user_a
        and laundering_record.get("metadata", {}).get("probe") == "identity-laundering"
    )
    identity = _scenario(
        NATIVE,
        laundering_passed,
        {
            "explicit_user_id": user_a,
            "metadata_attempted_user_id": user_b,
            "stored_user_id": laundering_record.get("user_id") if laundering_record else None,
        },
        "The tested creation path natively strips identity fields from freeform metadata. Agent Memory still supplies principal authentication and authority semantics above that identity hygiene.",
    )

    correction = memory.add("old correction value", user_id=user_a, infer=False)
    correction_id = str(correction["results"][0]["id"])
    memory.update(
        correction_id,
        text="new correction value",
        metadata={"user_id": user_b, "correction_note": "updated"},
    )
    corrected = memory.get(correction_id)
    correction_history = memory.history(correction_id)
    correction_passed = (
        corrected is not None
        and str(corrected.get("id")) == correction_id
        and corrected.get("memory") == "new correction value"
        and corrected.get("user_id") == user_a
        and corrected.get("metadata", {}).get("correction_note") == "updated"
        and _history_has(
            correction_history,
            "UPDATE",
            old="old correction value",
            new="new correction value",
        )
    )
    correction_scenario = _scenario(
        NATIVE,
        correction_passed,
        {
            "memory_id_stable": corrected is not None and str(corrected.get("id")) == correction_id,
            "stored_user_id_after_update": corrected.get("user_id") if corrected else None,
            "update_history_recorded": _history_has(
                correction_history,
                "UPDATE",
                old="old correction value",
                new="new correction value",
            ),
            "history_event_count": len(correction_history),
        },
        "Mem0 natively preserves ID and immutable session identity on this update path and records UPDATE history. Agent Memory must still govern who may correct and how correction propagates to derived state.",
    )

    deletion = memory.add("delete me completely", user_id=user_a, infer=False)
    deletion_id = str(deletion["results"][0]["id"])
    memory.delete(deletion_id)
    deleted_live = memory.get(deletion_id)
    deletion_history = memory.history(deletion_id)
    deletion_passed = deleted_live is None and _history_has(
        deletion_history,
        "DELETE",
        old="delete me completely",
        deleted=True,
    )
    deletion_scenario = _scenario(
        WRAPPER_REQUIRED,
        deletion_passed,
        {
            "live_record_after_delete": deleted_live is not None,
            "delete_history_recorded": _history_has(
                deletion_history,
                "DELETE",
                old="delete me completely",
                deleted=True,
            ),
            "history_retains_prior_memory_text": any(
                item.get("event") == "DELETE" and item.get("old_memory") == "delete me completely"
                for item in deletion_history
            ),
        },
        "Mem0 natively performs physical vector deletion and records a DELETE history event, but Agent Memory forgetting completeness requires governed treatment and independent residue measurement across derived representations.",
    )

    direct = memory.add("direct id boundary", user_id=user_b, infer=False)
    direct_id = str(direct["results"][0]["id"])
    direct_get = memory.get(direct_id)
    memory.update(direct_id, text="direct id updated")
    direct_history_before_delete = memory.history(direct_id)
    memory.delete(direct_id)
    direct_history_after_delete = memory.history(direct_id)
    direct_passed = (
        direct_get is not None
        and direct_get.get("user_id") == user_b
        and _history_has(direct_history_before_delete, "UPDATE", old="direct id boundary", new="direct id updated")
        and _history_has(direct_history_after_delete, "DELETE", old="direct id updated", deleted=True)
    )
    direct_scenario = _scenario(
        WRAPPER_REQUIRED,
        direct_passed,
        {
            "get_accepts_scope_argument": False,
            "update_accepts_scope_argument": False,
            "delete_accepts_scope_argument": False,
            "history_accepts_scope_argument": False,
            "direct_get_succeeded": direct_get is not None,
            "direct_update_succeeded": _history_has(
                direct_history_before_delete, "UPDATE", old="direct id boundary", new="direct id updated"
            ),
            "direct_delete_succeeded": _history_has(
                direct_history_after_delete, "DELETE", old="direct id updated", deleted=True
            ),
        },
        "Agent Memory cannot treat possession of a memory ID as authorization. A wrapper must bind direct-ID operations to principal, scope, purpose, policy, and current authority state before invoking this seam.",
    )

    bulk_a = memory.add("bulk delete A", user_id=user_a, infer=False)
    bulk_b = memory.add("bulk preserve B", user_id=user_b, infer=False)
    bulk_a_id = str(bulk_a["results"][0]["id"])
    bulk_b_id = str(bulk_b["results"][0]["id"])
    unscoped_rejected = False
    try:
        memory.delete_all()
    except ValueError:
        unscoped_rejected = True
    memory.delete_all(user_id=user_a)
    remaining_a = memory.get_all(filters={"user_id": user_a}, top_k=100)
    remaining_b = memory.get_all(filters={"user_id": user_b}, top_k=100)
    bulk_passed = (
        unscoped_rejected
        and bulk_a_id not in _ids(remaining_a)
        and bulk_b_id in _ids(remaining_b)
        and id_b in _ids(remaining_b)
    )
    bulk = _scenario(
        CONFIGURABLE,
        bulk_passed,
        {
            "unscoped_delete_all_rejected": unscoped_rejected,
            "user_a_bulk_target_remaining": bulk_a_id in _ids(remaining_a),
            "user_b_bulk_target_remaining": bulk_b_id in _ids(remaining_b),
            "user_b_seed_remaining": id_b in _ids(remaining_b),
        },
        "The tested bulk-delete API requires caller-supplied entity scope and preserves other scoped records. Agent Memory must still authorize the requested scope and verify downstream deletion completeness.",
    )

    return {
        "scoped_accumulation_and_retrieval": scoped,
        "metadata_identity_laundering": identity,
        "correction_and_update_history": correction_scenario,
        "deletion_and_history": deletion_scenario,
        "direct_id_boundary": direct_scenario,
        "scoped_bulk_deletion": bulk,
    }
