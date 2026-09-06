"""Compatibility alias -- this module lives at ``agentmem_ref.memory.maintenance_run``."""
import sys
from .memory import maintenance_run as _real
sys.modules[__name__] = _real
