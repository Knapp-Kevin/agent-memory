"""Compatibility alias -- this module lives at ``agentmem_ref.memory.policy_projection_compatibility``."""
import sys
from .memory import policy_projection_compatibility as _real
sys.modules[__name__] = _real
