#!/usr/bin/env python3
"""Validate the bounded #304 Atlas corpus synthesis.

This validator intentionally checks exact mechanism/pattern sets rather than merely
checking counts. A missing item must fail closed instead of being replaced by a
new item that happens to preserve the same total.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SYNTHESIS = ROOT / "docs/programs/atlas-research/corpus-synthesis.json"
ATLAS_COMMIT = "90bfeed14764e268c82c925d4c39645c7480d015"

EXPECTED_MECHANISMS = {
    "rejected_value_tombstone",
    "explicit_trust_state",
    "bitemporal_validity",
    "scope_enforced_in_retrieval",
    "append_only_mutation_audit",
    "human_review_surface",
    "negative_retrieval_assertion",
}

EXPECTED_PATTERNS = {
    "append-only-memory-audit",
    "bi-temporal-fact-validity",
    "cache-preserving-injection",
    "decay-and-reinforcement",
    "evidence-before-belief",
    "explicit-write-destination",
    "gate-the-expensive-path",
    "governed-write-gateway",
    "hybrid-retrieval-fusion",
    "pluggable-memory-provider",
    "promotion-between-tiers",
    "recoverable-background-work",
    "scope-as-a-first-class-key",
    "skills-as-procedural-memory",
    "trust-state-machine",
    "zero-llm-capture",
    "rejected-value-tombstone",
    "resolve-not-just-detect",
    "source-diverse-context",
    "retrieval-hysteresis",
    "memory-as-an-editing-surface",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def exact_ids(records: object, key: str, expected: set[str], label: str) -> None:
    require(isinstance(records, list), f"{label} must be an array")
    values = [record.get(key) for record in records if isinstance(record, dict)]
    require(len(values) == len(records), f"{label} entries must be objects")
    require(len(values) == len(set(values)), f"{label} contains duplicate {key} values")
    observed = set(values)
    missing = sorted(expected - observed)
    extra = sorted(observed - expected)
    require(not missing and not extra, f"{label} set drift: missing={missing} extra={extra}")


def main() -> int:
    data = json.loads(SYNTHESIS.read_text(encoding="utf-8"))

    require(data.get("schema_version") == "1.0.0", "synthesis schema_version must be 1.0.0")
    require(data.get("research_program") == "#304", "synthesis must remain bound to #304")
    require(data.get("atlas_snapshot") == ATLAS_COMMIT, "Atlas snapshot drifted")
    require(data.get("source_posture") == "secondary_source_index_and_hypothesis_generator", "Atlas source posture changed")
    require(data.get("authority_effect") == "none", "Atlas synthesis cannot create authority")
    require(data.get("doctrine_disposition") == "no_new_adr", "Atlas synthesis cannot silently create doctrine")

    head = data.get("agent_memory_evidence_boundary")
    require(isinstance(head, str) and len(head) == 40 and head == head.lower(), "Agent Memory evidence boundary must be 40 lowercase hex")
    try:
        int(head, 16)
    except ValueError as exc:
        raise SystemExit("Agent Memory evidence boundary must be hexadecimal") from exc

    counts = data.get("counts", {})
    require(counts.get("system_reports") == 283, "pinned Atlas report count must be 283")
    require(counts.get("design_patterns") == 21, "pinned Atlas pattern count must be 21")
    require(counts.get("atlas_mechanisms") == 7, "Atlas mechanism count must be 7")
    require(counts.get("verified_claim_ledger_minimum", 0) >= 8, "verified claim floor cannot regress below 8")

    exact_ids(data.get("mechanisms"), "mechanism_id", EXPECTED_MECHANISMS, "mechanisms")
    exact_ids(data.get("patterns"), "pattern_id", EXPECTED_PATTERNS, "patterns")

    for mechanism in data["mechanisms"]:
        require(mechanism.get("agent_memory_surfaces"), f"mechanism {mechanism['mechanism_id']} lacks Agent Memory surfaces")
        require(isinstance(mechanism.get("novel_gap"), bool), f"mechanism {mechanism['mechanism_id']} novel_gap must be boolean")
        require(mechanism.get("rationale"), f"mechanism {mechanism['mechanism_id']} lacks rationale")

    for pattern in data["patterns"]:
        require(pattern.get("atlas_stance") in {"established", "advocacy", "mixed", "category_bound"}, f"pattern {pattern['pattern_id']} has invalid stance")
        require(pattern.get("disposition"), f"pattern {pattern['pattern_id']} lacks disposition")
        require(pattern.get("agent_memory_surfaces"), f"pattern {pattern['pattern_id']} lacks Agent Memory surfaces")

    benchmarks = data.get("benchmarks")
    require(isinstance(benchmarks, list) and len(benchmarks) >= 4, "benchmark synthesis must retain verified benchmark set")
    for benchmark in benchmarks:
        require(benchmark.get("verification", "").startswith("primary"), f"benchmark {benchmark.get('benchmark')} is not primary-source verified")
        require(benchmark.get("disposition"), f"benchmark {benchmark.get('benchmark')} lacks disposition")

    comparators = data.get("comparators")
    require(isinstance(comparators, list) and comparators, "comparator ranking must not be empty")
    ranks = [entry.get("rank") for entry in comparators]
    require(ranks == list(range(1, len(comparators) + 1)), "comparator ranks must be contiguous and deterministic")
    for comparator in comparators:
        require(comparator.get("distinct_value"), f"comparator {comparator.get('system')} lacks distinct value")
        require(comparator.get("owners"), f"comparator {comparator.get('system')} lacks Agent Memory owner")

    self_audit = data.get("agent_memory_self_audit")
    require(isinstance(self_audit, list) and len(self_audit) >= 6, "Agent Memory Atlas self-audit is incomplete")
    require(any(item.get("atlas_claim") == "no dependency manifest" and item.get("current_status") == "fixed" for item in self_audit), "dependency-manifest reconciliation is missing")

    promotions = data.get("promotions")
    require(isinstance(promotions, list) and promotions, "promoted findings must be recorded")
    for promotion in promotions:
        require(promotion.get("evidence"), f"promotion {promotion.get('finding')} lacks evidence")
        require(promotion.get("doctrine_change") == "none", f"promotion {promotion.get('finding')} silently changes doctrine")

    rejections = data.get("rejections")
    require(isinstance(rejections, list) and rejections, "rejection/no-action ledger must not be empty")
    require(any("maturity score" in item.get("claim", "") for item in rejections), "Goodhart/maturity-score rejection must remain explicit")

    completion = data.get("completion")
    require(isinstance(completion, dict) and completion, "completion map is missing")
    incomplete = sorted(key for key, value in completion.items() if value is not True)
    require(not incomplete, f"#304 completion flags not satisfied: {incomplete}")

    print(
        "atlas-research-synthesis: valid "
        f"mechanisms={len(data['mechanisms'])} patterns={len(data['patterns'])} "
        f"benchmarks={len(benchmarks)} comparators={len(comparators)} "
        f"rejections={len(rejections)} authority_effect={data['authority_effect']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
