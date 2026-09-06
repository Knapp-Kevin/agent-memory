"""Compose actual P4 residue outcomes into P4.5 portable lifecycle evidence."""

from __future__ import annotations

import json
import sys
import unittest

from agentmem_ref.evidence_qualification import group_by_dependence
from tests.qualified_fixtures import corpus_for, registry_for, rule


def deletion_corpus():
    """The evaluator's adjudication of permitted deletions (ADR-037 4b-2,
    entry #24). Authored ahead of any proposal."""
    return corpus_for(rule(
        rule_id="rule:approved-deletion", target=SOURCE,
        criterion="permanent-deletion", from_state="current",
        to_values=("purged",),
    ))


def deletion_evidence():
    return deletion_corpus().evidence_for(
        target_reference=SOURCE, criterion="permanent-deletion",
        pre_state="current", proposed_value="purged",
    )
from pathlib import Path

import jsonschema
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from referencing import Registry, Resource

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy, projections, receipts, residue  # noqa: E402
from agentmem_ref.adapter import Clock, GovernedMemoryAdapter  # noqa: E402
from agentmem_ref.deletion_completeness import (  # noqa: E402
    build_deletion_completeness_chain,
    measure_deletion_completeness,
)
from agentmem_ref.portable_evidence import (  # noqa: E402
    IssuerKey,
    RuntimeObservation,
    verify_evidence,
)
from agentmem_ref.projection_governance import ProjectionGovernor  # noqa: E402
from agentmem_ref.substrate import InMemoryTemporalGraph  # noqa: E402

TENANT = "tenant-a"
SOURCE = "mem:alpha"
COMMIT = "a" * 40
ISSUER = "issuer:deletion-completeness-reference"
DOMAIN_AUTH_STATE = "domain-auth:deletion:40"
KEY = IssuerKey(
    issuer_id=ISSUER,
    key_id="key-p45-lifecycle",
    private_key=Ed25519PrivateKey.from_private_bytes(bytes(range(65, 97))),
    valid_from="2026-08-01T00:00:00Z",
    valid_until="2026-08-31T23:59:59Z",
)


def proposal(**overrides) -> policy.Proposal:
    base = dict(
        proposal_id="prop-delete",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference=SOURCE,
        target_class=policy.M2,
        scope=TENANT,
        operation="permanent_deletion",
        current_strength="reinforced",
        proposed_strength="removed",
        downstream_authority=policy.A1,
        reversibility="irreversible",
        risk_class="low",
        evidence_refs=("ev:deletion-request",),
        tenant_ref=TENANT,
        approval_refs=("approval:data-protection-officer",),
        review_satisfied=True,
    )
    base.update(overrides)
    return policy.Proposal(**base)


def make_governor() -> ProjectionGovernor:
    adapter = GovernedMemoryAdapter(
        InMemoryTemporalGraph(), TENANT, Clock(),
        verifier_registry=registry_for(deletion_corpus()),
    )
    gov = ProjectionGovernor(adapter)
    adapter.commit_proposal(
        policy.Proposal(
            proposal_id="prop-seed",
            actor_id="agent:planner",
            charter_version="charter-1",
            target_reference=SOURCE,
            target_class=policy.M2,
            scope=TENANT,
            operation="promotion",
            current_strength="reinforced",
            proposed_strength="promoted",
            downstream_authority=policy.A1,
            reversibility="reversible",
            risk_class="low",
            evidence_refs=("ev:seed",),
            tenant_ref=TENANT,
        ),
        "deleted-memory-content-that-must-never-enter-portable-evidence",
    )
    gov.declare(
        "summary:one",
        (SOURCE,),
        projections.ESTIMATOR_MEDIATED,
        projections.RECOVERABLE_CONTENT,
        projections.APPROXIMABLE,
        TENANT,
    )
    gov.declare(
        "summary:two",
        ("summary:one",),
        projections.ESTIMATOR_MEDIATED,
        projections.RECOVERABLE_CONTENT,
        projections.APPROXIMABLE,
        TENANT,
    )
    return gov


