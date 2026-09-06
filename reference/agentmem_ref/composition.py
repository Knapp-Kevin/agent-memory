"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.composition``."""
import sys
from .runtime import composition as _real
sys.modules[__name__] = _real
