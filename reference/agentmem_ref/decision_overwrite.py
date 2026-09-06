"""Compatibility alias -- this module lives at ``agentmem_ref.memory.decision_overwrite``."""
import sys
from .memory import decision_overwrite as _real
sys.modules[__name__] = _real
