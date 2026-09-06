"""Drive the doctrine fixture corpus through executable conformance checks.

The governance-path tests assert that the adapter behaves correctly on
scenarios written alongside the adapter. This module does something harder:
it takes the repository's independently authored conformance fixtures and
runs declared authority envelopes through the same enforcement function the
adapter uses, while also checking selected cross-cutting fixture contracts.

What is checked, per fixture carrying an authority envelope:

1. permitted and prohibited action sets are disjoint;
2. the declared selection is a member of the permitted set;
3. the declared selection is not a prohibited action;
4. every prohibited action is rejected by that same enforcement rule; and
5. a fixture expecting no crystallization does not permit one.

Fixtures carrying ``epistemic_promotion`` additionally prove that evidence
lineage, not retrieval/use volume, determines independent-origin count; that
derived evidence cannot silently invent a new origin; and that corroboration
does not itself satisfy a separate certification gate.

What is not checked is listed in ``exemptions()``. Decay, calibration,
retrieval ranking, and most lifecycle transition mechanics are outside this
adapter, and a runner that silently skipped them would misrepresent coverage.

Stdlib only apart from schema validation reached through ``receipts``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..core import receipts
from .._paths import REPO_ROOT

FIXTURE_DIR = REPO_ROOT / "fixtures"


def load_fixtures(fixture_dir: Path | None = None) -> list[tuple[str, dict]]:
    directory = fixture_dir or FIXTURE_DIR
    return [
        (path.stem, json.loads(path.read_text(encoding="utf-8")))
        for path in sorted(directory.glob("*.json"))
    ]


def _envelopes(fixture: dict) -> list[tuple[str, dict]]:
    """Every authority envelope a fixture declares, named by where it came from."""
    found: list[tuple[str, dict]] = []
    governed = fixture.get("governed_uncertainty")
    if isinstance(governed, dict):
        found.append(("governed_uncertainty", governed))
    authority = fixture.get("memory_unit", {}).get("authority")
    if isinstance(authority, dict) and ("permitted_actions" in authority or "prohibited_actions" in authority):
        found.append(("memory_unit.authority", authority))
    return found


def check_envelope(source: str, envelope: dict) -> list[str]:
    permitted = tuple(envelope.get("permitted_actions") or ())
    prohibited = tuple(envelope.get("prohibited_actions") or ())
    selected = envelope.get("selected_action")
    failures: list[str] = []

    overlap = sorted(set(permitted) & set(prohibited))
    if overlap:
        failures.append(f"{source}: actions both permitted and prohibited: {overlap}")

    if selected is not None:
        if selected in prohibited:
            failures.append(f"{source}: selected action {selected!r} is prohibited")
        try:
            receipts.enforce_selection(permitted, selected)
        except ValueError as exc:
            failures.append(f"{source}: {exc}")

    for action in prohibited:
        try:
            receipts.enforce_selection(permitted, action)
        except ValueError:
            continue
        failures.append(f"{source}: enforcement accepted prohibited action {action!r}")

    return failures


def check_epistemic_promotion(fixture: dict) -> list[str]:
    """Validate the optional source-lineage / corroboration assertion contract.

    ``retrieval_count`` and ``downstream_use_count`` are deliberately recorded
    but never used in independent-origin or certification calculations.
    """
    block = fixture.get("epistemic_promotion")
    if block is None:
        return []
    if not isinstance(block, dict):
        return ["epistemic_promotion must be an object"]

    failures: list[str] = []
    lineage = block.get("lineage")
    expected = block.get("expected")
    threshold = block.get("corroboration_threshold")
    gate_passed = block.get("certification_gate_passed")

    for counter_name in ("retrieval_count", "downstream_use_count"):
        value = block.get(counter_name)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            failures.append(f"epistemic_promotion.{counter_name} must be a non-negative integer")

    if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 1:
        failures.append("epistemic_promotion.corroboration_threshold must be a positive integer")
        threshold = None
    if not isinstance(gate_passed, bool):
        failures.append("epistemic_promotion.certification_gate_passed must be boolean")
    if not isinstance(lineage, list) or not lineage:
        failures.append("epistemic_promotion.lineage must be a non-empty list")
        return failures
    if not isinstance(expected, dict):
        failures.append("epistemic_promotion.expected must be an object")
        return failures

    evidence = fixture.get("memory_unit", {}).get("evidence") or []
    evidence_ids = {
        item.get("id") for item in evidence if isinstance(item, dict) and isinstance(item.get("id"), str)
    }

    entries: dict[str, dict] = {}
    for index, entry in enumerate(lineage):
        path = f"epistemic_promotion.lineage[{index}]"
        if not isinstance(entry, dict):
            failures.append(f"{path} must be an object")
            continue
        evidence_id = entry.get("evidence_id")
        origins = entry.get("origin_refs")
        parents = entry.get("derived_from")
        if not isinstance(evidence_id, str) or not evidence_id:
            failures.append(f"{path}.evidence_id must be a non-empty string")
            continue
        if evidence_id in entries:
            failures.append(f"{path}: duplicate evidence_id {evidence_id!r}")
            continue
        if evidence_id not in evidence_ids:
            failures.append(f"{path}: evidence_id {evidence_id!r} not present in memory_unit.evidence")
        if not isinstance(origins, list) or not origins or not all(isinstance(x, str) and x for x in origins):
            failures.append(f"{path}.origin_refs must be a non-empty list of strings")
        elif len(set(origins)) != len(origins):
            failures.append(f"{path}.origin_refs must be unique")
        if not isinstance(parents, list) or not all(isinstance(x, str) and x for x in parents):
            failures.append(f"{path}.derived_from must be a list of evidence ids")
        entries[evidence_id] = entry

    if set(entries) != evidence_ids:
        missing = sorted(evidence_ids - set(entries))
        extra = sorted(set(entries) - evidence_ids)
        if missing:
            failures.append(f"epistemic_promotion.lineage missing evidence ids: {missing}")
        if extra:
            failures.append(f"epistemic_promotion.lineage has unknown evidence ids: {extra}")

    # Derived evidence must preserve exactly the union of its parents' origins.
    # A summary/restatement therefore cannot acquire a fresh origin merely by
    # being transformed or copied.
    unresolved = dict(entries)
    resolved_origins: dict[str, set[str]] = {}
    while unresolved:
        progressed = False
        for evidence_id, entry in list(unresolved.items()):
            parents = entry.get("derived_from") or []
            declared = set(entry.get("origin_refs") or [])
            if not parents:
                resolved_origins[evidence_id] = declared
                unresolved.pop(evidence_id)
                progressed = True
                continue
            unknown = [parent for parent in parents if parent not in entries]
            if unknown:
                failures.append(
                    f"epistemic_promotion.lineage {evidence_id!r} references unknown parent(s): {sorted(unknown)}"
                )
                resolved_origins[evidence_id] = declared
                unresolved.pop(evidence_id)
                progressed = True
                continue
            if not all(parent in resolved_origins for parent in parents):
                continue
            inherited: set[str] = set()
            for parent in parents:
                inherited.update(resolved_origins[parent])
            if declared != inherited:
                failures.append(
                    f"epistemic_promotion.lineage {evidence_id!r} changes inherited origins: "
                    f"declared={sorted(declared)} inherited={sorted(inherited)}"
                )
            resolved_origins[evidence_id] = inherited
            unresolved.pop(evidence_id)
            progressed = True
        if not progressed:
            failures.append(
                "epistemic_promotion.lineage contains a derivation cycle that prevents origin reconstruction"
            )
            break

    independent_origins: set[str] = set()
    for origins in resolved_origins.values():
        independent_origins.update(origins)
    independent_count = len(independent_origins)

    expected_count = expected.get("independent_origin_count")
    if independent_count != expected_count:
        failures.append(
            "epistemic_promotion independent origin count mismatch: "
            f"derived={independent_count} expected={expected_count!r}"
        )

    if threshold is not None:
        threshold_met = independent_count >= threshold
        if threshold_met is not expected.get("corroboration_threshold_met"):
            failures.append(
                "epistemic_promotion corroboration threshold mismatch: "
                f"derived={threshold_met} expected={expected.get('corroboration_threshold_met')!r}"
            )

    certification = fixture.get("memory_unit", {}).get("certification") or {}
    certification_status = certification.get("status", "none")
    if certification_status != expected.get("certification_status"):
        failures.append(
            "epistemic_promotion certification status mismatch: "
            f"memory={certification_status!r} expected={expected.get('certification_status')!r}"
        )
    if gate_passed is False and certification_status == "pass":
        failures.append("epistemic_promotion certification passed without its separate certification gate")

    return failures


def check_fixture(fixture: dict) -> list[str]:
    failures: list[str] = []
    envelopes = _envelopes(fixture)
    for source, envelope in envelopes:
        failures.extend(check_envelope(source, envelope))

    expected = fixture.get("expected_behavior")
    if isinstance(expected, dict) and expected.get("crystallized") is False:
        for source, envelope in envelopes:
            permitted = tuple(envelope.get("permitted_actions") or ())
            crystallizing = [action for action in permitted if action.startswith("crystallize")]
            if crystallizing:
                failures.append(
                    f"{source}: fixture expects no crystallization but permits {crystallizing}"
                )

    failures.extend(check_epistemic_promotion(fixture))
    return failures


def exemptions() -> list[str]:
    return [
        "Decay, saturation scoring, and calibration are not implemented by this adapter, "
        "so fixtures exercising them are checked only for envelope enforcement.",
        "Retrieval ranking is not exercised: the adapter's recall uses lexical matching, "
        "not the substrate's hybrid search.",
        "Lifecycle transition mechanics beyond commit, supersession, pruning, and deletion "
        "are not driven through the adapter.",
        "Epistemic-promotion fixtures reconstruct declared evidence lineage and certification separation; "
        "they do not define a universal corroboration threshold or certification algorithm.",
        "Fixtures without a declared authority envelope or specialized assertion block contribute structural coverage only.",
    ]


def run(fixture_dir: Path | None = None) -> dict:
    """Execute the corpus and summarize per-fixture results."""
    results: dict[str, list[str]] = {}
    with_envelope = 0
    with_epistemic_promotion = 0
    for name, fixture in load_fixtures(fixture_dir):
        if _envelopes(fixture):
            with_envelope += 1
        if isinstance(fixture.get("epistemic_promotion"), dict):
            with_epistemic_promotion += 1
        results[name] = check_fixture(fixture)

    passed = sorted(name for name, failures in results.items() if not failures)
    failed = sorted(name for name, failures in results.items() if failures)
    return {
        "fixtures_run": sorted(results),
        "fixtures_passed": passed,
        "fixtures_failed": failed,
        "failures": {name: results[name] for name in failed},
        "fixtures_with_authority_envelope": with_envelope,
        "fixtures_with_epistemic_promotion": with_epistemic_promotion,
    }
