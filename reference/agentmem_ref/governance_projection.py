"""Compatibility alias -- this module lives at ``agentmem_ref.core.governance_projection``."""
import sys
from .core import governance_projection as _real
sys.modules[__name__] = _real
