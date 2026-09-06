"""Compatibility alias -- this module lives at ``agentmem_ref.memory.mcp_interaction``."""
import sys
from .memory import mcp_interaction as _real
sys.modules[__name__] = _real
