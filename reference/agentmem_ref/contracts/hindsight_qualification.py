"""Exact-version qualification normalizer for Hindsight v0.9.0.

This module does not execute Hindsight and does not grant authority. It consumes
raw evidence captured from the pinned provider runtime, checks the bounded
resource-artifact lifecycle contract, and emits a Capability Qualification v1.2
record only when the exact observed behavior supports the declared v3 contract.
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

HINDSIGHT_RELEASE = "v0.9.0"
HINDSIGHT_VERSION = "0.9.0"
HINDSIGHT_COMMIT = "b12646f49ec512136b9f709e608524ffed969668"
HINDSIGHT_REPOSITORY = "vectorize-io/hindsight"
HINDSIGHT_LICENSE = "MIT"
CAPABILITY_ID = "resource_artifact_memory"
CAPABILITY_VERSION = "1.0"
PROFILE_ID = "hindsight-v090-chunk-resource-artifact"
PROFILE_VERSION = "1.0.0"
ADAPTER_ID = "hindsight-v090-chunk-document-adapter"
ADAPTER_VERSION = "1.0.0"
FIXTURE_ID = "hindsight-v090-document-lifecycle-v1"


class HindsightQualificationError(ValueError):
    """Raw Hindsight evidence is incomplete or contradicts the claimed contract."""


@dataclass(frozen=True)
class HindsightObservation:
    check_id: str
    passed: bool
    evidence_ref: str
    detail: str = ""

    def as_check(self) -> tuple[str, bool, str]:
        return (self.check_id, self.passed, self.evidence_ref)


@dataclass(frozen=True)
class HindsightQualificationResult:
    qualification: dict[str, object] | None
    observations: tuple[HindsightObservation, ...]
    eligible: bool
    limitations: tuple[str, ...]

    @property
    def authority_effect(self) -> str:
        return "none"

    def to_dict(self) -> dict[str, object]:
        return {
            "provider": {
                "repository": HINDSIGHT_REPOSITORY,
                "release": HINDSIGHT_RELEASE,
                "version": HINDSIGHT_VERSION,
                "commit": HINDSIGHT_COMMIT,
                "license": HINDSIGHT_LICENSE,
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


def qualify_hindsight_v090(
    *,
    raw_evidence: dict[str, Any],
    component: ComponentDeclaration,
    agent_memory_commit: str,
    raw_evidence_ref: str,
) -> HindsightQualificationResult:
    """Normalize one exact Hindsight run into bounded qualification evidence."""
    _validate_component_identity(component)
    observations = _observations(raw_evidence, raw_evidence_ref)
    limitations = _limitations(raw_evidence, observations)
    eligible = all(item.passed for item in observations)
    if not eligible:
        return HindsightQualificationResult(
            qualification=None,
            observations=tuple(observations),
            eligible=False,
            limitations=tuple(limitations),
        )

    subject = QualificationSubject(
        component_id=component.component_id,
        component_version=component.component_version,
        implementation_ref=f"github:{HINDSIGHT_REPOSITORY}@{HINDSIGHT_COMMIT}",
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
                "provider_commit": HINDSIGHT_COMMIT,
                "provider_release": HINDSIGHT_RELEASE,
                "provider_version": HINDSIGHT_VERSION,
                "llm_provider": "none",
                "retain_extraction_mode": "chunks",
                "database": "pg0",
                "fixture": FIXTURE_ID,
            }
        ),
        fixture_id=FIXTURE_ID,
        fixture_digest=_sha256_json(raw_evidence.get("fixture", {})),
        dependency_refs=(
            f"pypi:hindsight-embed=={HINDSIGHT_VERSION}",
            f"github:{HINDSIGHT_REPOSITORY}@{HINDSIGHT_COMMIT}",
        ),
        runtime_refs=(
            "hindsight-embed:local-daemon",
            "hindsight:chunk-extraction",
            "hindsight:pg0",
        ),
    )
    common = dict(
        subject=subject,
        runtime_identity=f"hindsight-embed:{HINDSIGHT_VERSION}:pg0",
        input_refs=(FIXTURE_ID,),
        raw_provider_refs=(raw_evidence_ref,),
        normalized_refs=(f"qualification:{component.component_id}:{CAPABILITY_ID}",),
        failure_result="none",
    )
    adapter_results = (
        AdapterResult(
            operation="retain_read_recall",
            currentness="current",
            trace_ref="qualification:hindsight:initial-retain",
            **common,
        ),
        AdapterResult(
            operation="stable_key_replace",
            currentness="replacement_current",
            trace_ref="qualification:hindsight:stable-key-replace",
            **common,
        ),
        AdapterResult(
            operation="restart_readback",
            currentness="reconstructed_current",
            trace_ref="qualification:hindsight:restart-readback",
            **common,
        ),
        AdapterResult(
            operation="document_delete_residue_scan",
            currentness="deleted_no_recall_residue",
            trace_ref="qualification:hindsight:delete-residue",
            **common,
        ),
    )
    qualification = qualification_from_adapter_results(
        subject=subject,
        runtime=runtime,
        license_id=HINDSIGHT_LICENSE,
        license_ref=f"github:{HINDSIGHT_REPOSITORY}@{HINDSIGHT_COMMIT}:LICENSE",
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
    return HindsightQualificationResult(
        qualification=qualification.to_dict(),
        observations=tuple(observations),
        eligible=True,
        limitations=tuple(limitations),
    )


def _validate_component_identity(component: ComponentDeclaration) -> None:
    if component.component_id != "hindsight-v0.9.0":
        raise HindsightQualificationError("unexpected Hindsight component identity")
    if component.component_version != HINDSIGHT_VERSION:
        raise HindsightQualificationError("Hindsight component version does not match pinned provider")
    matches = [
        capability
        for capability in component.capabilities
        if capability.capability_id == CAPABILITY_ID
        and capability.capability_version == CAPABILITY_VERSION
    ]
    if len(matches) != 1:
        raise HindsightQualificationError("profile must expose exactly one bounded resource_artifact_memory capability")
    if len(component.capabilities) != 1:
        raise HindsightQualificationError("bounded Hindsight qualification must not promote unrelated capabilities")
    if matches[0].authority_effect != "none":
        raise HindsightQualificationError("Hindsight qualification cannot grant authority")


def _observations(raw: dict[str, Any], evidence_ref: str) -> list[HindsightObservation]:
    identity = raw.get("identity", {})
    config = raw.get("configuration", {})
    initial = raw.get("initial", {})
    repeat = raw.get("same_key_repeat", {})
    replacement = raw.get("replacement", {})
    restart = raw.get("restart", {})
    durable_repeat = raw.get("durable_repeat_after_restart", {})
    deletion = raw.get("deletion", {})

    def obs(check_id: str, passed: bool, detail: str) -> HindsightObservation:
        return HindsightObservation(check_id, bool(passed), evidence_ref, detail)

    return [
        obs(
            "exact-provider-identity",
            identity.get("release") == HINDSIGHT_RELEASE
            and identity.get("version") == HINDSIGHT_VERSION
            and identity.get("commit") == HINDSIGHT_COMMIT,
            "release/version/source commit must match the qualification pin",
        ),
        obs(
            "mit-runtime-rights",
            identity.get("license") == HINDSIGHT_LICENSE and identity.get("license_verified") is True,
            "exact pinned source must carry MIT license evidence",
        ),
        obs(
            "llm-free-chunk-path",
            config.get("llm_provider") == "none"
            and config.get("retain_extraction_mode") == "chunks"
            and config.get("external_llm_api_key_present") is False,
            "qualification must execute chunks mode without an external LLM credential",
        ),
        obs(
            "initial-document-readback",
            initial.get("document_count") == 1
            and initial.get("document_text_matches") is True
            and initial.get("recall_contains_initial") is True,
            "retained document must be readable and recall-visible",
        ),
        obs(
            "stable-key-repeat-idempotency",
            repeat.get("document_count") == 1
            and repeat.get("document_text_matches") is True,
            "repeating the same durable document key must not create a second current document",
        ),
        obs(
            "stable-key-replacement-currentness",
            replacement.get("document_count") == 1
            and replacement.get("document_text_matches_replacement") is True
            and replacement.get("recall_contains_replacement") is True
            and replacement.get("recall_contains_initial") is False,
            "replacement must make the new document current without old-content recall residue",
        ),
        obs(
            "restart-reconstruction",
            restart.get("daemon_restart_succeeded") is True
            and restart.get("document_count") == 1
            and restart.get("document_text_matches_replacement") is True
            and restart.get("recall_contains_replacement") is True,
            "document state and recall visibility must survive daemon restart",
        ),
        obs(
            "durable-key-after-restart",
            durable_repeat.get("document_count") == 1
            and durable_repeat.get("document_text_matches_replacement") is True,
            "the stable document key must remain singular after restart and retry",
        ),
        obs(
            "delete-readback-and-recall-residue",
            deletion.get("delete_succeeded") is True
            and deletion.get("get_after_delete_failed") is True
            and deletion.get("document_count") == 0
            and deletion.get("recall_contains_initial") is False
            and deletion.get("recall_contains_replacement") is False,
            "document deletion must remove current readback and both old/new recall residue",
        ),
        obs(
            "provider-identity-is-not-agent-memory-identity",
            raw.get("identity_boundary_preserved") is True,
            "provider bank/document IDs remain evidence refs rather than Agent Memory logical IDs",
        ),
    ]


def _limitations(raw: dict[str, Any], observations: list[HindsightObservation]) -> list[str]:
    limitations = [
        "Qualification is exact to Hindsight v0.9.0 and source commit b12646f49ec512136b9f709e608524ffed969668.",
        "Only chunk-backed resource_artifact_memory is qualified; richer LLM-backed Hindsight modes are outside this evidence boundary.",
        "Write atomicity and concurrent mutation ordering remain unqualified and are declared none.",
        "Provider-native recall ranking remains candidate/relevance evidence and carries no Agent Memory authority.",
        "The v0.9 prose documentation omitted chunks although the exact v0.9.0 source allowed it; source truth controls this fixture and the discrepancy is retained as provenance.",
    ]
    failed = [item.check_id for item in observations if not item.passed]
    if failed:
        limitations.append("Provider did not satisfy the candidate v3 contract: " + ", ".join(failed))
    provider_notes = raw.get("provider_notes", [])
    for note in provider_notes:
        if isinstance(note, str) and note:
            limitations.append(note)
    return limitations


def _sha256_json(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()
