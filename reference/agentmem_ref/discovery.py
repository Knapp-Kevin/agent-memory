"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.discovery``."""
import sys
from .runtime import discovery as _real
sys.modules[__name__] = _real
