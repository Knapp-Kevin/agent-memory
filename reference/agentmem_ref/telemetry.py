"""Compatibility alias -- this module lives at ``agentmem_ref.memory.telemetry``."""
import sys
from .memory import telemetry as _real
sys.modules[__name__] = _real
