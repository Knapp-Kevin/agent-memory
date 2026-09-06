"""GAP-ARCH-09: every docs/33 base-table cell must resolve as documented.

Transcribed from docs/33-pama-decision-table.md "Base decision table". The
table is the doctrine; this test is the binding between it and policy.py.
"""
import unittest

from agentmem_ref import policy

ALLOW = "allow_with_ledger"
REVIEW = "require_review"
EXTERNAL = "require_external_verification"
BLOCK = "block"

# operation -> (low, medium, high, critical), verbatim from docs/33:80-93
# plus domain_schema_mutation, which ADR-032 introduced after that table was
# written and which the plan adds to docs/33 in this cycle.
DOCTRINE = {
    "runtime_assembly": (ALLOW, ALLOW, REVIEW, REVIEW),
    "score_adjustment": (ALLOW, ALLOW, REVIEW, BLOCK),
    "link_creation": (ALLOW, ALLOW, REVIEW, REVIEW),
    "link_deletion": (ALLOW, REVIEW, REVIEW, EXTERNAL),
    "correction": (REVIEW, REVIEW, REVIEW, EXTERNAL),
    "decision_overwrite": (REVIEW, REVIEW, EXTERNAL, EXTERNAL),
    "domain_schema_mutation": (REVIEW, REVIEW, EXTERNAL, EXTERNAL),
    "promotion": (ALLOW, REVIEW, REVIEW, EXTERNAL),
    "crystallization": (REVIEW, REVIEW, EXTERNAL, EXTERNAL),
    "pruning": (ALLOW, ALLOW, REVIEW, EXTERNAL),
    "permanent_deletion": (REVIEW, REVIEW, EXTERNAL, EXTERNAL),
    "scope_expansion": (REVIEW, REVIEW, EXTERNAL, BLOCK),
    "policy_mutation": (REVIEW, EXTERNAL, EXTERNAL, EXTERNAL),
}
RISKS = ("low", "medium", "high", "critical")

# Enum members with no base cell by decision (LD4): they resolve through the
# conservative fallback rather than being enumerated.
FALLBACK_ONLY = ("capability_promotion", "authority_change", "other")


def _proposal(operation, risk_class):
    """A proposal carrying no floor or modifier, so the base cell is visible."""
    return policy.Proposal(
        proposal_id=f"p-{operation}-{risk_class}",
        actor_id="agent:a",
        charter_version="v1",
        target_reference="mem:1",
        target_class=policy.M1,
        scope="tenant-A",
        operation=operation,
        current_strength="observed",
        proposed_strength="tentative",
        downstream_authority=policy.A1,
        reversibility="reversible",
        risk_class=risk_class,
        evidence_refs=("ep-1",),
        tenant_ref="tenant-A",
        isolation_domain_refs=("tenant-A",),
    )


class DecisionTableDoctrineTest(unittest.TestCase):
    def test_every_documented_cell_resolves_as_documented(self):
        checked = 0
        for operation, outcomes in DOCTRINE.items():
            for risk_class, expected in zip(RISKS, outcomes):
                with self.subTest(operation=operation, risk_class=risk_class):
                    decision = policy.evaluate(_proposal(operation, risk_class))
                    self.assertEqual(
                        expected,
                        decision.outcome,
                        f"{operation}/{risk_class}: docs/33 says {expected}",
                    )
                checked += 1
        self.assertEqual(52, checked, "13 operations x 4 risk classes")

    def test_score_adjustment_critical_blocks(self):
        """Previously resolved require_review via the fallback -- weaker than
        doctrine's `block`."""
        self.assertEqual(
            BLOCK, policy.evaluate(_proposal("score_adjustment", "critical")).outcome
        )

    def test_link_deletion_critical_requires_external_verification(self):
        """The second previously-weaker cell."""
        self.assertEqual(
            EXTERNAL, policy.evaluate(_proposal("link_deletion", "critical")).outcome
        )

    def test_unknown_operations_keep_the_conservative_fallback(self):
        """LD4: removing the fallback would turn an unknown operation into a
        KeyError on the authority path."""
        for operation in FALLBACK_ONLY + ("not_a_real_operation",):
            with self.subTest(operation=operation):
                outcome = policy.evaluate(_proposal(operation, "low")).outcome
                self.assertEqual(REVIEW, outcome)


if __name__ == "__main__":
    unittest.main()
