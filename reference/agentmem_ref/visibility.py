"""Compatibility alias -- this module lives at ``agentmem_ref.state.visibility``."""
import sys
from .state import visibility as _real
sys.modules[__name__] = _real
