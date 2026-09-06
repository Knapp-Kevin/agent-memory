"""Compatibility alias -- this module lives at ``agentmem_ref.harness.unsafe_composition_harness``."""
import sys
from .harness import unsafe_composition_harness as _real
sys.modules[__name__] = _real
