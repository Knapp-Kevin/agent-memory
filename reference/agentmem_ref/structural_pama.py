"""Compatibility alias -- this module lives at ``agentmem_ref.memory.structural_pama``."""
import sys
from .memory import structural_pama as _real
sys.modules[__name__] = _real
