"""Compatibility alias -- this module lives at ``agentmem_ref.harness.authority_laundering_depth``."""
import sys
from .harness import authority_laundering_depth as _real
sys.modules[__name__] = _real
