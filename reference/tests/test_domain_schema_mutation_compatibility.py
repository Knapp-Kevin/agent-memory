"""PAMA 1.2 serialization and compatibility cases."""

import unittest

from agentmem_ref import domain_schema_mutation as dsm
from agentmem_ref import policy, receipts


def proposal(operation=dsm.DOMAIN_SCHEMA_MUTATION, risk="high", scope_change=""):
    return policy.Proposal(
        proposal_id=f"proposal:{operation}:{risk}", actor_id="agent:schema", charter_version="charter:1",
        target_reference="domain-model:project-a", target_class=policy.M3, scope="tenant-a/project-a",
        operation=operation, current_strength="promoted", proposed_strength="canonical",
        downstream_authority=policy.A3, reversibility="versioned_revocable", risk_class=risk,
        evidence_refs=("evidence:schema",), state_snapshot="snapshot:model:v4", tenant_ref="tenant-a",
        purpose="ontology evolution", isolation_domain_refs=("tenant-a/project-a",),
        required_isolation_domain_refs=("tenant-a/project-a",), project_ref="project-a",
        requested_scope_change=scope_change,
    )


def selected(decision, operation):
    if decision.outcome == policy.REQUIRE_REVIEW:
        return "enter_pending_verification"
    if decision.outcome == policy.REQUIRE_EXTERNAL_VERIFICATION:
        return "request_external_verification"
    if decision.outcome == policy.BLOCK:
        return receipts.NO_ACTION
    return operation


class DomainSchemaMutationCompatibilityTests(unittest.TestCase):
    def test_historical_1_0_and_1_1_decisions_remain_valid(self):
        for operation, risk, expected_version in (
            ("promotion", "medium", "1.0.0"),
            ("decision_overwrite", "high", "1.1.0"),
        ):
            with self.subTest(operation=operation):
                item = proposal(operation=operation, risk=risk)
                decision = policy.evaluate(item)
                document = receipts.build_pama_decision(
                    item, decision, selected_action=selected(decision, item.operation),
                    selection_mode="deterministic", receipt_ref=f"receipt:{operation}",
                )
                self.assertEqual(document["schema_version"], expected_version)
                receipts.validate("pama-decision.schema.json", document)

    def test_1_2_document_validates_and_binds_scope_change(self):
        item = proposal(scope_change="project-local -> tenant-shared")
        decision = dsm.evaluate(item, requested_scope_change=item.requested_scope_change)
        document = dsm.build_pama_decision(
            item, decision, selected_action=selected(decision, item.operation),
            selection_mode="deterministic", receipt_ref="receipt:schema:1",
            requested_scope_change=item.requested_scope_change,
        )
        self.assertEqual(document["schema_version"], "1.2.0")
        self.assertEqual(document["mutation"]["operation"], dsm.DOMAIN_SCHEMA_MUTATION)
        self.assertEqual(document["mutation"]["requested_scope_change"], item.requested_scope_change)
        receipts.validate("pama-decision.schema.json", document)

    def test_domain_schema_mutation_claiming_1_1_is_rejected(self):
        item = proposal()
        decision = dsm.evaluate(item)
        document = dsm.build_pama_decision(
            item, decision, selected_action=selected(decision, item.operation),
            selection_mode="deterministic", receipt_ref="receipt:schema:2",
        )
        document["schema_version"] = "1.1.0"
        with self.assertRaisesRegex(ValueError, "1.2.0"):
            receipts.validate("pama-decision.schema.json", document)

    def test_legacy_consumer_rejects_1_2_explicitly(self):
        item = proposal()
        decision = dsm.evaluate(item)
        document = dsm.build_pama_decision(
            item, decision, selected_action=selected(decision, item.operation),
            selection_mode="deterministic", receipt_ref="receipt:schema:3",
        )
        with self.assertRaisesRegex(ValueError, "unsupported PAMA schema version"):
            dsm.enforce_consumer_compatibility(document, supported_schema_versions=("1.0.0", "1.1.0"))

    def test_receipt_pair_preserves_exact_operation_and_version(self):
        item = proposal()
        decision = dsm.evaluate(item)
        chosen = selected(decision, item.operation)
        receipt = receipts.build_receipt(
            receipt_id="receipt:schema:pair", proposal=item, decision=decision, selected_action=chosen,
            selection_mode="deterministic", timestamp="2026-08-13T12:30:00Z",
            before_state="domain-model:v4", after_state="pending_verification",
        )
        pama = dsm.build_pama_decision(
            item, decision, selected_action=chosen, selection_mode="deterministic", receipt_ref=receipt["receipt_id"],
        )
        receipts.verify_receipt_decision_pair(receipt, pama)
        self.assertEqual(receipt["requested_action"], dsm.DOMAIN_SCHEMA_MUTATION)
        self.assertEqual(pama["mutation"]["operation"], dsm.DOMAIN_SCHEMA_MUTATION)
        self.assertEqual(pama["schema_version"], "1.2.0")


if __name__ == "__main__":
    unittest.main()
