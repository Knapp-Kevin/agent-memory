"""Compatibility alias -- this module lives at ``agentmem_ref.memory.structural_mutation``."""
import sys
from .memory import structural_mutation as _real
sys.modules[__name__] = _real
