"""Compatibility alias -- this module lives at ``agentmem_ref.memory.interchange``."""
import sys
from .memory import interchange as _real
sys.modules[__name__] = _real
