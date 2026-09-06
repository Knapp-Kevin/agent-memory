"""Compatibility alias -- this module lives at ``agentmem_ref.memory.derivation_evidence``."""
import sys
from .memory import derivation_evidence as _real
sys.modules[__name__] = _real
