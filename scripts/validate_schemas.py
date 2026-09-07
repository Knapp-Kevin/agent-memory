#!/usr/bin/env python3
"""Validate Agent Memory JSON Schemas, fixtures, and source-rights records.

Requires the `jsonschema` package. This complements `validate_fixtures.py` by
checking JSON Schema correctness, validating each fixture's `memory_unit`,
validating optional governance-context projections, and ensuring primary-source
reuse records satisfy the repository's rights gates.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("validate_schemas.py requires the 'jsonschema' package", file=sys.stderr)
    raise SystemExit(2)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    schema_dir = root / "schemas"
    fixture_dir = root / "fixtures"

    schema_errors: list[str] = []
    for path in sorted(schema_dir.glob("*.json")):
        try:
            schema = load(path)
            jsonschema.Draft202012Validator.check_schema(schema)
        except Exception as exc:
            schema_errors.append(f"{path.relative_to(root)}: {exc}")

    if schema_errors:
        print("Schema validation failed:", file=sys.stderr)
        for error in schema_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    memory_schema = load(schema_dir / "memory-unit.schema.json")
    memory_validator = jsonschema.Draft202012Validator(memory_schema)
    audit_event_schema = load(schema_dir / "memory-audit-event.schema.json")
    audit_event_validator = jsonschema.Draft202012Validator(audit_event_schema)
    governance_projection_schema = load(schema_dir / "governance-context-projection.schema.json")
    governance_projection_validator = jsonschema.Draft202012Validator(
        governance_projection_schema,
        format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
    )

    fixture_errors: list[str] = []
    fixture_count = 0
    audit_event_count = 0
    governance_projection_count = 0
    for path in sorted(fixture_dir.glob("*.json")):
        fixture_count += 1
        try:
            fixture = load(path)
        except Exception as exc:
            fixture_errors.append(f"{path.relative_to(root)}: invalid JSON: {exc}")
            continue

        memory = fixture.get("memory_unit")
        if not isinstance(memory, dict):
            fixture_errors.append(f"{path.relative_to(root)}: missing object memory_unit")
            continue

        for error in sorted(memory_validator.iter_errors(memory), key=lambda e: list(e.path)):
            location = ".".join(str(part) for part in error.path)
            suffix = f" at memory_unit.{location}" if location else " at memory_unit"
            fixture_errors.append(f"{path.relative_to(root)}{suffix}: {error.message}")

        audit_events = fixture.get("audit_events")
        if audit_events is not None:
            if not isinstance(audit_events, list) or not audit_events:
                fixture_errors.append(
                    f"{path.relative_to(root)}: audit_events must be a non-empty list when present"
                )
                continue
            for index, event in enumerate(audit_events):
                audit_event_count += 1
                if not isinstance(event, dict):
                    fixture_errors.append(
                        f"{path.relative_to(root)}: audit_events[{index}] must be an object"
                    )
                    continue
                for error in sorted(audit_event_validator.iter_errors(event), key=lambda e: list(e.path)):
                    location = ".".join(str(part) for part in error.path)
                    suffix = f".{location}" if location else ""
                    fixture_errors.append(
                        f"{path.relative_to(root)} at audit_events[{index}]{suffix}: {error.message}"
                    )

        projection = fixture.get("governance_projection")
        if projection is not None:
            governance_projection_count += 1
            if not isinstance(projection, dict):
                fixture_errors.append(
                    f"{path.relative_to(root)}: governance_projection must be an object"
                )
                continue

            for error in sorted(
                governance_projection_validator.iter_errors(projection),
                key=lambda e: list(e.path),
            ):
                location = ".".join(str(part) for part in error.path)
                suffix = f".{location}" if location else ""
                fixture_errors.append(
                    f"{path.relative_to(root)} at governance_projection{suffix}: {error.message}"
                )

            # Doctrine-level projection invariants that JSON Schema cannot express
            # cleanly without turning the projection into a consumer policy model.
            forbidden_authority_keys = {
                "decision",
                "verdict",
                "permission",
                "standing_permission",
                "risk_score",
                "final_decision",
                "require_approval",
            }
            present_forbidden = sorted(forbidden_authority_keys & projection.keys())
            if present_forbidden:
                fixture_errors.append(
                    f"{path.relative_to(root)}: governance_projection must not encode final "
                    f"consumer authority fields: {present_forbidden}"
                )

            source_refs = projection.get("source_memory_refs")
            precedents = projection.get("precedents")
            if isinstance(source_refs, list) and isinstance(precedents, list):
                source_ref_set = {ref for ref in source_refs if isinstance(ref, str)}
                precedent_refs = {
                    item.get("memory_ref")
                    for item in precedents
                    if isinstance(item, dict) and isinstance(item.get("memory_ref"), str)
                }
                missing_sources = sorted(precedent_refs - source_ref_set)
                if missing_sources:
                    fixture_errors.append(
                        f"{path.relative_to(root)}: precedent memory_ref values must be "
                        f"reconstructable through source_memory_refs; missing {missing_sources}"
                    )

                polarity_by_ref = {
                    item.get("memory_ref"): item.get("polarity")
                    for item in precedents
                    if isinstance(item, dict) and isinstance(item.get("memory_ref"), str)
                }
                negative_refs = projection.get("negative_precedent_refs", [])
                if isinstance(negative_refs, list):
                    for ref in negative_refs:
                        if ref not in precedent_refs:
                            fixture_errors.append(
                                f"{path.relative_to(root)}: negative precedent {ref!r} must "
                                "also appear in precedents"
                            )
                        elif polarity_by_ref.get(ref) not in {"cautionary", "contradictory"}:
                            fixture_errors.append(
                                f"{path.relative_to(root)}: negative precedent {ref!r} must "
                                "be cautionary or contradictory"
                            )

                for index, item in enumerate(precedents):
                    if not isinstance(item, dict):
                        continue
                    relationship = item.get("relationship")
                    conditions = item.get("material_conditions")
                    if relationship == "material_mismatch" and isinstance(conditions, list):
                        has_mismatch = any(
                            isinstance(condition, dict)
                            and condition.get("comparison") == "mismatch"
                            for condition in conditions
                        )
                        if not has_mismatch:
                            fixture_errors.append(
                                f"{path.relative_to(root)}: precedents[{index}] declares "
                                "material_mismatch without a mismatched material condition"
                            )

                    provenance = item.get("provenance")
                    if isinstance(provenance, dict):
                        source_type = provenance.get("source_type")
                        independent = provenance.get("independent_adjudication")
                        if independent is True and source_type != "human_adjudication":
                            fixture_errors.append(
                                f"{path.relative_to(root)}: precedents[{index}] may mark "
                                "independent_adjudication=true only for human_adjudication; "
                                "policy/runtime/derived outcomes must not launder themselves "
                                "into independent human precedent"
                            )

    if fixture_errors:
        print("Fixture/schema validation failed:", file=sys.stderr)
        for error in fixture_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    source_registry_path = root / "sources" / "source-registry.json"
    source_schema = load(schema_dir / "source-record.schema.json")
    source_validator = jsonschema.Draft202012Validator(
        source_schema,
        format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
    )

    source_errors: list[str] = []
    source_count = 0
    try:
        registry = load(source_registry_path)
    except Exception as exc:
        source_errors.append(f"{source_registry_path.relative_to(root)}: invalid JSON: {exc}")
        registry = {}

    records = registry.get("sources") if isinstance(registry, dict) else None
    if not isinstance(records, list):
        source_errors.append(f"{source_registry_path.relative_to(root)}: missing sources array")
        records = []

    seen_ids: set[str] = set()
    for index, record in enumerate(records):
        source_count += 1
        location = f"sources[{index}]"
        if not isinstance(record, dict):
            source_errors.append(f"{source_registry_path.relative_to(root)} {location}: must be an object")
            continue

        for error in sorted(source_validator.iter_errors(record), key=lambda e: list(e.path)):
            field = ".".join(str(part) for part in error.path)
            suffix = f".{field}" if field else ""
            source_errors.append(
                f"{source_registry_path.relative_to(root)} {location}{suffix}: {error.message}"
            )

        source_id = record.get("source_id")
        if isinstance(source_id, str):
            if source_id in seen_ids:
                source_errors.append(
                    f"{source_registry_path.relative_to(root)} {location}: duplicate source_id {source_id!r}"
                )
            seen_ids.add(source_id)

        reuse_mode = record.get("reuse_mode")
        rights_status = record.get("rights_status")
        reuse_basis = record.get("reuse_basis")

        if reuse_mode == "licensed_reuse":
            if rights_status != "verified_open_license":
                source_errors.append(
                    f"{source_registry_path.relative_to(root)} {location}: licensed_reuse requires verified_open_license"
                )
            if not record.get("license_spdx") or not record.get("license_url"):
                source_errors.append(
                    f"{source_registry_path.relative_to(root)} {location}: licensed_reuse requires license_spdx and license_url"
                )

        if reuse_mode == "permission_granted" and rights_status != "permission_verified":
            source_errors.append(
                f"{source_registry_path.relative_to(root)} {location}: permission_granted requires permission_verified"
            )

        if reuse_mode == "author_originated" and rights_status != "author_originated":
            source_errors.append(
                f"{source_registry_path.relative_to(root)} {location}: author_originated reuse requires author_originated rights_status"
            )

        if reuse_mode in {"licensed_reuse", "permission_granted", "author_originated"}:
            if not isinstance(reuse_basis, str) or not reuse_basis.strip():
                source_errors.append(
                    f"{source_registry_path.relative_to(root)} {location}: reuse-oriented mode requires a documented reuse_basis"
                )

        if rights_status == "unknown" and reuse_mode not in {"citation_only", "independent_synthesis"}:
            source_errors.append(
                f"{source_registry_path.relative_to(root)} {location}: unknown rights status may only cite or independently synthesize"
            )

    if source_errors:
        print("Source-rights validation failed:", file=sys.stderr)
        for error in source_errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    schema_count = len(list(schema_dir.glob("*.json")))
    print(
        f"Validated {schema_count} schema(s), {fixture_count} fixture memory unit(s), "
        f"{audit_event_count} audit event(s), {governance_projection_count} governance "
        f"projection(s), and {source_count} source-rights record(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
