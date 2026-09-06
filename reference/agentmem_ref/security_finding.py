"""Compatibility alias -- this module lives at ``agentmem_ref.memory.security_finding``."""
import sys
from .memory import security_finding as _real
sys.modules[__name__] = _real
