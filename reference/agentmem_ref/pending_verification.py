"""Compatibility alias -- this module lives at ``agentmem_ref.core.pending_verification``."""
import sys
from .core import pending_verification as _real
sys.modules[__name__] = _real
