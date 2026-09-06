"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.projection_governance``."""
import sys
from .runtime import projection_governance as _real
sys.modules[__name__] = _real
