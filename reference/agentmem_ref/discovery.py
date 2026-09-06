"""Read-only attach-mode discovery and provider availability probes.

Discovery is evidence only. It does not mutate configuration, install or replace
components, grant capability maturity, prove currentness, or create authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import metadata, util
import json
from pathlib import Path
import shutil
from typing import Mapping

import jsonschema


PROBE_SCHEMA_VERSION = "1.0.0"
_DISTRIBUTION_NAME = "agent-memory-reference"
_PROBE_SCHEMA_DATA_SUFFIX = "agent_memory_reference/schemas/provider-probes.schema.json"
_SECRET_SCHEMES = ("env://", "secret://", "vault://", "keyring://")
_SUPPORTED_PROBE_KINDS = frozenset({"executable", "python_import", "filesystem_path"})


class DiscoveryInputError(ValueError):
    """A discovery/probe input cannot be interpreted safely."""


@dataclass(frozen=True)
class ProbeDescriptor:
    probe_id: str
    subject_kind: str
    subject_id: str
    probe_kind: str
    target: str
    required_for_startability: bool


@dataclass(frozen=True)
class ProbeResult:
    descriptor: ProbeDescriptor
    status: str
    observed_at: str
    evidence: Mapping[str, object]

    @property
    def startability_satisfied(self) -> bool:
        if not self.descriptor.required_for_startability:
            return True
        return self.status == "available"

    def to_dict(self) -> dict[str, object]:
        return {
            "probe_id": self.descriptor.probe_id,
            "subject_kind": self.descriptor.subject_kind,
            "subject_id": self.descriptor.subject_id,
            "probe_kind": self.descriptor.probe_kind,
            "target": self.descriptor.target,
            "required_for_startability": self.descriptor.required_for_startability,
            "status": self.status,
            "observed_at": self.observed_at,
            "evidence": dict(self.evidence),
            "startability_satisfied": self.startability_satisfied,
            "authority_effect": "none",
        }


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _probe_schema_path() -> Path:
    source_path = _repo_root() / "schemas" / "provider-probes.schema.json"
    if source_path.is_file():
        return source_path

    try:
        distribution_files = metadata.files(_DISTRIBUTION_NAME) or ()
    except metadata.PackageNotFoundError:
        distribution_files = ()

    for entry in distribution_files:
        normalized = str(entry).replace("\\", "/")
        if normalized.endswith(_PROBE_SCHEMA_DATA_SUFFIX):
            installed_path = Path(entry.locate())
            if installed_path.is_file():
                return installed_path

    raise DiscoveryInputError(
        "provider probe schema is unavailable; install the distribution with its packaged schema data"
    )


def _probe_schema() -> dict:
    return json.loads(_probe_schema_path().read_text(encoding="utf-8"))


def _configured_subjects(config_value: Mapping[str, object]) -> dict[str, set[str]]:
    component_ids: set[str] = set()
    for raw in config_value.get("components", ()):  # type: ignore[union-attr]
        if not isinstance(raw, Mapping):
            continue
        declaration = raw.get("declaration")
        if isinstance(declaration, Mapping) and declaration.get("component_id"):
            component_ids.add(str(declaration["component_id"]))

    peer_ids: set[str] = set()
    for raw in config_value.get("governance_peers", ()):  # type: ignore[union-attr]
        if isinstance(raw, Mapping) and raw.get("peer_id"):
            peer_ids.add(str(raw["peer_id"]))

    return {"component": component_ids, "governance_peer": peer_ids}


def load_probe_manifest(
    path: str | Path,
    *,
    config_value: Mapping[str, object],
) -> tuple[ProbeDescriptor, ...]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DiscoveryInputError(f"provider probe manifest not found: {source}") from exc
    except json.JSONDecodeError as exc:
        raise DiscoveryInputError(f"provider probe manifest is not valid JSON: {source}") from exc

    try:
        jsonschema.Draft202012Validator(_probe_schema()).validate(value)
    except jsonschema.ValidationError as exc:
        location = ".".join(str(part) for part in exc.absolute_path)
        suffix = f" at {location}" if location else ""
        raise DiscoveryInputError(f"provider probe schema violation{suffix}: {exc.message}") from exc

    subjects = _configured_subjects(config_value)
    descriptors: list[ProbeDescriptor] = []
    probe_ids: set[str] = set()
    for raw in value["probes"]:
        descriptor = ProbeDescriptor(
            probe_id=str(raw["probe_id"]),
            subject_kind=str(raw["subject_kind"]),
            subject_id=str(raw["subject_id"]),
            probe_kind=str(raw["probe_kind"]),
            target=str(raw["target"]),
            required_for_startability=bool(raw["required_for_startability"]),
        )
        if descriptor.probe_id in probe_ids:
            raise DiscoveryInputError(f"duplicate provider probe id: {descriptor.probe_id!r}")
        probe_ids.add(descriptor.probe_id)
        if descriptor.subject_id not in subjects.get(descriptor.subject_kind, set()):
            raise DiscoveryInputError(
                f"provider probe {descriptor.probe_id!r} references unconfigured "
                f"{descriptor.subject_kind} {descriptor.subject_id!r}"
            )
        if descriptor.target.startswith(_SECRET_SCHEMES):
            raise DiscoveryInputError(
                f"provider probe {descriptor.probe_id!r} must not resolve or emit secret references"
            )
        descriptors.append(descriptor)
    return tuple(descriptors)


def _probe_executable(target: str) -> tuple[str, dict[str, object]]:
    resolved = shutil.which(target)
    if resolved is None:
        return "unavailable", {"lookup": "PATH_or_explicit_executable", "resolved": False}
    return "available", {
        "lookup": "PATH_or_explicit_executable",
        "resolved": True,
        "resolved_path": resolved,
    }


def _probe_python_import(target: str) -> tuple[str, dict[str, object]]:
    try:
        spec = util.find_spec(target)
    except (ImportError, AttributeError, ValueError) as exc:
        return "probe_failed", {"lookup": "python_import_spec", "error_type": type(exc).__name__}
    if spec is None:
        return "unavailable", {"lookup": "python_import_spec", "resolved": False}
    return "available", {
        "lookup": "python_import_spec",
        "resolved": True,
        "origin": spec.origin or "namespace_or_builtin",
    }


def _probe_filesystem_path(target: str) -> tuple[str, dict[str, object]]:
    path = Path(target).expanduser()
    try:
        exists = path.exists()
    except OSError as exc:
        return "probe_failed", {"lookup": "filesystem_exists", "error_type": type(exc).__name__}
    if not exists:
        return "unavailable", {"lookup": "filesystem_exists", "resolved": False}
    if path.is_file():
        path_type = "file"
    elif path.is_dir():
        path_type = "directory"
    else:
        path_type = "other"
    return "available", {
        "lookup": "filesystem_exists",
        "resolved": True,
        "path_type": path_type,
    }


def run_probe(descriptor: ProbeDescriptor, *, observed_at: str) -> ProbeResult:
    try:
        if descriptor.probe_kind == "executable":
            status, evidence = _probe_executable(descriptor.target)
        elif descriptor.probe_kind == "python_import":
            status, evidence = _probe_python_import(descriptor.target)
        elif descriptor.probe_kind == "filesystem_path":
            status, evidence = _probe_filesystem_path(descriptor.target)
        else:
            status, evidence = "unsupported", {"supported_probe_kinds": sorted(_SUPPORTED_PROBE_KINDS)}
    except OSError as exc:
        status, evidence = "probe_failed", {"error_type": type(exc).__name__}
    return ProbeResult(
        descriptor=descriptor,
        status=status,
        observed_at=observed_at,
        evidence=evidence,
    )


def discover_configuration(
    config_value: Mapping[str, object],
    *,
    probe_path: str | Path,
) -> dict[str, object]:
    descriptors = load_probe_manifest(probe_path, config_value=config_value)
    observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    results = tuple(run_probe(item, observed_at=observed_at) for item in descriptors)

    counts = {name: 0 for name in ("available", "unavailable", "probe_failed", "unsupported")}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1

    required = tuple(result for result in results if result.descriptor.required_for_startability)
    failed_required = tuple(result for result in required if not result.startability_satisfied)
    if failed_required:
        startability = "blocked_by_required_probe"
    elif required:
        startability = "proven_for_declared_probes"
    else:
        startability = "not_proven_no_required_probes"

    subjects = _configured_subjects(config_value)
    return {
        "schema_version": PROBE_SCHEMA_VERSION,
        "command": "discover",
        "observation_posture": "explicit_declared_signals_only",
        "configured_subjects": {
            "components": sorted(subjects["component"]),
            "governance_peers": sorted(subjects["governance_peer"]),
        },
        "probe_count": len(results),
        "status_counts": counts,
        "startability": startability,
        "results": [result.to_dict() for result in results],
        "mutated_configuration": False,
        "authority_effect": "none",
    }
