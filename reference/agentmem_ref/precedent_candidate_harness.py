"""Compatibility alias -- this module lives at ``agentmem_ref.harness.precedent_candidate_harness``."""
import sys
from .harness import precedent_candidate_harness as _real
sys.modules[__name__] = _real
