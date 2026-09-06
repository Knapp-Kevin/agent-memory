"""Compatibility alias -- this module lives at ``agentmem_ref.harness.derivation_currentness_harness``."""
import sys
from .harness import derivation_currentness_harness as _real
sys.modules[__name__] = _real
