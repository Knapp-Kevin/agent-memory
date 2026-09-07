"""Compatibility alias -- this module lives at ``agentmem_ref.memory.deletion_completeness``."""
import sys
from .memory import deletion_completeness as _real
sys.modules[__name__] = _real
