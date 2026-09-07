"""Compatibility alias -- this module lives at ``agentmem_ref.memory.runtime_trace_correlation``."""
import sys
from .memory import runtime_trace_correlation as _real
sys.modules[__name__] = _real
