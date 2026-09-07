"""Compatibility alias -- this module lives at ``agentmem_ref.contracts.component_fallback``."""
import sys
from .contracts import component_fallback as _real
sys.modules[__name__] = _real
