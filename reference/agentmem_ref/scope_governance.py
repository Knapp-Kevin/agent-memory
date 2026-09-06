"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.scope_governance``."""
import sys
from .runtime import scope_governance as _real
sys.modules[__name__] = _real
