"""Compatibility alias -- this module lives at ``agentmem_ref.memory.a2a_collaboration``."""
import sys
from .memory import a2a_collaboration as _real
sys.modules[__name__] = _real
