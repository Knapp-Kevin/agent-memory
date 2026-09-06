"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.runtime_behavior``."""
import sys
from .runtime import runtime_behavior as _real
sys.modules[__name__] = _real
