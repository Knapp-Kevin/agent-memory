"""Compatibility alias -- this module lives at ``agentmem_ref.harness.latent_predictive_state_harness``."""
import sys
from .harness import latent_predictive_state_harness as _real
sys.modules[__name__] = _real
