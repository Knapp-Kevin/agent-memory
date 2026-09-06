from __future__ import annotations

from dataclasses import replace
import json
import unittest
from pathlib import Path

import jsonschema

from agentmem_ref.resource_exchange import (
    LogicalResourceSnapshot,
    ProviderResourceBinding,
    ResourceExchangeError,
    prove_resource_exchange,
)
from agentmem_ref.resource_provider_substitution import (
    load_component,
    load_qualification_snapshot,
    qualification_with_use_posture,
)

ROOT = Path(__file__).resolve().parents[2]
HINDSIGHT_COMPONENT = ROOT / "reference/fixtures/component-capabilities/hindsight-v0.9.0.json"
MEMOS_COMPONENT = ROOT / "reference/fixtures/component-capabilities/memos-local-plugin-v2.0.17.json"
HINDSIGHT_QUALIFICATION = ROOT / "reference/fixtures/component-qualification/hindsight-v0.9.0-resource-artifact-qualified-v12.json"
MEMOS_QUALIFICATION = ROOT / "reference/fixtures/component-qualification/memos-local-plugin-v2.0.17-resource-artifact-qualified-v12.json"
EXCHANGE_SCHEMA = ROOT / "schemas/resource-exchange-receipt.schema.json"
CROSSING_SCHEMA = ROOT / "schemas/boundary-crossing-receipt.schema.json"

LOGICAL_ID = "agent-memory:resource:exchange-fixture-001"
CONTENT = "Federated resource exchange preserves exact bytes across qualified substrates."
DOMAIN = "memory-domain:project:exchange-fixture"
PROVENANCE = (
    "source:fixture:federated-resource-exchange-v1",
    "issue:https://github.com/MythologIQ-Labs-LLC/agent-memory/issues/358",
)


class ResourceExchangeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.hindsight_component = load_component(HINDSIGHT_COMPONENT)
        self.memos_component = load_component(MEMOS_COMPONENT)
        self.hindsight_qualification = load_qualification_snapshot(HINDSIGHT_QUALIFICATION)
        self.memos_qualification = load_qualification_snapshot(MEMOS_QUALIFICATION)
        self.snapshot = LogicalResourceSnapshot(
            logical_resource_id=LOGICAL_ID,
            representation_kind="text/plain; charset=utf-8",
            content=CONTENT,
            source_domain_refs=(DOMAIN,),
            provenance_refs=PROVENANCE,
        )
        self.hindsight_binding = ProviderResourceBinding(
            component_id=self.hindsight_component.component_id,
            component_version=self.hindsight_component.component_version,
            native_resource_id="hindsight-document:exchange-source",
            runtime_ref="hindsight-embed:0.9.0:pg0",
        )
        self.memos_binding = ProviderResourceBinding(
            component_id=self.memos_component.component_id,
            component_version=self.memos_component.component_version,
            native_resource_id="memos-trace:exchange-target",
            runtime_ref="memos-local-plugin:2.0.17:sqlite",
        )

    def test_hindsight_to_memos_same_domain_exchange_is_schema_valid(self) -> None:
        receipt = prove_resource_exchange(
            snapshot=self.snapshot,
            source_component=self.hindsight_component,
            source_qualification=self.hindsight_qualification,
            source_binding=self.hindsight_binding,
            target_component=self.memos_component,
            target_qualification=self.memos_qualification,
            target_binding=self.memos_binding,
            target_readback=CONTENT,
            destination_domain_refs=(DOMAIN,),
            source_retained=True,
        )
        value = receipt.to_dict()
        schema = json.loads(EXCHANGE_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(value)
        self.assertEqual(LOGICAL_ID, value["logical_resource_id"])
        self.assertEqual(self.snapshot.content_digest, value["content_digest"])
        self.assertEqual(value["content_digest"], value["target_readback_digest"])
        self.assertEqual(list(PROVENANCE), value["provenance_refs"])
        self.assertTrue(value["source_retained"])
        self.assertFalse(value["destructive_cutover"])
        self.assertEqual("none", value["authority_effect"])
        self.assertIsNone(value["crossing_receipt_ref"])

    def test_memos_to_hindsight_proves_direction_is_not_canonicalized(self) -> None:
        receipt = prove_resource_exchange(
            snapshot=self.snapshot,
            source_component=self.memos_component,
            source_qualification=self.memos_qualification,
            source_binding=self.memos_binding,
            target_component=self.hindsight_component,
            target_qualification=self.hindsight_qualification,
            target_binding=self.hindsight_binding,
            target_readback=CONTENT,
            destination_domain_refs=(DOMAIN,),
            source_retained=True,
        )
        value = receipt.to_dict()
        self.assertEqual("memos-local-plugin-v2.0.17", value["source_provider"]["component_id"])
        self.assertEqual("hindsight-v0.9.0", value["target_provider"]["component_id"])
        self.assertEqual("none", value["authority_effect"])

    def test_target_content_mismatch_fails_closed(self) -> None:
        with self.assertRaisesRegex(ResourceExchangeError, "direct readback differs"):
            self._hindsight_to_memos(target_readback=CONTENT + " drift")

    def test_provider_native_id_cannot_replace_logical_identity(self) -> None:
        bad_snapshot = LogicalResourceSnapshot(
            logical_resource_id=self.memos_binding.native_resource_id,
            representation_kind=self.snapshot.representation_kind,
            content=CONTENT,
            source_domain_refs=(DOMAIN,),
            provenance_refs=PROVENANCE,
        )
        with self.assertRaisesRegex(ResourceExchangeError, "provider-native identity"):
            prove_resource_exchange(
                snapshot=bad_snapshot,
                source_component=self.hindsight_component,
                source_qualification=self.hindsight_qualification,
                source_binding=self.hindsight_binding,
                target_component=self.memos_component,
                target_qualification=self.memos_qualification,
                target_binding=self.memos_binding,
                target_readback=CONTENT,
                destination_domain_refs=(DOMAIN,),
                source_retained=True,
            )

    def test_missing_provenance_is_rejected_before_exchange(self) -> None:
        with self.assertRaisesRegex(ResourceExchangeError, "provenance_refs"):
            LogicalResourceSnapshot(
                logical_resource_id=LOGICAL_ID,
                representation_kind="text/plain",
                content=CONTENT,
                source_domain_refs=(DOMAIN,),
                provenance_refs=(),
            )

    def test_comparator_only_target_qualification_cannot_receive_runtime_copy(self) -> None:
        with self.assertRaises(Exception):
            prove_resource_exchange(
                snapshot=self.snapshot,
                source_component=self.hindsight_component,
                source_qualification=self.hindsight_qualification,
                source_binding=self.hindsight_binding,
                target_component=self.memos_component,
                target_qualification=qualification_with_use_posture(
                    self.memos_qualification, "comparator_only"
                ),
                target_binding=self.memos_binding,
                target_readback=CONTENT,
                destination_domain_refs=(DOMAIN,),
                source_retained=True,
            )

    def test_provider_version_drift_invalidates_binding_or_qualification(self) -> None:
        drifted = replace(self.memos_component, component_version="2.0.18")
        with self.assertRaises(Exception):
            prove_resource_exchange(
                snapshot=self.snapshot,
                source_component=self.hindsight_component,
                source_qualification=self.hindsight_qualification,
                source_binding=self.hindsight_binding,
                target_component=drifted,
                target_qualification=self.memos_qualification,
                target_binding=self.memos_binding,
                target_readback=CONTENT,
                destination_domain_refs=(DOMAIN,),
                source_retained=True,
            )

    def test_exchange_cannot_claim_source_deletion_or_cutover(self) -> None:
        with self.assertRaisesRegex(ResourceExchangeError, "deleting the source"):
            self._hindsight_to_memos(source_retained=False)
        with self.assertRaisesRegex(ResourceExchangeError, "destructive cutover"):
            self._hindsight_to_memos(destructive_cutover=True)

    def test_cross_domain_exchange_requires_existing_committed_crossing_receipt(self) -> None:
        with self.assertRaisesRegex(ResourceExchangeError, "boundary-crossing receipt"):
            self._hindsight_to_memos(destination_domain_refs=("memory-domain:other",))

    def test_valid_cross_domain_receipt_is_composed_not_redefined(self) -> None:
        destination = "memory-domain:shared:exchange-fixture"
        crossing = self._crossing_receipt(destination)
        schema = json.loads(CROSSING_SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator(schema).validate(crossing)
        receipt = self._hindsight_to_memos(
            destination_domain_refs=(destination,),
            crossing_receipt=crossing,
            crossing_receipt_ref="boundary-crossing:fixture-001",
        )
        self.assertEqual("boundary-crossing:fixture-001", receipt.crossing_receipt_ref)
        self.assertEqual((DOMAIN,), receipt.source_domain_refs)
        self.assertEqual((destination,), receipt.destination_domain_refs)
        self.assertEqual("none", receipt.authority_effect)

    def test_crossing_receipt_domain_or_content_drift_is_rejected(self) -> None:
        destination = "memory-domain:shared:exchange-fixture"
        crossing = self._crossing_receipt(destination)
        crossing["destination_domain_refs"] = ["memory-domain:wrong"]
        with self.assertRaisesRegex(ResourceExchangeError, "destination domains"):
            self._hindsight_to_memos(
                destination_domain_refs=(destination,),
                crossing_receipt=crossing,
                crossing_receipt_ref="boundary-crossing:fixture-001",
            )

        crossing = self._crossing_receipt(destination)
        crossing["representation"]["content_ref"] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ResourceExchangeError, "content reference"):
            self._hindsight_to_memos(
                destination_domain_refs=(destination,),
                crossing_receipt=crossing,
                crossing_receipt_ref="boundary-crossing:fixture-001",
            )

    def _hindsight_to_memos(self, **overrides):
        args = dict(
            snapshot=self.snapshot,
            source_component=self.hindsight_component,
            source_qualification=self.hindsight_qualification,
            source_binding=self.hindsight_binding,
            target_component=self.memos_component,
            target_qualification=self.memos_qualification,
            target_binding=self.memos_binding,
            target_readback=CONTENT,
            destination_domain_refs=(DOMAIN,),
            source_retained=True,
            crossing_receipt=None,
            crossing_receipt_ref="",
            destructive_cutover=False,
        )
        args.update(overrides)
        return prove_resource_exchange(**args)

    def _crossing_receipt(self, destination: str) -> dict:
        return {
            "schema_version": "1.0.0",
            "receipt_id": "boundary-crossing:fixture-001",
            "operation": "copy",
            "source_domain_refs": [DOMAIN],
            "destination_domain_refs": [destination],
            "actor": "agent:test",
            "principal": "principal:test",
            "purpose": "federated-resource-exchange-test",
            "representation": {
                "kind": self.snapshot.representation_kind,
                "content_ref": self.snapshot.content_digest,
                "privacy_minimized": False,
            },
            "source_refs": [LOGICAL_ID],
            "requested_consequence": "copy resource without source deletion",
            "pama_disposition": "allow",
            "authority_refs": ["authority:test-boundary-crossing"],
            "policy_refs": ["policy:test-boundary-crossing"],
            "policy_version": "test-v1",
            "provenance_refs": list(PROVENANCE),
            "outcome": "committed",
            "before_scope_refs": [DOMAIN],
            "after_scope_refs": [destination],
            "timestamp": "2026-08-31T00:00:00Z",
        }


if __name__ == "__main__":
    unittest.main()
