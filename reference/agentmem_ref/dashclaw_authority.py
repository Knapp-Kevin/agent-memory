"""Compatibility alias -- this module lives at ``agentmem_ref.memory.dashclaw_authority``."""
import sys
from .memory import dashclaw_authority as _real
sys.modules[__name__] = _real
