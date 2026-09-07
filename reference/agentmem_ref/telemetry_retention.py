"""Compatibility alias -- this module lives at ``agentmem_ref.memory.telemetry_retention``."""
import sys
from .memory import telemetry_retention as _real
sys.modules[__name__] = _real
