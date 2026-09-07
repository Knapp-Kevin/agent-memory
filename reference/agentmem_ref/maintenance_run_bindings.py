"""Compatibility alias -- this module lives at ``agentmem_ref.memory.maintenance_run_bindings``."""
import sys
from .memory import maintenance_run_bindings as _real
sys.modules[__name__] = _real
