"""Exact-version qualification normalizer for MemOS local plugin v2.0.17.

Consumes raw provider evidence from the pinned local SQLite-backed MemoryCore
fixture. Qualification remains bounded to resource artifact memory and never
promotes MemOS provider verdicts, learned policy, L2/L3 state, or skills into
Agent Memory authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

from .capabilities import ComponentDeclaration
from .qualification import (
    AdapterResult,
    QualificationRuntime,
    QualificationSubject,
    QualifiedCapabilityContract,
    qualification_from_adapter_results,
)

MEMOS_RELEASE = "memos-local-plugin-v2.0.17"
MEMOS_VERSION = "2.0.17"
MEMOS_COMMIT = "d3d1bcfaff65f31b621d58bc236ece6d1e0da5ab"
MEMOS_REPOSITORY = "MemTensor/MemOS"
MEMOS_PACKAGE = "@memtensor/memos-local-plugin"
SOURCE_LICENSE = "Apache-2.0"
PACKAGE_LICENSE_METADATA = "MIT"
CAPABILITY_ID = "resource_artifact_memory"
CAPABILITY_VERSION = "1.0"
PROFILE_ID = "memos-local-v2017-trace-resource-artifact"
PROFILE_VERSION = "1.0.0"
ADAPTER_ID = "memos-local-v2017-trace-bundle-adapter"
ADAPTER_VERSION = "1.0.0"
FIXTURE_ID = "memos-local-v2017-trace-lifecycle-v1"


class MemOSQualificationError(ValueError):
    """Raw MemOS evidence is incomplete or contradicts the claimed contract."""


@dataclass(frozen=True)
class MemOSObservation:
    check_id: str
    passed: bool
    evidence_ref: str
    detail: str = ""

    def as_check(self) -> tuple[str, bool, str]:
        return (self.check_id, self.passed, self.evidence_ref)


@dataclass(frozen=True)
class MemOSQualificationResult:
    qualification: dict[str, object] | None
    observations: tuple[MemOSObservation, ...]
    eligible: bool
    limitations: tuple[str, ...]

    @property
    def authority_effect(self) -> str:
        return "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": {
                "repository": MEMOS_REPOSITORY,
                "release": MEMOS_RELEASE,
                "version": MEMOS_VERSION,
                "commit": MEMOS_COMMIT,
                "package": MEMOS_PACKAGE,
                "source_license": SOURCE_LICENSE,
                "package_license_metadata": PACKAGE_LICENSE_METADATA,
            },
            "capability": {
                "capability_id": CAPABILITY_ID,
                "capability_version": CAPABILITY_VERSION,
            },
            "eligible": self.eligible,
            "authority_effect": "none",
            "observations": [
                {
                    "check_id": item.check_id,
                    "passed": item.passed,
                    "evidence_ref": item.evidence_ref,
                    "detail": item.detail,
                }
                for item in self.observations
            ],
            "limitations": list(self.limitations),
            "qualification": self.qualification,
        }


def load_component_profile(path: Path) -> ComponentDeclaration:
    return ComponentDeclaration.from_dict(json.loads(path.read_text(encoding="utf-8")))


def qualify_memos_local_v2017(
    *,
    raw_evidence: dict[str, Any],
    component: ComponentDeclaration,
    agent_memory_commit: str,
    raw_evidence_ref: str,
) -> MemOSQualificationResult:
    _validate_component_identity(component)
    observations = _observations(raw_evidence, raw_evidence_ref)
    limitations = _limitations(raw_evidence, observations)
    eligible = all(item.passed for item in observations)
    if not eligible:
        return MemOSQualificationResult(
            qualification=None,
            observations=tuple(observations),
            eligible=False,
            limitations=tuple(limitations),
        )

    subject = QualificationSubject(
        component_id=component.component_id,
        component_version=component.component_version,
        implementation_ref=f"github:{MEMOS_REPOSITORY}@{MEMOS_COMMIT}:apps/memos-local-plugin",
        capability_id=CAPABILITY_ID,
        capability_version=CAPABILITY_VERSION,
        adapter_id=ADAPTER_ID,
        adapter_version=ADAPTER_VERSION,
        qualification_profile_id=PROFILE_ID,
        qualification_profile_version=PROFILE_VERSION,
    )
    runtime = QualificationRuntime(
        configuration_digest=_sha256_json(
            {
                "agent_memory_commit": agent_memory_commit,
                "provider_commit": MEMOS_COMMIT,
                "provider_release": MEMOS_RELEASE,
                "provider_version": MEMOS_VERSION,
                "package": MEMOS_PACKAGE,
                "adapter": "direct-memory-core",
                "database": "sqlite",
                "hosted_llm_credentials": False,
                "fixture": FIXTURE_ID,
            }
        ),
        fixture_id=FIXTURE_ID,
        fixture_digest=_sha256_json(raw_evidence.get("fixture", {})),
        dependency_refs=(
            f"npm:{MEMOS_PACKAGE}@{MEMOS_VERSION}",
            f"github:{MEMOS_REPOSITORY}@{MEMOS_COMMIT}",
        ),
        runtime_refs=(
            "memos-local-plugin:MemoryCore",
            "memos-local-plugin:importBundle",
            "memos-local-plugin:updateTrace",
            "memos-local-plugin:sqlite",
        ),
    )
    common = dict(
        subject=subject,
        runtime_identity=f"memos-local-plugin:{MEMOS_VERSION}:sqlite",
        input_refs=(FIXTURE_ID,),
        raw_provider_refs=(raw_evidence_ref,),
        normalized_refs=(f"qualification:{component.component_id}:{CAPABILITY_ID}",),
        failure_result="none",
    )
    adapter_results = (
        AdapterResult(
            operation="stable_trace_import_read_candidate",
            currentness="current",
            trace_ref="qualification:memos:initial-import",
            **common,
        ),
        AdapterResult(
            operation="stable_key_repeat_and_update",
            currentness="replacement_current",
            trace_ref="qualification:memos:stable-key-update",
            **common,
        ),
        AdapterResult(
            operation="restart_readback",
            currentness="reconstructed_current",
            trace_ref="qualification:memos:restart-readback",
            **common,
        ),
        AdapterResult(
            operation="trace_delete_residue_scan",
            currentness="deleted_no_candidate_residue",
            trace_ref="qualification:memos:delete-residue",
            **common,
        ),
    )
    qualification = qualification_from_adapter_results(
        subject=subject,
        runtime=runtime,
        license_id=SOURCE_LICENSE,
        license_ref=f"github:{MEMOS_REPOSITORY}@{MEMOS_COMMIT}:LICENSE",
        use_posture="runtime_allowed",
        results=adapter_results,
        checks=tuple(item.as_check() for item in observations),
        artifact_digests=(_sha256_json(raw_evidence),),
        maturity_before="runtime_wired",
        profile_maturity_ceiling="evidence_proven",
        earned_maturity="evidence_proven",
        limitations=tuple(limitations),
        qualified_contract=QualifiedCapabilityContract.from_component(
            component,
            capability_id=CAPABILITY_ID,
            capability_version=CAPABILITY_VERSION,
        ),
    )
    qualification.assert_current_declaration(component)
    return MemOSQualificationResult(
        qualification=qualification.to_dict(),
        observations=tuple(observations),
        eligible=True,
        limitations=tuple(limitations),
    )


def _validate_component_identity(component: ComponentDeclaration) -> None:
    if component.component_id != "memos-local-plugin-v2.0.17":
        raise MemOSQualificationError("unexpected MemOS component identity")
    if component.component_version != MEMOS_VERSION:
        raise MemOSQualificationError("MemOS component version does not match pinned package")
    matches = [
        capability
        for capability in component.capabilities
        if capability.capability_id == CAPABILITY_ID
        and capability.capability_version == CAPABILITY_VERSION
    ]
    if len(matches) != 1 or len(component.capabilities) != 1:
        raise MemOSQualificationError("bounded profile must expose only resource_artifact_memory@1.0")
    if matches[0].authority_effect != "none":
        raise MemOSQualificationError("MemOS qualification cannot grant authority")


def _observations(raw: dict[str, Any], evidence_ref: str) -> list[MemOSObservation]:
    identity = raw.get("identity", {})
    config = raw.get("configuration", {})
    initial = raw.get("initial", {})
    repeat = raw.get("same_key_repeat", {})
    replacement = raw.get("replacement", {})
    restart = raw.get("restart", {})
    durable_repeat = raw.get("durable_repeat_after_restart", {})
    deletion = raw.get("deletion", {})

    def obs(check_id: str, passed: bool, detail: str) -> MemOSObservation:
        return MemOSObservation(check_id, bool(passed), evidence_ref, detail)

    return [
        obs(
            "exact-provider-identity",
            identity.get("release") == MEMOS_RELEASE
            and identity.get("version") == MEMOS_VERSION
            and identity.get("commit") == MEMOS_COMMIT
            and identity.get("package") == MEMOS_PACKAGE,
            "tag/version/source commit/package must match the qualification pin",
        ),
        obs(
            "source-rights-discrepancy-preserved",
            identity.get("source_license") == SOURCE_LICENSE
            and identity.get("source_license_verified") is True
            and identity.get("package_license_metadata") == PACKAGE_LICENSE_METADATA
            and identity.get("license_discrepancy_preserved") is True,
            "root Apache-2.0 grant and package MIT metadata discrepancy must both be retained",
        ),
        obs(
            "direct-local-core-no-hosted-secret",
            config.get("adapter") == "direct-memory-core"
            and config.get("database") == "sqlite"
            and config.get("hosted_llm_api_key_present") is False
            and config.get("hosted_embedding_api_key_present") is False,
            "bounded fixture must use the direct local core and SQLite without hosted provider credentials",
        ),
        obs(
            "initial-stable-trace-readback",
            initial.get("imported") == 1
            and initial.get("skipped") == 0
            and initial.get("trace_count") == 1
            and initial.get("get_matches_initial") is True
            and initial.get("candidate_contains_initial") is True,
            "caller-supplied trace identity must be imported once, directly readable, and query-visible",
        ),
        obs(
            "stable-key-repeat-idempotency",
            repeat.get("imported") == 0
            and repeat.get("skipped") == 1
            and repeat.get("trace_count") == 1
            and repeat.get("get_matches_initial") is True,
            "re-importing the same stable trace ID must skip rather than mint a duplicate",
        ),
        obs(
            "stable-key-update-currentness",
            replacement.get("updated_same_id") is True
            and replacement.get("trace_count") == 1
            and replacement.get("get_matches_replacement") is True
            and replacement.get("candidate_contains_replacement") is True
            and replacement.get("candidate_contains_initial") is False,
            "updateTrace must replace user-facing content on the same durable provider ID",
        ),
        obs(
            "restart-reconstruction",
            restart.get("restart_succeeded") is True
            and restart.get("trace_count") == 1
            and restart.get("get_matches_replacement") is True
            and restart.get("candidate_contains_replacement") is True,
            "SQLite-backed trace state must reconstruct after MemoryCore shutdown/bootstrap",
        ),
        obs(
            "durable-key-after-restart",
            durable_repeat.get("imported") == 0
            and durable_repeat.get("skipped") == 1
            and durable_repeat.get("trace_count") == 1
            and durable_repeat.get("get_matches_replacement") is True,
            "the stable trace key must remain collision-detectable after restart",
        ),
        obs(
            "delete-readback-and-candidate-residue",
            deletion.get("delete_succeeded") is True
            and deletion.get("get_after_delete_is_null") is True
            and deletion.get("trace_count") == 0
            and deletion.get("candidate_contains_initial") is False
            and deletion.get("candidate_contains_replacement") is False,
            "hard delete must remove direct readback and old/new listTraces query residue",
        ),
        obs(
            "provider-identity-is-not-agent-memory-identity",
            raw.get("identity_boundary_preserved") is True,
            "MemOS trace/session/episode IDs remain provider-native evidence refs",
        ),
    ]


def _limitations(raw: dict[str, Any], observations: list[MemOSObservation]) -> list[str]:
    limitations = [
        "Qualification is exact to @memtensor/memos-local-plugin v2.0.17 and tag commit d3d1bcfaff65f31b621d58bc236ece6d1e0da5ab.",
        "Only stable-ID trace bundle resource memory is qualified; conversational capture, semantic ranking, L2/L3 state, skills, Hub behavior, and agent adapters remain outside this evidence boundary.",
        "Write atomicity and concurrent mutation ordering are not fault-injection qualified and remain declared none.",
        "Candidate lookup uses deterministic listTraces text filtering and carries no Agent Memory recall-admission authority.",
        "The tagged repository root grants Apache-2.0 while package metadata declares MIT; runtime posture relies on the exact root license grant and retains the metadata discrepancy rather than resolving it by convenience.",
    ]
    failed = [item.check_id for item in observations if not item.passed]
    if failed:
        limitations.append("Provider did not satisfy the candidate v3 contract: " + ", ".join(failed))
    for note in raw.get("provider_notes", []):
        if isinstance(note, str) and note:
            limitations.append(note)
    return limitations


def _sha256_json(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()
