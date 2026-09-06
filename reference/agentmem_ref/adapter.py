"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.adapter``."""
import sys
from .runtime import adapter as _real
sys.modules[__name__] = _real
