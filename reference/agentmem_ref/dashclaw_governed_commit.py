"""Compatibility alias -- this module lives at ``agentmem_ref.memory.dashclaw_governed_commit``."""
import sys
from .memory import dashclaw_governed_commit as _real
sys.modules[__name__] = _real
