"""Executable derived-scope and scope-promotion evidence for ADR-022."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref import policy  # noqa: E402
from agentmem_ref.scope_governance import (  # noqa: E402
    DerivedScope,
    ScopeConflict,
    SourceScope,
    derive_scope,
    evaluate_scope_promotion,
    scope_broadens,
)


def promotion_proposal(**overrides) -> policy.Proposal:
    base = dict(
        proposal_id="scope-promotion-1",
        actor_id="agent:planner",
        charter_version="charter-1",
        target_reference="mem:derived",
        target_class=policy.M4,
        scope="tenant-a",
        operation="scope_expansion",
        current_strength="reinforced",
        proposed_strength="reinforced",
        downstream_authority=policy.A2,
        reversibility="reversible",
        risk_class="medium",
        evidence_refs=("scope:source-a", "scope:source-b"),
        tenant_ref="tenant-a",
        purpose="assistance",
    )
    base.update(overrides)
    return policy.Proposal(**base)


class ScopeGovernanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.a = SourceScope(
            source_ref="mem:a",
            domain_refs=frozenset({"domain:project-a", "domain:shared-security"}),
            allowed_audiences=frozenset({"team:security", "agent:planner"}),
            allowed_purposes=frozenset({"security-review", "incident-response"}),
            restrictions=frozenset({"no-external-export"}),
        )
        self.b = SourceScope(
            source_ref="mem:b",
            domain_refs=frozenset({"domain:shared-security", "domain:project-b"}),
            allowed_audiences=frozenset({"team:security", "agent:auditor"}),
            allowed_purposes=frozenset({"security-review"}),
            restrictions=frozenset({"retain-provenance"}),
        )

    def test_multi_source_derivation_intersects_authority_and_unions_restrictions(self):
        derived = derive_scope((self.a, self.b))

        self.assertEqual(derived.domain_refs, frozenset({"domain:shared-security"}))
        self.assertEqual(derived.allowed_audiences, frozenset({"team:security"}))
        self.assertEqual(derived.allowed_purposes, frozenset({"security-review"}))
        self.assertEqual(
            derived.restrictions,
            frozenset({"no-external-export", "retain-provenance"}),
        )

    def test_incompatible_sources_fail_closed_instead_of_selecting_broadest_scope(self):
        private = SourceScope(
            source_ref="mem:private",
            domain_refs=frozenset({"domain:private"}),
            allowed_audiences=frozenset({"user:alice"}),
            allowed_purposes=frozenset({"personal"}),
        )
        public = SourceScope(
            source_ref="mem:public",
            domain_refs=frozenset({"domain:public"}),
            allowed_audiences=frozenset({"public"}),
            allowed_purposes=frozenset({"publication"}),
        )

        with self.assertRaises(ScopeConflict):
            derive_scope((private, public))

    def test_summary_does_not_erase_source_restrictions(self):
        inherited = derive_scope((self.a, self.b))
        requested = DerivedScope(
            source_refs=inherited.source_refs,
            domain_refs=inherited.domain_refs,
            allowed_audiences=inherited.allowed_audiences,
            allowed_purposes=inherited.allowed_purposes,
            restrictions=frozenset(),
        )

        self.assertTrue(scope_broadens(inherited, requested))

    def test_broadening_disguised_as_derivation_is_blocked(self):
        inherited = derive_scope((self.a, self.b))
        requested = DerivedScope(
            source_refs=inherited.source_refs,
            domain_refs=inherited.domain_refs | {"domain:public"},
            allowed_audiences=inherited.allowed_audiences | {"public"},
            allowed_purposes=inherited.allowed_purposes,
            restrictions=inherited.restrictions,
        )
        mislabeled = promotion_proposal(operation="promotion")

        decision = evaluate_scope_promotion(mislabeled, inherited, requested)

        self.assertEqual(decision.outcome, policy.BLOCK)
        self.assertIn("scope_expansion", decision.prohibited_actions)

    def test_unauthorized_scope_promotion_cannot_commit_by_default(self):
        inherited = derive_scope((self.a, self.b))
        requested = DerivedScope(
            source_refs=inherited.source_refs,
            domain_refs=inherited.domain_refs | {"domain:external"},
            allowed_audiences=inherited.allowed_audiences | {"partner:external"},
            allowed_purposes=inherited.allowed_purposes,
            restrictions=inherited.restrictions,
        )

        decision = evaluate_scope_promotion(promotion_proposal(), inherited, requested)

        self.assertEqual(decision.outcome, policy.REQUIRE_REVIEW)
        self.assertIn("scope_expansion", decision.prohibited_actions)
        self.assertNotIn("scope_expansion", decision.permitted_actions)

    def test_self_approved_scope_promotion_is_absorbing_block(self):
        inherited = derive_scope((self.a, self.b))
        requested = DerivedScope(
            source_refs=inherited.source_refs,
            domain_refs=inherited.domain_refs | {"domain:external"},
            allowed_audiences=inherited.allowed_audiences | {"partner:external"},
            allowed_purposes=inherited.allowed_purposes,
            restrictions=inherited.restrictions,
        )

        decision = evaluate_scope_promotion(
            promotion_proposal(approves_own_authority=True),
            inherited,
            requested,
        )

        self.assertEqual(decision.outcome, policy.BLOCK)
        self.assertEqual(decision.permitted_actions, ())

    def test_narrower_derived_scope_does_not_require_scope_expansion(self):
        inherited = derive_scope((self.a, self.b))
        requested = DerivedScope(
            source_refs=inherited.source_refs,
            domain_refs=inherited.domain_refs,
            allowed_audiences=inherited.allowed_audiences,
            allowed_purposes=inherited.allowed_purposes,
            restrictions=inherited.restrictions | {"no-copy"},
        )

        decision = evaluate_scope_promotion(promotion_proposal(), inherited, requested)

        self.assertEqual(decision.outcome, policy.ALLOW)
        self.assertEqual(decision.permitted_actions, ("retain_inherited_scope",))


if __name__ == "__main__":
    unittest.main()
