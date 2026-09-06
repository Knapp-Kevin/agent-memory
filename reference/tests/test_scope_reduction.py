"""Executable scope-reduction propagation evidence for issue #68."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agentmem_ref.scope_governance import (  # noqa: E402
    DerivedScope,
    SourceScope,
    derive_scope,
    reconcile_derived_scope,
)


class ScopeReductionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source_a = SourceScope(
            source_ref="mem:a",
            domain_refs=frozenset({"domain:shared", "domain:project-a"}),
            allowed_audiences=frozenset({"team:security", "agent:planner"}),
            allowed_purposes=frozenset({"security-review", "incident-response"}),
            restrictions=frozenset({"retain-provenance"}),
        )
        self.source_b = SourceScope(
            source_ref="mem:b",
            domain_refs=frozenset({"domain:shared", "domain:project-b"}),
            allowed_audiences=frozenset({"team:security", "agent:planner"}),
            allowed_purposes=frozenset({"security-review"}),
            restrictions=frozenset({"no-external-export"}),
        )
        self.original = derive_scope((self.source_a, self.source_b))

    def test_derived_state_becomes_non_current_when_source_scope_narrows(self):
        narrowed_a = SourceScope(
            source_ref="mem:a",
            domain_refs=self.source_a.domain_refs,
            allowed_audiences=frozenset({"team:security"}),
            allowed_purposes=frozenset({"security-review"}),
            restrictions=self.source_a.restrictions | {"no-agent-direct-use"},
        )

        result = reconcile_derived_scope(self.original, (narrowed_a, self.source_b))

        self.assertFalse(result.current_for_use)
        self.assertTrue(result.requires_narrowing)
        self.assertFalse(result.incompatible)
        self.assertEqual(result.reason, "derived_scope_exceeds_current_source_authority")
        self.assertEqual(result.inherited_scope.allowed_audiences, frozenset({"team:security"}))
        self.assertIn("no-agent-direct-use", result.inherited_scope.restrictions)

    def test_derived_state_stays_current_when_source_change_does_not_narrow_authority(self):
        equivalent_a = SourceScope(
            source_ref="mem:a",
            domain_refs=self.source_a.domain_refs,
            allowed_audiences=self.source_a.allowed_audiences,
            allowed_purposes=self.source_a.allowed_purposes,
            restrictions=self.source_a.restrictions,
        )

        result = reconcile_derived_scope(self.original, (equivalent_a, self.source_b))

        self.assertTrue(result.current_for_use)
        self.assertFalse(result.requires_narrowing)
        self.assertFalse(result.incompatible)

    def test_incompatible_source_scopes_fail_closed(self):
        isolated_b = SourceScope(
            source_ref="mem:b",
            domain_refs=frozenset({"domain:project-b-only"}),
            allowed_audiences=self.source_b.allowed_audiences,
            allowed_purposes=self.source_b.allowed_purposes,
            restrictions=self.source_b.restrictions,
        )

        result = reconcile_derived_scope(self.original, (self.source_a, isolated_b))

        self.assertFalse(result.current_for_use)
        self.assertTrue(result.incompatible)
        self.assertFalse(result.requires_narrowing)
        self.assertIn("no compatible intersection", result.reason)

    def test_changed_source_basis_does_not_reuse_old_derived_authority(self):
        replacement = SourceScope(
            source_ref="mem:c",
            domain_refs=frozenset({"domain:shared"}),
            allowed_audiences=frozenset({"team:security"}),
            allowed_purposes=frozenset({"security-review"}),
        )

        result = reconcile_derived_scope(self.original, (self.source_a, replacement))

        self.assertFalse(result.current_for_use)
        self.assertTrue(result.incompatible)
        self.assertEqual(result.reason, "source_basis_changed")

    def test_narrowed_copy_is_current_after_reconciliation(self):
        narrowed_a = SourceScope(
            source_ref="mem:a",
            domain_refs=self.source_a.domain_refs,
            allowed_audiences=frozenset({"team:security"}),
            allowed_purposes=frozenset({"security-review"}),
            restrictions=self.source_a.restrictions | {"no-agent-direct-use"},
        )
        inherited = derive_scope((narrowed_a, self.source_b))
        narrowed_copy = DerivedScope(
            source_refs=inherited.source_refs,
            domain_refs=inherited.domain_refs,
            allowed_audiences=inherited.allowed_audiences,
            allowed_purposes=inherited.allowed_purposes,
            restrictions=inherited.restrictions,
        )

        result = reconcile_derived_scope(narrowed_copy, (narrowed_a, self.source_b))

        self.assertTrue(result.current_for_use)
        self.assertFalse(result.requires_narrowing)


if __name__ == "__main__":
    unittest.main()
