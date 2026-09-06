"""Compatibility alias -- this module lives at ``agentmem_ref.runtime.configured_restart``."""
import sys
from .runtime import configured_restart as _real
sys.modules[__name__] = _real
