"""Optional UOR-Addr JSON content-reference profile for issue #232."""

from __future__ import annotations

import re
from typing import Callable, Mapping

from . import receipts

SCHEMA_VERSION = "0.1.0"
PROFILE_ID = "agent-memory/uor-addr-json-content-reference"
PROFILE_VERSION = "0.1.0"
UOR_REPOSITORY = "UOR-Foundation/uor-addr"
UOR_RELEASE = "v0.2.0"
UOR_TAG_OBJECT = "4bdc4ec022bbc99b3c1ec01a67b40a7e25f30de4"
UOR_SOURCE_COMMIT = "d78f82f26034880e91b1d54c21900a33ab73f695"
UOR_LICENSE = "Apache-2.0"
UOR_REALIZATION = "json:rfc8259+rfc8785-jcs+uax15-nfc+sha256"
AUTHORITY_EFFECT = "none"
_LABEL_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUIRED_PROFILE_METADATA = {"profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION, "uor_release": UOR_RELEASE, "uor_source_commit": UOR_SOURCE_COMMIT, "realization": UOR_REALIZATION}
_ALLOWED_PROFILE_METADATA = frozenset(_REQUIRED_PROFILE_METADATA)

class UorProfileError(RuntimeError):
    pass
class UorBindingUnavailable(UorProfileError):
    pass
class UorInvalidInput(UorProfileError):
    pass
AddressFunction = Callable[[bytes], str]

def default_profile_metadata() -> dict[str, str]:
    return dict(_REQUIRED_PROFILE_METADATA)

def _non_authority_fields() -> dict:
    return {"authority_effect": AUTHORITY_EFFECT, "can_create_logical_memory_identity": False, "can_create_lifecycle_currentness": False, "can_admit_recall": False, "can_certify_evidence_strength": False, "can_cross_isolation_boundary": False, "can_satisfy_pama_mutation_authority": False, "can_grant_deletion_or_export_authority": False}

def validate_label(label: str) -> str:
    if not isinstance(label, str) or not _LABEL_RE.fullmatch(label):
        raise ValueError("UOR label must be lowercase sha256:<64hex>")
    return label

def validate_profile_metadata(metadata: Mapping[str, str] | None) -> dict[str, str]:
    material = default_profile_metadata() if metadata is None else dict(metadata)
    unknown = sorted(set(material) - _ALLOWED_PROFILE_METADATA)
    if unknown:
        raise ValueError(f"unsupported UOR profile metadata fields: {unknown}")
    missing = sorted(_ALLOWED_PROFILE_METADATA - set(material))
    if missing:
        raise ValueError(f"missing UOR profile metadata fields: {missing}")
    for key, expected in _REQUIRED_PROFILE_METADATA.items():
        if material[key] != expected:
            raise ValueError(f"unsupported UOR profile metadata {key}={material[key]!r}; expected {expected!r}")
    return material

def evaluate_json_content_reference(content: bytes, *, address_fn: AddressFunction, binding_name: str, binding_version: str, claimed_label: str | None = None, profile_metadata: Mapping[str, str] | None = None) -> dict:
    base = {"schema_version": SCHEMA_VERSION, "profile_id": PROFILE_ID, "profile_version": PROFILE_VERSION, "optional_profile": True, "ordinary_agent_memory_requires_uor_runtime": False, "uor": {"repository": UOR_REPOSITORY, "release": UOR_RELEASE, "tag_object": UOR_TAG_OBJECT, "source_commit": UOR_SOURCE_COMMIT, "license": UOR_LICENSE, "realization": UOR_REALIZATION}, "binding": {"name": binding_name, "version": binding_version}, **_non_authority_fields()}
    if not isinstance(content, (bytes, bytearray, memoryview)):
        evidence = {**base, "status": "invalid_input", "failure": {"kind": "invalid_typed_input", "message": "content must be bytes-like JSON input", "fail_open": False}}
        receipts.validate("uor-content-reference.schema.json", evidence)
        return evidence
    try:
        metadata = validate_profile_metadata(profile_metadata)
    except ValueError as exc:
        evidence = {**base, "status": "unsupported", "failure": {"kind": "unsupported_profile_metadata", "message": str(exc), "fail_open": False}}
        receipts.validate("uor-content-reference.schema.json", evidence)
        return evidence
    if claimed_label is not None:
        try:
            validate_label(claimed_label)
        except ValueError as exc:
            evidence = {**base, "profile_metadata": metadata, "status": "invalid_label", "claimed_label": claimed_label, "failure": {"kind": "malformed_address_label", "message": str(exc), "fail_open": False}}
            receipts.validate("uor-content-reference.schema.json", evidence)
            return evidence
    try:
        generated_label = validate_label(address_fn(bytes(content)))
    except UorBindingUnavailable as exc:
        evidence = {**base, "profile_metadata": metadata, "status": "unavailable", "failure": {"kind": "external_binding_unavailable", "message": str(exc), "fail_open": False}}
        receipts.validate("uor-content-reference.schema.json", evidence)
        return evidence
    except UorInvalidInput as exc:
        evidence = {**base, "profile_metadata": metadata, "status": "invalid_input", "failure": {"kind": "canonicalization_or_typed_input_error", "message": str(exc), "fail_open": False}}
        receipts.validate("uor-content-reference.schema.json", evidence)
        return evidence
    status = "generated" if claimed_label is None else ("verified" if generated_label == claimed_label else "mismatch")
    evidence = {**base, "profile_metadata": metadata, "status": status, "generated_label": generated_label, "content_identity_only": True}
    if claimed_label is not None:
        evidence["claimed_label"] = claimed_label
        evidence["matches_claimed_label"] = generated_label == claimed_label
    if status == "mismatch":
        evidence["failure"] = {"kind": "content_address_mismatch", "message": "generated UOR content address does not match claimed label", "fail_open": False}
    receipts.validate("uor-content-reference.schema.json", evidence)
    return evidence
