"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.runtime_composition``."""
import sys
from .runtime import runtime_composition as _real
sys.modules[__name__] = _real
