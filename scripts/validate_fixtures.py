#!/usr/bin/env python3
"""Validate agent-memory conformance fixtures.

This validator intentionally uses only the Python standard library. It validates
baseline fixture structure plus a small set of doctrine-level governed-uncertainty
and forbidden-hit invariants. It is not a replacement for implementation-specific
behavioral tests.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL = {
    "fixture_id",
    "fixture_version",
    "class",
    "description",
    "expected_behavior",
    "memory_unit",
}

# Fixture versions describe the scenario contract (expected behavior, invariants,
# trap semantics, material inputs), not the memory-unit schema version.
FIXTURE_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

REQUIRED_MEMORY_UNIT = {
    "id",
    "type",
    "state",
    "provenance",
    "evidence",
    "saturation",
    "authority",
    "created_at",
}

REQUIRED_PROVENANCE = {"origin", "observer", "method", "timestamp"}
REQUIRED_SATURATION = {"sigma", "calibrated", "durability_dimensions"}
REQUIRED_AUTHORITY = {"pama_outcome", "risk_class"}
REQUIRED_FORBIDDEN_HIT = {
    "assertion_id",
    "forbidden_class",
    "source_lifecycle_state",
    "source_evidence",
    "candidate_discovered",
    "admitted",
    "context_surfaced",
    "downstream_influence",
    "expected_refusal",
}
FORBIDDEN_HIT_STAGE_FIELDS = {
    "candidate_discovered",
    "admitted",
    "context_surfaced",
    "downstream_influence",
}

VALID_STATES = {
    "transient",
    "observed",
    "linked",
    "reinforced",
    "candidate",
    "pending_verification",
    "crystallized",
    "operationally_reused",
    "stale",
    "disputed",
    "corrected",
    "reconciled",
    "pruned",
    "archived",
    "tombstoned",
}

VALID_PAMA_OUTCOMES = {
    "allow",
    "allow_with_ledger",
    "require_review",
    "require_external_verification",
    "abstain",
    "quarantine",
    "collect_more_evidence",
    "block",
}

VALID_RISK_CLASSES = {"low", "medium", "high", "critical"}
VALID_SELECTION_MODES = {"none", "deterministic", "stochastic", "learned", "human", "external"}


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc


def require_keys(obj: dict[str, Any], keys: set[str], path: str) -> list[str]:
    return [f"{path}: missing required key '{key}'" for key in sorted(keys - obj.keys())]


def validate_action_envelope(obj: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    permitted = obj.get("permitted_actions")
    prohibited = obj.get("prohibited_actions")
    selected = obj.get("selected_action")
    mode = obj.get("selection_mode")

    if permitted is not None and (not isinstance(permitted, list) or not all(isinstance(x, str) for x in permitted)):
        errors.append(f"{path}.permitted_actions must be a list of strings")
        permitted = None
    if prohibited is not None and (not isinstance(prohibited, list) or not all(isinstance(x, str) for x in prohibited)):
        errors.append(f"{path}.prohibited_actions must be a list of strings")
        prohibited = None

    if permitted is not None and prohibited is not None:
        overlap = sorted(set(permitted) & set(prohibited))
        if overlap:
            errors.append(f"{path}: actions cannot be both permitted and prohibited: {overlap}")

    if selected is not None:
        if not isinstance(selected, str):
            errors.append(f"{path}.selected_action must be a string")
        elif permitted is None:
            errors.append(f"{path}.selected_action requires permitted_actions")
        elif selected not in permitted:
            errors.append(f"{path}.selected_action {selected!r} is not in permitted_actions")

    if mode is not None and mode not in VALID_SELECTION_MODES:
        errors.append(f"{path}.selection_mode invalid: {mode!r}")

    return errors


def validate_forbidden_hit_assertions(data: dict[str, Any], path: Path) -> list[str]:
    """Validate the optional reusable negative-lifecycle assertion family."""
    assertions = data.get("forbidden_hit_assertions")
    if assertions is None:
        return []

    errors: list[str] = []
    fixture_path = str(path)
    if not isinstance(assertions, list) or not assertions:
        return [f"{fixture_path}:forbidden_hit_assertions must be a non-empty list"]

    seen_ids: set[str] = set()
    seen_classes: set[str] = set()
    for index, item in enumerate(assertions):
        item_path = f"{fixture_path}:forbidden_hit_assertions[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{item_path} must be an object")
            continue
        errors.extend(require_keys(item, REQUIRED_FORBIDDEN_HIT, item_path))

        assertion_id = item.get("assertion_id")
        if not isinstance(assertion_id, str) or not assertion_id.strip():
            errors.append(f"{item_path}.assertion_id must be a non-empty string")
        elif assertion_id in seen_ids:
            errors.append(f"{item_path}.assertion_id duplicates {assertion_id!r}")
        else:
            seen_ids.add(assertion_id)

        forbidden_class = item.get("forbidden_class")
        if not isinstance(forbidden_class, str) or not forbidden_class.strip():
            errors.append(f"{item_path}.forbidden_class must be a non-empty string")
        else:
            seen_classes.add(forbidden_class)

        for field in ("source_lifecycle_state", "source_evidence", "expected_refusal"):
            value = item.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{item_path}.{field} must be a non-empty string")

        for field in FORBIDDEN_HIT_STAGE_FIELDS:
            if not isinstance(item.get(field), bool):
                errors.append(f"{item_path}.{field} must be a boolean")

        # Later-stage influence cannot be true if the candidate never reached
        # the preceding stage. This is structural ordering, not a claim that
        # every runtime must block specifically at admission.
        if item.get("admitted") and not item.get("candidate_discovered"):
            errors.append(f"{item_path}: admitted=true requires candidate_discovered=true")
        if item.get("context_surfaced") and not item.get("admitted"):
            errors.append(f"{item_path}: context_surfaced=true requires admitted=true")
        if item.get("downstream_influence") and not item.get("context_surfaced"):
            errors.append(f"{item_path}: downstream_influence=true requires context_surfaced=true")

    expected = data.get("expected_behavior")
    if isinstance(expected, dict):
        declared_count = expected.get("forbidden_classes_covered")
        if declared_count is not None and declared_count != len(seen_classes):
            errors.append(
                f"{fixture_path}:expected_behavior.forbidden_classes_covered={declared_count!r} "
                f"does not match {len(seen_classes)} unique forbidden classes"
            )
        stages = expected.get("explicit_pipeline_stages")
        required_stages = sorted(FORBIDDEN_HIT_STAGE_FIELDS)
        if stages is not None:
            if not isinstance(stages, list) or sorted(stages) != required_stages:
                errors.append(
                    f"{fixture_path}:expected_behavior.explicit_pipeline_stages must contain "
                    f"exactly {required_stages!r}"
                )

    return errors


def validate_fixture(path: Path) -> list[str]:
    errors: list[str] = []
    data = load_json(path)

    if not isinstance(data, dict):
        return [f"{path}: fixture must be a JSON object"]

    errors.extend(require_keys(data, REQUIRED_TOP_LEVEL, str(path)))
    if errors:
        return errors

    version = data.get("fixture_version")
    if not isinstance(version, str) or not FIXTURE_VERSION_PATTERN.match(version):
        errors.append(f"{path}: fixture_version must be a MAJOR.MINOR.PATCH string, got {version!r}")

    expected = data.get("expected_behavior")
    if not isinstance(expected, (dict, list, str)):
        errors.append(f"{path}: expected_behavior must be an object, list, or string")

    memory = data["memory_unit"]
    if not isinstance(memory, dict):
        return [f"{path}: memory_unit must be an object"]

    errors.extend(require_keys(memory, REQUIRED_MEMORY_UNIT, f"{path}:memory_unit"))

    state = memory.get("state")
    if state not in VALID_STATES:
        errors.append(f"{path}:memory_unit.state invalid: {state!r}")

    provenance = memory.get("provenance")
    if not isinstance(provenance, dict):
        errors.append(f"{path}:memory_unit.provenance must be an object")
    else:
        errors.extend(require_keys(provenance, REQUIRED_PROVENANCE, f"{path}:memory_unit.provenance"))

    evidence = memory.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{path}:memory_unit.evidence must be a non-empty list")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                errors.append(f"{path}:memory_unit.evidence[{index}] must be an object")
                continue
            for key in ("id", "kind", "ref", "confidence"):
                if key not in item:
                    errors.append(f"{path}:memory_unit.evidence[{index}] missing {key!r}")
            confidence = item.get("confidence")
            if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
                errors.append(f"{path}:memory_unit.evidence[{index}].confidence must be 0..1")

    saturation = memory.get("saturation")
    if not isinstance(saturation, dict):
        errors.append(f"{path}:memory_unit.saturation must be an object")
    else:
        errors.extend(require_keys(saturation, REQUIRED_SATURATION, f"{path}:memory_unit.saturation"))
        sigma = saturation.get("sigma")
        if not isinstance(sigma, (int, float)) or not 0 <= sigma <= 1:
            errors.append(f"{path}:memory_unit.saturation.sigma must be 0..1")
        dims = saturation.get("durability_dimensions")
        if not isinstance(dims, list) or not dims:
            errors.append(f"{path}:memory_unit.saturation.durability_dimensions must be a non-empty list")

    authority = memory.get("authority")
    if not isinstance(authority, dict):
        errors.append(f"{path}:memory_unit.authority must be an object")
    else:
        errors.extend(require_keys(authority, REQUIRED_AUTHORITY, f"{path}:memory_unit.authority"))
        outcome = authority.get("pama_outcome")
        if outcome not in VALID_PAMA_OUTCOMES:
            errors.append(f"{path}:memory_unit.authority.pama_outcome invalid: {outcome!r}")
        risk = authority.get("risk_class")
        if risk not in VALID_RISK_CLASSES:
            errors.append(f"{path}:memory_unit.authority.risk_class invalid: {risk!r}")
        errors.extend(validate_action_envelope(authority, f"{path}:memory_unit.authority"))

    governed = data.get("governed_uncertainty")
    if governed is not None:
        if not isinstance(governed, dict):
            errors.append(f"{path}:governed_uncertainty must be an object")
        else:
            errors.extend(
                require_keys(
                    governed,
                    {"requested_action", "permitted_actions", "prohibited_actions", "expected_invariants"},
                    f"{path}:governed_uncertainty",
                )
            )
            if not isinstance(governed.get("requested_action"), str):
                errors.append(f"{path}:governed_uncertainty.requested_action must be a string")
            invariants = governed.get("expected_invariants")
            if not isinstance(invariants, list) or not invariants or not all(isinstance(x, str) for x in invariants):
                errors.append(f"{path}:governed_uncertainty.expected_invariants must be a non-empty list of strings")
            errors.extend(validate_action_envelope(governed, f"{path}:governed_uncertainty"))

    errors.extend(validate_forbidden_hit_assertions(data, path))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate conformance fixture JSON files.")
    parser.add_argument("paths", nargs="*", default=["fixtures"], help="Fixture files or directories to validate.")
    args = parser.parse_args()

    files: list[Path] = []
    for raw in args.paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
        else:
            files.append(path)

    if not files:
        print("No fixture files found.", file=sys.stderr)
        return 1

    all_errors: list[str] = []
    for file_path in files:
        try:
            all_errors.extend(validate_fixture(file_path))
        except Exception as exc:  # intentionally broad for CLI diagnostics
            all_errors.append(f"{file_path}: {exc}")

    if all_errors:
        print("Fixture validation failed:", file=sys.stderr)
        for error in all_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Validated {len(files)} fixture(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
