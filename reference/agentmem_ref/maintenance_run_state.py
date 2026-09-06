"""Compatibility alias -- this module lives at ``agentmem_ref.memory.maintenance_run_state``."""
import sys
from .memory import maintenance_run_state as _real
sys.modules[__name__] = _real
