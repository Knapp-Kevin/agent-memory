"""Compatibility alias -- this module lives at ``agentmem_ref.memory.predictive_memory``."""
import sys
from .memory import predictive_memory as _real
sys.modules[__name__] = _real
