"""Compatibility alias -- this module lives at ``agentmem_ref.contracts.capabilities``."""
import sys
from .contracts import capabilities as _real
sys.modules[__name__] = _real
