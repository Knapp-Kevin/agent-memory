"""Compatibility alias -- this module lives at ``agentmem_ref.memory.crossing``."""
import sys
from .memory import crossing as _real
sys.modules[__name__] = _real
