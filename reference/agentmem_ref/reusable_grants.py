"""Compatibility alias -- this module lives at ``agentmem_ref.memory.reusable_grants``."""
import sys
from .memory import reusable_grants as _real
sys.modules[__name__] = _real
