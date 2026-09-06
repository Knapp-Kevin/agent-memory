"""Compatibility alias -- this module lives at ``agentmem_ref.memory.trace_action_evidence``."""
import sys
from .memory import trace_action_evidence as _real
sys.modules[__name__] = _real
