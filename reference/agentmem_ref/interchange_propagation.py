"""Compatibility alias -- this module lives at ``agentmem_ref.memory.interchange_propagation``."""
import sys
from .memory import interchange_propagation as _real
sys.modules[__name__] = _real
