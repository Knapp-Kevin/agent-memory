"""Compatibility alias -- this module lives at ``agentmem_ref.core.policy``."""
import sys
from .core import policy as _real
sys.modules[__name__] = _real
