"""Compatibility alias -- this module lives at ``agentmem_ref.memory.external_evidence``."""
import sys
from .memory import external_evidence as _real
sys.modules[__name__] = _real
