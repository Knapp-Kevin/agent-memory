"""Compatibility alias -- this module lives at ``agentmem_ref.memory.conditional_memory_influence``."""
import sys
from .memory import conditional_memory_influence as _real
sys.modules[__name__] = _real
