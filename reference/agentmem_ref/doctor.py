"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.doctor``."""
import sys
from .runtime import doctor as _real
sys.modules[__name__] = _real
