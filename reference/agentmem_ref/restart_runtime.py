"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.restart_runtime``."""
import sys
from .runtime import restart_runtime as _real
sys.modules[__name__] = _real
