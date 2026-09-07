"""Compatibility alias -- this module lives at ``agentmem_ref.core.resumption``."""
import sys
from .core import resumption as _real
sys.modules[__name__] = _real
