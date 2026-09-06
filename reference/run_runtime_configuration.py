#!/usr/bin/env python3
"""Validate the portable #280 runtime configuration and emit exact-head evidence."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from agentmem_ref.runtime_config import (  # noqa: E402
    QualificationBinding,
    RuntimeConfigurationError,
    validate_runtime_configuration,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = ROOT / "reference" / "fixtures" / "runtime-configuration"


def _load_inputs() -> tuple[dict, tuple[QualificationBinding, ...], dict]:
    config = json.loads((FIXTURE_ROOT / "attached-existing-stack.json").read_text(encoding="utf-8"))
    binding_document = json.loads((FIXTURE_ROOT / "qualification-bindings.json").read_text(encoding="utf-8"))
    bindings = tuple(QualificationBinding(**row) for row in binding_document["bindings"])
    return config, bindings, binding_document["source"]


def _refused(config: dict, bindings: tuple[QualificationBinding, ...]) -> bool:
    try:
        validate_runtime_configuration(config, qualification_bindings=bindings)
    except RuntimeConfigurationError:
        return True
    return False


def build_report(agent_memory_commit: str) -> dict:
    if len(agent_memory_commit) != 40:
        raise ValueError("agent-memory commit must be an exact 40-character SHA")

    config, bindings, source = _load_inputs()
    plan = validate_runtime_configuration(config, qualification_bindings=bindings)

    stale = copy.deepcopy(config)
    for component in stale["components"]:
        if component["declaration"]["component_id"] == "codegenome":
            component["declaration"]["component_version"] = "unverified-next-version"

    ambiguous = copy.deepcopy(config)
    for route in ambiguous["routes"]:
        if route["route_id"] == "derived-code-graph":
            route.pop("preferred_component", None)

    literal_secret = copy.deepcopy(config)
    literal_secret["governance_peers"][0]["secret_refs"]["credential"] = "literal-secret"

    missing_owner = copy.deepcopy(config)
    missing_owner["canonical_state"]["owner_component_id"] = "missing-store"

    invariants = {
        "attach_existing_stack": plan.entry_mode == "attach_existing_stack",
        "canonical_owner_explicit": plan.canonical_owner_component_id == "existing-canonical-store",
        "qualified_primary_selected": any(
            route.route_id == "derived-code-graph"
            and route.primary.component_id == "codegenome"
            and bool(route.qualification_record_ref)
            for route in plan.resolved_routes
        ),
        "explicit_equivalent_fallback_bound": any(
            route.route_id == "derived-code-graph"
            and route.fallback_component_id == "graphify"
            and bool(route.fallback_qualification_record_ref)
            for route in plan.resolved_routes
        ),
        "derived_currentness_obligation_declared": plan.required_projection_ids == ("code-graph",),
        "governance_peer_declared": plan.governance_peer_ids == ("dashclaw",),
        "configuration_grants_no_authority": plan.authority_effect == "none",
        "stale_component_qualification_refused": _refused(stale, bindings),
        "ambiguous_provider_refused": _refused(ambiguous, bindings),
        "literal_secret_refused": _refused(literal_secret, bindings),
        "missing_canonical_owner_refused": _refused(missing_owner, bindings),
    }

    return {
        "schema_version": "1.0.0",
        "agent_memory_commit": agent_memory_commit,
        "configuration_contract": "schemas/runtime-configuration.schema.json@1.0.0",
        "qualification_source": source,
        "plan": plan.to_dict(),
        "structural_invariants": invariants,
        "structural_invariants_passed": all(invariants.values()),
        "limitations": [
            "JSON is the first reference serialization, not a mandated product configuration syntax.",
            "The validator consumes independently supplied qualification bindings; it does not make configuration self-qualifying.",
            "Component discovery, package installation, interactive wizard UX, and secret resolution are intentionally outside this slice.",
            "Execution-time provider outage continues to use the #300 fallback contract; this slice validates configured topology before startup.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-memory-commit", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report(args.agent_memory_commit)
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    if not report["structural_invariants_passed"]:
        failed = [name for name, passed in report["structural_invariants"].items() if not passed]
        print(f"runtime configuration invariant failed: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
