"""Compatibility alias -- this module lives at ``agentmem_ref.memory.enforcement_composition``."""
import sys
from .memory import enforcement_composition as _real
sys.modules[__name__] = _real
