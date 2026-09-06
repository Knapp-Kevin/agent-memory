"""Compatibility alias -- this module lives at ``agentmem_ref.memory.derivation_currentness``."""
import sys
from .memory import derivation_currentness as _real
sys.modules[__name__] = _real
