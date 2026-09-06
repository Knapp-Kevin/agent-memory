#!/usr/bin/env python3
"""Generate a calibration report from labeled calibration results.

Reads a results file conforming to `schemas/calibration-results.schema.json`
and emits the Markdown calibration report required by
`docs/09-calibration-protocol.md`. This generator intentionally uses only the
Python standard library. It derives measurements; it does not decide policy.
A passing report is a calibration signal, not certification and not authority.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL = {
    "implementation",
    "version",
    "doctrine_version",
    "estimator_version",
    "calibration_version",
    "threshold",
    "durability_dimensions_tested",
    "scope_of_validity",
    "cases",
}

REQUIRED_CASE = {"case_id", "class", "sigma", "observed_outcome"}
VALID_CLASSES = {"persist", "evaporate", "trap"}
VALID_OUTCOMES = {"retained", "evaporated", "crystallized", "abstained", "review"}

DURABLE_OUTCOMES = {"retained", "crystallized"}
NOT_TESTED = "not_tested"


def load_results(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("results must be a JSON object")
    return data


def validate_results(data: dict[str, Any]) -> list[str]:
    errors = [f"missing required key '{key}'" for key in sorted(REQUIRED_TOP_LEVEL - data.keys())]
    if errors:
        return errors

    cases = data["cases"]
    if not isinstance(cases, list) or not cases:
        return ["cases must be a non-empty list"]

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{index}] must be an object")
            continue
        errors.extend(
            f"cases[{index}] missing required key '{key}'" for key in sorted(REQUIRED_CASE - case.keys())
        )
        if case.get("class") not in VALID_CLASSES:
            errors.append(f"cases[{index}].class invalid: {case.get('class')!r}")
        if case.get("observed_outcome") not in VALID_OUTCOMES:
            errors.append(f"cases[{index}].observed_outcome invalid: {case.get('observed_outcome')!r}")
        sigma = case.get("sigma")
        if not isinstance(sigma, (int, float)) or not 0 <= sigma <= 1:
            errors.append(f"cases[{index}].sigma must be 0..1")

    return errors


def rate(numerator: int, denominator: int) -> float | str:
    if denominator == 0:
        return NOT_TESTED
    return round(numerator / denominator, 4)


def compute_measurements(data: dict[str, Any]) -> dict[str, Any]:
    cases = data["cases"]
    by_class: dict[str, list[dict[str, Any]]] = {name: [] for name in sorted(VALID_CLASSES)}
    for case in cases:
        by_class[case["class"]].append(case)

    persist = by_class["persist"]
    evaporate = by_class["evaporate"]
    trap = by_class["trap"]
    non_persist = evaporate + trap

    boundary_tested = [c for c in cases if "boundary_stable" in c]
    disagreement_tested = [c for c in cases if "estimator_disagreement" in c]

    return {
        "threshold": data["threshold"],
        "sample_size": len(cases),
        "persist_retention_rate": rate(
            sum(1 for c in persist if c["observed_outcome"] in DURABLE_OUTCOMES), len(persist)
        ),
        "false_permanence_rate": rate(
            sum(1 for c in non_persist if c["observed_outcome"] == "crystallized"), len(non_persist)
        ),
        "evaporation_rate_for_true_ephemeral": rate(
            sum(1 for c in evaporate if c["observed_outcome"] == "evaporated"), len(evaporate)
        ),
        "trap_class_failure_rate": rate(
            sum(1 for c in trap if c["observed_outcome"] == "crystallized"), len(trap)
        ),
        "boundary_instability_rate": rate(
            sum(1 for c in boundary_tested if not c["boundary_stable"]), len(boundary_tested)
        ),
        "abstention_rate": rate(
            sum(1 for c in cases if c["observed_outcome"] == "abstained"), len(cases)
        ),
        "estimator_disagreement_rate": rate(
            sum(1 for c in disagreement_tested if c["estimator_disagreement"]), len(disagreement_tested)
        ),
        "out_of_scope_rate": rate(sum(1 for c in cases if c.get("out_of_scope")), len(cases)),
    }


def sigma_summary(cases: list[dict[str, Any]]) -> str:
    if not cases:
        return f"0 | {NOT_TESTED} | {NOT_TESTED} | {NOT_TESTED}"
    sigmas = [c["sigma"] for c in cases]
    mean = round(sum(sigmas) / len(sigmas), 3)
    return f"{len(cases)} | {min(sigmas):.3f} | {mean:.3f} | {max(sigmas):.3f}"


def assess(measurements: dict[str, Any]) -> tuple[str, list[str]]:
    """Return (verdict, notes). Trap-class crystallization is a calibration failure."""
    trap_failure = measurements["trap_class_failure_rate"]
    notes: list[str] = []

    if trap_failure == NOT_TESTED:
        notes.append(
            "No trap-class cases were provided. The calibration protocol requires trap classes; "
            "this calibration is incomplete and must not be cited as a validity claim."
        )
        return "INCOMPLETE", notes

    if isinstance(trap_failure, float) and trap_failure > 0:
        notes.append(
            "One or more trap-class objects crystallized. Per the trap-class rule, the calibration "
            "failed: the scoring model or governance integration is measuring or using the wrong thing."
        )
        return "FAIL", notes

    for name in ("boundary_instability_rate", "estimator_disagreement_rate"):
        if measurements[name] == NOT_TESTED:
            notes.append(f"{name} was not tested; the scope of validity must exclude claims about it.")

    return "PASS", notes


def format_scope(value: Any, indent: int = 0) -> list[str]:
    pad = "  " * indent
    if isinstance(value, dict):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{pad}{key}:")
                lines.extend(format_scope(item, indent + 1))
            else:
                lines.append(f"{pad}{key}: {item}")
        return lines
    if isinstance(value, list):
        return [f"{pad}- {item}" for item in value]
    return [f"{pad}{value}"]


def render_report(data: dict[str, Any]) -> str:
    measurements = compute_measurements(data)
    verdict, notes = assess(measurements)
    by_class = {
        name: [c for c in data["cases"] if c["class"] == name] for name in ("persist", "evaporate", "trap")
    }

    lines: list[str] = []
    lines.append(f"# Calibration Report: {data['implementation']} {data['version']}")
    lines.append("")
    lines.append(f"**Overall assessment**: {verdict}")
    lines.append("")
    for note in notes:
        lines.append(f"> {note}")
        lines.append("")

    lines.append("## Versioning")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    for field in ("implementation", "version", "doctrine_version", "estimator_version", "calibration_version"):
        lines.append(f"| {field} | {data[field]} |")
    lines.append(f"| sigma_is_probabilistic | {str(data.get('sigma_is_probabilistic', False)).lower()} |")
    lines.append("")

    lines.append("## Operating point")
    lines.append("")
    lines.append(f"- threshold: {data['threshold']}")
    band = data.get("review_band")
    if isinstance(band, dict):
        lines.append(f"- review_band: {band['lower']} to {band['upper']}")
    else:
        lines.append("- review_band: none declared")
    lines.append("")

    lines.append("## Required measurements")
    lines.append("")
    lines.append("| Measurement | Value |")
    lines.append("|---|---|")
    for name, value in measurements.items():
        lines.append(f"| {name} | {value} |")
    lines.append(
        f"| durability_dimensions_tested | {', '.join(data['durability_dimensions_tested'])} |"
    )
    lines.append(f"| estimator_version | {data['estimator_version']} |")
    lines.append(f"| calibration_version | {data['calibration_version']} |")
    lines.append("")

    lines.append("## Class distributions")
    lines.append("")
    lines.append("| Class | Cases | sigma min | sigma mean | sigma max |")
    lines.append("|---|---|---|---|---|")
    for name in ("persist", "evaporate", "trap"):
        lines.append(f"| {name.upper()} | {sigma_summary(by_class[name])} |")
    lines.append("")
    lines.append(
        "Distribution overlap matters more than mean score. Performance must be read in the region "
        "where policy consequences change."
    )
    lines.append("")

    lines.append("## Trap-class outcomes")
    lines.append("")
    if by_class["trap"]:
        lines.append("| Case | sigma | Observed outcome |")
        lines.append("|---|---|---|")
        for case in by_class["trap"]:
            lines.append(f"| {case['case_id']} | {case['sigma']:.3f} | {case['observed_outcome']} |")
    else:
        lines.append("No trap-class cases provided.")
    lines.append("")

    probabilistic = data.get("probabilistic_metrics")
    if data.get("sigma_is_probabilistic") and isinstance(probabilistic, dict):
        lines.append("## Probabilistic metrics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|---|---|")
        for key, value in probabilistic.items():
            if key == "proper_scoring_rule" and isinstance(value, dict):
                lines.append(f"| {value['name']} | {value['value']} |")
            else:
                lines.append(f"| {key} | {json.dumps(value)} |")
        lines.append("")

    lines.append("## Scope of validity")
    lines.append("")
    lines.append("```yaml")
    lines.extend(format_scope(data["scope_of_validity"]))
    lines.append("```")
    lines.append("")
    lines.append("This calibration is valid only for the durability dimensions and consequence classes tested.")
    lines.append("")

    exemptions = data.get("known_exemptions")
    if exemptions:
        lines.append("## Known exemptions")
        lines.append("")
        for item in exemptions:
            lines.append(f"- {item}")
        lines.append("")

    lines.append("## Doctrine")
    lines.append("")
    lines.append("Calibrated saturation is a lifecycle signal. It is not identity, not truth, not")
    lines.append("certification, and not permission. Eligibility is not authorization: candidates")
    lines.append("identified by this calibration still require certification and PAMA authority")
    lines.append("before crystallization.")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a Markdown calibration report from results JSON.")
    parser.add_argument("results", help="Path to a calibration results JSON file.")
    parser.add_argument("-o", "--output", help="Write the report to this path instead of stdout.")
    args = parser.parse_args()

    try:
        data = load_results(Path(args.results))
    except (OSError, ValueError) as exc:
        print(f"error: {args.results}: {exc}", file=sys.stderr)
        return 1

    errors = validate_results(data)
    if errors:
        print("Calibration results validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    report = render_report(data)
    if args.output:
        Path(args.output).write_text(report + "\n", encoding="utf-8")
        print(f"Wrote calibration report to {args.output}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
