"""Compatibility alias -- this module lives at ``agentmem_ref.memory.epistemic_memory``."""
import sys
from .memory import epistemic_memory as _real
sys.modules[__name__] = _real
