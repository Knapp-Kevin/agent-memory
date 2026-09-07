"""Compatibility alias -- this module lives at ``agentmem_ref.state.projections``."""
import sys
from .state import projections as _real
sys.modules[__name__] = _real
