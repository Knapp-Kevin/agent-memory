"""Compatibility alias -- this module lives at ``agentmem_ref.memory.evolveai_cognitive_mesh``."""
import sys
from .memory import evolveai_cognitive_mesh as _real
sys.modules[__name__] = _real
