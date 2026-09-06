#!/usr/bin/env python
"""Move ``agentmem_ref``'s flat modules into layered subpackages (Sprint 3a, plan LD5).

This file is the single source of truth for the layout: the layer order, the
module-to-layer table, and the top-level residents. ``reference/tests/
test_package_layout.py`` reads them from here, so the test cannot drift from
the mover.

    python scripts/restructure_package.py          # perform the move (idempotent)
    python scripts/restructure_package.py --check  # report whether the tree matches the table

The move refuses to run while tracked files under the package are modified, moves each module
with ``git mv`` so history follows it, rewrites relative imports to the new
layout, replaces every ``Path(__file__).resolve().parents[N]`` with the roots
from ``agentmem_ref/_paths.py``, and writes a ``sys.modules`` alias at every
old path so ``agentmem_ref.X is agentmem_ref.<layer>.X``.

Layer names must not collide with module names: a subpackage directory
shadows a same-named module file, so ``substrate.py`` cannot keep its alias
beside a ``substrate/`` package. The state layer is therefore ``state`` and
the capability-contract layer is ``contracts`` (plan iteration 3).
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1] / "reference" / "agentmem_ref"

# Order matters: a module may import only from its own layer or an earlier one.
LAYER_ORDER = ("core", "state", "contracts", "runtime", "memory", "crg", "harness")

LAYERS: dict[str, tuple[str, ...]] = {
    "core": (
        "policy", "receipts", "evidence_qualification", "verification",
        "pending_verification", "resumption", "readmission", "contextual_recall",
        "governance_projection", "portable_evidence",
    ),
    "state": ("substrate", "graphiti_driver", "projections", "residue", "visibility"),
    "contracts": (
        "capabilities", "qualification", "component_fallback", "component_failure_probe",
        "hindsight_qualification", "memos_qualification", "resource_provider_substitution",
        "resource_exchange", "evolveai_profile",
    ),
    "runtime": (
        "adapter", "restart_runtime", "configured_restart", "runtime_composition",
        "runtime_config", "runtime_behavior", "doctor", "cli", "discovery", "composition",
        "contextual_recall_adapter", "projection_governance", "semantic_readmission_adapter",
        "write_claims", "scope_governance", "shared_revocation",
    ),
    "memory": (
        "a2a_collaboration", "agent_manifest_correlation", "agent_manifest_external_evidence",
        "approval_evidence", "cmcp_external_evidence", "cognitive_mesh",
        "conditional_memory_influence", "crossing", "dashclaw_authority",
        "dashclaw_external_verdict", "dashclaw_governed_commit", "decision_overwrite",
        "deletion_completeness", "derivation_currentness", "derivation_evidence",
        "domain_schema_mutation", "enforcement_composition", "enforcement_evidence",
        "epistemic_memory", "evolveai_cognitive_mesh", "external_evidence",
        "framework_lifecycle", "interchange", "interchange_propagation", "maintenance_run",
        "maintenance_run_bindings", "maintenance_run_rules", "maintenance_run_state",
        "mcp_interaction", "policy_projection_compatibility", "precedent_applicability",
        "precedent_candidate_retrieval", "predictive_memory", "procedural_memory",
        "reusable_grants", "runtime_trace_correlation", "security_finding",
        "structural_mutation", "structural_pama", "telemetry", "telemetry_retention",
        "temporal_commitment", "temporal_transparency", "temporal_trust",
        "trace_action_evidence", "uor_content_reference",
    ),
    "crg": (
        "code_graph_qualification", "codegenome_profile", "codegenome_cognitive_mesh",
        "codegenome_scope_residue",
    ),
    "harness": (
        "authority_laundering_harness", "authority_laundering_depth",
        "autonomous_maintenance_harness", "benchmark_security", "cedar_policy_comparator",
        "opa_policy_comparator", "mem0_comparator", "langgraph_lifecycle_comparator",
        "maf_lifecycle_comparator", "concurrency_evidence", "conditional_memory_harness",
        "derivation_currentness_harness", "derivation_currentness_depth",
        "domain_schema_discovery_harness", "fixture_conformance", "forbidden_hits",
        "latent_predictive_state_harness", "logical_state_algebra_pressure",
        "long_horizon_benchmark", "long_horizon_dataset", "operational_memory_benchmark",
        "precedent_candidate_harness", "reusable_grant_harness", "security_evidence_depth",
        "security_finding_harness", "security_finding_depth", "sleeper_poisoning_harness",
        "sleeper_poisoning_depth", "systems_characterization", "unsafe_composition_harness",
        "unsafe_composition_depth", "visibility_characterization",
        "architecture_family_closeout", "architecture_family_evidence",
    ),
}

# Top-level residents: neither moved nor aliased.
STAYS = ("__init__", "__main__", "_paths")

LAYER_DOCS = {
    "core": "The PAMA evaluator, receipts and schema validation, evidence qualification, "
            "verification, parking and resumption. Imports nothing outside this layer.",
    "state": "Canonical state (the temporal graph substrate and drivers) and derived state "
             "(projections, residue, visibility). Depends on ``core``.",
    "contracts": "The capability contract, provider qualification, substitution and "
                 "fallback. Depends on ``core``.",
    "runtime": "The governed adapter, restart-safe and configured runtimes, composition, "
               "discovery, doctor and CLI. Depends on ``core``, ``state``, ``contracts``.",
    "memory": "The governed memory kinds and the evidence they consume: cognitive, "
              "epistemic, predictive, procedural, decision overwrite, structural mutation, "
              "crossing, interchange, temporal, precedent, maintenance. Depends on "
              "``runtime`` and below.",
    "crg": "Agent Memory's Code Reality Graph.\n\n"
           "A Code Reality Graph is a governed graph of what a codebase actually is --\n"
           "its structure, its qualified components, its scope residue -- held as memory\n"
           "the PAMA evaluator governs like any other. CodeGenome is the first-party\n"
           "implementation profile of that graph (ADR-035, ADR-036); the ``codegenome_*``\n"
           "modules here are that profile, not an attributed external provider.\n"
           "Depends on ``memory`` and below.",
    "harness": "Characterization harnesses, depth probes, comparators and benchmarks: the "
               "leaves. Nothing imports from here.",
}

_PATHS_NAMES = ("REPO_ROOT", "REFERENCE_ROOT", "PACKAGE_ROOT", "PACKAGE_NAME")


def assignment() -> dict[str, str]:
    table: dict[str, str] = {}
    for layer in LAYER_ORDER:
        for mod in LAYERS[layer]:
            if mod in table:
                raise SystemExit(f"module assigned twice: {mod}")
            table[mod] = layer
    for layer in LAYERS:
        if layer in table:
            raise SystemExit(f"layer name collides with a module: {layer}")
    return table


def alias_source(mod: str, layer: str) -> str:
    return (
        f'"""Compatibility alias -- this module lives at ``agentmem_ref.{layer}.{mod}``."""\n'
        "import sys\n"
        f"from .{layer} import {mod} as _real\n"
        "sys.modules[__name__] = _real\n"
    )


def layer_init_source(layer: str) -> str:
    return f'"""{LAYER_DOCS[layer]}\n"""\n'


# ----------------------------------------------------------------------------- rewriting

_REL_IMPORT = re.compile(r"^(\s*)from \.(\w*) import (.+)$")
_ABS_IMPORT = re.compile(r"^(\s*)(from|import) agentmem_ref\.(\w+)(\b.*)$")
_PARENTS = re.compile(r"Path\(__file__\)\.resolve\(\)\.parents\[(\d)\]")


def _target(name: str, table: dict[str, str], from_layer: str | None) -> str:
    """Return the relative package path that reaches ``name`` from ``from_layer``.

    ``from_layer`` is None for a top-level resident (``__init__``, ``__main__``).
    """
    if name in STAYS:
        return "." if from_layer is None else ".."
    layer = table.get(name)
    if layer is None:
        raise SystemExit(f"relative import of unknown module: {name}")
    if from_layer is None:
        return f".{layer}"
    if layer == from_layer:
        return "."
    return f"..{layer}"


def rewrite_imports(text: str, table: dict[str, str], from_layer: str | None) -> str:
    out: list[str] = []
    for line in text.split("\n"):
        m = _REL_IMPORT.match(line)
        if m:
            indent, mod, names = m.groups()
            if mod == "":
                if names.strip().startswith("("):
                    raise SystemExit(f"unsupported multi-line `from . import (`: {line!r}")
                groups: dict[str, list[str]] = {}
                for entry in [n.strip() for n in names.split(",") if n.strip()]:
                    name = entry.split(" as ")[0].strip()
                    groups.setdefault(_target(name, table, from_layer), []).append(entry)
                for target, group in groups.items():
                    out.append(f"{indent}from {target} import {', '.join(group)}")
                continue
            target = _target(mod, table, from_layer)
            prefix = "." if target == "." else target + "."
            if target.endswith(mod):  # top-level resident reached from a layer: `.._paths`
                prefix = target[: -len(mod)]
            out.append(f"{indent}from {prefix}{mod} import {names}")
            continue
        m = _ABS_IMPORT.match(line)
        if m and m.group(3) in table:
            indent, kw, mod, rest = m.groups()
            out.append(f"{indent}{kw} agentmem_ref.{table[mod]}.{mod}{rest}")
            continue
        out.append(line)
    return "\n".join(out)


def _insert_after_imports(lines: list[str], new_line: str) -> list[str]:
    """Insert ``new_line`` after the last top-level import that precedes any code."""
    last = -1
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^(import |from )", line):
            if line.rstrip().endswith("("):
                while not lines[i].rstrip().endswith(")"):
                    i += 1
            last = i
        elif re.match(r"^(def |class |async def |[A-Za-z_][A-Za-z0-9_]* *=)", line):
            break
        i += 1
    if last < 0:
        raise SystemExit("could not find an import block to extend")
    return lines[: last + 1] + [new_line] + lines[last + 1 :]


def rewrite_paths(text: str) -> str:
    """Replace depth-coupled root computations with the roots from ``_paths``."""
    used: list[str] = []

    def sub(m: re.Match[str]) -> str:
        depth = m.group(1)
        name = {"2": "REPO_ROOT", "1": "REFERENCE_ROOT", "0": "PACKAGE_ROOT"}[depth]
        if name not in used:
            used.append(name)
        return name

    text = _PARENTS.sub(sub, text)
    if "resources.files(__package__)" in text:
        text = text.replace("resources.files(__package__)", "resources.files(PACKAGE_NAME)")
        used.append("PACKAGE_NAME")
    if not used:
        return text
    names = ", ".join(n for n in _PATHS_NAMES if n in used)
    lines = text.split("\n")
    if any(re.match(r"^from \.\.?_paths import", l) for l in lines):
        return text
    return "\n".join(_insert_after_imports(lines, f"from .._paths import {names}"))


# ----------------------------------------------------------------------------- moving

def _git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def _write(path: Path, text: str) -> None:
    path.write_bytes(text.encode("utf-8").replace(b"\r\n", b"\n"))


def move(package: Path) -> None:
    table = assignment()
    dirty = _git("status", "--porcelain", "--untracked-files=no", "--", str(package)).strip()
    if dirty:
        raise SystemExit("refusing to restructure with modified tracked files:\n" + dirty)
    for mod in table:
        if not (package / f"{mod}.py").is_file() and not (package / table[mod] / f"{mod}.py").is_file():
            raise SystemExit(f"module in table but not on disk: {mod}")
    for layer in LAYER_ORDER:
        (package / layer).mkdir(exist_ok=True)
        init = package / layer / "__init__.py"
        if not init.exists():
            _write(init, layer_init_source(layer))
            _git("add", str(init))
    for mod, layer in table.items():
        src = package / f"{mod}.py"
        dst = package / layer / f"{mod}.py"
        if dst.is_file():
            continue  # already moved
        _git("mv", str(src), str(dst))
        text = dst.read_text(encoding="utf-8")
        text = rewrite_imports(text, table, layer)
        text = rewrite_paths(text)
        _write(dst, text)
        _write(src, alias_source(mod, layer))
        _git("add", str(src))
    for resident in ("__init__", "__main__"):
        path = package / f"{resident}.py"
        _write(path, rewrite_imports(path.read_text(encoding="utf-8"), table, None))
    print(f"restructured {len(table)} modules into {len(LAYER_ORDER)} layers")


def problems(package: Path) -> list[str]:
    table = assignment()
    found: list[str] = []
    for layer in LAYER_ORDER:
        if not (package / layer / "__init__.py").is_file():
            found.append(f"missing layer package: {layer}")
    for mod, layer in table.items():
        real = package / layer / f"{mod}.py"
        alias = package / f"{mod}.py"
        if not real.is_file():
            found.append(f"not at assigned location: {layer}/{mod}.py")
        if not alias.is_file():
            found.append(f"missing alias: {mod}.py")
        elif alias.read_text(encoding="utf-8") != alias_source(mod, layer):
            found.append(f"alias does not match template: {mod}.py")
    for path in sorted(package.glob("*.py")):
        name = path.stem
        if name not in table and name not in STAYS:
            found.append(f"unassigned top-level module: {name}.py")
    for layer in LAYER_ORDER:
        for path in sorted((package / layer).glob("*.py")):
            if path.stem != "__init__" and table.get(path.stem) != layer:
                found.append(f"module in the wrong layer: {layer}/{path.name}")
    for path in package.rglob("*.py"):
        if path.stem == "_paths":
            continue
        if _PARENTS.search(path.read_text(encoding="utf-8")):
            found.append(f"depth-coupled path resolution remains: {path.relative_to(package)}")
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="report whether the tree matches the table")
    parser.add_argument("--package", type=Path, default=PACKAGE)
    args = parser.parse_args(argv)
    if args.check:
        found = problems(args.package)
        for item in found:
            print(item)
        print("layout matches table" if not found else f"{len(found)} problem(s)")
        return 1 if found else 0
    move(args.package)
    found = problems(args.package)
    for item in found:
        print(item)
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
