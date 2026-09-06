"""Compatibility alias -- this module lives at ``agentmem_ref.harness.conditional_memory_harness``."""
import sys
from .harness import conditional_memory_harness as _real
sys.modules[__name__] = _real
