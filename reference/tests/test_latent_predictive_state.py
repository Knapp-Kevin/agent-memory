"""Representation-neutral latent predictive-state tests for issue #137."""

from __future__ import annotations

import unittest

from agentmem_ref.latent_predictive_state_harness import run_latent_predictive_state_harness


class LatentPredictiveStateTests(unittest.TestCase):
    def test_pressure_test_passes(self):
        result = run_latent_predictive_state_harness()
        self.assertTrue(result["passed"], result)
        self.assertTrue(result["checks"]["opaque_probabilistic_derivation_representable"])
        self.assertTrue(result["checks"]["revocation_requires_revalidation"])
        self.assertTrue(result["checks"]["deletion_requires_revalidation"])
        self.assertTrue(result["checks"]["scope_reduction_requires_revalidation"])
        self.assertTrue(result["checks"]["prediction_quality_does_not_restore_currentness"])
        self.assertTrue(result["checks"]["planning_influence_separate_from_action_authority"])
        self.assertTrue(result["checks"]["historical_derivation_unchanged"])
        self.assertFalse(result["interpretation"]["jepa_implemented"])
        self.assertEqual(result["interpretation"]["capability_superiority_claim"], "not_established")


if __name__ == "__main__":
    unittest.main()
