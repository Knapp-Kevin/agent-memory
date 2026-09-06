"""Compatibility alias -- this module lives at ``agentmem_ref.memory.procedural_memory``."""
import sys
from .memory import procedural_memory as _real
sys.modules[__name__] = _real
