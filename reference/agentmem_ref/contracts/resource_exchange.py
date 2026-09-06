"""Provider-neutral evidence for bounded resource exchange across qualified stores.

The exchange layer does not define a second memory lifecycle and does not grant
copy, export, deletion, recall-admission, or mutation authority. It binds one
logical Agent Memory resource to exact provider-native representations and
proves target readback equality after both providers independently satisfy the
same Capability Contract v3 requirement.

Isolation-domain crossing authority remains owned by ADR-022 and the canonical
boundary-crossing receipt. This module only verifies that a supplied committed
crossing receipt matches the exchange it is being used to justify.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence

from .capabilities import ComponentDeclaration
from .qualification import QualificationError, QualificationRecord
from .resource_provider_substitution import prove_resource_artifact_substitution

RESOURCE_EXCHANGE_SCHEMA_VERSION = "1.0.0"
EXCHANGE_OUTCOME = "copied_verified"


class ResourceExchangeError(ValueError):
    """Federated resource exchange evidence is invalid or insufficient."""


@dataclass(frozen=True)
class ProviderResourceBinding:
    component_id: str
    component_version: str
    native_resource_id: str
    runtime_ref: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("component_id", self.component_id),
            ("component_version", self.component_version),
            ("native_resource_id", self.native_resource_id),
        ):
            if not value:
                raise ResourceExchangeError(f"provider binding {name} is required")

    def to_dict(self) -> dict[str, str]:
        value = {
            "component_id": self.component_id,
            "component_version": self.component_version,
            "native_resource_id": self.native_resource_id,
        }
        if self.runtime_ref:
            value["runtime_ref"] = self.runtime_ref
        return value


@dataclass(frozen=True)
class LogicalResourceSnapshot:
    """Exact logical payload crossing provider boundaries.

    The logical ID is Agent Memory identity. Provider-native IDs belong only in
    ProviderResourceBinding and must never replace this identity.
    """

    logical_resource_id: str
    representation_kind: str
    content: str
    source_domain_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.logical_resource_id:
            raise ResourceExchangeError("logical_resource_id is required")
        if not self.representation_kind:
            raise ResourceExchangeError("representation_kind is required")
        if not self.content:
            raise ResourceExchangeError("resource content is required")
        _nonempty_unique(self.source_domain_refs, "source_domain_refs")
        _nonempty_unique(self.provenance_refs, "provenance_refs")

    @property
    def content_digest(self) -> str:
        return _sha256_text(self.content)

    @property
    def snapshot_digest(self) -> str:
        return _sha256_json(self.to_dict())

    def to_dict(self) -> dict[str, object]:
        return {
            "logical_resource_id": self.logical_resource_id,
            "representation_kind": self.representation_kind,
            "content": self.content,
            "content_digest": self.content_digest,
            "source_domain_refs": list(self.source_domain_refs),
            "provenance_refs": list(self.provenance_refs),
        }


@dataclass(frozen=True)
class ResourceExchangeReceipt:
    exchange_id: str
    snapshot_digest: str
    logical_resource_id: str
    representation_kind: str
    content_digest: str
    source_domain_refs: tuple[str, ...]
    destination_domain_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    source_provider: ProviderResourceBinding
    target_provider: ProviderResourceBinding
    source_qualification_digest: str
    target_qualification_digest: str
    requirement_digest: str
    target_readback_digest: str
    source_retained: bool
    destructive_cutover: bool
    crossing_receipt_ref: str = ""
    outcome: str = EXCHANGE_OUTCOME

    @property
    def authority_effect(self) -> str:
        return "none"

    def __post_init__(self) -> None:
        for name, value in (
            ("exchange_id", self.exchange_id),
            ("snapshot_digest", self.snapshot_digest),
            ("logical_resource_id", self.logical_resource_id),
            ("representation_kind", self.representation_kind),
            ("content_digest", self.content_digest),
            ("source_qualification_digest", self.source_qualification_digest),
            ("target_qualification_digest", self.target_qualification_digest),
            ("requirement_digest", self.requirement_digest),
            ("target_readback_digest", self.target_readback_digest),
        ):
            if not value:
                raise ResourceExchangeError(f"exchange receipt {name} is required")
        _nonempty_unique(self.source_domain_refs, "source_domain_refs")
        _nonempty_unique(self.destination_domain_refs, "destination_domain_refs")
        _nonempty_unique(self.provenance_refs, "provenance_refs")
        if not self.source_retained:
            raise ResourceExchangeError("bounded resource exchange requires source_retained=true")
        if self.destructive_cutover:
            raise ResourceExchangeError("bounded resource exchange cannot claim destructive cutover authority")
        if self.outcome != EXCHANGE_OUTCOME:
            raise ResourceExchangeError(f"unsupported exchange outcome: {self.outcome}")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": RESOURCE_EXCHANGE_SCHEMA_VERSION,
            "exchange_id": self.exchange_id,
            "snapshot_digest": self.snapshot_digest,
            "logical_resource_id": self.logical_resource_id,
            "representation_kind": self.representation_kind,
            "content_digest": self.content_digest,
            "source_domain_refs": list(self.source_domain_refs),
            "destination_domain_refs": list(self.destination_domain_refs),
            "provenance_refs": list(self.provenance_refs),
            "source_provider": self.source_provider.to_dict(),
            "target_provider": self.target_provider.to_dict(),
            "source_qualification_digest": self.source_qualification_digest,
            "target_qualification_digest": self.target_qualification_digest,
            "requirement_digest": self.requirement_digest,
            "target_readback_digest": self.target_readback_digest,
            "source_retained": self.source_retained,
            "destructive_cutover": self.destructive_cutover,
            "crossing_receipt_ref": self.crossing_receipt_ref or None,
            "outcome": self.outcome,
            "authority_effect": "none",
        }


def prove_resource_exchange(
    *,
    snapshot: LogicalResourceSnapshot,
    source_component: ComponentDeclaration,
    source_qualification: QualificationRecord,
    source_binding: ProviderResourceBinding,
    target_component: ComponentDeclaration,
    target_qualification: QualificationRecord,
    target_binding: ProviderResourceBinding,
    target_readback: str,
    destination_domain_refs: Sequence[str],
    source_retained: bool,
    crossing_receipt: Mapping[str, object] | None = None,
    crossing_receipt_ref: str = "",
    destructive_cutover: bool = False,
) -> ResourceExchangeReceipt:
    """Prove one copy between qualified resource-memory providers.

    This validates provider eligibility with the existing real-substitution
    gate, then binds exact source and target bytes. Same-domain copies need no
    authority receipt. A domain-changing copy requires an already-committed
    ADR-022 boundary-crossing receipt whose source/destination domains match.
    """

    _assert_binding_matches_component(source_binding, source_component, "source")
    _assert_binding_matches_component(target_binding, target_component, "target")
    if source_binding.component_id == target_binding.component_id:
        raise ResourceExchangeError("federated exchange requires distinct provider components")
    if snapshot.logical_resource_id in {
        source_binding.native_resource_id,
        target_binding.native_resource_id,
    }:
        raise ResourceExchangeError(
            "provider-native identity must remain distinct from Agent Memory logical identity"
        )

    substitution = prove_resource_artifact_substitution(
        primary_component=source_component,
        primary_qualification=source_qualification,
        replacement_component=target_component,
        replacement_qualification=target_qualification,
    )["substitution"]
    if not isinstance(substitution, Mapping):
        raise ResourceExchangeError("provider substitution did not emit evidence")

    destination_domains = tuple(destination_domain_refs)
    _nonempty_unique(destination_domains, "destination_domain_refs")
    if target_readback != snapshot.content:
        raise ResourceExchangeError("target direct readback differs from source logical resource content")
    target_digest = _sha256_text(target_readback)
    if target_digest != snapshot.content_digest:
        raise ResourceExchangeError("target content digest differs from source snapshot digest")
    if not source_retained:
        raise ResourceExchangeError("copy evidence cannot claim success after deleting the source")
    if destructive_cutover:
        raise ResourceExchangeError("resource exchange does not authorize destructive cutover")

    domain_changed = tuple(snapshot.source_domain_refs) != destination_domains
    if domain_changed:
        _validate_crossing_receipt(
            crossing_receipt,
            source_domain_refs=snapshot.source_domain_refs,
            destination_domain_refs=destination_domains,
            logical_resource_id=snapshot.logical_resource_id,
            representation_kind=snapshot.representation_kind,
            content_digest=snapshot.content_digest,
        )
        if not crossing_receipt_ref:
            raise ResourceExchangeError("cross-domain exchange requires a crossing_receipt_ref")
    elif crossing_receipt is not None:
        _validate_crossing_receipt(
            crossing_receipt,
            source_domain_refs=snapshot.source_domain_refs,
            destination_domain_refs=destination_domains,
            logical_resource_id=snapshot.logical_resource_id,
            representation_kind=snapshot.representation_kind,
            content_digest=snapshot.content_digest,
        )

    source_q = str(substitution.get("primary_qualification_digest", ""))
    target_q = str(substitution.get("replacement_qualification_digest", ""))
    requirement_digest = str(substitution.get("requirement_digest", ""))
    if source_q != source_qualification.applicability_digest:
        raise QualificationError("source substitution qualification digest drifted")
    if target_q != target_qualification.applicability_digest:
        raise QualificationError("target substitution qualification digest drifted")

    exchange_basis = {
        "snapshot_digest": snapshot.snapshot_digest,
        "source_provider": source_binding.to_dict(),
        "target_provider": target_binding.to_dict(),
        "source_qualification_digest": source_q,
        "target_qualification_digest": target_q,
        "requirement_digest": requirement_digest,
        "destination_domain_refs": list(destination_domains),
        "target_readback_digest": target_digest,
        "source_retained": True,
        "destructive_cutover": False,
        "crossing_receipt_ref": crossing_receipt_ref,
    }
    return ResourceExchangeReceipt(
        exchange_id="resource-exchange:" + _sha256_json(exchange_basis).removeprefix("sha256:"),
        snapshot_digest=snapshot.snapshot_digest,
        logical_resource_id=snapshot.logical_resource_id,
        representation_kind=snapshot.representation_kind,
        content_digest=snapshot.content_digest,
        source_domain_refs=snapshot.source_domain_refs,
        destination_domain_refs=destination_domains,
        provenance_refs=snapshot.provenance_refs,
        source_provider=source_binding,
        target_provider=target_binding,
        source_qualification_digest=source_q,
        target_qualification_digest=target_q,
        requirement_digest=requirement_digest,
        target_readback_digest=target_digest,
        source_retained=True,
        destructive_cutover=False,
        crossing_receipt_ref=crossing_receipt_ref,
    )


def _validate_crossing_receipt(
    receipt: Mapping[str, object] | None,
    *,
    source_domain_refs: Sequence[str],
    destination_domain_refs: Sequence[str],
    logical_resource_id: str,
    representation_kind: str,
    content_digest: str,
) -> None:
    if receipt is None:
        raise ResourceExchangeError("cross-domain exchange requires an ADR-022 boundary-crossing receipt")
    if receipt.get("operation") not in {"copy", "export", "import"}:
        raise ResourceExchangeError("crossing receipt operation is not compatible with resource exchange")
    if receipt.get("outcome") != "committed":
        raise ResourceExchangeError("cross-domain exchange requires a committed crossing receipt")
    if receipt.get("pama_disposition") not in {"allow", "allow_with_ledger"}:
        raise ResourceExchangeError("committed crossing receipt lacks an allowing PAMA disposition")
    if tuple(receipt.get("source_domain_refs", ())) != tuple(source_domain_refs):
        raise ResourceExchangeError("crossing receipt source domains do not match resource snapshot")
    if tuple(receipt.get("destination_domain_refs", ())) != tuple(destination_domain_refs):
        raise ResourceExchangeError("crossing receipt destination domains do not match exchange target")
    source_refs = receipt.get("source_refs")
    if not isinstance(source_refs, (list, tuple)) or logical_resource_id not in source_refs:
        raise ResourceExchangeError("crossing receipt does not bind the logical resource identity")
    representation = receipt.get("representation")
    if not isinstance(representation, Mapping):
        raise ResourceExchangeError("crossing receipt representation is required")
    if representation.get("kind") != representation_kind:
        raise ResourceExchangeError("crossing receipt representation kind does not match resource")
    if representation.get("content_ref") != content_digest:
        raise ResourceExchangeError("crossing receipt content reference does not match resource digest")
    if not isinstance(receipt.get("receipt_id"), str) or not receipt.get("receipt_id"):
        raise ResourceExchangeError("crossing receipt identity is required")


def _assert_binding_matches_component(
    binding: ProviderResourceBinding,
    component: ComponentDeclaration,
    label: str,
) -> None:
    if binding.component_id != component.component_id:
        raise ResourceExchangeError(f"{label} provider binding component identity drifted")
    if binding.component_version != component.component_version:
        raise ResourceExchangeError(f"{label} provider binding component version drifted")


def _nonempty_unique(values: Sequence[str], name: str) -> None:
    if not values or any(not isinstance(item, str) or not item for item in values):
        raise ResourceExchangeError(f"{name} must contain non-empty strings")
    if len(set(values)) != len(values):
        raise ResourceExchangeError(f"{name} must be unique")


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()
