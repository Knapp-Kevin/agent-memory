"""Compatibility alias -- this module lives at ``agentmem_ref.memory.approval_evidence``."""
import sys
from .memory import approval_evidence as _real
sys.modules[__name__] = _real
