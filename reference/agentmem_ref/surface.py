"""Compatibility alias -- this module lives at ``agentmem_ref.api.surface``."""
import sys
from .api import surface as _real
sys.modules[__name__] = _real
