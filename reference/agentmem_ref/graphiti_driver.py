"""Compatibility alias -- this module lives at ``agentmem_ref.state.graphiti_driver``."""
import sys
from .state import graphiti_driver as _real
sys.modules[__name__] = _real
