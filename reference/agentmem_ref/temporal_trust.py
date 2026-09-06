"""Compatibility alias -- this module lives at ``agentmem_ref.memory.temporal_trust``."""
import sys
from .memory import temporal_trust as _real
sys.modules[__name__] = _real
