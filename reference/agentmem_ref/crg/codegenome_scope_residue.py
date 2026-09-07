"""#293 closeout pressure for CodeGenome traversal scope and deletion residue.

This module supplements the existing provider-neutral traversal qualification.
It does not grant a stronger capability maturity. It proves that CodeGenome's
external repository scope must be explicitly bound before Agent Memory may use
provider output, and that source deletion after full rebuild changes current
admissibility without fabricating a physical-erasure claim for historical
provider artifacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from pathlib import Path
from typing import Mapping

from .code_graph_qualification import CODEGENOME_COMMIT, PROFILE_ID, PROFILE_VERSION
from .codegenome_profile import profile_digest, validate_profile


CLOSEOUT_PROFILE_ID = "codegenome-traversal-scope-residue"
CLOSEOUT_PROFILE_VERSION = "1.0.0"
_LINE = re.compile(r"^line (\d+):(\d+)$")


class CodeGenomeScopeResidueError(ValueError):
    """The external scope or deletion/currentness evidence is unsafe or incomplete."""


@dataclass(frozen=True)
class ExternalScopeBinding:
    binding_ref: str
    component_id: str
    component_version: str
    component_profile_digest: str
    provider_scope_ref: str
    agent_memory_scope_ref: str
    tenant_ref: str
    project_ref: str
    binding_version: str = "1.0.0"

    def __post_init__(self) -> None:
        for name in (
            "binding_ref",
            "component_id",
            "component_version",
            "component_profile_digest",
            "provider_scope_ref",
            "agent_memory_scope_ref",
            "tenant_ref",
            "project_ref",
            "binding_version",
        ):
            if not getattr(self, name):
                raise CodeGenomeScopeResidueError(f"{name} is required")
        if self.component_id != "codegenome":
            raise CodeGenomeScopeResidueError("scope binding must target codegenome")
        if len(self.component_version) != 40 or any(
            ch not in "0123456789abcdef" for ch in self.component_version
        ):
            raise CodeGenomeScopeResidueError("component_version must be 40 lowercase hex")
        if not self.component_profile_digest.startswith("sha256:") or len(self.component_profile_digest) != 71:
            raise CodeGenomeScopeResidueError("component_profile_digest must be sha256:<64 lowercase hex>")
        try:
            int(self.component_profile_digest.removeprefix("sha256:"), 16)
        except ValueError as exc:
            raise CodeGenomeScopeResidueError(
                "component_profile_digest must be sha256:<64 lowercase hex>"
            ) from exc
        if self.component_profile_digest != self.component_profile_digest.lower():
            raise CodeGenomeScopeResidueError("component_profile_digest must be lowercase")

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class ScopeAdmission:
    admitted: bool
    reason: str
    binding_ref: str | None
    provider_scope_ref: str
    agent_memory_scope_ref: str
    authority_effect: str = "none"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def evaluate_scope_bridge(
    *,
    binding: ExternalScopeBinding | None,
    component_version: str,
    component_profile_digest: str,
    provider_scope_ref: str,
    agent_memory_scope_ref: str,
) -> ScopeAdmission:
    """Admit provider output only through an exact version-bound external-scope binding."""
    if not provider_scope_ref or not agent_memory_scope_ref:
        return ScopeAdmission(
            admitted=False,
            reason="scope_identity_missing",
            binding_ref=binding.binding_ref if binding else None,
            provider_scope_ref=provider_scope_ref,
            agent_memory_scope_ref=agent_memory_scope_ref,
        )
    if binding is None:
        return ScopeAdmission(
            admitted=False,
            reason="external_scope_binding_missing",
            binding_ref=None,
            provider_scope_ref=provider_scope_ref,
            agent_memory_scope_ref=agent_memory_scope_ref,
        )
    if component_version != binding.component_version:
        return ScopeAdmission(
            admitted=False,
            reason="component_version_mismatch",
            binding_ref=binding.binding_ref,
            provider_scope_ref=provider_scope_ref,
            agent_memory_scope_ref=agent_memory_scope_ref,
        )
    if component_profile_digest != binding.component_profile_digest:
        return ScopeAdmission(
            admitted=False,
            reason="component_profile_mismatch",
            binding_ref=binding.binding_ref,
            provider_scope_ref=provider_scope_ref,
            agent_memory_scope_ref=agent_memory_scope_ref,
        )
    if provider_scope_ref != binding.provider_scope_ref:
        return ScopeAdmission(
            admitted=False,
            reason="provider_scope_mismatch",
            binding_ref=binding.binding_ref,
            provider_scope_ref=provider_scope_ref,
            agent_memory_scope_ref=agent_memory_scope_ref,
        )
    if agent_memory_scope_ref != binding.agent_memory_scope_ref:
        return ScopeAdmission(
            admitted=False,
            reason="agent_memory_scope_mismatch",
            binding_ref=binding.binding_ref,
            provider_scope_ref=provider_scope_ref,
            agent_memory_scope_ref=agent_memory_scope_ref,
        )
    return ScopeAdmission(
        admitted=True,
        reason="exact_external_scope_binding",
        binding_ref=binding.binding_ref,
        provider_scope_ref=provider_scope_ref,
        agent_memory_scope_ref=agent_memory_scope_ref,
    )


def _codegenome_start_lines(path: Path) -> set[int]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise CodeGenomeScopeResidueError("CodeGenome query output must be a list")
    lines: set[int] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        node = item.get("node")
        if not isinstance(node, str):
            continue
        match = _LINE.fullmatch(node)
        if match:
            lines.add(int(match.group(1)))
    return lines


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def build_closeout_report(
    *,
    agent_memory_commit: str,
    component_profile: Mapping[str, object],
    binding: ExternalScopeBinding,
    v1_main_downstream: Path,
    v2_main_downstream: Path,
    v1_store_manifest: Path,
    v2_store_manifest: Path,
) -> dict[str, object]:
    if len(agent_memory_commit) != 40 or any(ch not in "0123456789abcdef" for ch in agent_memory_commit):
        raise CodeGenomeScopeResidueError("agent_memory_commit must be 40 lowercase hex")

    component = validate_profile(component_profile)
    current_profile_digest = profile_digest(component_profile)
    traversal = next(
        capability for capability in component.capabilities if capability.capability_id == "code_graph_traversal"
    )
    if traversal.maturity != "evidence_proven":
        raise CodeGenomeScopeResidueError("closeout requires the existing evidence-proven traversal qualification")
    if traversal.scope_posture != "external_scope_bridge":
        raise CodeGenomeScopeResidueError("CodeGenome traversal must use external_scope_bridge")

    v1_lines = _codegenome_start_lines(v1_main_downstream)
    v2_lines = _codegenome_start_lines(v2_main_downstream)
    source_deletion_current = 1 in v1_lines and 1 not in v2_lines and 13 in v2_lines

    common_scope_args = {
        "component_version": component.component_version,
        "component_profile_digest": current_profile_digest,
    }
    admitted = evaluate_scope_bridge(
        binding=binding,
        provider_scope_ref=binding.provider_scope_ref,
        agent_memory_scope_ref=binding.agent_memory_scope_ref,
        **common_scope_args,
    )
    missing_binding = evaluate_scope_bridge(
        binding=None,
        provider_scope_ref=binding.provider_scope_ref,
        agent_memory_scope_ref=binding.agent_memory_scope_ref,
        **common_scope_args,
    )
    stale_component = evaluate_scope_bridge(
        binding=binding,
        component_version="0" * 40,
        component_profile_digest=current_profile_digest,
        provider_scope_ref=binding.provider_scope_ref,
        agent_memory_scope_ref=binding.agent_memory_scope_ref,
    )
    stale_profile = evaluate_scope_bridge(
        binding=binding,
        component_version=component.component_version,
        component_profile_digest="sha256:" + "0" * 64,
        provider_scope_ref=binding.provider_scope_ref,
        agent_memory_scope_ref=binding.agent_memory_scope_ref,
    )
    foreign_provider = evaluate_scope_bridge(
        binding=binding,
        provider_scope_ref=binding.provider_scope_ref + "/foreign",
        agent_memory_scope_ref=binding.agent_memory_scope_ref,
        **common_scope_args,
    )
    foreign_agent_scope = evaluate_scope_bridge(
        binding=binding,
        provider_scope_ref=binding.provider_scope_ref,
        agent_memory_scope_ref=binding.agent_memory_scope_ref + "/foreign",
        **common_scope_args,
    )

    invariants = {
        "exact_codegenome_pin": component.component_version == CODEGENOME_COMMIT,
        "base_traversal_qualification_bound": any(
            ref == f"qualification:codegenome:{PROFILE_ID}@{PROFILE_VERSION}"
            for ref in traversal.evidence_refs
        ),
        "external_scope_bridge_declared": traversal.scope_posture == "external_scope_bridge",
        "scope_binding_version_bound": binding.component_version == component.component_version,
        "scope_binding_profile_bound": binding.component_profile_digest == current_profile_digest,
        "exact_scope_binding_admitted": admitted.admitted,
        "missing_scope_binding_refused": not missing_binding.admitted,
        "stale_component_scope_binding_refused": not stale_component.admitted,
        "stale_profile_scope_binding_refused": not stale_profile.admitted,
        "foreign_provider_scope_refused": not foreign_provider.admitted,
        "foreign_agent_memory_scope_refused": not foreign_agent_scope.admitted,
        "source_deleted_old_leaf_not_current_after_rebuild": source_deletion_current,
        "historical_v1_store_disclosed": v1_store_manifest.exists() and v1_store_manifest.stat().st_size > 0,
        "current_v2_store_disclosed": v2_store_manifest.exists() and v2_store_manifest.stat().st_size > 0,
        "physical_erasure_not_claimed": True,
        "no_authority_effect": all(
            result.authority_effect == "none"
            for result in (
                admitted,
                missing_binding,
                stale_component,
                stale_profile,
                foreign_provider,
                foreign_agent_scope,
            )
        ),
    }

    return {
        "schema_version": "1.0.0",
        "profile": {"id": CLOSEOUT_PROFILE_ID, "version": CLOSEOUT_PROFILE_VERSION},
        "agent_memory_commit": agent_memory_commit,
        "component": {
            "component_id": component.component_id,
            "component_version": component.component_version,
            "component_profile_version": component.profile_version,
            "component_profile_digest": current_profile_digest,
        },
        "base_qualification": {
            "profile_id": PROFILE_ID,
            "profile_version": PROFILE_VERSION,
            "evidence_ref": f"qualification:codegenome:{PROFILE_ID}@{PROFILE_VERSION}",
        },
        "scope_bridge": {
            "binding": binding.to_dict(),
            "exact": admitted.to_dict(),
            "missing_binding": missing_binding.to_dict(),
            "stale_component": stale_component.to_dict(),
            "stale_profile": stale_profile.to_dict(),
            "foreign_provider": foreign_provider.to_dict(),
            "foreign_agent_memory_scope": foreign_agent_scope.to_dict(),
        },
        "deletion_rebuild": {
            "source_change": "v1_leaf_removed_v2_replacement_leaf",
            "historical_v1_start_lines": sorted(v1_lines),
            "current_v2_start_lines": sorted(v2_lines),
            "old_source_current_after_rebuild": 1 in v2_lines,
            "replacement_source_current_after_rebuild": 13 in v2_lines,
            "currentness_result": "deleted_source_not_current" if source_deletion_current else "unproven",
            "historical_provider_artifact_retained": True,
            "historical_provider_artifact_current": False,
            "physical_erasure_proven": False,
            "residue_posture": "historical_provider_artifact_disclosed_not_current",
            "v1_store_manifest_sha256": sha256_file(v1_store_manifest),
            "v2_store_manifest_sha256": sha256_file(v2_store_manifest),
        },
        "invariants": invariants,
        "authority_effect": "none",
    }
