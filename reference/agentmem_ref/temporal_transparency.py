"""Compatibility alias -- this module lives at ``agentmem_ref.memory.temporal_transparency``."""
import sys
from .memory import temporal_transparency as _real
sys.modules[__name__] = _real
