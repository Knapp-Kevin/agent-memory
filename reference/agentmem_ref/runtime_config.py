"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.runtime_config``."""
import sys
from .runtime import runtime_config as _real
sys.modules[__name__] = _real
