"""Compatibility alias -- this module lives at ``agentmem_ref.memory.temporal_commitment``."""
import sys
from .memory import temporal_commitment as _real
sys.modules[__name__] = _real
