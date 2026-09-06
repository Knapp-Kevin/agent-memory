"""Compatibility alias -- this module lives at ``agentmem_ref.memory.cognitive_mesh``."""
import sys
from .memory import cognitive_mesh as _real
sys.modules[__name__] = _real
