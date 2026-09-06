#!/usr/bin/env python3
"""Normalize exact-provider copy evidence into federated resource receipts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from agentmem_ref.resource_exchange import (
    LogicalResourceSnapshot,
    ProviderResourceBinding,
    ResourceExchangeError,
    prove_resource_exchange,
)
from agentmem_ref.resource_provider_substitution import load_component, load_qualification_snapshot

HINDSIGHT_COMPONENT_ID = "hindsight-v0.9.0"
HINDSIGHT_VERSION = "0.9.0"
MEMOS_COMPONENT_ID = "memos-local-plugin-v2.0.17"
MEMOS_VERSION = "2.0.17"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-evidence", type=Path, required=True)
    parser.add_argument("--hindsight-component", type=Path, required=True)
    parser.add_argument("--hindsight-qualification", type=Path, required=True)
    parser.add_argument("--memos-component", type=Path, required=True)
    parser.add_argument("--memos-qualification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    raw = json.loads(args.raw_evidence.read_text(encoding="utf-8"))
    if raw.get("execution_error"):
        raise ResourceExchangeError(f"provider fixture failed: {raw['execution_error']}")
    if raw.get("authority_effect") != "none":
        raise ResourceExchangeError("provider fixture cannot grant authority")

    identity = _mapping(raw.get("identity"), "identity")
    hindsight_identity = _mapping(identity.get("hindsight"), "identity.hindsight")
    memos_identity = _mapping(identity.get("memos"), "identity.memos")
    if hindsight_identity.get("component_id") != HINDSIGHT_COMPONENT_ID or hindsight_identity.get("version") != HINDSIGHT_VERSION:
        raise ResourceExchangeError("raw Hindsight provider identity drifted")
    if memos_identity.get("component_id") != MEMOS_COMPONENT_ID or memos_identity.get("version") != MEMOS_VERSION:
        raise ResourceExchangeError("raw MemOS provider identity drifted")

    boundary = _mapping(raw.get("exchange_boundary"), "exchange_boundary")
    if boundary.get("cross_domain_authority_exercised") is not False:
        raise ResourceExchangeError("bounded runtime fixture must not synthesize cross-domain authority")
    if boundary.get("destructive_cutover_exercised") is not False:
        raise ResourceExchangeError("bounded runtime fixture cannot exercise destructive cutover")

    hindsight_component = load_component(args.hindsight_component)
    memos_component = load_component(args.memos_component)
    hindsight_qualification = load_qualification_snapshot(args.hindsight_qualification)
    memos_qualification = load_qualification_snapshot(args.memos_qualification)

    h2m = _direction(_mapping(raw.get("hindsight_to_memos"), "hindsight_to_memos"))
    m2h = _direction(_mapping(raw.get("memos_to_hindsight"), "memos_to_hindsight"))

    if h2m["source"].component_id != HINDSIGHT_COMPONENT_ID or h2m["target"].component_id != MEMOS_COMPONENT_ID:
        raise ResourceExchangeError("Hindsight-to-MemOS fixture provider direction drifted")
    if m2h["source"].component_id != MEMOS_COMPONENT_ID or m2h["target"].component_id != HINDSIGHT_COMPONENT_ID:
        raise ResourceExchangeError("MemOS-to-Hindsight fixture provider direction drifted")

    h2m_receipt = prove_resource_exchange(
        snapshot=h2m["snapshot"],
        source_component=hindsight_component,
        source_qualification=hindsight_qualification,
        source_binding=h2m["source"],
        target_component=memos_component,
        target_qualification=memos_qualification,
        target_binding=h2m["target"],
        target_readback=h2m["target_readback"],
        destination_domain_refs=h2m["destination_domain_refs"],
        source_retained=h2m["source_retained"],
    )
    m2h_receipt = prove_resource_exchange(
        snapshot=m2h["snapshot"],
        source_component=memos_component,
        source_qualification=memos_qualification,
        source_binding=m2h["source"],
        target_component=hindsight_component,
        target_qualification=hindsight_qualification,
        target_binding=m2h["target"],
        target_readback=m2h["target_readback"],
        destination_domain_refs=m2h["destination_domain_refs"],
        source_retained=m2h["source_retained"],
    )

    output = {
        "schema_version": "1.0.0",
        "capability": "federated_memory_exchange",
        "eligible": True,
        "directions": {
            "hindsight_to_memos": h2m_receipt.to_dict(),
            "memos_to_hindsight": m2h_receipt.to_dict(),
        },
        "invariants": {
            "bidirectional": True,
            "logical_identity_provider_independent": True,
            "exact_target_readback": True,
            "source_retained": True,
            "source_scope_provenance_preserved": True,
            "destructive_cutover": False,
            "cross_domain_authority_exercised": False,
            "authority_effect": "none",
        },
        "authority_effect": "none",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def _direction(value: Mapping[str, object]) -> dict[str, Any]:
    content = _string(value, "content")
    snapshot = LogicalResourceSnapshot(
        logical_resource_id=_string(value, "logical_resource_id"),
        representation_kind=_string(value, "representation_kind"),
        content=content,
        source_domain_refs=_strings(value.get("source_domain_refs"), "source_domain_refs"),
        provenance_refs=_strings(value.get("provenance_refs"), "provenance_refs"),
    )
    destination = _strings(value.get("destination_domain_refs"), "destination_domain_refs")
    source_raw = _mapping(value.get("source"), "source")
    target_raw = _mapping(value.get("target"), "target")
    source = _binding(source_raw)
    target = _binding(target_raw)
    source_before = source_raw.get("readback_before")
    source_after = source_raw.get("readback_after_target")
    target_readback = target_raw.get("readback")
    if source_before != content:
        raise ResourceExchangeError("source direct readback before copy differs from logical snapshot")
    if source_after != content:
        raise ResourceExchangeError("source direct readback after copy does not prove source retention")
    if target_readback != content:
        raise ResourceExchangeError("target direct readback differs from logical snapshot")
    if value.get("source_retained") is not True:
        raise ResourceExchangeError("provider fixture did not prove source retention")
    if value.get("target_readback_matches") is not True:
        raise ResourceExchangeError("provider fixture did not prove exact target readback")
    return {
        "snapshot": snapshot,
        "source": source,
        "target": target,
        "target_readback": str(target_readback),
        "destination_domain_refs": destination,
        "source_retained": True,
    }


def _binding(value: Mapping[str, object]) -> ProviderResourceBinding:
    return ProviderResourceBinding(
        component_id=_string(value, "component_id"),
        component_version=_string(value, "component_version"),
        native_resource_id=_string(value, "native_resource_id"),
        runtime_ref=str(value.get("runtime_ref") or ""),
    )


def _mapping(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ResourceExchangeError(f"{name} must be an object")
    return value


def _string(value: Mapping[str, object], key: str) -> str:
    raw = value.get(key)
    if not isinstance(raw, str) or not raw:
        raise ResourceExchangeError(f"{key} must be a non-empty string")
    return raw


def _strings(value: object, name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not value:
        raise ResourceExchangeError(f"{name} must be a non-empty array")
    if any(not isinstance(item, str) or not item for item in value):
        raise ResourceExchangeError(f"{name} values must be non-empty strings")
    return tuple(value)


if __name__ == "__main__":
    sys.exit(main())