def chain_for(receipt: dict, measurement, action_ref: str) -> dict:
    return build_deletion_completeness_chain(
        receipt,
        measurement,
        agent_memory_commit=COMMIT,
        issuer_id=ISSUER,
        issuer_key=KEY,
        issued_at="2026-08-11T21:30:02Z",
        action_ref=action_ref,
        policy_ref="policy:pama-2026-08",
        authority_state_ref="authority:rev-40",
        decision_time="2026-08-11T21:30:01Z",
        scope_ref="scope:opaque:deletion-completeness",
        before_state_ref="sha256:" + "5" * 64,
        source_domain_ref="domain:opaque:project-a",
        destination_domain_ref="domain:opaque:deleted",
        domain_authorization_state_ref=DOMAIN_AUTH_STATE,
    )


class DeletionCompletenessEvidenceTests(unittest.TestCase):
    def _verify_chain(self, receipt: dict, chain: dict) -> dict:
        trust = KEY.trust_key()
        return verify_evidence(
            chain["portable_evidence"],
            {(trust.issuer_id, trust.key_id): trust},
            canonical_receipt=receipt,
            runtime=RuntimeObservation(
                action_ref=chain["action_ref"],
                execution_time="2026-08-11T21:30:03Z",
                domain_authorization_state_ref=DOMAIN_AUTH_STATE,
                authority_valid_at_execution=True,
                domain_authorization_valid_at_execution=True,
            ),
        )

    def test_declared_residual_is_observed_and_portably_reported(self):
        gov = make_governor()
        result = gov.purge(
            proposal(), SOURCE, retained_by_policy={"summary:two"},
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=deletion_evidence(),
            verifier_registry=registry_for(deletion_corpus()),
        )
        self.assertTrue(result.committed)

        observed = gov.sweep(set())
        self.assertEqual(observed, ["summary:two"])
        measurement = measure_deletion_completeness(result.buckets, observed)
        self.assertTrue(measurement.hard_gate_passed)
        self.assertEqual(measurement.total_residual_count, 1)
        self.assertEqual(measurement.lifecycle_satisfaction, "residual")

        chain = chain_for(result.receipt, measurement, "action:delete:declared-residual")
        verified = self._verify_chain(result.receipt, chain)
        self.assertEqual(verified["evidence_integrity"], "valid")
        self.assertEqual(verified["runtime_execution"], "executed_as_authorized")
        self.assertEqual(verified["lifecycle_satisfaction"], "residual")
        self.assertEqual(chain["measurement"]["independently_observed_residual_count"], 1)

    def test_undeclared_residue_hard_gate_failure_is_portably_reported(self):
        gov = make_governor()
        delete = proposal(proposal_id="prop-delete-partial")
        # ADR-037 step 4b-2: expected semantic change (entry #24).
        # This test is about how an undeclared-residue gate failure is REPORTED,
        # not about how the deletion is authorised. It needs a decision that
        # permits the deletion, which now comes from qualified evidence rather
        # than from `review_satisfied=True`.
        decision = policy.evaluate_with_qualified_evidence(
            delete,
            group_by_dependence(
                deletion_evidence(),
                verifiers=registry_for(deletion_corpus()).as_mapping(),
            ),
        )
        self.assertIn("permanent_deletion", decision.permitted_actions)
        canonical_receipt = receipts.build_receipt(
            receipt_id="receipt:delete:partial",
            proposal=delete,
            decision=decision,
            selected_action="permanent_deletion",
            selection_mode="deterministic",
            timestamp="2026-08-11T21:30:01Z",
            before_state="v1",
            after_state="v1",
        )

        one_hop = residue.ResiduePlan(purged=["summary:one"])
        residue.apply_purge(gov.store, one_hop, gov._purged)
        gov._purged.add(SOURCE)
        buckets = residue.partition(gov.store, gov.view(), one_hop)
        observed = gov.sweep(set())
        self.assertEqual(buckets[residue.UNDECLARED], ["summary:two"])
        self.assertEqual(observed, ["summary:two"])

        measurement = measure_deletion_completeness(buckets, observed)
        self.assertFalse(measurement.hard_gate_passed)
        self.assertEqual(measurement.undeclared_residual_count, 1)
        self.assertEqual(measurement.lifecycle_satisfaction, "residual")

        chain = chain_for(canonical_receipt, measurement, "action:delete:undeclared-residual")
        verified = self._verify_chain(canonical_receipt, chain)
        self.assertEqual(verified["evidence_integrity"], "valid")
        self.assertEqual(verified["lifecycle_satisfaction"], "residual")
        self.assertFalse(chain["measurement"]["hard_gate_passed"])

    def test_transitive_purge_zero_residue_is_portably_satisfied(self):
        gov = make_governor()
        result = gov.purge(
            proposal(proposal_id="prop-delete-clean"), SOURCE,
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=deletion_evidence(),
            verifier_registry=registry_for(deletion_corpus()),
        )
        self.assertTrue(result.committed)
        self.assertTrue(result.hard_gate_passed)

        observed = gov.sweep(set())
        self.assertEqual(observed, [])
        measurement = measure_deletion_completeness(result.buckets, observed)
        self.assertEqual(measurement.total_residual_count, 0)
        self.assertEqual(measurement.lifecycle_satisfaction, "satisfied")

        chain = chain_for(result.receipt, measurement, "action:delete:zero-residue")
        verified = self._verify_chain(result.receipt, chain)
        self.assertEqual(verified["evidence_integrity"], "valid")
        self.assertEqual(verified["runtime_execution"], "executed_as_authorized")
        self.assertEqual(verified["lifecycle_satisfaction"], "satisfied")
        self.assertEqual(chain["measurement"]["independently_observed_residual_count"], 0)

    def test_public_chains_exclude_memory_and_projection_identifiers(self):
        gov = make_governor()
        result = gov.purge(
            proposal(), SOURCE, retained_by_policy={"summary:two"},
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=deletion_evidence(),
            verifier_registry=registry_for(deletion_corpus()),
        )
        measurement = measure_deletion_completeness(result.buckets, gov.sweep(set()))
        chain = chain_for(result.receipt, measurement, "action:delete:privacy")

        rendered = json.dumps(chain, sort_keys=True)
        self.assertNotIn("deleted-memory-content", rendered)
        self.assertNotIn("summary:one", rendered)
        self.assertNotIn("summary:two", rendered)
        self.assertNotIn(SOURCE, rendered)

    def test_chain_and_embedded_portable_evidence_validate(self):
        gov = make_governor()
        result = gov.purge(
            proposal(proposal_id="prop-delete-schema"), SOURCE,
            # ADR-037 step 4b-2: expected semantic change (entry #24).
            evidence=deletion_evidence(),
            verifier_registry=registry_for(deletion_corpus()),
        )
        measurement = measure_deletion_completeness(result.buckets, gov.sweep(set()))
        chain = chain_for(result.receipt, measurement, "action:delete:schema")

        root = Path(__file__).resolve().parents[2]
        schema_dir = root / "schemas"
        chain_schema = json.loads((schema_dir / "deletion-completeness-chain.schema.json").read_text())
        portable_schema = json.loads((schema_dir / "portable-governance-evidence.schema.json").read_text())
        registry = Registry().with_resource(
            portable_schema["$id"],
            Resource.from_contents(portable_schema),
        )
        jsonschema.Draft202012Validator(chain_schema, registry=registry).validate(chain)
        jsonschema.Draft202012Validator(portable_schema).validate(chain["portable_evidence"])

    def test_measurement_rejects_a_partition_not_supported_by_independent_sweep(self):
        buckets = {
            residue.PURGED: [],
            residue.DECLARED_CONTROLLED: ["projection:claimed"],
            residue.DECLARED_UNCONTROLLABLE: [],
            residue.UNDECLARED: [],
        }
        with self.assertRaises(ValueError):
            measure_deletion_completeness(buckets, [])


if __name__ == "__main__":
    unittest.main()
