"""Compatibility alias -- this module lives at ``agentmem_ref.memory.dashclaw_external_verdict``."""
import sys
from .memory import dashclaw_external_verdict as _real
sys.modules[__name__] = _real
