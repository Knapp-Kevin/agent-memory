"""Compatibility alias -- this module lives at ``agentmem_ref.memory.enforcement_evidence``."""
import sys
from .memory import enforcement_evidence as _real
sys.modules[__name__] = _real
