"""Compatibility alias -- this module lives at ``agentmem_ref.memory.precedent_applicability``."""
import sys
from .memory import precedent_applicability as _real
sys.modules[__name__] = _real
