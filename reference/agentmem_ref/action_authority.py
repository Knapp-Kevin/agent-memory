"""Compatibility alias -- this module lives at ``agentmem_ref.memory.action_authority``."""
import sys
from .memory import action_authority as _real
sys.modules[__name__] = _real
