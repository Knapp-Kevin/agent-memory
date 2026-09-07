"""Compatibility alias -- this module lives at ``agentmem_ref.api.contract``."""
import sys
from .api import contract as _real
sys.modules[__name__] = _real
