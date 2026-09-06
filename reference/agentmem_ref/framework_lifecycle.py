"""Compatibility alias -- this module lives at ``agentmem_ref.memory.framework_lifecycle``."""
import sys
from .memory import framework_lifecycle as _real
sys.modules[__name__] = _real
